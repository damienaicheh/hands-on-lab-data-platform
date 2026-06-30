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
from datetime import datetime, timedelta, timezone
from pathlib import Path

from azure.core.exceptions import HttpResponseError, ResourceExistsError
from azure.identity.aio import DefaultAzureCredential
from azure.search.documents.indexes.aio import SearchIndexClient, SearchIndexerClient
from azure.search.documents.indexes.models import (
    IndexerExecutionResult,
    SearchIndex,
    SearchIndexer,
    SearchIndexerDataSourceConnection,
    SearchIndexerSkillset,
    SearchIndexerStatus,
)
from azure.storage.blob.aio import BlobServiceClient
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

# --- Azure AI Search ---
SEARCH_ENDPOINT = get_required_env("SEARCH_ENDPOINT")

# --- Blob storage (data source) ---
BLOB_ACCOUNT_URL = get_required_env("BLOB_ACCOUNT_URL")
BLOB_CONTAINER_NAME = get_required_env("BLOB_CONTAINER_NAME")
BLOB_DATASOURCE_CONNECTION_STRING = get_required_env(
    "BLOB_DATASOURCE_CONNECTION_STRING"
)
LOCAL_DATA_DIR = os.environ.get("LOCAL_DATA_DIR", "documents")

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
        # 1. Push the local documents to the blob container the indexer reads.
        print("\nUploading local files to blob storage...")
        await upload_local_files_to_blob()

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


async def upload_local_files_to_blob() -> None:
    """Upload every file from ``LOCAL_DATA_DIR`` to the configured container.

    Files already present in the container are skipped so the script stays
    idempotent across runs.
    """
    directory_path = resolve_documents_dir()
    if not directory_path.is_dir():
        raise RuntimeError(
            f"Local data directory '{directory_path}' does not exist or is "
            "not a directory."
        )

    async with BlobServiceClient(BLOB_ACCOUNT_URL, credential) as blob_service_client:
        container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)
        # Create the container on first run; ignore the error when it exists.
        try:
            await container_client.create_container()
            print(f"Container '{BLOB_CONTAINER_NAME}' created.")
        except ResourceExistsError:
            print(f"Container '{BLOB_CONTAINER_NAME}' already exists.")

        # Only regular files (not sub-directories) are uploaded, in a stable order.
        local_files = sorted(p for p in directory_path.iterdir() if p.is_file())
        if not local_files:
            print(f"No files found in '{directory_path}'.")
            return

        # Fetch the blobs already present once, to skip re-uploads and keep the
        # script idempotent across runs.
        existing_blobs = {blob.name async for blob in container_client.list_blobs()}

        for file_path in local_files:
            name = file_path.name
            if name in existing_blobs:
                print(f"  - skipped (already exists): {name}")
                continue
            # ``overwrite=False`` is a safety net: existing blobs are already
            # filtered out, so a clash still raises instead of replacing data.
            with file_path.open("rb") as data:
                await container_client.get_blob_client(name).upload_blob(
                    data, overwrite=False
                )
            print(f"  - uploaded: {name}")


# The four ``apply_*`` helpers each load a JSON template from ``data/``, fill in
# its ${VAR} placeholders and create-or-update the matching AI Search object.
# They are idempotent: running them again simply updates the existing object.
async def apply_data_source() -> None:
    """Render the data source template and create/update it via the SDK."""
    # The data source tells the indexer which storage account/container to read.
    body = render_template("blob-datasource.json")
    await indexer_client.create_or_update_data_source_connection(
        SearchIndexerDataSourceConnection(body)
    )
    print(f"datasources/{DATA_SOURCE_NAME} updated.")


async def apply_index() -> None:
    """Render the index template and create/update it via the SDK."""
    # The index defines the target schema (fields, vector + semantic config).
    body = render_template("blob-index.json")
    await index_client.create_or_update_index(SearchIndex(body))
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
