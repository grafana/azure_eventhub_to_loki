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

    def apply(self, line: dict) -> list:
        """Apply the jq filter to the line.

        Returns a list of processed lines or an empty list if the line was filtered out.
        """
        if self.filter is None:
            return [line]

        try:
            r = self.filter.input(line).all()
        except ValueError as e:
            raise FilterError(f"Error executing filter: {e}") from e

        if r is None:
            return []
        elif len(r) == 0:
            return []
        elif len(r) == 1 and r[0] is None:
            return []
        else:
            return r
