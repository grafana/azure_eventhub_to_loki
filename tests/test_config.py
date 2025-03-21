import jq

from logexport.config import get_additional_labels_from_mapping, get_filter_from_mapping


def test_get_additional_labels():
    assert get_additional_labels_from_mapping({}) == {}
    assert get_additional_labels_from_mapping({"ADDITIONAL_LABEL_a": "b"}) == {"a": "b"}
    assert get_additional_labels_from_mapping(
        {"ADDITIONAL_LABEL_a": "b", "c": "d"}
    ) == {"a": "b"}
    assert get_additional_labels_from_mapping(
        {"ADDITIONAL_LABEL_a": "b", "ADDITIONAL_LABEL_c": "d"}
    ) == {"a": "b", "c": "d"}
    assert get_additional_labels_from_mapping({"ADDITIONAL_LABEL_a,b": "b"}) == {
        "a_b": "b"
    }
    assert get_additional_labels_from_mapping({"ADDITIONAL_LABEL_a": "{}"}) == {
        "a": "{}"
    }
    assert get_additional_labels_from_mapping({"ADDITIONAL_LABEL_": "b"}) == {}


def test_get_filter():
    assert get_filter_from_mapping(None).filter is None
    assert get_filter_from_mapping(".").filter is not None
