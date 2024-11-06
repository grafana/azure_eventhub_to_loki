An Azure function that consume eventhub messages and ships them to Grafana Loki / Grafana Cloud. 

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
