"""E3 evaluator side: D6/D4 calibration labels from gold, D6 conflict metrics, D4 reorder-only gate."""
import json
from pathlib import Path
from types import SimpleNamespace

from sanctum_contracts import EvidenceResponse, Receipt
from sanctum_eval.calibration_labels import d4_labels, d6_labels, labels_from_run
from sanctum_eval.metrics import (
    d4_reorder_violations, false_conflicts_flagged, relation_type_accuracy, score_case,
)

ROOT = Path(__file__).resolve().parents[1]

# m0-001: ev-a1 covers the codehub witness, ev-b1 the skillhub witness of relation r1
# (policy_implementation_divergence).


def _unit(response, evidence_id, **changes):
    base = next(unit for unit in response["evidence"] if unit["evidence_id"] == "ev-a1")
    return {**base, "evidence_id": evidence_id, **changes}


def test_d6_labels_follow_gold_relations(case):
    gold, response, _, _ = case("m0-001")
    other = _unit(response, "ev-x", artifact_id="art-other", native_ref="codehub:art-other@R42#100-200")
    units = EvidenceResponse.model_validate({**response, "evidence": response["evidence"] + [other]}).evidence
    labels = d6_labels(gold, units, [("ev-a1", "ev-b1"), ("ev-b1", "ev-a1"), ("ev-a1", "ev-x"), ("ev-a1", "ev-gone")])
    assert labels == {("ev-a1", "ev-b1"): 1, ("ev-b1", "ev-a1"): 1, ("ev-a1", "ev-x"): 0, ("ev-a1", "ev-gone"): 0}


def test_d4_labels_follow_necessary_spans(case):
    gold, response, _, _ = case("m0-001")
    outside = _unit(response, "ev-far", span={"start": 900, "end": 950}, native_ref="codehub:art-rc@R42#900-950")
    wrong_version = _unit(response, "ev-old", source_version="R40", native_ref="codehub:art-rc@R40#100-200")
    parsed = EvidenceResponse.model_validate({**response, "evidence": response["evidence"] + [outside, wrong_version]})
    labels = d4_labels(gold, parsed.evidence)
    necessary = {span.artifact_id for o in gold.obligations for b in o.bundles for span in b.spans}
    assert labels["ev-far"] == 0 and labels["ev-old"] == 0
    assert labels["ev-a1"] == int("art-rc" in necessary)


def test_labels_from_run_keys_by_case(case, tmp_path):
    gold, response, receipt, _ = case("m0-001")
    (tmp_path / "responses.jsonl").write_text(json.dumps(response) + "\n")
    (tmp_path / "receipts.jsonl").write_text(json.dumps(receipt) + "\n")
    cases = tmp_path / "cases"
    cases.mkdir()
    (cases / "m0-001.yaml").write_text((ROOT / "gold" / "m0" / "m0-001.yaml").read_text())
    assert labels_from_run("d6", tmp_path, cases) == {("m0-001", "ev-a1|ev-b1"): 1}
    d4 = labels_from_run("d4", tmp_path, cases)
    assert set(d4) == {("m0-001", unit["evidence_id"]) for unit in response["evidence"]}


def test_false_conflicts_and_relation_type_accuracy(case):
    gold, response, _, _ = case("m0-001")
    parsed = EvidenceResponse.model_validate(response)
    assert false_conflicts_flagged(gold, parsed) == 0 and relation_type_accuracy(gold, parsed) == 1.0
    extra = _unit(response, "ev-x", artifact_id="art-other", native_ref="codehub:art-other@R42#100-200")
    mistyped = {**response, "evidence": response["evidence"] + [extra], "conflicts": [
        {**response["conflicts"][0], "relation_type": "version_difference"},
        {"conflict_id": "c2", "a": "ev-a1", "b": "ev-x", "relation_type": "contradiction", "status": "possible_conflict"}]}
    parsed = EvidenceResponse.model_validate(mistyped)
    assert false_conflicts_flagged(gold, parsed) == 1 and relation_type_accuracy(gold, parsed) == 0.0


def _d4_decision(rules_only_packed):
    return {"status": "answered", "value": {"scores": {}, "rules_only_packed": rules_only_packed}, "target": "D4",
            "disposition": "use", "provider": "local-test", "model_version": "m", "policy_version": "d4-noul-v1",
            "latency_ms": 5, "cost": 0.0}


def test_d4_reorder_only_gate(case):
    gold, response, receipt, trace = case("m0-001")
    parsed = EvidenceResponse.model_validate(response)
    assert d4_reorder_violations(parsed, Receipt.model_validate(receipt)) is None          # no D4 decision
    kept = Receipt.model_validate({**receipt, "decisions": [_d4_decision(["ev-a1", "ev-b1"])]})
    assert d4_reorder_violations(parsed, kept) == []
    dropped = Receipt.model_validate({**receipt, "decisions": [_d4_decision(["ev-a1", "ev-b1", "ev-rules-only"])]})
    assert d4_reorder_violations(parsed, dropped) == ["ev-rules-only"]
    score = score_case(gold, parsed, dropped, trace)
    assert "d4_reorder_only" in score.gates_failed and not score.safe_grounded_success


def test_report_counts_model_calls_per_decision_and_conflicts(tmp_path):
    from tools.report import render_conflicts, render_system_one

    run_dir = tmp_path / "C4-d6"
    run_dir.mkdir()
    calls = [{"provider": "local-test", "model": "m1", "profile": "strict", "round": r, "questions": q,
              "outcome": "ok", "reason": None, "elapsed_ms": ms, "calls": 1}
             for r, q, ms in (("d6", ["d6:ev-a1|ev-b1"], 30.0), ("d6", ["d6:ev-c|ev-d"], 50.0), ("d4", ["d4:ev-a1"], 90.0))]
    (run_dir / "traces.jsonl").write_text(json.dumps({"request_id": "r", "calls": [], "model_calls": calls}) + "\n")
    view = SimpleNamespace(dir=run_dir, config_id="C4+D6", manifest={"system_one": {"provider": "local-test",
                                                                                     "resolved_models": ["m1"],
                                                                                     "profile": "strict"}},
                           scores={"a": {"conflict_witnesses": 1.0, "false_conflicts_flagged": 2,
                                         "relation_type_accuracy": 0.5},
                                   "b": {"conflict_witnesses": None, "false_conflicts_flagged": 0,
                                         "relation_type_accuracy": None}})
    text = "\n".join(render_system_one([view]))
    assert "| C4+D6 | D4 | local-test | m1 | strict | 1 | ok 1 | 90.0 | 90.0 |" in text
    assert "| C4+D6 | D6 | local-test | m1 | strict | 2 | ok 2 | 30.0 | 50.0 |" in text
    assert "| C4+D6 | 1.00 | 2 | 0.50 |" in "\n".join(render_conflicts([view]))
