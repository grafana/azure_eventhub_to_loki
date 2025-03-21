import jq  # type: ignore

from logexport.push import push_pb2


class Filter:
    def __init__(self, filter):
        self.filter = filter

    def apply(self, line: str) -> dict | list | str | None:
        if self.filter is None:
            return line

        r = self.filter.input(line).all()
        if len(r) == 0:
            return None
        return r[0]
