import os
from typing import Final, Mapping

ADDITIONAL_LABEL_PREFIX: Final[str] = "ADDITIONAL_LABEL_"


def get_additional_labels() -> dict[str, str]:
    """Returns a dictionary of additional labels to add to the exported streams.
    The labels are configured through environment variables."""
    return get_additional_labels_from_env(os.environ)


def get_additional_labels_from_env(env: Mapping[str, str]) -> dict[str, str]:
    labels = {}
    for key, value in env.items():
        if key.startswith(ADDITIONAL_LABEL_PREFIX):
            labels[key[len(ADDITIONAL_LABEL_PREFIX) :]] = value

    return labels
