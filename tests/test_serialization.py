import json
from function_app import EntryFromJson, StreamFromEvent
from logexport.push import push_pb2


def test_deserialization_message():
    load = {"properties": {"key": "value"}, "time": "2024-06-05T10:47:31.676Z"}
    entry = EntryFromJson(load)
    assert json.loads(entry.line) == {
        "time": "2024-06-05T10:47:31.676Z",
        "properties": {"key": "value"},
    }
    assert entry.structuredMetadata == [
        push_pb2.LabelPairAdapter(name="key", value="value")
    ]
    assert entry.timestamp.ToSeconds() == 1717584451


def test_deserialization_records():
    with open("tests/record_sample.json", "rb") as f:
        stream = StreamFromEvent(f)
        assert len(stream.entries) == 2
