import logging
import os
from collections.abc import Iterable
from typing import Final, List

import azure.functions as func

from logexport.config import get_additional_labels
from logexport.deserialize import streams_from_events
from logexport.loki import LokiClient
from logexport.loki.client import LokiClientError

# Constants defining environment variables names
EVENTHUB_NAME_VAR: Final[str] = "EVENTHUB_NAME"
EVENTHUB_CONNECTION_VAR: Final[str] = "EVENTHUB_CONNECTION"
FUNCTION_NAME_VAR: Final[str] = "FUNCTION_NAME"

MAX_RETRY_COUNT: Final[str] = "3"
MINIMUM_INTERVAL: Final[str] = "00:00:01"
MAXIMUM_INTERVAL: Final[str] = "00:00:10"

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
# Configures an exponential backoff retry strategy in the trigger from eventhub to the function.
# When eventuhb executes the function, it will not commit a checkpoint until all retries are exhausted,
# and then progress in that partition is restarted.
@app.retry(
    strategy="exponential_backoff",
    max_retry_count=MAX_RETRY_COUNT,
    minimum_interval=MINIMUM_INTERVAL,
    maximum_interval=MAXIMUM_INTERVAL,
)
def logexport(events: List[func.EventHubEvent], context: func.Context) -> None:
    try:
        streams = streams_from_events(
            (event.get_body() for event in events), get_additional_labels()
        )
        logging.info(
            "Python EventHub trigger processed a %d events",
            len(events),
        )
        loki_client.push(streams)
    except Exception as e:
        if isinstance(e, LokiClientError) and not e.is_retryable():
            logging.exception("failed to process event with non-retryable error.")
        elif context.retry_context.retry_count == context.retry_context.max_retry_count:
            logging.exception(
                "failed to process event %d times. Giving up.",
                context.retry_context.retry_count + 1,
            )
        else:
            logging.exception(
                "failed to process event %d times. Retrying...",
                context.retry_context.retry_count + 1,
            )
            raise
