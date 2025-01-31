import json
import time
from collections.abc import Iterable
from typing import Final, Tuple

import ijson  # type: ignore

from logexport._version import __version__
from logexport.push import push_pb2

VERSION_LABEL_KEY: Final[str] = "__grafana_azure_logexport_version__"


def entry_from_event_record(
    load: dict, current_ts_nanos: int
) -> Tuple[str | None, str | None, push_pb2.EntryAdapter]:
    """Returns the category and type of the event and the entry."""
    entry = push_pb2.EntryAdapter()

    ts = get_timestamp(load)
    if ts is not None:
        entry.timestamp.FromJsonString(ts)
    else:
        entry.timestamp.FromNanoseconds(current_ts_nanos)

    entry.structuredMetadata.add(name=VERSION_LABEL_KEY, value=__version__)

    if "resourceId" in load:
        entry.structuredMetadata.add(name="resourceId", value=load["resourceId"])

    if "correlationId" in load:
        entry.structuredMetadata.add(name="correlationId", value=load["correlationId"])

    # TODO: decide what the body should be
    entry.line = json.dumps(load)

    return load.get("category"), load.get("type"), entry


def stream_from_event_body(
    f, addional_labels: dict[str, str]
) -> Iterable[push_pb2.StreamAdapter]:
    """Deserializes a single event body into a list of streams.
    Each stream has the job label and category and type labels if present.
    """

    stream_index: dict[str, push_pb2.StreamAdapter] = {}
    current_ts = time.time_ns()
    for i in ijson.items(f, "records.item", use_float=True):

        # Each record should receive it's own unique timestamp.
        current_ts += 1

        (category, type, entry) = entry_from_event_record(i, current_ts)
        labels = create_labels_string(category, type, addional_labels)
        stream = stream_index.setdefault(labels, push_pb2.StreamAdapter(labels=labels))
        stream.entries.append(entry)

    return stream_index.values()


def streams_from_events(
    events: Iterable[bytes], additional_labels: dict[str, str]
) -> Iterable[push_pb2.StreamAdapter]:
    for event in events:
        for stream in stream_from_event_body(event, additional_labels):
            yield stream


def get_timestamp(load: dict) -> str | None:
    return (
        load.get("timeStamp")
        or load.get("timestamp")
        or load.get("time")
        or load.get("created")
    )


def create_labels_string(
    category: str | None, type: str | None, addional_labels: dict[str, str]
) -> str:
    labels = 'job="integrations/azure-logexport"'

    for key, value in addional_labels.items():
        labels += f',{key}="{value}"'

    if category is not None:
        labels += f',category="{category}"'
    if type is not None:
        labels += f',type="{type}"'

    return "{" + labels + "}"
