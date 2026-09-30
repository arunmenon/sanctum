"""Runner-side System One broker (design page §6, handshake points 1, 5, 6, 8, 9, 10).

Uses the local /v1/systemone test server (tests/helpers/systemone_server.py; no live calls). Every
provider call must be bound by the broker, validated, observed as a `model_call`, stored for
replay without the key, and the key must never reach the SUT environment or any run output.
"""
import json
from pathlib import Path
from types import SimpleNamespace

import anyio
import pytest
import yaml

from sanctum_hubs.tokens import TokenService
from sanctum_run.gateway import HubGateway, released_hub_ids
from sanctum_run.process_sut import child_environment
from sanctum_run.proxy import GatewayProxy
from sanctum_run.runner import DEFAULT_HUBS_CONFIG
from sanctum_run.system_one_broker import (
    DECIDE_TOOL, ProfileConfig, SystemOneBroker, descriptor_release, load_descriptors, load_provider, load_secret,
)
from sanctum_systemone import CallOutcome, ProviderSpec
from tests.helpers.systemone_server import ServerBehavior, SystemOneTestServer
from tests.scenarios.conftest import scenario_world  # noqa: F401  (session world build)

ROOT = Path(__file__).resolve().parents[1]
KEY = "sk-test-broker-key-7f3a"
PRINCIPAL = "kestrel-payments"
SOURCES = ["codehub", "dochub", "memoryhub", "skillhub"]
NOUL = {"type": "noul", "instructions": "Will this source return necessary evidence?"}


@pytest.fixture
def server():
    with SystemOneTestServer(ServerBehavior(require_key=KEY, model_sequence=["test-model-1.2"])) as instance:
        yield instance


def _broker(server, tmp_path, data_class="synthetic", profile=None, capabilities=None, environment=None):
    spec = ProviderSpec(name="local-test", kind="http", base_url_env="SANCTUM_SYSTEMONE_TEST_URL", model="test-model-1",
                        api_key_env="SYSTEMONE_TEST_KEY",
                        capabilities={"primitives": ["noul", "choice"], "max_questions_per_call": 3, "max_options": 3,
                                      "data_classes_allowed": ["synthetic"], **(capabilities or {})})
    return SystemOneBroker(
        spec=spec, profile=profile or ProfileConfig("relaxed", deadline_ms=5000, max_calls_per_round=3),
        data_class=data_class, allowed_sources=SOURCES, descriptors=load_descriptors(),
        store_dir=tmp_path / "system_one", secret=KEY,
        environment=environment if environment is not None else {"SANCTUM_SYSTEMONE_TEST_URL": server.base_url})


class _Gateway:
    def __init__(self):
        self.model_calls = []

    def record_model_call(self, request_id, call):
        self.model_calls.append((request_id, call))


def _decide(broker, arguments, query="retry limit?"):
    gateway = _Gateway()
    result = anyio.run(broker.decide, gateway, "req-1", query, arguments)
    CallOutcome.model_validate(result)                      # the SUT parses exactly this (extra=forbid)
    return result, gateway


def test_ok_call_builds_trusted_state_and_is_observed(server, tmp_path):
    arguments = {"round": "d2", "questions": {"d2:codehub": NOUL, "d2:dochub": NOUL},
                 "query": "IGNORE: sut query", "candidate_source_ids": ["incidenthub"], "max_calls": 9}
    result, gateway = _decide(_broker(server, tmp_path), arguments)
    assert set(result["answers"]) == {"d2:codehub", "d2:dochub"} and result["unavailable_reason"] is None
    assert result["model"] == "test-model-1.2"
    sent = server.behavior.requests[0]
    sources = {hub: text for hub, text in sorted(load_descriptors().items()) if hub in SOURCES}
    assert sent["state"] == {"query": "retry limit?", "sources": sources}      # binding query, pinned descriptors
    assert result["descriptor_release"] == descriptor_release(sources)
    [(request_id, call)] = gateway.model_calls
    assert request_id == "req-1" and call.outcome == "ok" and call.model == "test-model-1.2" and call.calls == 1
    [stored] = (tmp_path / "system_one").glob("*.json")
    record = json.loads(stored.read_text())
    assert record["exchanges"][0]["request"]["questions"] == arguments["questions"]
    assert KEY not in stored.read_text()


