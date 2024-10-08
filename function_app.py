import json
import azure.functions as func
import dataclasses
import ijson
import logging
from datetime import datetime

app = func.FunctionApp()


@app.event_hub_message_trigger(
    arg_name="azeventhub",
    event_hub_name="cspazure",
    connection="cspazure_logsexport_EVENTHUB",
)
def logexport(azeventhub: func.EventHubEvent):
    messages = list(records(azeventhub.get_body()))
    logging.info("Python EventHub trigger processed an event: %s", messages)


@dataclasses.dataclass
class Message:
    body: str
    attributes: dict
    timestamp: datetime  # TODO: support nanoseconds

    @staticmethod
    def from_json(load: dict):
        return Message(
            body=json.dumps(load),  # TODO: decide what the body should be
            attributes={k: v for k, v in load["properties"].items()},
            timestamp=datetime.fromisoformat(load["time"]),
        )


def records(f):
    for i in ijson.items(f, "records.item"):
        # TODO: catch errors
        yield Message.from_json(i)
