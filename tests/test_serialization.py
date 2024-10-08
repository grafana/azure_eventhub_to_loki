
from function_app import Message

def test_deserialization():
    json = {
        "body": "test",
        "attributes": {"key": "value"},
        "timestamp": "2024-06-05T10:47:31.676Z"
    }
    message = Message.from_json(json)
    assert message.body == "test"
    assert message.attributes == {"key": "value"}
    assert message.timestamp.day == 5
