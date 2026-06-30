import logging
import os

from agent_framework._agents import Agent
from agent_framework_devui import serve
from agent_framework_foundry._chat_client import FoundryChatClient
from azure.ai.projects.aio._client import AIProjectClient
from azure.ai.projects.models._models import PromptAgentDefinition
from azure.identity.aio import DefaultAzureCredential
from dotenv import load_dotenv
from utils.identity_propagation_ai_search import (
    IdentityAwareAzureAISearchContextProvider,
)

load_dotenv()


credential = DefaultAzureCredential()

project = AIProjectClient(
    endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
    credential=credential,
)

foundry_client = FoundryChatClient(
    project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
    model=os.environ["ADVANCED_CHAT_MODEL_DEPLOYMENT"],
    credential=credential,
)

agent_detail = project.agents.create_version(
    agent_name="Orchestrator",
    definition=PromptAgentDefinition(
        model=foundry_client.model,
        instructions="""
                You are a helpful assistant with advanced reasoning capabilities.
                You must only use the provided context from the knowledge base to answer the questions.
            """,
    ),
)

aisearch_context_provider = IdentityAwareAzureAISearchContextProvider(
    source_id="search_provider",
    endpoint=os.environ["SEARCH_ENDPOINT"],
    credential=credential,
    mode="agentic",
    knowledge_base_name=os.environ["KNOWLEDGE_BASE_NAME"],
    # Optional: Configure retrieval behavior. "answer_synthesis" output mode and
    # "medium"/"low" reasoning effort require the preview build of azure-search-documents
    # (`pip install --pre azure-search-documents`); the provider auto-detects the build.
    knowledge_base_output_mode="answer_synthesis",  # or "answer_synthesis" (preview build only)
    retrieval_reasoning_effort="low",  # or "medium", "low" (preview build only)
)

orchestrator_agent = Agent(
    name="Orchestrator",
    client=foundry_client,
    context_providers=[aisearch_context_provider],
)


def main() -> None:

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    logger.info("Starting Foundry Agents with DevUI...")

    serve(
        entities=[
            orchestrator_agent,
        ],
        port=8090,
        auth_enabled=False,
        auto_open=True,
    )


if __name__ == "__main__":
    main()
