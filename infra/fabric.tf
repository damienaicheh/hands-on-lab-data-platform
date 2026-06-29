resource "azurerm_fabric_capacity" "this" {
  name                = format("fc%s", local.resource_suffix_lowercase)
  resource_group_name = local.resource_group_name
  location            = local.resource_group_location

  administration_members = [data.azuread_user.current.user_principal_name]

  sku {
    name = "F2"
    tier = "Fabric"
  }

  tags = local.tags
}