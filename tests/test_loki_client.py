import pytest

from logexport.loki.client import LokiClient, LokiClientError
from logexport.push import push_pb2
from loki_test_server import LokiContainer

loki = LokiContainer()


@pytest.fixture(scope="module", autouse=True)
def setup(request):
    loki.start()

    def remove_container():
        loki.stop()

    request.addfinalizer(remove_container)


@pytest.fixture
def client() -> LokiClient:
    return loki.get_client()


def test_push(client: LokiClient):
    entry = push_pb2.EntryAdapter()
    entry.line = "one line"
    entry.timestamp.GetCurrentTime()

    stream = push_pb2.StreamAdapter(
        labels='{foo="bar"}',
        entries=[entry],
    )
    client.push([stream])

    res = client.query_range('{foo="bar"}')
    assert res["status"] == "success"
    assert res["data"]["result"][0]["values"][0][1] == "one line"


def test_push_non_retryable_error(client: LokiClient):
    entry = push_pb2.EntryAdapter()
    entry.line = "one line"
    entry.timestamp.FromSeconds(0)

    stream = push_pb2.StreamAdapter(
        labels='{foo="bar"}',
        entries=[entry],
    )
    with pytest.raises(LokiClientError) as e:
        client.push([stream])
    assert e.value.is_retryable() == False


def test_push_empty_stream(client: LokiClient):
    client.push([])
    stream = push_pb2.StreamAdapter(
        labels='{foo="bar"}',
        entries=[],
    )
    client.push([stream])
