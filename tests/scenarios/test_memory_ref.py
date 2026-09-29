"""Memory arms out of process: EX-09b (memory projection unavailable) and release pinning."""
import json

from .conftest import ROOT, run_ref


def _rows(result, name):
    return [json.loads(line) for line in (result.out_dir / name).read_text().splitlines()]


def test_ex09b_memory_unavailable_degrades_visibly(scenario_world, c2_run, tmp_path):
    """No release: every response says `memory_unavailable`, routes from the registry only (never
    wider than C2's plan) and claims no memory release."""
    result = run_ref(scenario_world, tmp_path / "run", config_id="C4", memory_seed=tmp_path / "no-seed")
    assert result.integrity_ok
    c2_sources = [row for row in _rows(c2_run, "traces.jsonl")]
    for response, receipt, trace, c2_trace in zip(_rows(result, "responses.jsonl"), _rows(result, "receipts.jsonl"),
                                                  _rows(result, "traces.jsonl"), c2_sources):
        assert response["degraded_reasons"] == ["memory_unavailable"]
        assert response["memory_release_id"] == "none" and receipt["activations"] == []
        assert {c["source_id"] for c in trace["calls"]} <= {c["source_id"] for c in c2_trace["calls"]}


def test_memory_arms_pin_and_report_the_release(scenario_world, tmp_path):
    result = run_ref(scenario_world, tmp_path / "run", config_id="C4")
    for response, receipt in zip(_rows(result, "responses.jsonl"), _rows(result, "receipts.jsonl")):
        active = (ROOT / "owners" / "memory_seed" / "ACTIVE").read_text().strip()
        assert response["memory_release_id"] == receipt["memory_release_id"] == active
        assert receipt["config_id"] == "C4"
