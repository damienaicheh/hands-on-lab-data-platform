import asyncio
import os

from agent_framework._agents import Agent
from agent_framework.azure import AzureAISearchContextProvider
from agent_framework_foundry._chat_client import FoundryChatClient
from azure.ai.projects.aio._client import AIProjectClient
from azure.ai.projects.models._models import PromptAgentDefinition
from azure.identity.aio import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()


async def main() -> None:
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

    agent_detail = await project.agents.create_version(
        agent_name="Orchestrator",
        definition=PromptAgentDefinition(
            model=foundry_client.model,
            instructions="You are an orchestrator agent that can call other agents to answer questions. You have access to the following agents: \n\n- Search Agent: Can answer questions about the data in the Azure AI Search index.\n- Web Agent: Can answer questions about the data in the web knowledge source.\n\nWhen you receive a question, you should determine which agent is best suited to answer it and call that agent. If you need to call multiple agents, you can do so in sequence and combine their answers.",
        ),
    )

    AzureAISearchContextProvider(
        source_id="search_provider",
        endpoint=os.environ["SEARCH_ENDPOINT"],
        credential=credential,
        mode="agentic",
        knowledge_base_name=os.environ["KNOWLEDGE_BASE_NAME"],
        # Optional: Configure retrieval behavior. "answer_synthesis" output mode and
        # "medium"/"low" reasoning effort require the preview build of azure-search-documents
        # (`pip install --pre azure-search-documents`); the provider auto-detects the build.
        knowledge_base_output_mode="extractive_data",  # or "answer_synthesis" (preview build only)
        retrieval_reasoning_effort="minimal",  # or "medium", "low" (preview build only)
    )

    agent = Agent(
        name=agent_detail.name,
        client=foundry_client,
    )

    stream = agent.run("What can you do?", stream=True)
    async for chunk in stream:
        if chunk.text:
            print(chunk.text, end="", flush=True)
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
