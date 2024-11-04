import requests
from requests import Request
from requests.auth import HTTPBasicAuth
import urllib
from logexport.push import push_pb2


class LokiClient:

    endpoint: str
    auth: HTTPBasicAuth | None

    def __init__(
        self, url: str, username: str | None = None, password: str | None = None
    ):
        self.endpoint = url
        if username is not None and password is not None:
            self.auth = HTTPBasicAuth(username, password)

    def push(self, stream: push_pb2.StreamAdapter):
        req = Request(
            "POST",
            urllib.parse.urljoin(self.endpoint, "loki/api/v1/push"),
            data=stream.SerializeToString(),
            headers={"Content-Type": "application/x-protobuf"},
        )
        if self.auth is not None:
            req.auth = self.auth
        res = requests.Session().send(req.prepare())
        res.raise_for_status()