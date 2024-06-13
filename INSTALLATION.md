# Installation of the Azure Function

## High-Level Steps Using the Azure UI

1. **Create a Function App**
   - Open the Azure portal and navigate to the "Create a resource" page.
   - Select "Function App."
   - Configure the Function App with the following settings:
     - **Runtime stack:** Node.js
     - **Version:** 20 LTS
     - **Operating System:** Windows

2. **Create a Function**
   - After the Function App is deployed, navigate to the Function App resource.
   - In the Function App resource, select "Functions" and then "Add" to create a new function.
   - Choose the "Azure Event Hub trigger" template, which runs a function whenever an event hub receives a new event.

3. **Configure Event Hub Connection**
   - Ensure you set a valid Event Hub connection string in the trigger settings. This connection allows the function to receive events from the Event Hub.

4. **Add Function Code**
   - Navigate to the code editor for the function.
   - Replace the contents of `index.js` with the code from `gl_alternative_index.js`.
   - Save your changes.

5. **Set Environment Variables**
   - Within the Function App, go to "Configuration" under the "Settings" section.
   - Add the necessary environment variables as per your requirements.
   - Refer to the next section for details on required and optional environment variables.

These steps will guide you through setting up and configuring a Node.js Function App with an Azure Event Hub trigger using the Azure portal.

## Environment Variables and Their Usage

### Required Environment Variables

- **GL_API_USER**: The user ID for the Grafana Cloud logs endpoint, which is an integer value.
- **GL_API_KEY**: The Grafana.com API token with at least `logs:write` scope.

### Optional Environment Variables

- **GL_SITE**: The FQDN of the Grafana Cloud cluster for your stack logs endpoint. If not specified, the default value 'logs-prod-013.grafana.net' will be used.
- **GL_HTTP_PATH**: The path of the Grafana Cloud logs push API endpoint. Default is '/loki/api/v1/push' and typically does not need to be changed.
- **GL_HTTP_PORT**: Default port is 443.
- **GL_REQUEST_TIMEOUT_MS**: Default request timeout is 10000 milliseconds.

- **GL_DEFAULT_ATTRIBUTES**: Key/value pairs used as indexed stream labels on all log lines by default. If a log line is in JSON format and contains a field with the same name, the field value will be used instead.

- **GL_TIMESTAMP_ATTRIBUTES**: For JSON-formatted logs, fields listed here will be automatically detected and used for the log line's timestamp. If not detected, the processing time is used. Default is 'timeStamp,timestamp,time,created'. Requires a comma-separated list without whitespace.

- **GL_INDEXED_ATTRIBUTES**: For JSON-formatted logs, fields listed here will be promoted to indexed stream labels. Default is 'source,sourceType,resourceId'. Requires a comma-separated list without whitespace.

- **GL_STRUCTURED_METADATA_ATTRIBUTES**: For JSON-formatted logs, fields listed here will be promoted to structured metadata. Default is 'ActivityId'. Requires a comma-separated list without whitespace.

- **GL_LOG_INCLUDE_FILTER**: Allows inclusion of log lines matching specific criteria. Provide an array of objects, each containing key-value pairs for attribute names and values. If a log line matches all key-value pairs, it is included.

Example:
```json
GL_LOG_INCLUDE_FILTER = "[{ 'category': 'AuditEvent', 'operationName': 'SecretGet' }]"
```
This includes log lines with `category` set to 'AuditEvent' and `operationName` set to 'SecretGet', discarding all others.

- **GL_LOG_EXCLUDE_FILTER**: Allows exclusion of log lines matching specific criteria. Provide an array of objects, each containing key-value pairs for attribute names and values. If a log line matches all key-value pairs, it is excluded.

Example:
```json
GL_LOG_EXCLUDE_FILTER = "[{ 'category': 'AuditEvent', 'operationName': 'SecretGet' }]"
```
This excludes log lines with `category` set to 'AuditEvent' and `operationName` set to 'SecretGet', including all others.

Both `GL_LOG_INCLUDE_FILTER` and `GL_LOG_EXCLUDE_FILTER` require an array of objects.