import json
from collections.abc import Iterable
from typing import Final

import ijson  # type: ignore

from logexport._version import __version__
from logexport.push import push_pb2

VERSION_LABEL_KEY: Final[str] = "__grafana_azure_logexport_version__"


def entry_from_json(load: dict) -> push_pb2.EntryAdapter:
    entry = push_pb2.EntryAdapter()
    entry.timestamp.FromJsonString(get_timestamp(load))

    # Add version information to the metadata
    entry.structuredMetadata.add(name=VERSION_LABEL_KEY, value=__version__)

    # TODO: decide what the body should be
    entry.line = json.dumps(load)

    return entry


def stream_from_bytes(f) -> push_pb2.StreamAdapter:
    stream = push_pb2.StreamAdapter()

    # TODO: use category and type fields if present.
    stream.labels = """{job="integrations/azure-logexport"}"""
    for i in ijson.items(f, "records.item"):
        stream.entries.append(entry_from_json(i))

    return stream


def streams_from_event(events: Iterable[bytes]) -> Iterable[push_pb2.StreamAdapter]:
    for event in events:
        yield stream_from_bytes(event)


def get_timestamp(load: dict) -> str:
    return (
        load.get("timeStamp")
        or load.get("timestamp")
        or load.get("time")
        or load.get("created")
        or ""  # TODO: decide on a default
    )
