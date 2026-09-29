import pytest
from pydantic import ValidationError

from sanctum_contracts import (
    Applicability, DecisionResult, EvidenceResponse, RetrieveRequest, SourceOutcome,
    load_reason_codes,
)
from sanctum_contracts.enums import EvidenceStatus, ReplayLevel, SourceStatus


def test_closed_enums_match_hld():
    assert {e.value for e in EvidenceStatus} == {"sufficient", "partial", "insufficient", "unknown"}
    assert {e.value for e in SourceStatus} == {"called", "skipped", "timeout", "error", "unsupported_for_mode"}
    assert {e.value for e in ReplayLevel} == {"none", "recompute_on_candidates", "exact_bundle"}
    assert "frozen_corpus" not in {e.value for e in ReplayLevel}  # research profile, not a wire value


def test_request_rejects_credentials_and_unknown_fields():
    base = dict(request_id="req-1", query="q", mode="scoped", budget_tokens=100, deadline_ms=100)
    RetrieveRequest(**base)
    for bad in ("caller_token", "principal", "api_key", "password"):
        with pytest.raises(ValidationError):
            RetrieveRequest(**base, **{bad: "x"})
    with pytest.raises(ValidationError):
        RetrieveRequest(**base, gold={"x": 1})


def test_default_caller_profile_is_agent():
    r = RetrieveRequest(request_id="r", query="q", mode="explore", budget_tokens=1, deadline_ms=1)
    assert r.caller_profile.value == "agent"


def test_reason_codes_versioned_and_attach_points_enforced():
    assert load_reason_codes()["version"] == "1.0.0"
    with pytest.raises(ValidationError):
        SourceOutcome(source_id="s", status="skipped", reasons=["unresolved_term"])  # response-level code
    with pytest.raises(ValidationError):
        SourceOutcome(source_id="s", status="skipped", reasons=[])  # skipped needs a reason
    with pytest.raises(ValidationError):
        SourceOutcome(source_id="s", status="called", reasons=["made_up"])


def test_applicability_never_fabricated():
    Applicability(applicability_status="unknown")
    Applicability(branch="main", applicability_status="partial")
    with pytest.raises(ValidationError):
        Applicability(branch="main", applicability_status="unknown")
    with pytest.raises(ValidationError):
        Applicability(branch="main", applicability_status="known")


def test_decision_failure_is_not_a_zero_score():
    common = dict(target="P(useful)", provider="stub", policy_version="p1", latency_ms=1, cost=0)
    with pytest.raises(ValidationError):
        DecisionResult(status="unavailable", value=0.0, disposition="preserve_candidate", **common)
    DecisionResult(status="unavailable", disposition="preserve_candidate", **common)


def _resp(**kw):
    base = dict(request_id="r", receipt_id="rc", effective_scope_ref="s",
                replay_level="recompute_on_candidates", evidence_status="unknown",
                budget={"requested": 10, "used": 0, "tokenizer_id": "t"})
    base.update(kw)
    return EvidenceResponse(**base)


def test_reference_closure():
    with pytest.raises(ValidationError):
        _resp(conflicts=[{"conflict_id": "c", "a": "ev-x", "b": "ev-y",
                          "relation_type": "contradiction", "status": "possible_conflict"}])
    _resp(conflicts=[{"conflict_id": "c", "a": "ev-x", "b": "ev-y",
                      "relation_type": "contradiction", "status": "possible_conflict"}],
          omitted=[{"ref_id": "ev-x", "reason": "insufficient_budget"},
                   {"ref_id": "ev-y", "reason": "insufficient_budget"}])


def test_round_trip(case):
    _, resp, _, _ = case("m0-001")
    r = EvidenceResponse.model_validate(resp)
    assert EvidenceResponse.model_validate_json(r.model_dump_json()) == r
