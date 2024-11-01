import json
import azure.functions as func
from collections.abc import Iterator
import ijson  # type: ignore
import logging
from datetime import datetime
from logexport.push import push_pb2

app = func.FunctionApp()


@app.function_name(name="logexport")
@app.event_hub_message_trigger(
    arg_name="azeventhub",  # TODO: make this configurable
    event_hub_name="cspazure",
    connection="cspazure_logsexport_EVENTHUB",
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


def EntryFromJson(load: dict) -> push_pb2.EntryAdapter:
    entry = push_pb2.EntryAdapter()
    entry.timestamp.FromJsonString(load["time"])
    # TODO: decide what should be metadata
    labels = [
        push_pb2.LabelPairAdapter(name=k, value=str(v))
        for k, v in load["properties"].items()
    ]
    entry.structuredMetadata.extend(labels)
    # TODO: decide what the body should be
    entry.line = json.dumps(load)

    return entry


def StreamFromEvent(f) -> push_pb2.StreamAdapter:
    stream = push_pb2.StreamAdapter()

    # TODO: decide what should be stream labels
    stream.labels = """{foo="bar"}"""
    for i in ijson.items(f, "records.item"):
        stream.entries.append(EntryFromJson(i))

    return stream
