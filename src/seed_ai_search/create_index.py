"""Seed script: build the Azure AI Search index.

This module owns everything related to building the Azure AI Search index:
blob upload, data source, index, skillset and indexer creation, plus running
and polling the indexer. Run it once at startup to seed the data and index::

    uv run python create_index.py

The ``agents`` project does not import from this module; it consumes the
resulting index through the same environment variables.
"""

import asyncio
import json
import logging
import os
import re
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path

import aiohttp
from azure.core.exceptions import HttpResponseError, ResourceExistsError
from azure.identity.aio import DefaultAzureCredential
from azure.search.documents.indexes.aio import SearchIndexClient, SearchIndexerClient
from azure.search.documents.indexes.models import (
    IndexerExecutionResult,
    SearchIndexer,
    SearchIndexerSkillset,
    SearchIndexerStatus,
)
from azure.storage.filedatalake.aio import DataLakeServiceClient
from dotenv import load_dotenv

# Load configuration from a local ``.env`` file (when present) into
# ``os.environ`` so the variables below are read the same way locally and in
# the cloud.
load_dotenv()

logger = logging.getLogger(__name__)


def get_required_env(name: str) -> str:
    """Return the environment variable ``name`` or raise if it is missing."""
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable '{name}'.")
    return value


API_VERSION = os.environ.get("API_VERSION", "2025-11-01-preview")
# Microsoft Entra scope used to call the Azure AI Search data/management plane.
SEARCH_TOKEN_SCOPE = "https://search.azure.com/.default"

# --- Azure AI Search ---
SEARCH_ENDPOINT = get_required_env("SEARCH_ENDPOINT")

# --- Blob storage (data source) ---
BLOB_ACCOUNT_URL = get_required_env("BLOB_ACCOUNT_URL")
BLOB_CONTAINER_NAME = get_required_env("BLOB_CONTAINER_NAME")
BLOB_DATASOURCE_CONNECTION_STRING = get_required_env(
    "BLOB_DATASOURCE_CONNECTION_STRING"
)
LOCAL_DATA_DIR = os.environ.get("LOCAL_DATA_DIR", "documents")

# --- Document-level access control (POSIX ACL ingestion) ---
# Documents are organised in two folders that map to two Microsoft Entra groups:
#   * ``RESTRICTED_FOLDER`` -> ``RESTRICTED_DOCS_GROUP_ID`` (a subset of
#     participants, e.g. project managers).
#   * every other folder    -> ``ALL_PARTICIPANTS_GROUP_ID`` (every participant).
# The AI Search indexer computes the *effective* access of each named group by
# walking the ADLS Gen2 hierarchy (container root -> folder -> file). A group is
# only recorded as having access to a file when it has Execute (traverse) on
# every parent directory AND Read on the file, so we grant ``r-x`` on the root
# and folders and ``r--`` on the files. ADLS Gen2 has no "everyone/other" ACL
# category that the indexer honours, which is why "public" content is expressed
# through the all-participants group rather than an empty ACL.
RESTRICTED_DOCS_GROUP_ID = get_required_env("RESTRICTED_DOCS_GROUP_ID")
ALL_PARTICIPANTS_GROUP_ID = get_required_env("ALL_PARTICIPANTS_GROUP_ID")
RESTRICTED_FOLDER = "restricted"
# ADLS Gen2 (Data Lake) endpoint, derived from the blob endpoint.
ADLS_ACCOUNT_URL = BLOB_ACCOUNT_URL.replace(".blob.", ".dfs.")

# --- Azure OpenAI (embeddings) ---
AOAI_ENDPOINT = get_required_env("AOAI_ENDPOINT")
EMBEDDING_DEPLOYMENT = get_required_env("EMBEDDING_DEPLOYMENT")
EMBEDDING_DIMENSIONS = int(os.environ.get("EMBEDDING_DIMENSIONS", "3072"))

# --- Object names ---
KNOWLEDGE_SOURCE_NAME = get_required_env("AI_SEARCH_KNOWLEDGE_BASE_NAME")

