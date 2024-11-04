An Azure function that consume eventhub messages and ships them to Grafana Loki / Grafana Cloud. 

## Configuration

- `EVENTHUB_NAME`: The name of the EventHub to consume from.
- `EVENTHUB_CONNECTION`: The connection string for the EventHub.
- `FUNCTION_NAME`: The name of the Azure Function; defaults to `logexport`.

## Release

The logexport function is packaged as a ZIP file via `make "logexport.$(python -m setuptools_scm).zip"`. The version is
derived from the `setuptools_scm` package. The build process also updates the version in the `_version.py` file.
