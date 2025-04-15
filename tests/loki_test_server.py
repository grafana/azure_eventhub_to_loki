from typing import TYPE_CHECKING

from requests import ConnectionError, HTTPError, get
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_container_is_ready

from logexport.loki.client import LokiClient

if TYPE_CHECKING:
    from requests import Response


# TODO: contribute to testcontainers modules
class LokiContainer(DockerContainer):

    def __init__(
        self,
        image: str = "grafana/loki:3.4.3",
        port: int = 3100,
        **kwargs,
    ) -> None:
        super().__init__(image, **kwargs)

        self.port = port

        self.with_exposed_ports(self.port)

    @wait_container_is_ready(ConnectionError, HTTPError)
    def _readiness_check(self) -> None:
        """This is an internal method used to check if the Loki container
        is healthy and ready to receive requests."""
        url = f"{self.get_endpoint()}/ready"
        response: Response = get(url)

        # Loki will return HTTP 503 if it is not ready
        response.raise_for_status()

    def get_endpoint(self) -> str:
        ip = self.get_container_host_ip()
        port = self.get_exposed_port(self.port)
        return f"http://{ip}:{port}"

    def get_client(self) -> "LokiClient":
        return LokiClient(self.get_endpoint())

    def start(self) -> "LokiContainer":
        """This method starts the Loki container and runs the readniness check
        to verify that the container is ready to use."""
        super().start()
        self._readiness_check()
        return self
