import pytest
from pydantic import ValidationError

from sanctum_eval.gold import GoldCase

from .conftest import CASES


def test_gold_cases_load(case):
    for cid in CASES:
        gold, *_ = case(cid)
        assert gold.bundle_id and gold.family


def test_separate_alternatives_needs_two(case):
    gold, *_ = case("m0-002")
    data = gold.model_dump(mode="json")
    data["interpretations"] = data["interpretations"][:1]
    data["obligations"] = data["obligations"][:1]
    with pytest.raises(ValidationError):
        GoldCase.model_validate(data)


def test_request_id_cannot_encode_case(case):
    gold, *_ = case("m0-001")
    data = gold.model_dump(mode="json")
    data["request"]["request_id"] = "req-m0-001"
    with pytest.raises(ValidationError):
        GoldCase.model_validate(data)
