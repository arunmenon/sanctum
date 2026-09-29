"""M6 on sanctum-ref: EX-09a (decision layer unavailable) on C3 and C5, out of process."""
import json

import pytest

from .conftest import run_ref


@pytest.mark.parametrize("config_id,baseline", [("C3", "c2_run"), ("C5", "c4_run")])
def test_ex09a_decision_layer_unavailable_keeps_candidates(scenario_world, tmp_path, request, config_id, baseline):
    """No provider params: every D2 result is `unavailable` (no value), the response reports
    `decision_layer_unavailable`, and routing keeps every candidate: the same sources as the arm
    without a provider, never fewer and never more."""
    result = run_ref(scenario_world, tmp_path / "run", config_id=config_id,
                     extra_arguments=("--decision-params", str(tmp_path / "missing.yaml")))
    base = request.getfixturevalue(baseline)
    assert result.integrity_ok
    responses = [json.loads(line) for line in (result.out_dir / "responses.jsonl").read_text().splitlines()]
    receipts = [json.loads(line) for line in (result.out_dir / "receipts.jsonl").read_text().splitlines()]
    traces = [json.loads(line) for line in (result.out_dir / "traces.jsonl").read_text().splitlines()]
    base_traces = [json.loads(line) for line in (base.out_dir / "traces.jsonl").read_text().splitlines()]
    for response, receipt, trace, base_trace in zip(responses, receipts, traces, base_traces):
        if receipt["decisions"]:
            assert "decision_layer_unavailable" in response["degraded_reasons"]
            assert all(d["status"] == "unavailable" and d["value"] is None for d in receipt["decisions"])
        assert {c["source_id"] for c in trace["calls"]} == {c["source_id"] for c in base_trace["calls"]}
    assert [s.safe_grounded_success for s in result.scores] == [s.safe_grounded_success for s in base.scores]


def test_c3_receipts_carry_d2_decisions(scenario_world, tmp_path):
    result = run_ref(scenario_world, tmp_path / "run", config_id="C3")
    receipts = [json.loads(line) for line in (result.out_dir / "receipts.jsonl").read_text().splitlines()]
    decisions = [d for receipt in receipts for d in receipt["decisions"]]
    assert decisions and all(d["provider"] == "standin" and d["status"] == "answered" for d in decisions)
    # D2 never judges a must-consult source
    for receipt, response in zip(receipts, (json.loads(l) for l in (result.out_dir / "responses.jsonl").read_text().splitlines())):
        required = {s["source_id"] for s in response["sources"] if "must_consult" in s["reasons"]}
        assert not required & {d["value"]["source"] for d in receipt["decisions"]}
