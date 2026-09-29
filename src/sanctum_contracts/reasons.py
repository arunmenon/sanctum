from functools import lru_cache
from importlib import resources

import yaml

REASON_CODES_VERSION = None  # populated on load


@lru_cache(maxsize=1)
def load_reason_codes() -> dict:
    global REASON_CODES_VERSION
    text = resources.files(__package__).joinpath("reason_codes.yaml").read_text()
    data = yaml.safe_load(text)
    REASON_CODES_VERSION = data["version"]
    return data


def validate_reasons(reasons: list[str], attach_point: str) -> list[str]:
    codes = load_reason_codes()["codes"]
    for r in reasons:
        if r not in codes:
            raise ValueError(f"unknown reason code: {r!r}")
        if attach_point not in codes[r]["attaches_to"]:
            raise ValueError(f"reason {r!r} cannot attach to {attach_point}")
    return reasons
