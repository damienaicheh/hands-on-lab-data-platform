# =============================================================================
# Role assignments for the Foundry Search
# =============================================================================

resource "azurerm_role_assignment" "ms_foundry_foundry_developer_to_ai_search" {
  scope                = azapi_resource.ms_foundry.id
  role_definition_name = "Azure AI Developer"
  principal_id         = azapi_resource.ai_search.output.identity.principalId
}

resource "azurerm_role_assignment" "ms_foundry_cognitive_services_user_to_ai_search" {
  scope                = azapi_resource.ms_foundry.id
  role_definition_name = "Cognitive Services User"
  principal_id         = azapi_resource.ai_search.output.identity.principalId
}

# =============================================================================
# Role assignments for User Assigned Identity (UAI)
# These must be assigned BEFORE the capability host is created
# =============================================================================

resource "azurerm_role_assignment" "storage_blob_data_contributor_uai" {
  scope                = azurerm_storage_account.this.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.this.principal_id
}

resource "azurerm_role_assignment" "search_index_data_contributor_uai" {
  scope                = azapi_resource.ai_search.id
  role_definition_name = "Search Index Data Contributor"
  principal_id         = azurerm_user_assigned_identity.this.principal_id
}

resource "azurerm_role_assignment" "search_service_contributor_uai" {
  scope                = azapi_resource.ai_search.id
  role_definition_name = "Search Service Contributor"
  principal_id         = azurerm_user_assigned_identity.this.principal_id
}

# =============================================================================
# Role assignment for Storage Blob Data Owner with condition
# This must be assigned AFTER the capability host is created
# =============================================================================

resource "azurerm_role_assignment" "storage_blob_data_owner_uai" {
  scope                = azurerm_storage_account.this.id
  role_definition_name = "Storage Blob Data Owner"
  principal_id         = azurerm_user_assigned_identity.this.principal_id
  condition_version    = "2.0"
  condition            = <<-EOT
  (
    (
      !(ActionMatches{'Microsoft.Storage/storageAccounts/blobServices/containers/blobs/tags/read'})
      AND !(ActionMatches{'Microsoft.Storage/storageAccounts/blobServices/containers/blobs/filter/action'})
      AND !(ActionMatches{'Microsoft.Storage/storageAccounts/blobServices/containers/blobs/tags/write'})
    )
    OR
    (@Resource[Microsoft.Storage/storageAccounts/blobServices/containers:name] StringStartsWithIgnoreCase '${local.project_id_guid}'
    AND @Resource[Microsoft.Storage/storageAccounts/blobServices/containers:name] StringLikeIgnoreCase '*-azureml-agent')
  )
  EOT
}

# =============================================================================
# User deployment role assignments end here
# =============================================================================

resource "azurerm_role_assignment" "ms_foundry_foundry_user_to_user" {
  scope                = azapi_resource.ms_foundry.id
  role_definition_name = "Foundry User"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_role_assignment" "ms_foundry_foundry_project_manager_to_user" {
  scope                = azapi_resource.ms_foundry.id
  role_definition_name = "Foundry Project Manager"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_role_assignment" "ms_foundry_project_foundry_user_to_user" {
  scope                = azapi_resource.ms_foundry_project.id
  role_definition_name = "Foundry User"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_role_assignment" "ms_foundry_project_foundry_project_manager_to_user" {
  scope                = azapi_resource.ms_foundry_project.id
  role_definition_name = "Foundry Project Manager"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_role_assignment" "ai_search_cognitive_services_user_to_user" {
  scope                = azapi_resource.ai_search.id
  role_definition_name = "Cognitive Services User"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_role_assignment" "ai_search_search_service_contributor_to_user" {
  scope                = azapi_resource.ai_search.id
  role_definition_name = "Search Service Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Needed to query data to Foundry IQ
resource "azurerm_role_assignment" "ai_search_index_data_reader_to_user" {
  scope                = azapi_resource.ai_search.id
  role_definition_name = "Search Index Data Reader"
  principal_id         = data.azurerm_client_config.current.object_id
}

# ---- RBAC for the user running the script (az login) ------------------------
# Required to upload local files to blob storage.
resource "azurerm_role_assignment" "blob_demo_storage_blob_data_contributor_user" {
  scope                = azurerm_storage_account.this.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_role_assignment" "blob_demo_storage_blob_data_owner_user" {
  scope                = azurerm_storage_account.this.id
  role_definition_name = "Storage Blob Data Owner"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Required to read indexer status / document count from the index.
resource "azurerm_role_assignment" "blob_demo_search_index_data_contributor_user" {
  scope                = azapi_resource.ai_search.id
  role_definition_name = "Search Index Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

# ---- RBAC for the Foundry Search system-assigned managed identity ----------
# Allows the indexer to read documents from the blob container (key-less).
resource "azurerm_role_assignment" "blob_demo_storage_blob_data_reader_search" {
  scope                = azurerm_storage_account.this.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azapi_resource.ai_search.output.identity.principalId
}

# Allows the AI Search vectorizer / embedding skill to call Azure OpenAI hosted
# in the Foundry resource. The "Cognitive Services User" role already granted
# in roles.tf covers Azure OpenAI inference, so no additional role is needed.

# ---- RBAC for the Foundry user-assigned managed identity (Foundry IQ) -------
# Foundry IQ portal needs to read the knowledge base / index and to manage it
# via the project ↔ Search connection.
resource "azurerm_role_assignment" "blob_demo_search_index_data_reader_foundry" {
  scope                = azapi_resource.ai_search.id
  role_definition_name = "Search Index Data Reader"
  principal_id         = azurerm_user_assigned_identity.this.principal_id
}