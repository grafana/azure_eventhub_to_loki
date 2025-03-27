import json
from dataclasses import dataclass

import jq  # type: ignore

from logexport.config import Config
from logexport.deserialize import (
    VERSION_LABEL_KEY,
    create_labels_string,
    entry_from_event_record,
    get_timestamp,
    stream_from_event_body,
)
from logexport.filter import Filter
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
    @dataclass
    class TestCase:
        path: str
        expected_labels: list[str]

    test_cases = [
        TestCase(
            "tests/record_sample.json",
            [
                '{job="integrations/azure-logexport",category="SQLSecurityAuditEvents"}',
                '{job="integrations/azure-logexport",category="SQLSecurityAuditEvents",type="AuditEvent"}',
            ],
        ),
        TestCase(
            "tests/issue_15.json",
            ['{job="integrations/azure-logexport"}'],
        ),
        TestCase(
            "tests/issue_19_sample_1.json",
            [
                '{job="integrations/azure-logexport",type="Alert/SIMULATED_KV_ListGetAnomaly"}'
            ],
        ),
        TestCase(
            "tests/issue_19_sample_2.json",
            [
                '{job="integrations/azure-logexport",type="Microsoft.Security/assessments/subAssessments"}'
            ],
        ),
    ]
    for case in test_cases:
        with open(case.path, "rb") as f:
            streams = list(
                stream_from_event_body(
                    f, Config(additional_labels={}, filter=Filter(None))
                )
            )
            assert len(streams) == len(case.expected_labels)
            for i, stream in enumerate(streams):
                assert stream.labels == case.expected_labels[i]


def test_deserialization_filter():
    f = Filter('. | select(.type == "AuditEvent")')
    config = Config(additional_labels={}, filter=f)
    with open("tests/record_sample.json", "rb") as f:
        streams = list(stream_from_event_body(f, config))
        assert len(streams) == 1
        assert (
            streams[0].labels
            == '{job="integrations/azure-logexport",category="SQLSecurityAuditEvents",type="AuditEvent"}'
        )


def test_deserialization_expanded_records():
    f = Filter(".properties[].message")
    config = Config(additional_labels={}, filter=f)
    data = """
           {
             "records": [
               {
                 "category": "cat1",
                 "properties": [
                   {"message": {"say": "hello"}},
                   {"message": {"say": "world"}}
                 ]
               },
               {
                 "category": "cat2",
                 "properties": [
                    {"message": {"say": "hi"}}
                  ]
               }
             ]
           }
           """
    streams = list(stream_from_event_body(data.encode("utf-8"), config))
    assert len(streams) == 2
    assert streams[0].labels == '{job="integrations/azure-logexport",category="cat1"}'
    assert streams[1].labels == '{job="integrations/azure-logexport",category="cat2"}'

    assert len(streams[0].entries) == 2
    assert streams[0].entries[0].line == '{"say": "hello"}'
    assert streams[0].entries[1].line == '{"say": "world"}'

    assert len(streams[1].entries) == 1
    assert streams[1].entries[0].line == '{"say": "hi"}'


def test_deserialization_filter_without_records():
    f = Filter(".ExtendedProperties")
    config = Config(additional_labels={}, filter=f)
    with open("tests/issue_19_sample_1.json", "rb") as f:
        streams = list(stream_from_event_body(f, config))
        assert len(streams) == 1
        assert (
            streams[0].labels
            == '{job="integrations/azure-logexport",type="Alert/SIMULATED_KV_ListGetAnomaly"}'
        )
        assert len(streams[0].entries) == 1

        properties = json.loads(streams[0].entries[0].line)
        assert properties["resourceType"] == "Key Vault"
        assert properties["End Time UTC"] == "02/20/2025 18:44:10"
        assert (
            properties["All vault operations in last 24 hours"]
            == "[Authentication:1, SecretGet:3, VaultGet:1, SecretList:5]"
        )
        assert properties["Suspicious Operations"] == "[SecretGet:3, SecretList:5]"


def test_deserialization_extracted_fields():
    f = Filter(".properties.log | fromjson")
    config = Config(additional_labels={}, filter=f)
    with open("tests/audit_log.json", "rb") as f:
        streams = list(stream_from_event_body(f, config))
        assert len(streams) == 1
        assert (
            streams[0].labels
            == '{job="integrations/azure-logexport",category="kube-audit"}'
        )

        event = json.loads(streams[0].entries[0].line)
        assert event["kind"] == "Event"
        assert event["apiVersion"] == "audit.k8s.io/v1"
        assert event["level"] == "Metadata"
        assert event["stage"] == "ResponseComplete"
        assert event["verb"] == "patch"


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
    assert (
        create_labels_string(None, None, {}) == '{job="integrations/azure-logexport"}'
    )
    assert (
        create_labels_string("cat1", "type1", {})
        == '{job="integrations/azure-logexport",category="cat1",type="type1"}'
    )
    assert (
        create_labels_string(None, "type1", {})
        == '{job="integrations/azure-logexport",type="type1"}'
    )
    assert (
        create_labels_string("cat1", None, {})
        == '{job="integrations/azure-logexport",category="cat1"}'
    )
    assert (
        create_labels_string("cat1", None, {"cluster": "dev"})
        == '{job="integrations/azure-logexport",cluster="dev",category="cat1"}'
    )