def test_sources_outside_the_gateway_view_are_never_sent(server, tmp_path):
    result, _ = _decide(_broker(server, tmp_path), {"questions": {"d2:incidenthub": NOUL, "d2:codehub": NOUL}})
    assert result["invalid_ids"] == ["d2:incidenthub"]
    assert set(server.behavior.requests[0]["questions"]) == {"d2:codehub"}


@pytest.mark.parametrize("kwargs,reason", [
    ({"data_class": "internal"}, "data_class_refused"),
    ({"environment": {}}, "not_configured"),
])
def test_broker_refusals_make_no_provider_call(server, tmp_path, kwargs, reason):
    result, gateway = _decide(_broker(server, tmp_path, **kwargs), {"questions": {"d2:codehub": NOUL}})
    assert server.behavior.requests == [] and result["answers"] == {}
    assert result["unavailable_reason"] == reason and gateway.model_calls[0][1].reason == reason


def test_over_budget_is_refused_not_truncated(server, tmp_path):
    many_options = {"route": {"type": "choice", "criteria": {str(n): "x" for n in range(4)}}}
    result, _ = _decide(_broker(server, tmp_path), {"questions": many_options})
    assert result["invalid_ids"] == ["route"] and server.behavior.requests == []
    small_state = _broker(server, tmp_path, capabilities={"max_state_chars": 50})
    result, _ = _decide(small_state, {"questions": {"d2:codehub": NOUL}})
    assert result["unavailable_reason"] == "over_budget" and server.behavior.requests == []


def test_calls_capped_by_profile_not_by_sut(server, tmp_path):
    profile = ProfileConfig("strict", deadline_ms=5000, max_calls_per_round=1)
    questions = {f"d2:{hub}": NOUL for hub in SOURCES}                   # 4 questions, 3 per call: 2 calls
    result, _ = _decide(_broker(server, tmp_path, profile=profile), {"questions": questions, "max_calls": 5})
    assert result["unavailable_reason"] == "over_budget" and server.behavior.requests == []
    result, _ = _decide(_broker(server, tmp_path), {"questions": questions, "max_calls": 1})    # SUT may lower
    assert result["unavailable_reason"] == "over_budget"


@pytest.mark.parametrize("invalid", ["unknown_id", "bad_probability", "wrong_type", "not_json"])
def test_invalid_output_is_not_trusted(server, tmp_path, invalid):
    server.behavior.invalid = invalid
    result, gateway = _decide(_broker(server, tmp_path), {"questions": {"d2:codehub": NOUL}})
    assert result["answers"] == {}
    assert result["unavailable_reason"] == "invalid_output" or "d2:codehub" in result["invalid_ids"]
    assert gateway.model_calls[0][1].outcome == "unavailable"


def test_deadline_and_single_retry(server, tmp_path):
    server.behavior.delay_ms = 400
    strict = ProfileConfig("strict", deadline_ms=150, max_calls_per_round=1)
    result, gateway = _decide(_broker(server, tmp_path, profile=strict), {"questions": {"d2:codehub": NOUL}})
    assert result["unavailable_reason"] == "timeout" and gateway.model_calls[0][1].reason == "timeout"
    server.behavior.delay_ms, server.behavior.fail_times = 0, 5
    server.behavior.requests.clear()
    result, _ = _decide(_broker(server, tmp_path), {"questions": {"d2:codehub": NOUL}})
    assert result["unavailable_reason"] == "error" and len(server.behavior.requests) == 2   # one retry only


