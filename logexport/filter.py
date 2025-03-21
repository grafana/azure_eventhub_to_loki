import jq  # type: ignore

from logexport.push import push_pb2


class Filter:
    def __init__(self, filter):
        self.filter = filter

    def apply(self, line: str) -> dict | list | str | None:
        if self.filter is None:
            return line

        return self.filter.input(line).first()
