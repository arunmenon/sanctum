"""Register row 24: the intermittent crash "unhandled errors in a TaskGroup" was ProcessSUT's
per-request timeout (deadline + 30 s grace) raising TimeoutError out of the runner's task groups
when a System One round (relaxed profile, slow provider) legitimately took longer. The runner now
(1) extends the per-request limit by the System One rounds' profile deadlines, and (2) records a
request that still times out as a failed case (sut_failures.jsonl) and goes on."""
import json
from pathlib import Path

import pytest
import yaml

import sanctum_run.process_sut as process_sut
from sanctum_run.process_sut import ProcessSUT
from sanctum_run.runner import RunConfig, run
from tests.helpers.systemone_server import ServerBehavior, SystemOneTestServer
from tests.scenarios.conftest import scenario_world  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "gold" / "m1"


def _providers(tmp_path, relaxed_ms):
    data = yaml.safe_load((ROOT / "configs" / "system_one_providers.yaml").read_text())
    data["profiles"]["relaxed"] = {"deadline_ms": relaxed_ms, "max_calls_per_round": 3}
    path = tmp_path / "providers.yaml"
    path.write_text(yaml.safe_dump(data))
    return path


def _run(world, tmp_path, providers):
    return run(ProcessSUT(["--config", "C3", "--decision-provider", "local-test"]), RunConfig(
        cases_dir=GOLD, out_dir=tmp_path / "run", seed=1, sut_name="ref", config_id="C3", world_build_dir=world,
        system_one_provider="local-test", system_one_profile="relaxed", system_one_providers_path=providers))


def test_slow_model_rounds_extend_the_request_limit(scenario_world, tmp_path, monkeypatch):  # noqa: F811
    # before the fix this crashed with ExceptionGroup(... TimeoutError) on the first case
    monkeypatch.setattr(process_sut, "RETRIEVE_GRACE_SECONDS", 0.5)
    with SystemOneTestServer(ServerBehavior(delay_ms=4500)) as server:
        monkeypatch.setenv("SANCTUM_SYSTEMONE_TEST_URL", server.base_url)
        result = _run(scenario_world, tmp_path, _providers(tmp_path, 20000))
    assert result.manifest["sut_failures"] == 0 and len(result.scores) == 10


def test_a_request_that_still_times_out_fails_its_case_not_the_run(scenario_world, tmp_path, monkeypatch):  # noqa: F811
    monkeypatch.setattr(process_sut, "RETRIEVE_GRACE_SECONDS", -3.0 - 3 * 1.0 + 0.05)   # ~0.05 s per request
    with SystemOneTestServer(ServerBehavior(delay_ms=2000)) as server:
        monkeypatch.setenv("SANCTUM_SYSTEMONE_TEST_URL", server.base_url)
        result = _run(scenario_world, tmp_path, _providers(tmp_path, 1000))
    failures = [json.loads(line) for line in (result.out_dir / "sut_failures.jsonl").read_text().splitlines()]
    assert failures and {f["kind"] for f in failures} == {"sut_timeout"}
    assert result.manifest["sut_failures"] == len(failures) and len(result.scores) == 10
    failed = {f["case_id"] for f in failures}
    assert all("sut_timeout" in s.gates_failed and not s.safe_grounded_success
               for s in result.scores if s.case_id in failed)