DATA_SOURCE_NAME = f"{KNOWLEDGE_SOURCE_NAME}-datasource"
INDEX_NAME = f"{KNOWLEDGE_SOURCE_NAME}-index"
SKILLSET_NAME = f"{KNOWLEDGE_SOURCE_NAME}-skillset"
INDEXER_NAME = f"{KNOWLEDGE_SOURCE_NAME}-indexer"
SEMANTIC_CONFIGURATION_NAME = f"{KNOWLEDGE_SOURCE_NAME}-semantic-configuration"

INDEXER_POLL_INTERVAL_MS = int(os.environ.get("INDEXER_POLL_INTERVAL_MS", "5000"))
INDEXER_POLL_ATTEMPTS = int(os.environ.get("INDEXER_POLL_ATTEMPTS", "120"))

# ``reset_indexer`` returns before the reset is fully applied, so an immediate
# ``run_indexer`` can briefly fail with HTTP 409. Retry the start a few times
# instead of pausing for an arbitrary fixed delay.
RESET_RUN_MAX_ATTEMPTS = 5
RESET_RUN_RETRY_INTERVAL_MS = 1000

# Statuses that mean an indexer execution has finished an indexing run.
TERMINAL_EXECUTION_STATUSES = ("success", "transientFailure")
# Tolerance applied when matching an execution to the run we triggered, to
# absorb minor clock skew between this client and the search service.
RUN_MATCH_TOLERANCE = timedelta(seconds=30)

# Directory that holds the AI Search JSON templates (data source, index,
# skillset, indexer). Lives in ``data``.
TEMPLATE_DIR = Path(__file__).resolve().parent / "data"

# Values substituted into the ${VAR} placeholders of the JSON templates.
TEMPLATE_VARIABLES: dict[str, str] = {
    "KS_NAME": KNOWLEDGE_SOURCE_NAME,
    "BLOB_CONTAINER_NAME": BLOB_CONTAINER_NAME,
    "BLOB_DATASOURCE_CONNECTION_STRING": BLOB_DATASOURCE_CONNECTION_STRING,
    "AOAI_ENDPOINT": AOAI_ENDPOINT,
    "EMBEDDING_DEPLOYMENT": EMBEDDING_DEPLOYMENT,
    "EMBEDDING_DIMENSIONS": str(EMBEDDING_DIMENSIONS),
}

# A single async credential is shared by every client. ``DefaultAzureCredential``
# tries several sources in order (environment, managed identity, Azure CLI, ...).
credential = DefaultAzureCredential()
# ``index_client`` manages indexes/knowledge sources, ``indexer_client`` manages
# data sources, skillsets and indexers. Both are async clients and are closed in
# ``create_search_index`` once the pipeline finishes.
index_client = SearchIndexClient(SEARCH_ENDPOINT, credential, api_version=API_VERSION)
indexer_client = SearchIndexerClient(
    SEARCH_ENDPOINT, credential, api_version=API_VERSION
)


async def create_search_index() -> None:
    """Build the blob -> Azure AI Search index pipeline end to end.

    Uploads the local documents, applies the data source, index, skillset and
    indexer, then resets and runs the indexer.
    """
    logger.info("🚀 Building Azure AI Search index ...")
    print(f"Search service : {SEARCH_ENDPOINT}")
    print(f"Index          : {INDEX_NAME}")

    try:
        # 1. Upload the local documents to ADLS Gen2 and apply POSIX ACLs so the
        #    indexer can ingest per-document permissions.
        print("\nUploading documents to ADLS Gen2 and applying ACLs...")
        await upload_documents_and_apply_acls()

        # 2. Declare the four AI Search objects from the JSON templates:
        #    data source (where to read), index (target schema), skillset
        #    (chunking + embeddings) and indexer (the pipeline tying them).
        print("\nApplying data source, index, skillset and indexer...")
        await apply_data_source()
        await apply_index()
        await apply_skillset()
        await apply_indexer()

        # 3. Reset clears the indexer's bookkeeping so every document is
        #    re-ingested, then we run it and wait until the run completes.
        print(f"\nResetting and running indexer '{INDEXER_NAME}'...")
        run_requested_at = await reset_and_run_indexer()
        print("Waiting for indexer completion...")
        await wait_for_indexer(run_requested_at)

        print(f"\nAzure AI Search index '{INDEX_NAME}' is ready.")
    finally:
        # Async SDK clients hold network sessions that must be closed explicitly.
        await index_client.close()
        await indexer_client.close()
        await credential.close()


