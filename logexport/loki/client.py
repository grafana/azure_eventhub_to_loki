import urllib.parse
from collections.abc import Iterable

import requests
import snappy  # type: ignore
from requests import HTTPError, Request
from requests.auth import HTTPBasicAuth

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
        else:
            self.auth = None

    def push(self, streams: Iterable[push_pb2.StreamAdapter]):
        push_request = push_pb2.PushRequest()
        for stream in streams:
            push_request.streams.append(stream)

        data: bytes = snappy.compress(push_request.SerializeToString())

        req = Request(
            "POST",
            urllib.parse.urljoin(self.endpoint, "/loki/api/v1/push"),
            data=data,
            headers={"Content-Type": "application/x-protobuf"},
        )
        if self.auth is not None:
            req.auth = self.auth
        res = requests.Session().send(req.prepare())
        if 400 <= res.status_code < 500:
            raise HTTPError(
                f"{res.status_code} Client Error for url: {res.url}: {res.text}"
            )
        elif 500 <= res.status_code < 600:
            raise HTTPError(
                f"{res.status_code} Server Error for url: {res.url}: {res.text}"
            )

    def query(self, query: str):
        res = requests.get(
            urllib.parse.urljoin(self.endpoint, "/loki/api/v1/query"),
            params={"query": query},
        )
        res.raise_for_status()
        return res.json()