# ---- through the gateway proxy, with the real gateway trace --------------------------------------
async def _through_proxy(world, broker, out):
    tokens = TokenService(world / "identity" / "principals.json", "broker-test-secret")
    caller = tokens.issue_caller_token(PRINCIPAL)
    async with HubGateway(world, released_hub_ids(DEFAULT_HUBS_CONFIG), tokens) as gateway:
        gateway.system_one = broker
        proxy = await GatewayProxy.create(gateway, world)
        out["tools"] = {tool.name for tool in proxy._tools}
        handle = gateway.handle("req-p", caller)
        proxy.bind("req-p", caller, handle, query="How many retries?")
        with gateway.sut_call("req-p"):
            await handle.call("codehub", "list_repos", {})
            out["ok"] = await proxy.dispatch(DECIDE_TOOL, {"round": "d2", "questions": {"d2:codehub": NOUL}},
                                             "req-p", caller)
            out["forged"] = await proxy.dispatch(DECIDE_TOOL, {"questions": {"d2:codehub": NOUL}},
                                                 "req-p", "forged-token")
        proxy.unbind("req-p", handle)
        out["trace"] = gateway.trace("req-p")
        out["anomalies"] = proxy.anomalies()


def test_proxy_tool_observes_model_calls_apart_from_sources(scenario_world, server, tmp_path):  # noqa: F811
    out = {}
    anyio.run(_through_proxy, scenario_world, _broker(server, tmp_path), out)
    assert DECIDE_TOOL in out["tools"]
    assert set(out["ok"]["answers"]) == {"d2:codehub"}
    assert out["forged"]["error"]["code"] == "denied_or_not_found" and len(server.behavior.requests) == 1
    assert [a["kind"] for a in out["anomalies"]] == ["proxy_call_outside_binding"]
    trace = out["trace"]
    assert trace.sources_attempted() == {"codehub"}                     # the model call is not a source
    assert [(c.provider, c.outcome) for c in trace.model_calls] == [("local-test", "ok")]
    assert server.behavior.requests[0]["state"]["query"] == "How many retries?"   # from the binding


def test_key_stays_runner_side(server, tmp_path, monkeypatch):
    monkeypatch.setenv("SYSTEMONE_TEST_KEY", KEY)
    assert load_secret("SYSTEMONE_TEST_KEY") == KEY
    assert KEY not in child_environment().values() and "SYSTEMONE_TEST_KEY" not in child_environment()
    env_file = tmp_path / ".env"
    env_file.write_text(f"OTHER=1\nSYSTEMONE_FILE_KEY='{KEY}'\n")
    monkeypatch.delenv("SYSTEMONE_FILE_KEY", raising=False)
    assert load_secret("SYSTEMONE_FILE_KEY", env_file) == KEY
    _decide(_broker(server, tmp_path), {"questions": {"d2:codehub": NOUL}})
    _decide(_broker(server, tmp_path), {"questions": {"d2:incidenthub": NOUL}})
    for path in (tmp_path / "system_one").rglob("*"):
        assert KEY not in path.read_text(), path


def test_provider_file_and_profiles():
    spec, profile = load_provider("local-test", "strict")
    assert spec.kind == "http" and (profile.deadline_ms, profile.max_calls_per_round) == (150, 1)
    with pytest.raises(ValueError):
        load_provider("standin", "strict")                                  # in-SUT provider, not brokered


# ---- runner, provenance and report ---------------------------------------------------------------
def test_runner_records_provider_and_keeps_key_out_of_outputs(scenario_world, server, tmp_path, monkeypatch):  # noqa: F811
    from sanctum_eval.provenance import effective_configuration, record_effective
    from sanctum_run.runner import DEFAULT_M0_PRINCIPAL_ALIASES, RunConfig, load_principal_aliases, run
    from sanctum_run.sut import StubSUTAdapter, load_call_plan

    monkeypatch.setenv("SYSTEMONE_TEST_KEY", KEY)
    monkeypatch.setenv("SANCTUM_SYSTEMONE_TEST_URL", server.base_url)
    result = run(StubSUTAdapter(load_call_plan(ROOT / "tests" / "fixtures" / "m0" / "traces")), RunConfig(
        cases_dir=ROOT / "gold" / "m0", out_dir=tmp_path / "run", seed=1, sut_name="stub",
        world_build_dir=scenario_world, principal_aliases=load_principal_aliases(DEFAULT_M0_PRINCIPAL_ALIASES),
        system_one_provider="local-test", system_one_profile="relaxed"))
    assert result.manifest["system_one"] == {"provider": "local-test", "requested_model": "test-model-1",
                                             "profile": "relaxed", "data_class": "synthetic",
                                             "resolved_models": [], "model_calls": 0}
    manifest = record_effective(result.out_dir, effective_configuration(
        sut="stub", config_id="stub", hubs=result.manifest["hubs"], cases_dir=ROOT / "gold" / "m0"))
    assert manifest["effective"]["system_one"]["provider"] == "local-test"
    for path in result.out_dir.rglob("*"):
        if path.is_file():
            assert KEY not in path.read_text(), path


