"""Runner and gateway (plan M2 task 5, decision 9)."""
import json
import os
import subprocess
import sys
from dataclasses import asdict, fields
from pathlib import Path

import anyio
import pytest
from mcp import ClientSession
from mcp.server.fastmcp import FastMCP

from sanctum_contracts import EvidenceResponse, Receipt, RetrieveRequest
from sanctum_eval.load import load_gold, load_trace
from sanctum_eval.metrics import score_case
from sanctum_eval.trace import ObservedTrace
from sanctum_hubs.corpus import HubStore
from sanctum_hubs.tokens import TokenService
from sanctum_run.gateway import GatewayHandle, HubGateway, released_hub_ids
from sanctum_run.runner import DEFAULT_HUBS_CONFIG, DEFAULT_M0_PRINCIPAL_ALIASES, load_principal_aliases, RunConfig, run
from sanctum_run.sut import SUTContext, StubSUTAdapter, load_call_plan
from sanctum_stub.stub import StubSUT
from sanctum_world.render import build
from tests.helpers.probe_sut import FanOutProbeSUT, RecordingSUT

ROOT = Path(__file__).resolve().parents[1]
GOLD_M0 = ROOT / "gold" / "m0"
M0_TRACES = ROOT / "tests" / "fixtures" / "m0" / "traces"
SEED = 20260930
GOLD_ONLY_KEYS = {"case_id", "bundle_id", "family", "principal", "scenario_script", "answerable",
                  "interpretation_policy", "interpretations", "obligations", "source_obligations",
                  "relations", "forbidden", "expected"}


@pytest.fixture(scope="module")
def world_build(tmp_path_factory) -> Path:
    out_dir = tmp_path_factory.mktemp("runner-build") / "world"
    build(ROOT / "world", SEED, out_dir)
    return out_dir


GOLD_M1 = ROOT / "gold" / "m1"


def _config(world_build: Path, out_dir: Path, sut_name: str) -> RunConfig:
    return RunConfig(cases_dir=GOLD_M0, out_dir=out_dir, seed=SEED, sut_name=sut_name,
                     world_build_dir=world_build,
                     principal_aliases=load_principal_aliases(DEFAULT_M0_PRINCIPAL_ALIASES))


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def test_stub_run_is_schema_valid_and_scores_like_score_m0(world_build, tmp_path):
    result = run(StubSUTAdapter(load_call_plan(M0_TRACES)), _config(world_build, tmp_path / "run", "stub"))
    out_dir = result.out_dir
    manifest = json.loads((out_dir / "manifest.json").read_text())
    for key in ("world_manifest_sha256", "seed", "config_id", "failure_profile", "git_commit",
                "git_dirty", "git_diff_sha256"):
        assert key in manifest
    assert manifest["integrity"] == {"ok": True, "anomalies": 0}
    assert (out_dir / "anomalies.jsonl").read_text() == ""
    assert manifest["failure_profile"] == "none" and manifest["seed"] == SEED

    responses = [EvidenceResponse.model_validate(row) for row in _read_jsonl(out_dir / "responses.jsonl")]
    receipts = [Receipt.model_validate(row) for row in _read_jsonl(out_dir / "receipts.jsonl")]
    traces = [ObservedTrace.model_validate(row) for row in _read_jsonl(out_dir / "traces.jsonl")]
    assert len(responses) == len(receipts) == len(traces) == 3

    stub = StubSUT()
    expected_scores = []
    for gold_path in sorted(GOLD_M0.glob("*.yaml")):
        gold = load_gold(gold_path)
        response, receipt = stub.retrieve(RetrieveRequest.model_validate(gold.request.model_dump()))
        fixture_trace = load_trace(M0_TRACES / f"{gold.request.request_id}.json")
        expected_scores.append(asdict(score_case(gold, response, receipt, fixture_trace)))
    assert [asdict(score) for score in result.scores] == expected_scores
    assert _read_jsonl(out_dir / "scores.jsonl") == json.loads(json.dumps(expected_scores))

    for trace in traces:
        fixture_trace = load_trace(M0_TRACES / f"{trace.request_id}.json")
        assert trace == fixture_trace


def test_fan_out_probe_gets_one_ok_call_per_released_hub(world_build, tmp_path):
    released = released_hub_ids(DEFAULT_HUBS_CONFIG)
    assert "incidenthub" not in released and len(released) == 4
    probe = FanOutProbeSUT()
    result = run(probe, _config(world_build, tmp_path / "probe", "probe"))
    for row in _read_jsonl(result.out_dir / "traces.jsonl"):
        trace = ObservedTrace.model_validate(row)
        assert sorted(call.source_id for call in trace.calls) == released
        assert all(call.outcome == "ok" and call.audience_valid for call in trace.calls)
    assert all("error" not in payload for payload in probe.payloads.values())


def test_m1_runs_on_world_principals_without_aliases(world_build, tmp_path):
    cases = sorted(GOLD_M1.glob("*.yaml"))
    world_principals = TokenService(world_build / "identity" / "principals.json", "x").principals
    assert all(load_gold(path).principal in world_principals for path in cases)
    config = RunConfig(cases_dir=GOLD_M1, out_dir=tmp_path / "m1", seed=SEED, sut_name="probe",
                       config_id="probe", world_build_dir=world_build)
    assert config.principal_aliases is None
    result = run(FanOutProbeSUT(), config)
    traces = [ObservedTrace.model_validate(row) for row in _read_jsonl(result.out_dir / "traces.jsonl")]
    assert len(traces) == len(result.scores) == len(cases)
    released = released_hub_ids(DEFAULT_HUBS_CONFIG)
    for trace in traces:
        assert sorted(call.source_id for call in trace.calls) == released
        assert all(call.outcome == "ok" and call.audience_valid for call in trace.calls)