def _file_acl(group_id: str) -> str:
    """Build a POSIX access ACL granting read on a file to a named group.

    The base entries (owner / owning-group / other) are always present. A
    ``mask`` entry is required whenever a named entry exists; it caps the
    effective rights of the named group at read-only.
    """
    return f"user::rw-,group::r--,group:{group_id}:r--,mask::r--,other::---"


def _dir_acl(group_ids: Sequence[str]) -> str:
    """Build a POSIX access ACL granting traverse (read+execute) on a directory.

    Named groups need Execute on every parent directory for the indexer to
    resolve their effective read access on the files underneath. The ``mask`` is
    set to ``r-x`` so the named group entries keep their read+execute rights.
    """
    named = ",".join(f"group:{group_id}:r-x" for group_id in group_ids)
    return f"user::rwx,group::r-x,{named},mask::r-x,other::---"


def _group_for_path(relative: Path) -> str:
    """Return the Entra group allowed to read the document at ``relative``.

    Files under ``RESTRICTED_FOLDER`` are limited to ``RESTRICTED_DOCS_GROUP_ID``;
    every other file is readable by ``ALL_PARTICIPANTS_GROUP_ID`` (all
    participants).
    """
    top_folder = relative.parts[0] if len(relative.parts) > 1 else ""
    if top_folder == RESTRICTED_FOLDER:
        return RESTRICTED_DOCS_GROUP_ID
    return ALL_PARTICIPANTS_GROUP_ID


async def upload_documents_and_apply_acls() -> None:
    """Upload local documents to ADLS Gen2 and apply per-folder POSIX ACLs.

    Each document is tagged with the named ACL of the Entra group allowed to
    read it (restricted folder -> restricted group, everything else -> all
    participants). The container root and every folder also grant those groups
    Execute (traverse) so the Azure AI Search indexer can resolve each group's
    *effective* read access while walking the hierarchy and write it as the
    document's permission metadata. The search service still indexes every file
    because it reads through its Storage Blob Data Reader role, which bypasses
    ACLs.
    """
    documents_dir = resolve_documents_dir()
    if not documents_dir.is_dir():
        raise RuntimeError(
            f"Local data directory '{documents_dir}' does not exist or is "
            "not a directory."
        )

    async with DataLakeServiceClient(ADLS_ACCOUNT_URL, credential) as service:
        file_system = service.get_file_system_client(BLOB_CONTAINER_NAME)
        try:
            await file_system.create_file_system()
            print(f"Filesystem '{BLOB_CONTAINER_NAME}' created.")
        except ResourceExistsError:
            print(f"Filesystem '{BLOB_CONTAINER_NAME}' already exists.")

        # Grant every group traverse (read+execute) on the container root so the
        # indexer's hierarchical evaluation can reach the files in each subtree.
        root_directory = file_system._get_root_directory_client()
        await root_directory.set_access_control(
            acl=_dir_acl([ALL_PARTICIPANTS_GROUP_ID, RESTRICTED_DOCS_GROUP_ID])
        )
        print("  - root '/' ACL set (traverse for all groups)")

        created_dirs: set[str] = set()
        local_files = sorted(p for p in documents_dir.rglob("*") if p.is_file())
        for file_path in local_files:
            relative = file_path.relative_to(documents_dir)
            relative_posix = relative.as_posix()
            group_id = _group_for_path(relative)

            # Recreate the parent directory hierarchy (HNS requires it before a
            # file can be created at a nested path) and grant the document's
            # group traverse on that directory.
            parent = relative.parent.as_posix()
            if parent not in (".", "") and parent not in created_dirs:
                directory_client = file_system.get_directory_client(parent)
                try:
                    await directory_client.create_directory()
                except ResourceExistsError:
                    pass
                await directory_client.set_access_control(acl=_dir_acl([group_id]))
                created_dirs.add(parent)

            file_client = file_system.get_file_client(relative_posix)
            # ``overwrite=True`` is required: with ``overwrite=False`` the SDK
            # skips the create call and appends to a non-existent path. Re-seeding
            # simply overwrites the file content, which is idempotent.
            await file_client.upload_data(file_path.read_bytes(), overwrite=True)
            await file_client.set_access_control(acl=_file_acl(group_id))
            print(f"  - uploaded: {relative_posix} -> group {group_id}")


