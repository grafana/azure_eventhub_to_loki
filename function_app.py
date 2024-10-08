import azure.functions as func
import dataclasses
import logging
from datetime import datetime 

app = func.FunctionApp()

@app.event_hub_message_trigger(arg_name="azeventhub", event_hub_name="cspazure",
                               connection="cspazure_logsexport_EVENTHUB") 
def logexport(azeventhub: func.EventHubEvent):
    logging.info('Python EventHub trigger processed an event: %s',
                azeventhub.get_body().decode('utf-8'))


@dataclasses.dataclass
class Message:
    body: str
    attributes: dict
    timestamp: datetime# TODO: support nanoseconds 

    @staticmethod
    def from_json(json: dict):
        return Message(
            body=json["body"],
            attributes=json["attributes"],
            timestamp=datetime.fromisoformat(json["timestamp"])
        )
