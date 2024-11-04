import os
import azure.functions as func
import logging
from datetime import datetime
from logexport.deserialize import stream_from_event
from logexport.loki import LokiClient
from typing import Final

# Constants defining environment variables names
EVENTHUB_NAME_VAR: Final[str] = "EVENTHUB_NAME"
EVENTHUB_CONNECTION_VAR: Final[str] = "EVENTHUB_CONNECTION"
FUNCTION_NAME_VAR: Final[str] = "FUNCTION_NAME"

app = func.FunctionApp()

loki_client = LokiClient(
    os.environ.get("LOKI_URL") or "",
    os.environ.get("LOKI_USERNAME"),
    os.environ.get("LOKI_PASSWORD"),
)

if "EVENTHUB_NAME" not in os.environ:
    logging.error("EVENTHUB_NAME environment variable is not set")
    exit(1)


@app.function_name(name=os.getenv(FUNCTION_NAME_VAR, default="logexport"))
@app.event_hub_message_trigger(
    arg_name="azeventhub",
    event_hub_name=os.environ.get(EVENTHUB_NAME_VAR) or "",
    connection=EVENTHUB_CONNECTION_VAR,  # the parameter expects the env var name not the value.
    cardinality="many",
)
def logexport(azeventhub: func.EventHubEvent):
    try:
        stream = stream_from_event(azeventhub.get_body())
        logging.info(
            "Python EventHub trigger processed an %d events: %s",
            len(stream.entries),
            stream,
        )
        loki_client.push(stream)
    except Exception:
        logging.exception("failed to process event")