# The four ``apply_*`` helpers each load a JSON template from ``data/``, fill in
# its ${VAR} placeholders and create-or-update the matching AI Search object.
# They are idempotent: running them again simply updates the existing object.
#
# The data source and index are sent with a raw REST PUT because they carry
# preview-only keys (``indexerPermissionOptions``, ``permissionFilter``,
# ``permissionFilterOption``) that the stable SDK models silently drop.
async def _search_rest_put(resource_path: str, body: dict, *, query: str = "") -> None:
    """PUT a JSON object to the Azure AI Search management plane via REST."""
    token = (await credential.get_token(SEARCH_TOKEN_SCOPE)).token
    url = f"{SEARCH_ENDPOINT}/{resource_path}?api-version={API_VERSION}{query}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    async with aiohttp.ClientSession() as session:
        async with session.put(url, headers=headers, json=body) as response:
            if response.status not in (200, 201, 204):
                detail = await response.text()
                raise RuntimeError(
                    f"PUT {resource_path} failed with HTTP {response.status}: {detail}"
                )


async def _search_rest_delete(resource_path: str) -> None:
    """DELETE an Azure AI Search object via REST (ignores 404)."""
    token = (await credential.get_token(SEARCH_TOKEN_SCOPE)).token
    url = f"{SEARCH_ENDPOINT}/{resource_path}?api-version={API_VERSION}"
    headers = {"Authorization": f"Bearer {token}"}
    async with aiohttp.ClientSession() as session:
        async with session.delete(url, headers=headers) as response:
            if response.status not in (204, 404):
                detail = await response.text()
                raise RuntimeError(
                    f"DELETE {resource_path} failed with HTTP "
                    f"{response.status}: {detail}"
                )


async def apply_data_source() -> None:
    """Render the data source template and create/update it via REST."""
    # The data source tells the indexer which ADLS Gen2 account/container to read
    # and that it must ingest user/group permission metadata. The data source
    # ``type`` is immutable, so an existing ``azureblob`` data source must be
    # deleted before it can be recreated as ``adlsgen2``. The indexer is deleted
    # first because it holds change-tracking state tied to the old data source
    # (it is recreated from its template by ``apply_indexer``).
    await _search_rest_delete(f"indexers/{INDEXER_NAME}")
    await _search_rest_delete(f"datasources/{DATA_SOURCE_NAME}")
    body = render_template("blob-datasource.json")
    await _search_rest_put(f"datasources/{DATA_SOURCE_NAME}", body)
    print(f"datasources/{DATA_SOURCE_NAME} updated.")


async def apply_index() -> None:
    """Render the index template and create/update it via REST."""
    # The index defines the target schema (fields, vector + semantic config) plus
    # the permission filter fields. ``allowIndexDowntime`` lets the permission
    # settings be enabled on an existing index.
    body = render_template("blob-index.json")
    await _search_rest_put(
        f"indexes/{INDEX_NAME}", body, query="&allowIndexDowntime=true"
    )
    print(f"indexes/{INDEX_NAME} updated.")


async def apply_skillset() -> None:
    """Render the skillset template and create/update it via the SDK."""
    # The skillset enriches documents during indexing (e.g. split into chunks
    # and generate embeddings via the Azure OpenAI deployment).
    body = render_template("blob-skillset.json")
    await indexer_client.create_or_update_skillset(SearchIndexerSkillset(body))
    print(f"skillsets/{SKILLSET_NAME} updated.")


