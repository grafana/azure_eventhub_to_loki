import json
from dataclasses import dataclass
from logexport.deserialize import entry_from_json, get_timestamp, stream_from_bytes
from logexport.push import push_pb2


def test_deserialization_message():
    load = {"properties": {"key": "value"}, "time": "2024-06-05T10:47:31.676Z"}
    entry = entry_from_json(load)
    assert json.loads(entry.line) == {
        "time": "2024-06-05T10:47:31.676Z",
        "properties": {"key": "value"},
    }
    assert push_pb2.LabelPairAdapter(name="key", value="value") in entry.structuredMetadata
    assert entry.timestamp.ToSeconds() == 1717584451


def test_deserialization_records():
    with open("tests/record_sample.json", "rb") as f:
        stream = stream_from_bytes(f)
        assert len(stream.entries) == 2

def test_deserialization_timestamp():
    @dataclass
    class TestCase:
        field: str
        input: dict 
        expected: int

    test_cases = [
            TestCase("timestamp", {"timestamp": "2024-06-05T10:47:31.676Z"}, "2024-06-05T10:47:31.676Z"),
            TestCase("timeStamp", {"timeStamp": "2024-06-05T10:47:31.676Z"},"2024-06-05T10:47:31.676Z"),
            TestCase("time", {"time": "2024-06-05T10:47:31.676Z"},"2024-06-05T10:47:31.676Z"),
            TestCase("created", {"time": "2024-06-05T10:47:31.676Z"}, "2024-06-05T10:47:31.676Z"),
    ]

    for case in test_cases:
        ts = get_timestamp(case.input)
        assert ts == case.expected
