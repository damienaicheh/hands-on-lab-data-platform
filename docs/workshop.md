---
published: true
type: workshop
title: Product Hands-on Lab - AI Data Platform
short_title: AI Data Platform
description: This workshop will cover how to build agentic applications using different data sources. It will cover Foundry IQ, Fabric IQ, and Foundry RTI. It will also cover how to build a multi-agent system using MCP.
level: beginner # Required. Can be 'beginner', 'intermediate' or 'advanced'
navigation_numbering: true
authors: # Required. You can add as many authors as needed
  - Vincent Guyonvarch
  - Damien Aicheh
contacts: # Required. Must match the number of authors
  - "@damienaicheh"
  - "@viguyonv"
duration_minutes: 300
tags: microsoft foundry, fabric, foundry iq, fabric iq, agent framework, mcp, ai search, foundry iq, dev-ui, csu, codespace, devcontainer
navigation_levels: 2
banner_url: assets/banner.jpg
audience: developers, architects, AI engineers

---

# Product Hands-on Lab - AI Data Platform

## What You Will Learn

### Architecture

Orchestrator Agent => Agent Fabric => Sell, products..
                   => Agent Foundry => New products, discounts, other..


### Key Technologies


---

## Prerequisites

Before starting this lab, be sure to set your Azure environment :

- An Azure Subscription with the **Contributor** role to create and manage the labs' resources and deploy the infrastructure as code
- Register the Azure providers on your Azure Subscription if not done yet: `Microsoft.CognitiveServices`, `Microsoft.Search`, `Microsoft.Storage`, `Microsoft.KeyVault`, `Microsoft.ManagedIdentity`,`Microsoft.Fabric`.

To retrieve the lab content :

- A GitHub account (Free, Team or Enterprise)
- From the workshop repository on GitHub, open the **Releases** page and [download starter.zip][repo-starter] from the latest **Starter Lab** release, then unzip it.

3 development options are available:
  - 🥇 *Preferred method* : Pre-configured GitHub Codespace 
  - 🥈 Local Devcontainer
  - 🥉 Local Dev Environment with all the prerequisites detailed below

<div class="tip" data-title="Tips">

> To focus on the main purpose of the lab, we encourage the usage of devcontainers/codespace as they abstract the dev environment configuration, and avoid potential local dependencies conflict.
>
> You could decide to run everything without relying on a devcontainer : To do so, make sure you install all the prerequisites detailed below.

</div>

### 🥇 : Pre-configured GitHub Codespace

To use a GitHub Codespace, you will need :

- [A GitHub Account][github-account]

Create a new GitHub repository, unzip the starter project and push it to your new repository. Then, you can create a new GitHub Codespace from your repository.

GitHub Codespace offers the ability to run a complete dev environment (Visual Studio Code, Extensions, Tools, Secure port forwarding etc.) on a dedicated virtual machine.
The configuration for the environment is defined in the `.devcontainer` folder, making sure everyone gets to develop and practice on identical environments : No more conflict on dependencies or missing tools !

Every GitHub account (even the free ones) grants access to 120 vcpu hours per month, _**for free**_. A 2 vcpu dedicated environment is enough for the purpose of the lab, meaning you could run such environment for 60 hours a month at no cost!

To get your codespace ready for the labs, here are a few steps to execute :

- After you forked the repo, click on `<> Code`, `Codespaces` tab and then click on the `+` button:

![codespace-new](./assets/codespace-new.png)

- You can also provision a beefier configuration by defining creation options and select the **Machine Type** you like :

![codespace-configure](./assets/codespace-configure.png)

### 🥈 : Using a local Devcontainer

This starter comes with a Devcontainer configuration that will let you open a fully configured dev environment from your local Visual Studio Code, while still being completely isolated from the rest of your local machine configuration : No more dependancy conflict.
Here are the required tools to do so :

- [Git client][git-client]
- [Docker Desktop][docker-desktop] running
- [Visual Studio Code][vs-code] installed on your machine

Start by cloning the repository you just forked on your local Machine and open the local folder in Visual Studio Code.
Once you have cloned the repository locally, make sure Docker Desktop is up and running and open the cloned repository in Visual Studio Code.  

