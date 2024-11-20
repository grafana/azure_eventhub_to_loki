An Azure function that consume eventhub messages and ships them to Grafana Loki / Grafana Cloud. 

## Installation

The repository comes with an [Azure ARM template](https://learn.microsoft.com/en-us/azure/azure-resource-manager/templates/overview)
that can be used to deploy the function to an existing Azure resource group:

```bash
az group deployment create -g <resource-group> -n <deployment-name> --template-file azdeploy.json \
  --parameters packageUri=https://github.com/grafana/azure_eventhub_to_loki/releases/download/<version>/logexport.<version>.zip
```

This command will ask for the Loki endpoint and username/password.

The template can be consumed from Terraform:

```terraform
resource "azurerm_resource_group" "logexport" {
  name     = "logexport-group"
  location = var.location
}

resource "azurerm_resource_group_template_deployment" "logexport" {
  name                = "${azurerm_resource_group.logexport.name}-deploy"
  resource_group_name = azurerm_resource_group.logexport.name
  deployment_mode     = "Complete"
  template_content    = file("azdeploy.json")

  parameters_content = jsonencode({
    "lokiEndpoint" = {
      value = var.loki_endpoint
    }
    "lokiUsername" = {
      value = var.loki_username
    }
    "lokiPassword" = {
      value = var.loki_password
    }
    "packageUri" = {
      value = var.package_uri
    }
  })
}
```

## Configuration

- `EVENTHUB_NAME`: The name of the EventHub to consume from.
- `EVENTHUB_CONNECTION`: The connection string for the EventHub.
- `FUNCTION_NAME`: The name of the Azure Function; defaults to `logexport`.
- `LOKI_ENDPOINT`: The root URL of the Loki instance to send logs to.
- `LOKI_USERNAME`: The optional username to use for authentication with Loki.
- `LOKI_PASSWORD`: The optional password to use for authentication with Loki.

## Release

The logexport function is packaged as a ZIP file via `make "logexport.$(python -m setuptools_scm).zip"`. The version is
derived from the `setuptools_scm` package. The build process also updates the version in the `_version.py` file.

Once built the package can deployed to Azure using the Azure CLI:

```bash
az functionapp deployment source config-zip -g <resource-group> -n <function-app-name> --src <path-to-zip-file>
```

Changes to `logexport/_version.py` have been ignored with

```bash
git update-index --skip-worktree logexport/_version.py
```
