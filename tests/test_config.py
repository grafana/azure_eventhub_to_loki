from logexport.config import get_additional_labels_from_env


def test_get_additional_labels():
    assert get_additional_labels_from_env({}) == {}
    assert get_additional_labels_from_env({"ADDITIONAL_LABEL_a": "b"}) == {"a": "b"}
    assert get_additional_labels_from_env({"ADDITIONAL_LABEL_a": "b", "c": "d"}) == {
        "a": "b"
    }
    assert get_additional_labels_from_env(
        {"ADDITIONAL_LABEL_a": "b", "ADDITIONAL_LABEL_c": "d"}
    ) == {"a": "b", "c": "d"}