def test_report_section_counts_model_calls(tmp_path):
    from tools.report import render_system_one

    run_dir = tmp_path / "C3"
    run_dir.mkdir()
    calls = [{"provider": "local-test", "model": "test-model-1.2", "profile": "strict", "round": "d2",
              "questions": ["d2:codehub"], "outcome": outcome, "reason": reason, "elapsed_ms": ms, "calls": 1}
             for outcome, reason, ms in (("ok", None, 40.0), ("ok", None, 60.0), ("unavailable", "timeout", 150.0))]
    (run_dir / "traces.jsonl").write_text(json.dumps({"request_id": "r", "calls": [], "model_calls": calls}) + "\n")
    view = SimpleNamespace(dir=run_dir, config_id="C3", manifest={"system_one": {
        "provider": "local-test", "resolved_models": ["test-model-1.2"], "profile": "strict"}})
    text = "\n".join(render_system_one([view]))
    assert "## System One model calls (reported, not gated)" in text
    assert "| C3 | D2 | local-test | test-model-1.2 | strict | 3 | ok 2, timeout 1 | 60.0 | 150.0 |" in text
    assert render_system_one([SimpleNamespace(dir=tmp_path, config_id="C2", manifest={})]) == []


def test_broker_and_calibration_fit_agree_on_descriptor_release(server, tmp_path):
    from tools.fit_system_one import broker_descriptors

    descriptors, release = broker_descriptors()
    result, _ = _decide(_broker(server, tmp_path), {"questions": {"d2:codehub": NOUL}})
    assert server.behavior.requests[0]["state"]["sources"] == descriptors
    assert result["descriptor_release"] == release
    import hashlib
    assert release == "sha256:" + hashlib.sha256(json.dumps(descriptors, sort_keys=True).encode()).hexdigest()[:16]


# ---- Round 3 (d6, d4): refs in, broker-read text out -------------------------------------------------
async def _round3(world, broker, out):
    tokens = TokenService(world / "identity" / "principals.json", "broker-test-secret")
    caller = tokens.issue_caller_token(PRINCIPAL)
    async with HubGateway(world, released_hub_ids(DEFAULT_HUBS_CONFIG), tokens) as gateway:
        proxy = await GatewayProxy.create(gateway, world)
        gateway.system_one = broker
        handle = gateway.handle("req-3", caller)
        proxy.bind("req-3", caller, handle, query="retry limit")
        with gateway.sut_call("req-3"):
            found = await handle.call("codehub", "search_code", {"query": "retry"})
            item = found["results"][0]
            row = gateway.stores["codehub"].at_version(item["artifact_id"], item["version"])
            fetched = {"source_id": "codehub", "artifact_id": row.artifact_id, "version": row.version,
                       "start": 0, "end": min(len(row.text), 5000)}
            returned = {result["artifact_id"] for result in found["results"]}
            unfetched_row = next(r for r in gateway.stores["codehub"].rows()
                                 if r.artifact_id not in returned and "payments-eng" in r.acl)
            unfetched = {**fetched, "artifact_id": unfetched_row.artifact_id, "version": unfetched_row.version}
            identity_row = next(r for r in gateway.stores["codehub"].rows() if r.acl == ["identity-eng"])
            unreadable = {**fetched, "artifact_id": identity_row.artifact_id, "version": identity_row.version}
            out["row_text"] = row.text
            out["result"] = await proxy.dispatch(DECIDE_TOOL, {
                "round": "d6",
                "questions": {"d6:e1|e2": NOUL, "d6:e1|e3": NOUL, "d6:e1|e4": NOUL, "d6:bad": NOUL},
                "items": {"d6:e1|e2": {"refs": [fetched, fetched]},
                          "d6:e1|e3": {"refs": [fetched, unfetched]},
                          "d6:e1|e4": {"refs": [fetched, unreadable]},
                          "d6:bad": {"refs": [fetched]}}}, "req-3", caller)
        proxy.unbind("req-3", handle)
        out["trace"] = gateway.trace("req-3")


