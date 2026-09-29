"""Each bad strategy must fail a gate or lose the targeted metric (lab-plan review L05, M1 preview)."""
import copy

from sanctum_contracts import EvidenceResponse, Receipt
from sanctum_eval.metrics import score_case
from sanctum_eval.trace import ObservedCall, ObservedTrace


def run(gold, r, rc, t):
    return score_case(gold, EvidenceResponse.model_validate(r), Receipt.model_validate(rc), t)


def test_always_empty(case):
    gold, r, rc, t = case("m0-001")
    r = copy.deepcopy(r); r["evidence"] = []; r["conflicts"] = []
    r["interpretations"][0]["evidence_ids"] = []; r["interpretations"][0]["conflict_ids"] = []
    s = run(gold, r, rc, t)
    assert s.recall == 0 and s.silent_omission and not s.safe_grounded_success


def test_ids_only(case):
    gold, r, rc, t = case("m0-001")
    r = copy.deepcopy(r)
    for e in r["evidence"]:
        e["text"] = " "
    s = run(gold, r, rc, t)
    assert s.recall == 0 and not s.safe_grounded_success


def test_over_budget(case):
    gold, r, rc, t = case("m0-001")
    r = copy.deepcopy(r); r["budget"]["used"] = 5000
    s = run(gold, r, rc, t)
    assert "budget" in s.gates_failed and not s.safe_grounded_success


def test_generic_gap_does_not_excuse_omission(case):
    gold, r, rc, t = case("m0-001")
    r = copy.deepcopy(r)
    r["evidence"] = [e for e in r["evidence"] if e["source_id"] != "skillhub"]
    r["conflicts"] = []; r["interpretations"][0]["conflict_ids"] = []
    r["interpretations"][0]["evidence_ids"] = ["ev-a1"]
    r["reasons"] = ["no_coverage"]                  # wrong, generic gap
    r["evidence_status"] = "partial"
    s = run(gold, r, rc, t)
    assert s.harmful_omission and s.silent_omission and not s.safe_grounded_success


def test_missing_conflict_flag(case):
    gold, r, rc, t = case("m0-001")
    r = copy.deepcopy(r); r["conflicts"] = []; r["interpretations"][0]["conflict_ids"] = []
    s = run(gold, r, rc, t)
    assert s.conflict_witnesses == 0 and not s.safe_grounded_success


def test_wrongly_typed_conflict(case):
    gold, r, rc, t = case("m0-001")
    r = copy.deepcopy(r); r["conflicts"][0]["relation_type"] = "contradiction"
    s = run(gold, r, rc, t)
    assert s.conflict_witnesses == 0


def test_dishonest_receipt(case):
    gold, r, rc, t = case("m0-001")
    rc = copy.deepcopy(rc)
    rc["calls"].append({"source_id": "memoryhub", "tool": "search_sessions", "status": "ok",
                        "started_ms": 1, "ended_ms": 2})
    s = run(gold, r, rc, t)
    assert "receipt_honesty" in s.gates_failed


def test_wrong_entity_activation(case):
    gold, r, rc, t = case("m0-001")
    rc = copy.deepcopy(rc); rc["activations"][1]["entity_ref"] = "ent-23"
    s = run(gold, r, rc, t)
    assert "wrong_entity_activation" in s.gates_failed


def test_leak(case):
    gold, r, rc, t = case("m0-001")
    r = copy.deepcopy(r); r["evidence"][0]["text"] += " see CANARY-7731"
    s = run(gold, r, rc, t)
    assert "confidentiality" in s.gates_failed


def test_false_ambiguity(case):
    gold, r, rc, t = case("m0-001")
    r = copy.deepcopy(r); r["reasons"] = ["ambiguous_term"]
    s = run(gold, r, rc, t)
    assert s.false_ambiguity and not s.safe_grounded_success


def test_everything_returned_lowers_precision(case):
    gold, r, rc, t = case("m0-001")
    base = run(gold, r, rc, t).precision
    r = copy.deepcopy(r)
    for i in range(10):
        e = copy.deepcopy(r["evidence"][0])
        e.update(evidence_id=f"ev-pad{i}", artifact_id=f"art-noise{i}", exact_token_count=100)
        r["evidence"].append(e)
    assert run(gold, r, rc, t).precision < base


def test_blended_interpretations(case):
    gold, r, rc, t = case("m0-002")
    r = copy.deepcopy(r)
    r["interpretations"][0]["evidence_ids"] = ["ev-b1", "ev-c1"]
    r["interpretations"][1]["evidence_ids"] = []
    s = run(gold, r, rc, t)
    assert s.ambiguity_handled is False and not s.safe_grounded_success


def test_agent_clarification_alone_fails(case):
    gold, r, rc, t = case("m0-002")
    r = copy.deepcopy(r)
    r.update(interpretations=[], evidence=[], reasons=["clarification_requested"], evidence_status="unknown")
    s = run(gold, r, rc, t)
    assert s.ambiguity_handled is False


def test_guessing_one_meaning_fails(case):
    gold, r, rc, t = case("m0-002")
    r = copy.deepcopy(r)
    r["interpretations"] = r["interpretations"][:1]
    r["evidence"] = r["evidence"][:1]
    r["reasons"] = []
    s = run(gold, r, rc, t)
    assert s.ambiguity_handled is False and not s.safe_grounded_success


def test_denied_source_called_anyway(case):
    gold, r, rc, t = case("m0-003")
    t = ObservedTrace(request_id=t.request_id,
                      calls=list(t.calls) + [ObservedCall(source_id="skillhub", tool="search_skills", outcome="denied")])
    rc = copy.deepcopy(rc)
    rc["calls"].append({"source_id": "skillhub", "tool": "search_skills", "status": "denied",
                        "started_ms": 1, "ended_ms": 2})
    s = run(gold, r, rc, t)
    assert "mandatory_source" in s.gates_failed


def test_denied_source_hidden_as_sufficient(case):
    gold, r, rc, t = case("m0-003")
    r = copy.deepcopy(r); r["evidence_status"] = "sufficient"; r["reasons"] = []
    r["sources"][1]["reasons"] = ["not_selected"]
    s = run(gold, r, rc, t)
    assert not s.status["all"] and "mandatory_source" in s.gates_failed and s.silent_omission


def test_wrong_audience_token(case):
    gold, r, rc, t = case("m0-001")
    t = ObservedTrace(request_id=t.request_id,
                      calls=[c.model_copy(update={"audience_valid": False}) for c in t.calls])
    assert "audience" in run(gold, r, rc, t).gates_failed
