output "project_endpoint" {
  description = "AI Foundry project endpoint"
  value       = azapi_resource.ms_foundry_project.output.properties.endpoints["AI Foundry API"]
}

output "chat_model_deployment" {
  description = "Chat model deployment name"
  value       = azurerm_cognitive_deployment.msfoundry_chat_deployment_model.name
}

output "advanced_chat_model_deployment" {
  description = "Advanced chat model deployment name"
  value       = azurerm_cognitive_deployment.msfoundry_advanced_chat_deployment_model.name
}

output "embedding_deployment" {
  description = "Embedding model deployment name"
  value       = azurerm_cognitive_deployment.msfoundry_embedding_deployment_model.name
}

output "azure_resource_group" {
  description = "Azure resource group name"
  value       = local.resource_group_name
}

output "search_service_name" {
  description = "Azure AI Search service name"
  value       = azapi_resource.ai_search.name
}

output "search_service_endpoint" {
  description = "Azure AI Search service endpoint"
  value       = "https://${azapi_resource.ai_search.name}.search.windows.net"
}

output "search_system_identity_principal_id" {
  description = "Principal ID of the Azure AI Search system-assigned managed identity"
  value       = azapi_resource.ai_search.output.identity.principalId
}

output "azure_tenant_id" {
  description = "Azure tenant ID"
  value       = data.azurerm_client_config.current.tenant_id
}

# --- Dedicated ADLS Gen2 storage account for AI Search ACL ingestion ----------
output "search_data_storage_account_name" {
  description = "Name of the dedicated ADLS Gen2 storage account for searchable documents"
  value       = azurerm_storage_account.search_data.name
}

output "search_data_blob_endpoint" {
  description = "Blob endpoint of the dedicated ADLS Gen2 storage account (BLOB_ACCOUNT_URL)"
  value       = azurerm_storage_account.search_data.primary_blob_endpoint
}

output "search_data_dfs_endpoint" {
  description = "DFS (Data Lake) endpoint of the dedicated ADLS Gen2 storage account"
  value       = azurerm_storage_account.search_data.primary_dfs_endpoint
}

output "search_data_resource_id" {
  description = "Resource ID of the dedicated ADLS Gen2 storage account (for BLOB_DATASOURCE_CONNECTION_STRING)"
  value       = azurerm_storage_account.search_data.id
}