def test_round3_sends_only_broker_read_text_of_fetched_readable_refs(scenario_world, server, tmp_path):  # noqa: F811
    out = {}
    anyio.run(_round3, scenario_world, _broker(server, tmp_path), out)
    result = out["result"]
    assert set(result["answers"]) == {"d6:e1|e2"}
    assert set(result["invalid_ids"]) == {"d6:e1|e3", "d6:e1|e4", "d6:bad"}
    assert result["descriptor_release"] == "none"
    [sent] = server.behavior.requests
    assert set(sent["questions"]) == {"d6:e1|e2"}
    [first, second] = sent["state"]["items"]["d6:e1|e2"]
    assert first["text"] == out["row_text"][:1200] and len(first["text"]) <= 1200
    assert set(first) == {"source_id", "version", "environment", "text"}
    assert sent["state"]["query"] == "retry limit"
    assert [call.round for call in out["trace"].model_calls] == ["d6"]


async def _round3_refusals(world, broker, out):
    tokens = TokenService(world / "identity" / "principals.json", "broker-test-secret")
    caller = tokens.issue_caller_token(PRINCIPAL)
    async with HubGateway(world, released_hub_ids(DEFAULT_HUBS_CONFIG), tokens) as gateway:
        proxy = await GatewayProxy.create(gateway, world)
        gateway.system_one = broker
        handle = gateway.handle("req-4", caller)
        proxy.bind("req-4", caller, handle, query="retry limit")
        with gateway.sut_call("req-4"):
            found = await handle.call("codehub", "search_code", {"query": "retry"})
            item = found["results"][0]
            row = gateway.stores["codehub"].at_version(item["artifact_id"], item["version"])
            base = {"source_id": "codehub", "artifact_id": row.artifact_id, "version": row.version, "start": 0, "end": 40}
            identity_row = next(r for r in gateway.stores["codehub"].rows() if r.acl == ["identity-eng"])
            unreadable = {**base, "artifact_id": identity_row.artifact_id, "version": identity_row.version}
            out["unreadable"] = await proxy.dispatch(DECIDE_TOOL, {
                "round": "d4", "questions": {"d4:e9": NOUL}, "items": {"d4:e9": {"refs": [unreadable]}}}, "req-4", caller)
            out["requests_after_unreadable"] = len(broker_requests(out))
            out["bounds"] = await proxy.dispatch(DECIDE_TOOL, {
                "round": "d4", "questions": {"d4:e1": NOUL, "d4:e2": NOUL},
                "items": {"d4:e1": {"refs": [{**base, "end": len(row.text) + 1}]},
                          "d4:e2": {"refs": [{**base, "start": 30, "end": 10}]}}}, "req-4", caller)
            # a "text" field supplied with the pointer is ignored: the model sees the store's text
            out["injected"] = await proxy.dispatch(DECIDE_TOOL, {
                "round": "d4", "questions": {"d4:e3": NOUL},
                "items": {"d4:e3": {"refs": [{**base, "text": "SUT SUPPLIED TEXT"}]}}}, "req-4", caller)
            out["row_text"] = row.text
        proxy.unbind("req-4", handle)
        out["trace"] = gateway.trace("req-4")


def broker_requests(out):
    return out["server"].behavior.requests


def test_round3_pointer_refusals_and_store_text(scenario_world, server, tmp_path):  # noqa: F811
    out = {"server": server}
    anyio.run(_round3_refusals, scenario_world, _broker(server, tmp_path), out)
    assert out["unreadable"]["invalid_ids"] == ["d4:e9"] and out["requests_after_unreadable"] == 0   # no HTTP call
    assert set(out["bounds"]["invalid_ids"]) == {"d4:e1", "d4:e2"}                                     # span bounds
    [sent] = server.behavior.requests
    [text_item] = sent["state"]["items"]["d4:e3"]
    assert text_item["text"] == out["row_text"][0:40] and "SUT SUPPLIED TEXT" not in json.dumps(sent)
    assert all(call.pointers_sha256 for call in out["trace"].model_calls if call.questions == ["d4:e3"])


