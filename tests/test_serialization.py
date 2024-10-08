import json
from function_app import Message, records


def test_deserialization_message():
    load = {"properties": {"key": "value"}, "time": "2024-06-05T10:47:31.676Z"}
    message = Message.from_json(load)
    assert json.loads(message.body) == {
        "time": "2024-06-05T10:47:31.676Z",
        "properties": {"key": "value"},
    }
    assert message.attributes == {"key": "value"}
    assert message.timestamp.day == 5


def test_deserialization_records():
    messages = list()
    with open("tests/record_sample.json", "rb") as f:
        messages = list(records(f))

    assert len(messages) == 2
