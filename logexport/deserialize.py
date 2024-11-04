import ijson  # type: ignore
import json
from logexport._version import __version__
from logexport.push import push_pb2


def EntryFromJson(load: dict) -> push_pb2.EntryAdapter:
    entry = push_pb2.EntryAdapter()
    entry.timestamp.FromJsonString(getTimestamp(load))

    # TODO: decide what should be metadata
    labels = [
        push_pb2.LabelPairAdapter(name=k, value=str(v))
        for k, v in load["properties"].items()
    ]
    entry.structuredMetadata.extend(labels)

    # Add version information to the metadata
    entry.structuredMetadata.add(
        name="__grafana_azure_logexport_version__", value=__version__
    )

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

def getTimestamp(load: dict) -> str:
    return load.get("timeStamp") or load.get("timestamp") or load.get("time") or load.get("created")