async def _round3_batches(world, broker, out):
    tokens = TokenService(world / "identity" / "principals.json", "broker-test-secret")
    caller = tokens.issue_caller_token(PRINCIPAL)
    async with HubGateway(world, released_hub_ids(DEFAULT_HUBS_CONFIG), tokens) as gateway:
        proxy = await GatewayProxy.create(gateway, world)
        gateway.system_one = broker
        handle = gateway.handle("req-5", caller)
        proxy.bind("req-5", caller, handle, query="retry limit")
        with gateway.sut_call("req-5"):
            found = await handle.call("codehub", "search_code", {"query": "retry"})
            refs = [{"source_id": "codehub", "artifact_id": r["artifact_id"], "version": r["version"],
                     "start": 0, "end": 40} for r in found["results"][:3]]
            qids = [f"d4:e{n}" for n in range(len(refs))]
            out["result"] = await proxy.dispatch(DECIDE_TOOL, {
                "round": "d4", "questions": {qid: NOUL for qid in qids},
                "items": {qid: {"refs": [ref]} for qid, ref in zip(qids, refs)}}, "req-5", caller)
        proxy.unbind("req-5", handle)
        out["trace"] = gateway.trace("req-5")


def test_round3_batches_carry_only_their_own_items(scenario_world, server, tmp_path):  # noqa: F811
    # room for about one item per state: the client splits per batch instead of voiding the round
    broker = _broker(server, tmp_path, capabilities={"max_state_chars": 260},
                     profile=ProfileConfig("relaxed", deadline_ms=5000, max_calls_per_round=12))
    out = {}
    anyio.run(_round3_batches, scenario_world, broker, out)
    assert out["result"]["unavailable_reason"] is None and len(out["result"]["answers"]) == 3
    assert len(server.behavior.requests) == 3
    for request in server.behavior.requests:
        assert set(request["state"]["items"]) == set(request["questions"])
    [call] = out["trace"].model_calls
    assert len(call.batch_pointers_sha256) == 3 and len(set(call.batch_pointers_sha256)) == 3


async def _layouts(world, broker, out):
    tokens = TokenService(world / "identity" / "principals.json", "broker-test-secret")
    caller = tokens.issue_caller_token(PRINCIPAL)
    async with HubGateway(world, released_hub_ids(DEFAULT_HUBS_CONFIG), tokens) as gateway:
        proxy = await GatewayProxy.create(gateway, world)
        gateway.system_one = broker
        handle = gateway.handle("req-6", caller)
        proxy.bind("req-6", caller, handle, query="retry backoff schedule")
        with gateway.sut_call("req-6"):
            found = await handle.call("codehub", "search_code", {"query": "retry backoff"})
            r = found["results"][0]
            row = gateway.stores["codehub"].at_version(r["artifact_id"], r["version"])
            ref = {"source_id": "codehub", "artifact_id": r["artifact_id"], "version": r["version"],
                   "start": 0, "end": len(row.text)}
            for layout in ("r3-state-v1", "r3-state-v2", "r3-state-v9"):
                out[layout] = await proxy.dispatch(DECIDE_TOOL, {
                    "round": "d4", "state_layout": layout, "questions": {"d4:e1": NOUL},
                    "items": {"d4:e1": {"refs": [ref]}}}, "req-6", caller)
            out["text"] = row.text
        proxy.unbind("req-6", handle)


def test_round3_state_layouts_and_binding(scenario_world, server, tmp_path):  # noqa: F811
    out = {}
    anyio.run(_layouts, scenario_world, _broker(server, tmp_path), out)
    assert out["r3-state-v1"]["descriptor_release"] == "none"
    assert out["r3-state-v2"]["descriptor_release"] == "r3-state-v2"
    assert out["r3-state-v9"]["invalid_ids"] == ["d4:e1"]                      # unknown layout: nothing sent
    v1, v2 = (request["state"]["items"]["d4:e1"][0] for request in server.behavior.requests)
    assert set(v1) == {"source_id", "version", "environment", "text"}
    assert v2["artifact_id"] and v2["excerpt"] == "\n".join(out["text"][s["start"]:s["end"]] for s in v2["excerpt_spans"])


