import json
import re
import time
from collections.abc import Iterable
from dataclasses import dataclass
from io import IOBase
from typing import Final, Iterator, Tuple

from logexport._version import __version__
from logexport.config import Config
from logexport.push import push_pb2

VERSION_LABEL_KEY: Final[str] = "__grafana_azure_logexport_version__"


def extract_env_from_resource_id(resource_id: str | None) -> str | None:
    """Extract environment label from Azure resource ID based on resource group name.

    Assumes the environment token is the trailing segment of the resource group
    name (e.g. rg-ecos-compute-dev → dev, rg-ecos-api-prod → prod).
    """
    if not resource_id:
        return None

    match = re.search(r"/resourceGroups/([^/]+)", resource_id, re.IGNORECASE)
    if not match:
        return None

    parts = [p for p in match.group(1).lower().split("-") if p]
    if len(parts) < 2:
        return None

    if parts[-1] == "rg":
        return None

    return parts[-1]


def entry_from_event_record(
    load: dict, current_ts_nanos: int
) -> Tuple[str | None, str | None, str | None, push_pb2.EntryAdapter]:
    """Returns the category, type, env of the event and the entry."""
    entry = push_pb2.EntryAdapter()

    ts = get_timestamp(load)
    if ts is not None:
        entry.timestamp.FromJsonString(ts)
    else:
        entry.timestamp.FromNanoseconds(current_ts_nanos)

    entry.structuredMetadata.add(name=VERSION_LABEL_KEY, value=__version__)

    resource_id = load.get("resourceId")
    env = None
    
    if resource_id:
        entry.structuredMetadata.add(name="resourceId", value=resource_id)
        env = extract_env_from_resource_id(resource_id)
        if env is not None:
            entry.structuredMetadata.add(name="env", value=env)

    if "correlationId" in load:
        entry.structuredMetadata.add(name="correlationId", value=load["correlationId"])

    entry.line = json.dumps(load)

    typ = load.get("type")
    if typ is None and load.get("ProductName") == "Microsoft Defender for Cloud":
        typ = "Alert/" + (load.get("AlertType") or "Unknown")

    return load.get("category"), typ, env, entry


def stream_from_event_body(
    f: IOBase | bytes, config: Config
) -> Iterable[push_pb2.StreamAdapter]:
    """Deserializes a single event body into a list of streams.
    Each stream has the job label and category and type labels if present.
    """

    stream_index: dict[str, push_pb2.StreamAdapter] = {}
    current_ts = time.time_ns()

    if isinstance(f, bytes):
        data = json.loads(f)
    else:
        data = json.load(f)

    for record in get_records(data):
        # Each record should receive it's own unique timestamp.
        current_ts += 1
        (category, type, env, entry) = entry_from_event_record(record, current_ts)

        for i in config.filter.apply(record):
            updated = push_pb2.EntryAdapter()
            updated.CopyFrom(entry)
            updated.line = json.dumps(i)

            labels = create_labels_string(category, type, env, config.additional_labels)
            stream = stream_index.setdefault(
                labels, push_pb2.StreamAdapter(labels=labels)
            )
            stream.entries.append(updated)

    return stream_index.values()


def get_records(data: dict) -> Iterator[dict]:
    for i in data.get("records", []):
        yield i
    if "records" not in data:
        yield data


def streams_from_events(
    events: Iterable[bytes], config: Config
) -> Iterable[push_pb2.StreamAdapter]:
    for event in events:
        for stream in stream_from_event_body(event, config):
            yield stream


def get_timestamp(load: dict) -> str | None:
    return (
        load.get("timeStamp")
        or load.get("timestamp")
        or load.get("time")
        or load.get("created")
    )


def create_labels_string(
    category: str | None, type: str | None, env: str | None, addional_labels: dict[str, str]
) -> str:
    # Build labels deterministically and avoid duplicate env
    parts: list[str] = ['job="integrations/azure-logexport"']

    for key, value in addional_labels.items():
        if env is not None and key == "env":
            continue
        parts.append(f'{key}="{value}"')

    if category is not None:
        parts.append(f'category="{category}"')
    if type is not None:
        parts.append(f'type="{type}"')
    if env is not None:
        parts.append(f'env="{env}"')

    return "{" + ",".join(parts) + "}"
