"""Regression: no `sufficient` when a source authoritative for a needed fact kind failed.

Replays the overclaims found by the M6 failure matrix (runs/m6-failures, seed 20260930, real
latency scale): the failed source was the owner of a fact kind the question needs (code for
deployed values, skills for a skill's procedure) but not a must-consult source, and the SUT
answered `sufficient` from the others. Checked with the evaluator's own honesty rule."""
import json
import shutil

import pytest

from sanctum_eval.degradation import case_honesty
from sanctum_eval.load import load_gold

from .conftest import ROOT, SEED, run_ref

CASES = [
    ("C2", "flaky", "dev", "dev-056"),
    ("C4", "degraded", "dev", "dev-010"),
    ("C4", "skillhub_timeout", "scenarios", "sc-fx-17-1"),
    ("C2", "skillhub_timeout", "dev", "dev-044"),
]


@pytest.mark.parametrize("config_id,profile,gold_set,case_id", CASES, ids=[f"{c[0]}-{c[1]}-{c[3]}" for c in CASES])
def test_failed_authoritative_source_is_never_sufficient(scenario_world, tmp_path, config_id, profile, gold_set, case_id):
    assert SEED == 20260930
    cases = tmp_path / "cases"
    cases.mkdir()
    gold_path = ROOT / "gold" / gold_set / f"{case_id}.yaml"
    shutil.copy(gold_path, cases)
    result = run_ref(scenario_world, tmp_path / "run", config_id=config_id, failure_profile=profile, cases_dir=cases)
    response = json.loads((result.out_dir / "responses.jsonl").read_text().splitlines()[0])
    trace = json.loads((result.out_dir / "traces.jsonl").read_text().splitlines()[0])
    honesty = case_honesty(load_gold(gold_path), response, trace)
    assert not honesty.overclaimed, (response["evidence_status"], response["sources"])
    failed = {c["source_id"] for c in trace["calls"]} - {c["source_id"] for c in trace["calls"] if c["outcome"] == "ok"}
    if failed and response["evidence_status"] != "insufficient":
        assert "required_source_unavailable" in response["reasons"] or response["evidence_status"] != "sufficient"