You will be prompted to open the project in a Dev Container. Click on `Reopen in Container`.

If you are not prompted by Visual Studio Code, you can open the command palette (`Ctrl + Shift + P`) and search for `Reopen in Container` and select it:

![devcontainer-reopen](./assets/devcontainer-reopen.png)

### 🥉 : Using your own local environment

The following tools and access will be necessary to run the lab on a local environment:  

<div class="tip" data-title="Windows note">

> If you're installing prerequisites with `winget`, open **Windows PowerShell as Administrator**.

</div>

- [Git client][git-client]
- [Visual Studio Code][vs-code] installed
- [Azure CLI][az-cli-install] installed on your machine
- [Python 3.13][download-python] installed on your machine
- [UV package manager][download-uv] installed on your machine
- [Terraform][download-terraform] installed on your machine
- [Fabric CLI][ms-fabric-cli] installed on your machine

Visual Studio Code Extensions to install :

- [ms-python.python][ms-python-extension]
- [github.copilot][github-copilot-extension]
- [github.copilot-chat][github-copilot-chat-extension]
- [ms-python.vscode-pylance][ms-python-vscode-pylance-extension]
- [ms-vscode-remote.remote-containers][ms-vscode-remote-containers-extension]
- [charliermarsh.ruff][charliermarsh-ruff-extension]
- [ms-python.debugpy][ms-python-debugpy-extension]
- [hashicorp.terraform][hashicorp-terraform-extension]

Once you have set up your local environment, you can clone the repository you just forked on your machine, and open the local folder in Visual Studio Code and head to the next step.

### Sign in to Azure

> - Log into your Azure subscription in your environment using Azure CLI and on the [Azure Portal][az-portal] using your credentials.
> - Instructions and solutions will be given for the Azure CLI, but you can also use the Azure Portal if you prefer.
> - Register the Azure providers on your Azure Subscription if not done yet: `Microsoft.CognitiveServices`

```bash
# Login to Azure : 
# --tenant : Optional | In case your Azure account has access to multiple tenants

# Option 1 : Local Environment 
az login --tenant <yourtenantid or domain.com>
# Option 2 : Github Codespace : you might need to specify --use-device-code parameter to ease the az cli authentication process
az login --use-device-code --tenant <yourtenantid or domain.com>

# Display your account details
az account show
# Select your Azure subscription
az account set --subscription <subscription-id>

# Register the following Azure providers if they are not already

# Azure Cognitive Services
az provider register --namespace 'Microsoft.CognitiveServices'

# Azure Search
az provider register --namespace 'Microsoft.Search'

# Azure Storage
az provider register --namespace 'Microsoft.Storage'

# Azure Key Vault
az provider register --namespace 'Microsoft.KeyVault'

# Azure Managed Identity
az provider register --namespace 'Microsoft.ManagedIdentity'

# Azure Fabric
az provider register --namespace 'Microsoft.Fabric'
```

### Deploy the infrastructure

First, you need to initialize the terraform infrastructure by running the following command:

```bash
# Run the following line which will dynamically set the subscription ID as an environment variable:
export ARM_SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Initialize terraform
cd infra && terraform init
```

Then run the following command to deploy the infrastructure:

```bash
# Apply the deployment directly
terraform apply -auto-approve
```

The deployment should take a few minutes to complete.

[ms-python-extension]: https://marketplace.visualstudio.com/items?itemName=ms-python.python
[github-copilot-extension]: https://marketplace.visualstudio.com/items?itemName=GitHub.copilot
[github-copilot-chat-extension]: https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-chat
[ms-python-vscode-pylance-extension]: https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance
[charliermarsh-ruff-extension]: https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff
[ms-python-bandit-extension]: https://marketplace.visualstudio.com/items?itemName=ms-python.bandit
[ms-python-debugpy-extension]: https://marketplace.visualstudio.com/items?itemName=ms-python.debugpy
[hashicorp-terraform-extension]: https://marketplace.visualstudio.com/items?itemName=hashicorp.terraform
[ms-vscode-remote-containers-extension]: https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers
[az-cli-install]: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli
[az-portal]: https://portal.azure.com
[vs-code]: https://code.visualstudio.com/
[azure-function-vs-code-extension]: https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azurefunctions
[docker-desktop]: https://www.docker.com/products/docker-desktop/
[repo-starter]: https://github.com/damienaicheh/hands-on-lab-data-platform/releases
[git-client]: https://git-scm.com/downloads
[github-account]: https://github.com/join
[download-python]: https://www.python.org/downloads/
[download-uv]: https://docs.astral.sh/uv/
[download-terraform]: https://developer.hashicorp.com/terraform/install
[ms-fabric-cli]: https://github.com/microsoft/fabric-cli

