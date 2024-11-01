import os
import azure.functions as func
import logging
from datetime import datetime
from logexport.deserialize import StreamFromEvent

app = func.FunctionApp()


@app.function_name(name=os.getenv("FUNCTION_NAME", default="logexport"))
@app.event_hub_message_trigger(
    arg_name="azeventhub",  # TODO: make this configurable
    event_hub_name=os.getenv("EVENTHUB_NAME"),
    connection="EVENTHUB_CONNECTION",
    cardinality="many",
)
def logexport(azeventhub: func.EventHubEvent):
    try:
        stream = StreamFromEvent(azeventhub.get_body())
        logging.info(
            "Python EventHub trigger processed an %d events: %s",
            len(stream.entries),
            stream,
        )
    except Exception:
        logging.exception("failed to process event")