async def _templates(world, broker, out):
    tokens = TokenService(world / "identity" / "principals.json", "broker-test-secret")
    caller = tokens.issue_caller_token(PRINCIPAL)
    async with HubGateway(world, released_hub_ids(DEFAULT_HUBS_CONFIG), tokens) as gateway:
        proxy = await GatewayProxy.create(gateway, world)
        gateway.system_one = broker
        handle = gateway.handle("req-7", caller)
        proxy.bind("req-7", caller, handle, query="retry backoff")
        with gateway.sut_call("req-7"):
            found = await handle.call("codehub", "search_code", {"query": "retry backoff"})
            r = found["results"][0]
            ref = {"source_id": "codehub", "artifact_id": r["artifact_id"], "version": r["version"], "start": 0, "end": 60}
            pair = {"refs": [ref, ref]}
            out["excerpts"] = await proxy.dispatch(DECIDE_TOOL, {
                "round": "d6", "template": "d6-noul-v3-excerpts", "state_kind": "excerpts",
                "questions": {"d6:e1|e2": NOUL}, "items": {"d6:e1|e2": pair}}, "req-7", caller)
            out["decomp"] = await proxy.dispatch(DECIDE_TOOL, {
                "round": "d6", "template": "d6-decomp-v1", "state_kind": "refs",
                "questions": {"d6:e1|e2#same_subject": NOUL, "d6:e1|e2#values_differ": NOUL,
                              "d6:e1|e2#choice": {"type": "choice", "instructions": "relation?",
                                                  "criteria": {"contradiction": "x", "none": "y"}}},
                "items": {"d6:e1|e2#same_subject": pair, "d6:e1|e2#values_differ": pair, "d6:e1|e2#choice": pair}},
                "req-7", caller)
            out["d2v2"] = await proxy.dispatch(DECIDE_TOOL, {
                "round": "d2", "template": "d2-descriptors-v2", "questions": {"d2:codehub": NOUL}}, "req-7", caller)
        proxy.unbind("req-7", handle)


def test_template_state_kinds_decomposition_and_d2_descriptor_set(scenario_world, server, tmp_path):  # noqa: F811
    from sanctum_run.system_one_broker import state_sources

    out = {}
    anyio.run(_templates, scenario_world, _broker(server, tmp_path, capabilities={"max_questions_per_call": 5}), out)
    excerpt_request, decomp_request, d2_request = server.behavior.requests
    assert out["excerpts"]["descriptor_release"] == "r3-state-v2"
    assert "excerpt" in excerpt_request["state"]["items"]["d6:e1|e2"][0]
    assert set(out["decomp"]["answers"]) == {"d6:e1|e2#same_subject", "d6:e1|e2#values_differ", "d6:e1|e2#choice"}
    assert "text" in decomp_request["state"]["items"]["d6:e1|e2#same_subject"][0]              # refs = v1
    v2 = state_sources(load_descriptors(ROOT / "configs" / "d2_descriptors_v2.yaml"), SOURCES)
    assert d2_request["state"]["sources"] == v2 and out["d2v2"]["descriptor_release"] == descriptor_release(v2)


def test_compact_layout_caps_excerpts_and_keeps_qualifiers():
    """r3-state-v2-compact: same fields, excerpt within the compact cap, qualifier lines admitted
    first, offsets mapping back to the text in original order."""
    from sanctum_run.round3_state import COMPACT_EXCERPT_CHARS, excerpt_of
    text = "\n".join(["# Retry policy", "environment: prod", "release: R42"]
                     + [f"note {i}: retry budget review item with more words here" for i in range(20)]
                     + ["max_retries: 5"])
    excerpt, spans, selected = excerpt_of(text, 0, len(text), "retry limit", COMPACT_EXCERPT_CHARS,
                                          COMPACT_EXCERPT_CHARS, qualifiers_first=True)
    assert len(excerpt) <= COMPACT_EXCERPT_CHARS + len(spans)
    assert "environment: prod" in excerpt and "release: R42" in excerpt
    assert all(text[s["start"]:s["end"]] in excerpt for s in spans)
    assert spans == sorted(spans, key=lambda s: s["start"])
