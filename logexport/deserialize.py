import json
import time
from collections.abc import Iterable
from typing import Final

import ijson  # type: ignore

from logexport._version import __version__
from logexport.push import push_pb2

VERSION_LABEL_KEY: Final[str] = "__grafana_azure_logexport_version__"


def entry_from_event_record(load: dict, current_ts_nanos: int) -> push_pb2.EntryAdapter:
    entry = push_pb2.EntryAdapter()

    ts = get_timestamp(load)
    if ts is not None:
        entry.timestamp.FromJsonString(ts)
    else:
        entry.timestamp.FromNanoseconds(current_ts_nanos)

    # Add version information to the metadata
    entry.structuredMetadata.add(name=VERSION_LABEL_KEY, value=__version__)

    if "resourceId" in load:
        entry.structuredMetadata.add(name="resourceId", value=load["resourceId"])

    if "correlationId" in load:
        entry.structuredMetadata.add(name="correlationId", value=load["correlationId"])

    # TODO: decide what the body should be
    entry.line = json.dumps(load)

    return entry


def stream_from_event_body(f) -> push_pb2.StreamAdapter:
    stream = push_pb2.StreamAdapter()

    # TODO: use category and type fields if present.
    stream.labels = """{job="integrations/azure-logexport"}"""
    current_ts = time.time_ns()
    for i in ijson.items(f, "records.item"):

        # Each record should receive it's own unique timestamp.
        current_ts += 1

        stream.entries.append(entry_from_event_record(i, current_ts))

    return stream


def streams_from_events(events: Iterable[bytes]) -> Iterable[push_pb2.StreamAdapter]:
    for event in events:
        yield stream_from_event_body(event)


def get_timestamp(load: dict) -> str | None:
    return (
        load.get("timeStamp")
        or load.get("timestamp")
        or load.get("time")
        or load.get("created")
    )
