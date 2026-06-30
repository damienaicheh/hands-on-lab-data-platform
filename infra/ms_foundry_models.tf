resource "azurerm_cognitive_deployment" "msfoundry_advanced_chat_deployment_model" {
  name                 = "gpt-5.4"
  cognitive_account_id = azapi_resource.ms_foundry.id

  sku {
    name     = "GlobalStandard"
    capacity = 200
  }

  model {
    format  = "OpenAI"
    name    = "gpt-5.4"
    version = "2026-03-05"
  }

  version_upgrade_option = "OnceNewDefaultVersionAvailable"
  rai_policy_name        = "Microsoft.DefaultV2"

  depends_on = [
    azapi_resource.ms_foundry
  ]
}

resource "azurerm_cognitive_deployment" "msfoundry_chat_deployment_model" {
  name                 = "gpt-4.1-mini"
  cognitive_account_id = azapi_resource.ms_foundry.id

  sku {
    name     = "GlobalStandard"
    capacity = 120
  }

  model {
    format  = "OpenAI"
    name    = "gpt-4.1-mini"
    version = "2025-04-14"
  }

  version_upgrade_option = "OnceNewDefaultVersionAvailable"
  rai_policy_name        = "Microsoft.DefaultV2"

  depends_on = [
    azapi_resource.ms_foundry
  ]
}

resource "azurerm_cognitive_deployment" "msfoundry_embedding_deployment_model" {
  name                 = "text-embedding-3-large"
  cognitive_account_id = azapi_resource.ms_foundry.id

  sku {
    name     = "GlobalStandard"
    capacity = 50
  }

  model {
    format  = "OpenAI"
    name    = "text-embedding-3-large"
    version = "1"
  }

  version_upgrade_option = "OnceNewDefaultVersionAvailable"
  rai_policy_name        = "Microsoft.DefaultV2"

  depends_on = [
    azapi_resource.ms_foundry
  ]
}
