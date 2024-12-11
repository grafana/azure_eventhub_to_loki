import json
from dataclasses import dataclass

from logexport.deserialize import (
    VERSION_LABEL_KEY,
    create_labels_string,
    entry_from_event_record,
    get_timestamp,
    stream_from_event_body,
)
from logexport.push import push_pb2


def test_deserialization_message():
    load = {
        "properties": {"key": "value"},
        "time": "2024-06-05T10:47:31.676Z",
        "resourceId": "/SUBSCRIPTIONS/1234",
        "category": "cat1",
    }
    (cat, _, entry) = entry_from_event_record(load, 0)

    assert cat == "cat1"
    assert json.loads(entry.line) == {
        "category": "cat1",
        "resourceId": "/SUBSCRIPTIONS/1234",
        "time": "2024-06-05T10:47:31.676Z",
        "properties": {"key": "value"},
    }

    keys = [pair.name for pair in entry.structuredMetadata]
    assert VERSION_LABEL_KEY in keys
    assert "resourceId" in keys
    assert "correlationId" not in keys

    assert entry.timestamp.ToSeconds() == 1717584451


def test_deserialization_records():
    with open("tests/record_sample.json", "rb") as f:
        streams = list(stream_from_event_body(f))
        assert len(streams) == 2
        assert len(streams[0].entries) == 2
        assert (
            streams[0].labels
            == """{job="integration/azure-logexport",category="SQLSecurityAuditEvents"}"""
        )
        assert len(streams[1].entries) == 1
        assert (
            streams[1].labels
            == """{job="integration/azure-logexport",category="SQLSecurityAuditEvents",type="AuditEvent"}"""
        )


def test_deserialization_timestamp():
    @dataclass
    class TestCase:
        field: str
        input: dict
        expected: int

    test_cases = [
        TestCase(
            "timestamp",
            {"timestamp": "2024-06-05T10:47:31.676Z"},
            "2024-06-05T10:47:31.676Z",
        ),
        TestCase(
            "timeStamp",
            {"timeStamp": "2024-06-05T10:47:31.676Z"},
            "2024-06-05T10:47:31.676Z",
        ),
        TestCase(
            "time", {"time": "2024-06-05T10:47:31.676Z"}, "2024-06-05T10:47:31.676Z"
        ),
        TestCase(
            "created", {"time": "2024-06-05T10:47:31.676Z"}, "2024-06-05T10:47:31.676Z"
        ),
    ]

    for case in test_cases:
        ts = get_timestamp(case.input)
        assert ts == case.expected


def test_create_labels_string():
    assert create_labels_string(None, None) == '{job="integration/azure-logexport"}'
    assert (
        create_labels_string("cat1", "type1")
        == '{job="integration/azure-logexport",category="cat1",type="type1"}'
    )
    assert (
        create_labels_string(None, "type1")
        == '{job="integration/azure-logexport",type="type1"}'
    )
    assert (
        create_labels_string("cat1", None)
        == '{job="integration/azure-logexport",category="cat1"}'
    )
