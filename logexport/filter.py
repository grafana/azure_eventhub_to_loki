import jq

from logexport.push import push_pb2


def apply_filter(line: str, filter: jq._Program) -> dict | list | str | None:
    if filter is None:
        return line

    return filter.input(line).first()
