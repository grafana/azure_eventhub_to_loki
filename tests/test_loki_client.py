import pytest
from loki_test_server import LokiContainer

from logexport.loki.client import LokiClient
from logexport.push import push_pb2

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

    res = client.query('{foo="bar"}')
    assert res["status"] == "success"
    assert res["data"]["result"][0]["values"][0][1] == "one line"