---

## Set up your environment

### The starter project

You do not start from an empty folder: the workshop provides a starter project where the code you have to write is marked with `# TODO` comments (a few placeholders keep a `raise NotImplementedError` where Python needs a statement to stay valid). 

Each step in the labs points you to a file, explains why the code matters, and then gives you the exact snippet to write in place of the `# TODO` you find there.

### Update the `.env` file

The project reads its configuration from a `.env` file, but at this point you only have the template `src/.env.template`. Start by duplicating it and renaming the copy to `.env`:

```bash
cp src/.env.template src/.env
```

You do not have to fill everything at once. A few values are produced while you work through the labs (for example `VECTOR_STORE_ID`, which Lab 1 generates). Most of the others come from the resources that were deployed for the workshop, and the easiest way to read them is to browse those resources in the Azure portal. Open the portal, go to **Resource groups**, and select the resource group provisioned for this workshop. It holds a handful of resources, and you will pick one value from each.

#### From the Azure AI Search service

Select the **Search service** in the resource group. On the **Overview** blade, copy the **Url** (it looks like `https://<name>.search.windows.net`) into `SEARCH_ENDPOINT`.

#### From the Foundry resource

Select the **Foundry Project** resource, then open it in the [Go to Foundry portal](https://ai.azure.com) with **Go to Azure AI Foundry portal**.

- On the project **Home** page, copy the project endpoint (`https://<resource>.services.ai.azure.com/api/projects/<project>`) into `FOUNDRY_PROJECT_ENDPOINT`. The shorter base of that same URL, `https://<resource>.services.ai.azure.com`, goes into `FOUNDRY_ENDPOINT`.
- Still in the  **Home** page copy the Azure OpenAI endpoint (`https://<resource>.openai.azure.com/`); copy it into `AOAI_ENDPOINT`.

#### From the Storage Account

Select the ADLS Gen2 **Storage account** starting with the prefix `stsearch` in the resource group.

- Inside the **Endpoints** tab, copy the **Blob service** URL (`https://<account>.blob.core.windows.net`) into `BLOB_ACCOUNT_URL`.
- Inside **Overview** on top right click on **Json View**, copy the storage account **Resource ID** and wrap it as `ResourceId=<id>;` in `BLOB_DATASOURCE_CONNECTION_STRING`.

#### From Microsoft Entra ID

For the purpose of the labs, you will need 2 groups, one to represent all participants and one to represent the restricted documents. You can create them yourself or ask whoever provisioned the workshop to create them for you.

If you need to create them yourself, follow these steps:

```bash
az ad group create --display-name "Contoso-RestrictedDocs" --mail-nickname "contoso-restricteddocs"
```

Add yourself as a user to the Entra ID group

```bash
az ad group member add --group "<group-id>" --member-id "<user-object-id>"
```

When you are done, you should have two groups in your Entra ID, one for all participants and one for the restricted documents.

In the portal, search for **Microsoft Entra ID** and open **Groups**. Find your 2 groups, open each one, and copy its **Object ID** into `RESTRICTED_DOCS_GROUP_ID` (the restricted-documents group) and `ALL_PARTICIPANTS_GROUP_ID` (the all-participants group) inside your `.env` file.

### Seed the Azure AI Search index

Before touching any lab, you need data to work with. The workshop ships a ready-to-run script that uploads the sample documents to storage and builds the Azure AI Search index the agent will query later, including the document-level access rules.

```bash
cd src/seed_ai_search
# Get the project dependencies and create a virtual environment
uv sync
# Activate the virtual environment
source .venv/bin/activate
# Run the script to upload the documents and create the index
uv run python main_create_index.py
```

`uv sync` installs the project dependencies into a local virtual environment. You only need it the first time you work in a given folder; on later runs from the same folder you can skip it and call `uv run` directly. The script then uploads the documents, creates the data source, index, skillset and indexer, and polls the indexer until ingestion completes.

<div class="task" data-title="Validation">

> Wait for the script to report that the indexer has finished. In the Azure portal, inside your resource group, open the Search service, go to **Indexes**, and confirm the index appeated with few documents in it.

</div>

---

## Foundry IQ Managed

In this lab, you create a managed vector store in Foundry IQ. This kind of vectors allows you to quickly vectorize and search documents with a generic approach. This is perfect for use cases like sharing guidelines, where you want to make sure the agent follows the company standards when writing reports.

### What You Will Learn

- Create an `AIProjectClient` and get an OpenAI-compatible client from it.
- Upload local guideline files to Foundry.
- Create a managed vector store from those files.
- Put a first orchestrator agent in front of that store and test it end to end.

### Files To Open

This lab spans two files, which you edit in order:

- `src/foundry_iq/main_managed_index.py` — build the vector store.
- `src/agents/main.py` — wire a first version of the orchestrator agent that searches it.

Both files already load the environment variables, configure logging, and set up the boilerplate for you. You only fill the placeholders called out below.

### Create the Managed Index

#### Create The Project Client

Open `src/foundry_iq/main_managed_index.py` and find the first Lab 1 placeholder.

The `AIProjectClient` is your entry point to the Foundry project. It authenticates with `DefaultAzureCredential`, which reuses your Azure CLI sign-in locally and a managed identity once deployed, so you never store a key in the code. From that client you get an OpenAI-compatible client, which exposes the familiar `files` and `vector_stores` APIs you will use next.

Replace it with:

```python
project_client = AIProjectClient(
    endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)
openai_client = project_client.get_openai_client()
```

Reading the endpoint from the environment keeps the same code working across every environment, because only the `FOUNDRY_PROJECT_ENDPOINT` value changes.

#### Upload The Guideline Files

Before Foundry can index the guidelines, the raw markdown files must exist on the service side. Let's upload the contoso guidelines already prepared in the `files` folder.
 Find the second Lab 1 placeholder and upload each file, keeping the returned identifiers.

Replace it with:

```python
file_ids = []
for file_path in file_paths:
    logger.info("📄 Uploading %s ...", file_path)
    with open(file_path, "rb") as f:
        file = openai_client.files.create(file=f, purpose="assistants")
    file_ids.append(file.id)
```

The `purpose="assistants"` value tells Foundry these files are meant to be used as knowledge for assistants, not for another workflow such as fine-tuning. You collect every `file.id` because the vector store is built from those ids, not from the local paths.

Then create the vector store from the uploaded files:

```python
vector_store = openai_client.vector_stores.create(
    name="report-writing-guidelines-vector-store", file_ids=file_ids
)
logger.info("✅ Created vector store id: %s", vector_store.id)
```

Foundry chunks and embeds each file automatically, so a single call is enough to get a store the agent can query semantically. The store keeps a stable id that will be used by your agent.

#### Run The Script

```bash
cd src/foundry_iq
# Get the project dependencies and create a virtual environment
uv sync
source .venv/bin/activate
# Run the script to upload the files and create the vector store
uv run python main_managed_index.py
```

`uv sync` pulls the project dependencies the first time you enter this folder; you can skip it on the next runs from `src/foundry_iq`. The logs print the created vector store id.

<div class="task" data-title="Validation">

> The script should log `✅ Created vector store id: ...`.
>
> Copy that id and save it in your `.env` file as `VECTOR_STORE_ID`. The agent you will create during the next step needs it to reach the guidelines.

</div>

You can go to Foundry portal inside **Build** > **Knowledge** > **Indexes** to confirm the files were uploaded successfully:

![foundry-knowledge-indexes](./assets/foundry-iq-managed-index.png)

### Consume the Managed Index

Open `src/agents/main.py`. It already registers the agent in Foundry and starts DevUI for you. 

<div class="tip" data-title="DevUI">

> DevUI is a local web app that lets you chat with the agent and see its reasoning. It is automatically launched when you run the agent, so you can test it end-to-end without writing any front-end code.

</div>

#### Create The Foundry Chat Client

Find the first Lab 1 placeholder in `src/agents/main.py`.

The `FoundryChatClient` is the bridge between the agent framework and your Foundry model deployment. It carries the same `credential` used everywhere else, so the agent runs with the caller identity rather than a shared key.

Replace it with:

```python
foundry_client = FoundryChatClient(
    project_endpoint=project_endpoint,
    model=model_deployment,
    credential=credential,
)
```

#### Expose The Guidelines As A Tool

Next step is to turn the vector store you just created into a tool the agent can call on demand. When the agent decides it needs the report-writing guidelines, it uses this store instead of relying on the model memory, which keeps the reports aligned with the company standards.

Find the second Lab 1 placeholder, replace it with:

```python
company_guidelines_tool = foundry_client.get_file_search_tool(
    vector_store_ids=[vector_store_id]
)
```

Here the pieces come together: the chat client drives the model and the tool gives the agent explicit access to the guidelines. The agent starts with an empty `context_providers` list, you will update it later.

Find the last Lab 1 placeholder, replace it with:

```python
orchestrator_agent = Agent(
    name=agent_name,
    client=foundry_client,
    context_providers=context_providers,
    tools=[company_guidelines_tool],
)
```

### Run The Agent

```bash
cd src/agents
# Get the project dependencies and create a virtual environment
source .venv/bin/activate
uv sync
# Run the agent to open DevUI
uv run python main.py
```

`uv sync` installs this project dependencies the first time you enter the `src/agents` folder. DevUI then opens automatically so you can chat with the orchestrator agent.

<div class="task" data-title="Validation">

> Ask the agent: "What are the guidelines for Naming and Formatting Conventions on Contoso products?" and confirm it searches the product guidelines before writing, and that the result follows them.

</div>

---

## Create Knowledge sources

The vector store you just built covers internal writing guidelines. In this lab, you add two more retrieval sources to Foundry IQ, and they play complementary roles:

- an **Azure AI Search source** over the company documents that were indexed at startup. This is where the agent will look first, to ask for company content.
- a **web source** used as a fallback, so when the answer is not in the indexed documents the agent can still ground it on trusted public documentation instead of guessing.

A knowledge source is just a named connector that tells Foundry IQ *where* to look. On their own, these two sources are not enough: the agent needs a single entry point that knows to try the company documents first and fall back to the web when needed. That is exactly why, in the next lab, you group both sources into one knowledge base.

### What You Will Learn

- Define a web knowledge source with allowed and blocked domains.
- Define a search-index knowledge source backed by an existing Azure AI Search index.
- Register both sources in Foundry IQ.

### Files To Open

You only need to edit this file:

- `src/foundry_iq/main_knowledge_base.py`

### Define The Web Knowledge Source

Open `src/foundry_iq/main_knowledge_base.py` and find the Lab 2 placeholder inside `create_web_knowledge_source(...)`.

A web knowledge source lets the agent ground its answers in live documentation instead of guessing. The allow and block lists matter: you explicitly trust `learn.microsoft.com` (including its subpages) and explicitly refuse `bing.com`, so the agent cannot wander onto general search results. This keeps answers relevant and predictable.

Replace it with:

```python
knowledge_source = WebKnowledgeSource(
    name=WEB_KNOWLEDGE_SOURCE_NAME,
    description="A sample Web Knowledge Source.",
    encryption_key=None,
    web_parameters=WebKnowledgeSourceParameters(
        domains=WebKnowledgeSourceDomains(
            allowed_domains=[
                WebKnowledgeSourceDomain(
                    address="learn.microsoft.com", include_subpages=True
                )
            ],
            blocked_domains=[
                WebKnowledgeSourceDomain(address="bing.com", include_subpages=False)
            ],
        )
    ),
)

index_client.create_or_update_knowledge_source(knowledge_source)
logger.info(
    f"Knowledge source '{knowledge_source.name}' created or updated successfully."
)
```

Using `create_or_update_knowledge_source` makes the script safe to run several times: it creates the source the first time and updates it on the next runs instead of failing.

### Define The Search-Index Knowledge Source

Still in the same file, find the Lab 2 placeholder inside `create_index_knowledge_source(...)`.

This source points Foundry IQ at the Azure AI Search index that already holds the company documents. You describe which fields carry the content (`chunk`) and the title, and which semantic configuration to use, so Foundry IQ knows how to retrieve and rank the most relevant passages.

Replace it with:

```python
knowledge_source = SearchIndexKnowledgeSource(
    {
        "name": AI_SEARCH_KNOWLEDGE_BASE_NAME,
        "kind": "searchIndex",
        "description": (
            f"Knowledge source backed by the '{INDEX_NAME}' Azure AI Search index."
        ),
        "searchIndexParameters": {
            "searchIndexName": INDEX_NAME,
            "semanticConfigurationName": SEMANTIC_CONFIGURATION_NAME,
            "sourceDataFields": [{"name": "title"}, {"name": "chunk"}],
            "searchFields": [{"name": "chunk"}],
        },
    }
)

index_client.create_or_update_knowledge_source(knowledge_source)
logger.info(f"Knowledge source '{AI_SEARCH_KNOWLEDGE_BASE_NAME}' ready.")
```

<div class="tip" data-title="Why two field lists?">

> `searchFields` is where Foundry IQ runs the query, while `sourceDataFields` is what it reads back to build the answer. Separating them lets you search only the chunk text but still return the title alongside each result.

</div>

Do not run the script yet. It also needs the knowledge base you build in the next lab, so move on before executing it end-to-end.

---

## Create Knowledge bases with agent retrieval

The two knowledge sources are registered, but the agent cannot query them directly. In this lab, you create a Foundry IQ knowledge base that groups both sources behind a single name and adds the reasoning model that turns retrieved passages into a final answer.

### What You Will Learn

- Group several knowledge sources into one knowledge base.
- Configure answer synthesis so Foundry IQ returns a written answer, not just raw chunks.
- Attach a Foundry model to the knowledge base.

### Files To Open

You stay in the same file:

- `src/foundry_iq/main_knowledge_base.py`

Complete the Lab 3 placeholder inside `create_knowledge_base(...)`.

### Define and Create The Knowledge Base

The knowledge base is what the agent actually talks to. A knowledge base can have multiple sources, and it can be configured to return either raw passages or a synthesized answer. This answer is made by the agentic retrieval model you attach to the knowledge base, which reads the retrieved passages and writes a concise, citation-backed answer.

The advantage of Knowledge Bases is that you can share it across multiple agents, and you can change the sources or the model without touching the agents themselves.

You can also create multiples knowledge bases, by using different sources or different models and use them based on your use case. This is a good way to build multiple scenario based on the same sources, but with different models or different answer instructions.

Open `src/foundry_iq/main_knowledge_base.py` and find the Lab 3 placeholder, replace it with:

```python
knowledge_base = KnowledgeBase(
    {
        "name": KNOWLEDGE_BASE_NAME,
        "description": (
            "Foundry IQ knowledge base over the Azure AI Search index."
        ),
        "knowledgeSources": [
            {"name": WEB_KNOWLEDGE_SOURCE_NAME},
            {"name": AI_SEARCH_KNOWLEDGE_BASE_NAME},
        ],
        "outputMode": "answerSynthesis",
        "answerInstructions": (
            "Provide a concise, citation-backed answer based on the "
            "retrieved documents."
        ),
        "models": [
            {
                "kind": "azureOpenAI",
                "azureOpenAIParameters": {
                    "resourceUri": FOUNDRY_ENDPOINT,
                    "deploymentId": CHAT_MODEL_DEPLOYMENT,
                    "modelName": CHAT_MODEL_DEPLOYMENT,
                },
            }
        ],
        "retrievalReasoningEffort": {"kind": "low"},
    }
)

result = index_client.create_or_update_knowledge_base(knowledge_base)
logger.info(f"Knowledge base '{KNOWLEDGE_BASE_NAME}' ready.")
return result
```

It lists the sources to search (both the web source and the search-index source you defined in previous lab, and because `outputMode` is set to `answerSynthesis`, Foundry IQ uses the configured model to read the retrieved passages and write a concise, citation-backed answer. Pointing the model block at `FOUNDRY_ENDPOINT` and `CHAT_MODEL_DEPLOYMENT` keeps deployment details in configuration rather than hard-coded here.

`retrievalReasoningEffort` set to `low` keeps retrieval fast and inexpensive, which is a good default for a workshop. You can raise it later when you need deeper multi-step reasoning over the sources.

### Run The Script

Now that the sources and the knowledge base are all defined, run the whole file:

```bash
cd src/foundry_iq
uv run python main_knowledge_base.py
```

<div class="task" data-title="Validation">

> The logs should confirm that both knowledge sources and the knowledge base are created or updated.
>
> The script also prints the knowledge base definition as JSON, so you can double-check the sources and the model it references.

</div>

If you go to Foundry portal inside **Build** > **Knowledge** > **Knowledge Bases**, you should see the `contoso-knowledge-base` knowledge base you just created:

![foundry-knowledge-bases](./assets/foundry-iq-knowledge-base.png)

If you click on it, you can see the two sources and the model it uses for answer synthesis:

![foundry-knowledge-bases-detail](./assets/foundry-knowledge-bases-detail.png)

Also, you can see it direcly inside your AI Search instance:

![foundry-knowledge-sources](./assets/ai-search-knowledge-sources.png)

And also the knowledge base itself:

![foundry-knowledge-base](./assets/ai-search-knowledge-base.png)

If you click on it, you will see that you have also a playground to test it directly from the Azure AI Search portal.

---

## Access data from the index based on the user / agent

Your orchestrator agent already retrieves the report-writing guidelines from the managed indexed you built previously. In this final lab, you will connect it to the knowledge base you just created.

### What You Will Learn

- Add an identity-aware Azure AI Search context provider to the existing agent.
- Enforce per-user document permissions at retrieval time.

### Files To Open

You will need the same file you edited in the previous lab:

- `src/agents/main.py`

The chat client, the guidelines tool and the agent wiring are already there from previous labs. You only complete the remaining Lab 4 placeholder that will plug the identity-aware search provider into the agent.

### Add The Identity-Aware Search Provider

A context provider automatically enriches the conversation with relevant knowledge before the model answers. This one runs in `agentic` mode by using the knowledge base you created previously, so retrieval and answer synthesis happen through Foundry IQ. The important detail is that it is identity-aware: it propagates the signed-in user identity to Azure AI Search, so document-level permissions are enforced and each user only retrieves what they are allowed to see. Assigning it to `context_providers` is what adds it to the agent you wired in Lab 1.

Open `src/agents/main.py` and find the Lab 4 placeholder, replace it with:

```python
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
```

<div class="tip" data-title="Why identity-aware retrieval matters">

> Without identity propagation, every user would query Azure AI Search with the same application identity and could read restricted documents. Passing the user identity down to the search call is what makes per-user document trimming possible.

</div>

### Run The Agent

```bash
cd src/agents
uv run python main.py
```

DevUI opens again so you can chat with the full orchestrator agent.

<div class="task" data-title="Validation">

> Ask a question that should rely on the indexed company documents and confirm the answer uses that content.
>
> Sign in as different users and confirm the Azure AI Search results are trimmed according to each user document permissions.

</div>

If you ask content that are inside the restricted documents, you should see that the answer is different based on the user you are signed in with.

For instance "What is the Q3 2026 Event Budget Tracker ?" should return the content of the document if you are signed in as a user that has access to it, otherwise the agent should answer that it cannot find any information about it.

You can test this easily by adding and removing yourself from the `Contoso-RestrictedDocs` group in Microsoft Entra ID, and then signing in again to the agent.

---

## Fabric IQ

- TODO
- Connect the orchestrator agent to the Fabric IQ agent

---

## Ontology

- Ontology

---

## Fabric RTI

- Realtime ingestion

---

## MCP

MCP Dev (Optional)
MCP Fabric => Consommer BDD / RTI / Données
MCP Agentic 

---

## Closing

