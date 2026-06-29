output "project_endpoint" {
  description = "AI Foundry project endpoint"
  value       = azapi_resource.ms_foundry_project.output.properties.endpoints["AI Foundry API"]
}

output "model_deployment" {
  description = "Chat model deployment name"
  value       = azurerm_cognitive_deployment.msfoundry_chat_deployment_model.name
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