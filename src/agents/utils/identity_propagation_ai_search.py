from collections.abc import Sequence

from agent_framework import Message
from agent_framework.azure import AzureAISearchContextProvider
from azure.core.credentials_async import AsyncTokenCredential

# Scope used to request a Microsoft Entra token for Azure AI Search query-time
# permission enforcement (the same token is forwarded as the query source identity).
SEARCH_TOKEN_SCOPE = "https://search.azure.com/.default"


class IdentityAwareAzureAISearchContextProvider(AzureAISearchContextProvider):
    """Azure AI Search provider that enforces document-level permissions at query time.

    The index was populated with ``GroupIds`` / ``UserIds`` permission fields that the
    indexer synchronizes from the source ADLS Gen2 ACLs. To have the service trim the
    retrieval results for the caller, every agentic retrieval request must carry the
    caller's Microsoft Entra token in the ``x-ms-query-source-authorization`` header.

    This subclass forwards that token (acquired from ``query_source_credential``, which
    defaults to the provider credential) on each agentic retrieve call.
    """

    def __init__(
        self,
        *args: object,
        query_source_credential: AsyncTokenCredential | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._query_source_credential = query_source_credential or self.credential
        self._retrieve_patched = False

    async def _agentic_search(self, messages: Sequence[Message]) -> list[Message]:
        await self._ensure_knowledge_base()
        self._patch_retrieve_with_identity()
        return await super()._agentic_search(list(messages))

    def _patch_retrieve_with_identity(self) -> None:
        client = self._retrieval_client
        if self._retrieve_patched or client is None:
            return

        original_retrieve = client.retrieve
        query_source_credential = self._query_source_credential

        async def retrieve_with_identity(*args: object, **kwargs: object):
            if not kwargs.get("x_ms_query_source_authorization"):
                access_token = await query_source_credential.get_token(
                    SEARCH_TOKEN_SCOPE
                )
                kwargs["x_ms_query_source_authorization"] = access_token.token
            return await original_retrieve(*args, **kwargs)

        client.retrieve = retrieve_with_identity  # type: ignore[method-assign]
        self._retrieve_patched = True
