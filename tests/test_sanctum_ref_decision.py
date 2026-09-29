"""D2 decision providers (HLD §6.3-§6.7, lab plan §7.3)."""
from pathlib import Path

import pytest
import yaml

from sanctum_contracts import DecisionResult
from sanctum_ref.decision import (
    ProviderNotApproved, RulesProvider, StandinProvider, build_provider, d2_request, tfidf_cosine,
)

ROOT = Path(__file__).resolve().parents[1]
PARAMS = ROOT / "configs" / "d2_standin.yaml"


def test_params_are_fitted_on_dev_with_provenance():
    params = yaml.safe_load(PARAMS.read_text())
    assert params["provenance"]["fitted_on"] == "dev" and "holdout" not in params["provenance"]["cases"]
    assert set(params["descriptors"]) == {"codehub", "skillhub", "dochub", "memoryhub"}
    assert params["bands"]["skip"] < params["bands"]["use"]


def test_rules_keeps_every_candidate():
    result = RulesProvider().decide(d2_request("codehub", "anything", 3000))
    assert result.status.value == "answered" and result.value["call"] and result.disposition.value == "use"


def test_standin_bands_and_uncertainty_keeps(tmp_path):
    params = yaml.safe_load(PARAMS.read_text())
    params["calibration"] = {"a": 10.0, "b": -3.0}
    params["bands"] = {"use": 0.7, "skip": 0.1}
    path = tmp_path / "p.yaml"
    path.write_text(yaml.safe_dump(params))
    provider = StandinProvider(path)
    session = provider.decide(d2_request("memoryhub", "what did I look into last session", 3000))
    code = provider.decide(d2_request("memoryhub", "zzz qqq", 3000))
    assert session.value["p"] > code.value["p"]
    assert code.value["call"] is False and code.disposition.value == "use"      # confident no
    for result in (session, code):
        DecisionResult.model_validate(result.model_dump())
        assert result.target.startswith("P(source") and result.provider == "standin"
    params["calibration"] = {"a": 0.0, "b": 0.0}                                # p = 0.5 everywhere
    path.write_text(yaml.safe_dump(params))
    uncertain = StandinProvider(path).decide(d2_request("codehub", "zzz", 3000))
    assert uncertain.value["call"] is True and uncertain.disposition.value == "preserve_candidate"


def test_standin_unavailable_is_not_a_score(tmp_path):
    result = StandinProvider(tmp_path / "missing.yaml").decide(d2_request("codehub", "q", 3000))
    assert result.status.value == "unavailable" and result.value is None


def test_jev_is_not_approved():
    with pytest.raises(ProviderNotApproved):
        build_provider("jev", PARAMS)


def test_similarity_is_local_and_bounded():
    descriptors = yaml.safe_load(PARAMS.read_text())["descriptors"]
    value = tfidf_cosine("max retries batch size", descriptors["codehub"], descriptors)
    assert 0.0 < value <= 1.0