def test_m0_aliases_map_only_onto_world_principals(world_build):
    aliases = load_principal_aliases(DEFAULT_M0_PRINCIPAL_ALIASES)
    world_principals = TokenService(world_build / "identity" / "principals.json", "x").principals
    m0_principals = {load_gold(path).principal for path in GOLD_M0.glob("*.yaml")}
    assert set(aliases) == m0_principals
    assert set(aliases.values()) <= set(world_principals)


def test_sut_request_carries_no_gold_and_context_is_token_plus_gateway(world_build, tmp_path):
    recorder = RecordingSUT()
    run(recorder, _config(world_build, tmp_path / "recorded", "recorder"))
    assert len(recorder.requests) == 3
    for payload in recorder.requests:
        assert set(payload) <= set(RetrieveRequest.model_fields)
        assert not set(payload) & GOLD_ONLY_KEYS
    assert {field.name for field in fields(SUTContext)} == {"caller_token", "gateway"}


def test_sut_reaches_hubs_only_through_the_gateway(world_build, tmp_path):
    recorder = RecordingSUT()
    run(recorder, _config(world_build, tmp_path / "isolated", "recorder"))
    forbidden_types = (HubStore, TokenService, HubGateway, FastMCP, ClientSession)
    for context in recorder.contexts:
        assert isinstance(context.caller_token, str)
        handle = context.gateway
        assert isinstance(handle, GatewayHandle)
        assert not hasattr(handle, "__dict__")
        public_values = [getattr(handle, name) for name in dir(handle) if not name.startswith("_")]
        assert not any(isinstance(value, forbidden_types) for value in public_values)
        assert {name for name in dir(handle) if not name.startswith("_")} == {"call", "hub_ids"}
        # the caller token is for audience `sanctum`; it carries no secret or store handle
        assert "secret" not in context.caller_token


class TokenTheftSUT:
    """Reproduces the validator's H1 exploit: reach the token service through the handle's
    mangled slot, mint an admin-probe caller token, and try to use it."""

    def __init__(self):
        self.payloads: dict = {}

    async def retrieve(self, request, context):
        gateway = context.gateway._GatewayHandle__gateway
        stolen = gateway._token_service.issue_caller_token("admin-probe")
        gateway.bind(request.request_id, stolen)  # rebinding is visible too: the exchange is checked
        self.payloads["rebound"] = await context.gateway.call("dochub", "search", {"query": "CANARY"})
        return StubSUT().retrieve(request)


def test_token_theft_through_the_handle_is_detected(world_build, tmp_path):
    sut = TokenTheftSUT()
    result = run(sut, _config(world_build, tmp_path / "theft", "theft"))
    assert not result.integrity_ok
    kinds = {entry["kind"] for entry in result.anomalies}
    assert "caller_token_issued_during_sut_call" in kinds
    manifest = json.loads((result.out_dir / "manifest.json").read_text())
    assert manifest["integrity"]["ok"] is False
    assert _read_jsonl(result.out_dir / "anomalies.jsonl") == result.anomalies


def test_exchanged_token_must_name_the_bound_principal(world_build):
    async def scenario():
        service = TokenService(world_build / "identity" / "principals.json", "bind-secret")
        own_token = service.issue_caller_token("kestrel-payments")
        async with HubGateway(world_build, ["dochub"], service) as gateway:
            handle = gateway.handle("req-bound", own_token)
            original_exchange = service.exchange
            # a SUT that swaps the exchange result for another principal's hub token
            service.exchange = lambda token, audience: original_exchange(
                service.issue_caller_token("admin-probe"), audience)
            with gateway.sut_call("req-bound"):
                payload = await handle.call("dochub", "search", {"query": "retry"})
            return payload, gateway.trace("req-bound"), gateway.anomalies("req-bound")

    payload, trace, anomalies = anyio.run(scenario)
    assert payload["error"]["code"] == "denied_or_not_found"
    assert [(call.outcome, call.audience_valid) for call in trace.calls] == [("denied", False)]
    assert {entry["kind"] for entry in anomalies} >= {"principal_mismatch"}


def test_handle_call_takes_no_token():
    import inspect
    assert list(inspect.signature(GatewayHandle.call).parameters) == ["self", "hub_id", "tool", "arguments"]


def test_run_lab_stub_on_m1_exits_with_clear_message(world_build, tmp_path):
    completed = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "run_lab.py"), "--sut", "stub", "--cases", str(GOLD_M1),
         "--world-build", str(world_build), "--out", str(tmp_path / "m1-stub")],
        cwd=ROOT, capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": f"{ROOT / 'src'}{os.pathsep}{ROOT}"})
    assert completed.returncode != 0
    assert "run_lab: the stub has no canned responses" in completed.stderr
    assert "Traceback" not in completed.stderr and "ExceptionGroup" not in completed.stderr


def test_runs_directory_is_gitignored():
    assert "runs/" in (ROOT / ".gitignore").read_text().splitlines()
    tracked = subprocess.run(["git", "check-ignore", "-q", "runs/example/manifest.json"], cwd=ROOT)
    assert tracked.returncode in (0, 128)  # 128: not a git checkout, the .gitignore line suffices
