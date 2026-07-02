import logging
import os

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    """Create a vector store with guidelines documents."""

    logger.info("🚀 Starting ...")

    # <lab id="1">
    #|# TODO: create an AIProjectClient and get its OpenAI client (Lab 1).
    project_client = AIProjectClient(
        endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        credential=DefaultAzureCredential(),
    )
    openai_client = project_client.get_openai_client()
    # </lab>

    file_paths = [
        "./files/product-report-writing-guidelines.md",
        "./files/sales-report-writing-guidelines.md",
    ]

    # <lab id="1">
    #|# TODO: upload the guideline files and collect their file IDs (Lab 1).
    file_ids = []
    for file_path in file_paths:
        logger.info("📄 Uploading %s ...", file_path)
        with open(file_path, "rb") as f:
            file = openai_client.files.create(file=f, purpose="assistants")
        file_ids.append(file.id)
    # </lab>

    # <lab id="1">
    #|# TODO: create the vector store from the uploaded file IDs (Lab 1).
    vector_store = openai_client.vector_stores.create(
        name="report-writing-guidelines-vector-store", file_ids=file_ids
    )
    # </lab>

    logger.info("✅ Created vector store id: %s", vector_store.id)


if __name__ == "__main__":
    main()
