import jq  # type: ignore

from logexport.push import push_pb2


class FilterError(ValueError):
    """Error raised when a filter fails to execute."""

    def __init__(self, message: str):
        super().__init__(message)


class Filter:
    def __init__(self, filter: str | None):
        try:
            self.filter = jq.compile(filter) if filter else None
        except ValueError as e:
            raise FilterError(f"Error compiling filter: {e}") from e

    def apply(self, line: str) -> dict | list | str | None:
        if self.filter is None:
            return line

        try:
            r = self.filter.input(line).all()
        except ValueError as e:
            raise FilterError(f"Error executing filter: {e}") from e

        if len(r) == 0:
            return None
        elif len(r) == 1:
            return r[0]
        else:
            return r