async def apply_indexer() -> None:
    """Render the indexer template and create/update it via the SDK."""
    # The indexer ties data source + skillset + index together and performs the
    # actual ingestion when triggered.
    body = render_template("blob-indexer.json")
    await indexer_client.create_or_update_indexer(SearchIndexer(body))
    print(f"indexers/{INDEXER_NAME} updated.")


async def reset_and_run_indexer() -> datetime | None:
    """Reset indexer state and start a fresh execution.

    Returns the UTC time marker used later to identify the completion record
    that belongs to this specific run, or ``None`` when an execution is
    already in progress.
    """
    status = await indexer_client.get_indexer_status(INDEXER_NAME)
    # If a run is already in progress, don't start a competing one; let the
    # caller wait for the existing execution instead.
    if get_active_execution(status) is not None:
        print(
            f"Indexer '{INDEXER_NAME}' is already running. Waiting for the "
            "active invocation to finish."
        )
        return None

    # Reset clears the change-tracking state so the next run reprocesses
    # everything from scratch.
    await indexer_client.reset_indexer(INDEXER_NAME)

    if not await start_indexer_after_reset():
        return None

    # Record when we triggered the run so ``wait_for_indexer`` can later match
    # the correct execution record.
    print(f"Indexer '{INDEXER_NAME}' triggered.")
    return datetime.now(timezone.utc)


async def start_indexer_after_reset() -> bool:
    """Start the indexer once the reset has been applied.

    ``reset_indexer`` returns as soon as the request is accepted (HTTP 204),
    before the reset is fully propagated, so an immediate ``run_indexer`` can
    briefly fail with HTTP 409. Retry the start while the service still reports
    that transient conflict instead of pausing for a fixed amount of time.
    Returns ``False`` when another run is already in progress.
    """
    for attempt in range(1, RESET_RUN_MAX_ATTEMPTS + 1):
        try:
            await indexer_client.run_indexer(INDEXER_NAME)
            return True
        except HttpResponseError as error:
            if error.status_code != 409:
                raise
            status = await indexer_client.get_indexer_status(INDEXER_NAME)
            if get_active_execution(status) is not None:
                print(
                    f"Indexer '{INDEXER_NAME}' is already running elsewhere. "
                    "Waiting for the active invocation to finish."
                )
                return False
            if attempt == RESET_RUN_MAX_ATTEMPTS:
                raise
            await asyncio.sleep(RESET_RUN_RETRY_INTERVAL_MS / 1000)
    return False


async def wait_for_indexer(run_requested_at: datetime | None) -> None:
    """Poll the indexer status until the triggered run succeeds or fails."""
    for attempt in range(1, INDEXER_POLL_ATTEMPTS + 1):
        status = await indexer_client.get_indexer_status(INDEXER_NAME)

        overall_status = status.status or "unknown"
        active_execution = get_active_execution(status)
        # Pick which execution record represents "our" run:
        #  - if we triggered it, match the one started around that time;
        #  - if another run is active, keep waiting (no completed record yet);
        #  - otherwise fall back to the most recent finished execution.
        if run_requested_at is not None:
            completed_execution = find_completed_execution(status, run_requested_at)
        elif active_execution is not None:
            completed_execution = None
        else:
            completed_execution = find_latest_completed_execution(status)

        if completed_execution is not None:
            execution_status = completed_execution.status or overall_status
            # Treat the run as successful only when it succeeded with zero failed
            # items and no item-level errors.
            if (
                execution_status == "success"
                and (completed_execution.failed_item_count or 0) == 0
                and len(completed_execution.errors or []) == 0
            ):
                print(
                    f"Indexer completed with status '{execution_status}' "
                    f"(processed {completed_execution.item_count or 0} "
                    "item(s))."
                )
                return

            raise RuntimeError(
                format_indexer_failure(
                    INDEXER_NAME, execution_status, completed_execution
                )
            )

        if active_execution is not None:
            processed = active_execution.item_count or 0
            print(
                f"Indexer execution status: "
                f"{active_execution.status or 'inProgress'}, processed "
                f"{processed} item(s) ({attempt}/{INDEXER_POLL_ATTEMPTS}). "
                f"Overall indexer status: {overall_status}."
            )
        else:
            print(
                f"Indexer overall status: {overall_status}, latest execution "
                f"not available yet ({attempt}/{INDEXER_POLL_ATTEMPTS})."
            )

        await asyncio.sleep(INDEXER_POLL_INTERVAL_MS / 1000)

    raise RuntimeError(f"Indexer '{INDEXER_NAME}' did not finish in time.")


