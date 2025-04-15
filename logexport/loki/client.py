import logging
import urllib.parse
from collections.abc import Iterable

import requests
import snappy  # type: ignore
from requests import HTTPError, Request
from requests.auth import HTTPBasicAuth

from logexport.push import push_pb2


class LokiClientError(HTTPError):
    """An error occurred when making a request to Loki."""

    def __init__(self, status_code: int, url: str, message: str):
        super().__init__(f"{status_code} Client Error for url: {url}: {message}")
        self.status_code = status_code
        self.url = url
        self.message = message

    def is_retryable(self) -> bool:
        return (
            "entry too far behind" not in self.message
            and "timestamp too old" not in self.message
        )


class LokiServerError(HTTPError):
    """An error occurred when making a request to Loki."""

    def __init__(self, status_code: int, url: str, message: str):
        super().__init__(f"{status_code} Server Error for url: {url}: {message}")
        self.status_code = status_code
        self.url = url
        self.message = message


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
        num_streams = 0
        for stream in streams:
            push_request.streams.append(stream)
            num_streams += 1

        if num_streams == 0:
            logging.info("Skipping push of 0 streams")
            return

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
            raise LokiClientError(res.status_code, res.url, res.text)
        elif 500 <= res.status_code < 600:
            raise LokiServerError(res.status_code, res.url, res.text)

    def query_range(self, query: str):
        res = requests.get(
            urllib.parse.urljoin(self.endpoint, "/loki/api/v1/query_range"),
            params={"query": query},
        )
        if 400 <= res.status_code < 500:
            raise LokiClientError(res.status_code, res.url, res.text)
        elif 500 <= res.status_code < 600:
            raise LokiServerError(res.status_code, res.url, res.text)

        return res.json()
