An Azure function that consume eventhub messages and ships them to Grafana Loki / Grafana Cloud. 

## Configuration

- `EVENTHUB_NAME`: The name of the EventHub to consume from.
- `EVENTHUB_CONNECTION`: The connection string for the EventHub.
- `FUNCTION_NAME`: The name of the Azure Function; defaults to `logexport`.
