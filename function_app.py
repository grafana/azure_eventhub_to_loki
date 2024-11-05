import logging
import os
from collections.abc import Iterable
from typing import Final, List

import azure.functions as func

from logexport.deserialize import streams_from_event
from logexport.loki import LokiClient

# Constants defining environment variables names
EVENTHUB_NAME_VAR: Final[str] = "EVENTHUB_NAME"
EVENTHUB_CONNECTION_VAR: Final[str] = "EVENTHUB_CONNECTION"
FUNCTION_NAME_VAR: Final[str] = "FUNCTION_NAME"

app = func.FunctionApp()

loki_client = LokiClient(
    os.environ["LOKI_ENDPOINT"],
    os.environ.get("LOKI_USERNAME"),
    os.environ.get("LOKI_PASSWORD"),
)

if "EVENTHUB_NAME" not in os.environ:
    logging.error("EVENTHUB_NAME environment variable is not set")
    exit(1)


@app.function_name(name=os.getenv(FUNCTION_NAME_VAR, default="logexport"))
@app.event_hub_message_trigger(
    arg_name="events",
    event_hub_name=os.environ.get(EVENTHUB_NAME_VAR) or "",
    connection=EVENTHUB_CONNECTION_VAR,  # the parameter expects the env var name not the value.
    cardinality="many",
)
def logexport(events: List[func.EventHubEvent]):
    try:
        streams = streams_from_event((event.get_body() for event in events))
        logging.info(
            "Python EventHub trigger processed a %d events",
            len(events),
        )
        loki_client.push(streams)
    except Exception:
        logging.exception("failed to process event")
