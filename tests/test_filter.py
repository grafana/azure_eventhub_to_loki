from dataclasses import dataclass

import jq

from logexport.filter import Filter
from logexport.push import push_pb2


def test_filter():
    @dataclass
    class TestCase:
        filter: str
        input: dict
        expected: dict | str

    test_cases = [
        TestCase(".", {"message": "hello"}, {"message": "hello"}),
        TestCase(".message", {"message": "hello", "other": "field"}, "hello"),
        TestCase(".not_existing", {"message": "hello", "other": "field"}, None),
        TestCase(
            '.|[.message,.uid]|join(",")',
            {"message": "hello", "uid": "123", "dropped": True},
            "hello,123",
        ),
    ]

    for case in test_cases:
        filter = jq.compile(case.filter)
        assert Filter(filter).apply(case.input) == case.expected