def render_template(template_file: str) -> dict:
    """Load a JSON template from ``TEMPLATE_DIR`` and substitute ${VAR}."""
    template_path = TEMPLATE_DIR / template_file
    template = template_path.read_text(encoding="utf-8")

    # Called for every ${VAR} match; fails fast if a placeholder has no value.
    def replace(match: re.Match[str]) -> str:
        variable_name = match.group(1)
        if variable_name not in TEMPLATE_VARIABLES:
            raise RuntimeError(
                f"Missing template variable '{variable_name}' for {template_file}."
            )
        return TEMPLATE_VARIABLES[variable_name]

    # Replace every ${UPPER_CASE} placeholder, then parse the result as JSON.
    rendered = re.sub(r"\$\{([A-Z0-9_]+)\}", replace, template)
    return json.loads(rendered)


def resolve_documents_dir() -> Path:
    """Resolve ``LOCAL_DATA_DIR`` to an absolute path (relative to this script)."""
    path = Path(LOCAL_DATA_DIR)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path
    return path.resolve()


def _executions(status: SearchIndexerStatus) -> list[IndexerExecutionResult]:
    """Return indexer executions, most recent first."""
    # Prefer the full history; fall back to the single last result, or nothing.
    if status.execution_history:
        return list(status.execution_history)
    if status.last_result is not None:
        return [status.last_result]
    return []


def get_active_execution(
    status: SearchIndexerStatus,
) -> IndexerExecutionResult | None:
    """Return the currently in-progress execution, if any."""
    for execution in _executions(status):
        if (execution.status or "") == "inProgress":
            return execution
    return None


def find_completed_execution(
    status: SearchIndexerStatus, run_requested_at: datetime
) -> IndexerExecutionResult | None:
    """Return the finished execution that belongs to the triggered run."""
    for execution in _executions(status):
        # Skip executions that haven't reached a terminal state yet.
        if (execution.status or "") not in TERMINAL_EXECUTION_STATUSES:
            continue
        start_time = execution.start_time
        if start_time is None:
            continue
        # Match by start time (minus a tolerance for clock skew) so we don't
        # accidentally pick up an older run.
        if start_time >= run_requested_at - RUN_MATCH_TOLERANCE:
            return execution
    return None


def find_latest_completed_execution(
    status: SearchIndexerStatus,
) -> IndexerExecutionResult | None:
    """Return the most recent finished execution, if any."""
    for execution in _executions(status):
        if (execution.status or "") in TERMINAL_EXECUTION_STATUSES:
            return execution
    return None


def format_indexer_failure(
    indexer_name: str,
    execution_status: str,
    execution: IndexerExecutionResult,
) -> str:
    """Build a detailed error message for a failed indexer execution."""
    lines = [
        f"Indexer '{indexer_name}' did not complete successfully "
        f"(status '{execution_status}')."
    ]
    if execution.error_message:
        lines.append(f"Error message: {execution.error_message}")
    if execution.failed_item_count:
        lines.append(f"Failed items: {execution.failed_item_count}.")
    for error in (execution.errors or [])[:5]:
        key = error.key or "<no key>"
        lines.append(f"  - [{key}] {error.error_message}")
    return "\n".join(lines)


if __name__ == "__main__":
    # Script entry point: configure logging and drive the async pipeline from a
    # fresh event loop.
    logging.basicConfig(level=logging.INFO)
    asyncio.run(create_search_index())
