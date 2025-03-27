from dataclasses import dataclass

import jq
import pytest

from logexport.filter import Filter, FilterError
from logexport.push import push_pb2


def test_filter():
    @dataclass
    class TestCase:
        filter: str
        input: dict
        expected: dict | str

    test_cases = [
        TestCase(
            ".",
            {"message": "hello"},
            [{"message": "hello"}],
        ),
        TestCase(
            ".message",
            {"message": "hello", "other": "field"},
            ["hello"],
        ),
        TestCase(".not_existing", {"message": "hello", "other": "field"}, []),
        TestCase(
            '.|[.message,.uid]|join(",")',
            {"message": "hello", "uid": "123", "dropped": True},
            ["hello,123"],
        ),
        TestCase(
            ".messages[].message",
            {"messages": [{"message": "hello"}, {"message": "world"}]},
            ["hello", "world"],
        ),
        TestCase(
            ".messages[].message",
            {"messages": [{"message": "hello"}]},
            ["hello"],
        ),
    ]

    for case in test_cases:
        filter = Filter(case.filter)
        assert filter.apply(case.input) == case.expected


def test_filter_error():
    with pytest.raises(FilterError):
        Filter("broken filter").apply({"message": "hello"})
