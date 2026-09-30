"""D2 through the runner's System One broker, end to end and out of process (design page §5-§8).

C3 names the `local-test` provider; the broker (runner side) calls the local test server. With no
calibration for the resolved model the provider runs shadow-only, so every candidate is kept and
the sources called equal C2's. Model calls are observed by the runner, never listed as receipt
calls, and receipts stay honest."""
import json

from sanctum_run.process_sut import ProcessSUT
from sanctum_run.runner import RunConfig, run
from tests.helpers.systemone_server import ServerBehavior, SystemOneTestServer

from .conftest import SCENARIO_GOLD, SEED


def _rows(result, name):
    return [json.loads(line) for line in (result.out_dir / name).read_text().splitlines()]


def test_c3_brokered_shadow_only_keeps_candidates(scenario_world, c2_run, tmp_path, monkeypatch):
    with SystemOneTestServer(ServerBehavior()) as server:
        monkeypatch.setenv("SANCTUM_SYSTEMONE_TEST_URL", server.base_url)
        result = run(ProcessSUT(["--config", "C3", "--decision-provider", "local-test"]), RunConfig(
            cases_dir=SCENARIO_GOLD, out_dir=tmp_path / "run", seed=SEED, sut_name="ref", config_id="C3",
            world_build_dir=scenario_world, system_one_provider="local-test", system_one_profile="relaxed"))
        received = len(server.behavior.requests)
    assert result.integrity_ok and received > 0
    receipts, traces = _rows(result, "receipts.jsonl"), _rows(result, "traces.jsonl")
    decisions = [d for receipt in receipts for d in receipt["decisions"]]
    assert decisions and all(d["provider"] == "local-test" for d in decisions)
    answered = [d for d in decisions if d["status"] == "answered"]
    assert answered and all(d["model_version"] == "test-model-1" and d["value"]["shadow"] for d in answered)
    assert all(d["value"]["call"] for d in answered)                          # shadow-only: nothing skipped
    for receipt, trace, base in zip(receipts, traces, _rows(c2_run, "traces.jsonl")):
        assert {c["source_id"] for c in receipt["calls"]} == {c["source_id"] for c in trace["calls"]}
        assert "system_one" not in {c["source_id"] for c in receipt["calls"]}
        assert {c["source_id"] for c in trace["calls"]} == {c["source_id"] for c in base["calls"]}
    assert all(score.receipt_honest for score in result.scores)
    assert [s.safe_grounded_success for s in result.scores] == [s.safe_grounded_success for s in c2_run.scores]
