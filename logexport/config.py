import os
from typing import Final, Mapping

import jq

ADDITIONAL_LABEL_PREFIX: Final[str] = "ADDITIONAL_LABEL_"
FILTER: Final[str] = "FILTER"


def get_additional_labels() -> dict[str, str]:
    """Returns a dictionary of additional labels to add to the exported streams.
    The labels are configured through environment variables."""
    return get_additional_labels_from_mapping(os.environ)


def get_additional_labels_from_mapping(env: Mapping[str, str]) -> dict[str, str]:
    labels = {}
    for key, value in env.items():
        if key.startswith(ADDITIONAL_LABEL_PREFIX):
            label_name = key[len(ADDITIONAL_LABEL_PREFIX) :]
            if label_name:
                label_name = label_name.replace(",", "_")
                labels[label_name] = value.replace(",", "_")

    return labels


def get_filter() -> jq._Program | None:
    """Returns a jq filter to apply to the exported streams.
    The filter is configured through an environment variable."""
    return get_filter_from_mapping(os.environ.get(FILTER))


def get_filter_from_mapping(filter: str | None) -> jq._Program | None:
    if filter is not None:
        return jq.compile(filter)

    return None
