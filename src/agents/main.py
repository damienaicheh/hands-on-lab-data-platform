import asyncio
import logging
import os
from typing import List

from agent_framework import ToolTypes
from agent_framework._agents import Agent
from agent_framework_devui import serve
from agent_framework_foundry._chat_client import FoundryChatClient
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity.aio import DefaultAzureCredential
from dotenv import load_dotenv
from httpx import AsyncClient, Timeout

from utils.identity_propagation_ai_search import (
    IdentityAwareAzureAISearchContextProvider,
)
from utils.fabric_mcp_tool import FabricDataAgentMCPTool


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    project_endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    model_deployment = os.environ["ADVANCED_CHAT_MODEL_DEPLOYMENT"]
    vector_store_id = os.environ["VECTOR_STORE_ID"]
    search_endpoint = os.environ["SEARCH_ENDPOINT"]
    knowledge_base_name = os.environ["KNOWLEDGE_BASE_NAME"]
    fabric_sales_agent_endpoint = os.environ["FABRIC_SALES_AGENT_ENDPOINT"]

    credential = DefaultAzureCredential()
    # <lab id="5">
    #|# TODO: Get an access token for the Fabric Sales agent
    async def get_fabric_token() -> str:
        access_token = await credential.get_token(
            "https://api.fabric.microsoft.com/.default"
        )
        return access_token.token
    #</lab>
    
    async def register_agent_version() -> tuple[str, str]:
        async with AIProjectClient(
            endpoint=project_endpoint,
            credential=credential,
        ) as project:
            agent_detail = await project.agents.create_version(
                agent_name="Orchestrator",
                definition=PromptAgentDefinition(
                    model=model_deployment,
                    instructions="""
                            You are a helpful assistant with advanced reasoning capabilities.
                            You must only use the provided context from the knowledge base to answer the questions.
                            IMPORTANT: You MUST search for guidelines BEFORE creating any product or sales report.
                        """,
                ),
            )
            return (
                getattr(agent_detail, "name", "Orchestrator"),
                str(getattr(agent_detail, "version", "unknown")),
            )

    try:
        logger.info("Ensuring Orchestrator agent is registered in Foundry...")
        agent_name, agent_version = asyncio.run(register_agent_version())
        logger.info(
            "Foundry agent version created: %s (version %s)",
            agent_name,
            agent_version,
        )

        # <lab id="1">
        #|# TODO: create the Foundry chat client (Lab 1).
        foundry_client = FoundryChatClient(
            project_endpoint=project_endpoint,
            model=model_deployment,
            credential=credential,
        )
        # </lab>

        # <lab id="1">
        #|# TODO: create the file-search tool for the company guidelines (Lab 1).
        company_guidelines_tool = foundry_client.get_file_search_tool(
            vector_store_ids=[vector_store_id]
        )
        tools: List[ToolTypes] = [company_guidelines_tool]
        # </lab>

        # The orchestrator starts with the guidelines tool only. Lab 4 adds the
        # identity-aware Azure AI Search retrieval below.
        context_providers = []

        # <lab id="4">
        #|# TODO: create the identity-aware Azure AI Search context provider (Lab 4).
        aisearch_context_provider = IdentityAwareAzureAISearchContextProvider(
            source_id="search_provider",
            endpoint=search_endpoint,
            credential=credential,
            mode="agentic",
            knowledge_base_name=knowledge_base_name,
            knowledge_base_output_mode="answer_synthesis",
            retrieval_reasoning_effort="low",
        )
        context_providers = [aisearch_context_provider]
        # </lab>
        
        # <lab id="5">
        #|# TODO: Connect the orchestrator agent to the Fabric Sales agent
        fabric_token = asyncio.run(get_fabric_token())
        fabric_http_client = AsyncClient(
            follow_redirects=True,
            timeout=Timeout(30.0, read=300.0),
            headers={"Authorization": f"Bearer {fabric_token}"},
        )
        fabric_sales_agent = FabricDataAgentMCPTool(
            name="Sales Agent",
            description="A sales agent that can provide information about products and sales reports.",
            url=fabric_sales_agent_endpoint,
            http_client=fabric_http_client,
        )
        tools.append(fabric_sales_agent)
        # </lab>

        # <lab id="1">
        #|# TODO: wire the orchestrator agent with the guidelines tool (Lab 1).
        orchestrator_agent = Agent(
            name=agent_name,
            client=foundry_client,
            context_providers=context_providers,
            tools=tools,
        )
        # </lab>

        logger.info("Starting Foundry Agents with DevUI...")

        serve(
            entities=[
                orchestrator_agent,
            ],
            port=8090,
            auth_enabled=False,
            auto_open=True,
        )
    finally:
        asyncio.run(credential.close())


if __name__ == "__main__":
    main()
