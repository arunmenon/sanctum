"""Runner-side System One broker (design page §6, handshake points 1, 5, 6, 8, 9, 10).

Uses a local /v1/systemone test server in this file (no live calls). Every provider call must be
bound by the broker, validated, observed as a `model_call`, stored for replay without the key,
and the key must never reach the SUT environment or any run output.
"""
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import anyio
import pytest

from sanctum_hubs.tokens import TokenService
from sanctum_run.gateway import HubGateway, released_hub_ids
from sanctum_run.process_sut import child_environment
from sanctum_run.proxy import GatewayProxy
from sanctum_run.runner import DEFAULT_HUBS_CONFIG
from sanctum_run.system_one_broker import (
    DECIDE_TOOL, ProfileConfig, SystemOneBroker, load_secret, provider_from_dict, validate_answers,
)
from tests.scenarios.conftest import scenario_world  # noqa: F401  (session world build)

KEY = "sk-test-broker-key-7f3a"
PRINCIPAL = "kestrel-payments"


class _Server:
    """Minimal /v1/systemone: requires the Bearer key; `mode` picks the behaviour."""

    def __init__(self):
        self.mode, self.delay_s, self.requests = "ok", 0.0, []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                outer.requests.append({"auth": self.headers.get("Authorization"), "body": body})
                if self.headers.get("Authorization") != f"Bearer {KEY}":
                    return self._send(401, {"error": "unauthorized"})
                if outer.mode == "error":
                    return self._send(500, {"error": "boom"})
                time.sleep(outer.delay_s)
                answers = {}
                for qid, question in body["questions"].items():
                    if question["type"] == "noul":
                        answers[qid] = {"type": "noul", "noul": 1.5 if outer.mode == "bad_probability" else 0.7}
                    elif question["type"] == "choice":
                        choice = "not-offered" if outer.mode == "bad_choice" else question["criteria"][0]
                        answers[qid] = {"type": "choice", "choice": choice,
                                        "probabilities": {question["criteria"][0]: 0.9}, "confidence": 0.8}
                if outer.mode == "extra_question":
                    answers["d2:incidenthub"] = {"type": "noul", "noul": 0.5}
                self._send(200, {"model": "jev-test-1.0.0", "answers": answers,
                                 "usage": {"input_tokens": 10, "output_tokens": 2}})

            def _send(self, status, payload):
                data = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()


@pytest.fixture
def server():
    instance = _Server()
    yield instance
    instance.httpd.shutdown()


class _Gateway:
    def __init__(self):
        self.model_calls = []

    def record_model_call(self, request_id, call):
        self.model_calls.append((request_id, call))


def _broker(server, tmp_path, **overrides):
    capabilities = {"primitives": ["noul", "choice"], "max_questions_per_call": 20, "max_options": 3,
                    "max_context_chars": 4000, "data_classes_allowed": ["synthetic"],
                    **overrides.pop("capabilities", {})}
    provider = provider_from_dict("local-test", {"base_url": server.url, "model": "jev-test",
                                                 "credential_env": "SYSTEMONE_TEST_KEY", "capabilities": capabilities})
    profile = overrides.pop("profile", ProfileConfig("strict", deadline_ms=2000, max_calls_per_round=4))
    return SystemOneBroker(provider=provider, profile=profile, data_class=overrides.pop("data_class", "synthetic"),
                           allowed_sources=["codehub", "dochub", "skillhub"],
                           descriptors={"codehub": {"k": "v"}}, store_dir=tmp_path / "system_one", secret=KEY,
                           **overrides)


def _decide(broker, questions, gateway=None, round_id="r1"):
    gateway = gateway or _Gateway()
    result = anyio.run(broker.decide, gateway, "req-1", "retry limit?", {"round": round_id, "questions": questions})
    return result, gateway


NOUL = {"type": "noul", "instructions": "Will this source return necessary evidence?"}


def test_ok_call_is_bound_validated_observed_and_stored(server, tmp_path):
    result, gateway = _decide(_broker(server, tmp_path), {"d2:codehub": NOUL, "d2:dochub": NOUL})
    assert result["answers"]["d2:codehub"]["noul"] == 0.7 and result["unavailable"] == {}
    assert result["model"] == "jev-test-1.0.0"
    sent = server.requests[0]
    assert sent["auth"] == f"Bearer {KEY}"
    assert sent["body"]["state"] == {"query": "retry limit?", "sources": ["codehub", "dochub"],
                                     "descriptors": {"codehub": {"k": "v"}, "dochub": None}}
    [(request_id, call)] = gateway.model_calls
    assert request_id == "req-1" and call.outcome == "ok" and call.model == "jev-test-1.0.0"
    assert call.questions == ["d2:codehub", "d2:dochub"] and call.request_sha256
    stored = list((tmp_path / "system_one").glob("*.json"))
    assert len(stored) == 1 and KEY not in stored[0].read_text()


@pytest.mark.parametrize("questions,overrides,reason", [
    ({"d2:incidenthub": NOUL}, {}, "not_allowed"),                         # not in the gateway's view
    ({"d2:codehub": NOUL}, {"data_class": "internal"}, "data_class_ineligible"),
    ({"route": {"type": "choice", "criteria": ["a", "b", "c", "d"]}}, {}, "over_budget"),
    ({"q": {"type": "score", "criteria": ["low", "high"]}}, {}, "primitive_unsupported"),
    ({"q": {"type": "noul", "instructions": "x" * 5000}}, {}, "over_budget"),   # context budget, no truncation
])
def test_refusals_make_no_provider_call(server, tmp_path, questions, overrides, reason):
    result, gateway = _decide(_broker(server, tmp_path, **overrides), questions)
    assert server.requests == []
    assert set(result["unavailable"].values()) == {reason} and result["answers"] == {}
    assert gateway.model_calls[0][1].outcome == "refused" and gateway.model_calls[0][1].reason == reason


@pytest.mark.parametrize("mode", ["extra_question", "bad_probability", "bad_choice"])
def test_invalid_output_is_never_partially_trusted(server, tmp_path, mode):
    server.mode = mode
    questions = {"d2:codehub": NOUL, "route": {"type": "choice", "criteria": ["codehub", "dochub"]}}
    result, gateway = _decide(_broker(server, tmp_path), questions)
    assert result["answers"] == {} and set(result["unavailable"]) == set(questions)
    assert gateway.model_calls[0][1].outcome == "invalid_output"


def test_batches_split_and_round_call_limit(server, tmp_path):
    broker = _broker(server, tmp_path, capabilities={"max_questions_per_call": 2},
                     profile=ProfileConfig("strict", deadline_ms=2000, max_calls_per_round=1))
    result, gateway = _decide(broker, {"d2:codehub": NOUL, "d2:dochub": NOUL, "d2:skillhub": NOUL})
    assert len(server.requests) == 1
    assert set(result["answers"]) == {"d2:codehub", "d2:dochub"}
    assert result["unavailable"] == {"d2:skillhub": "call_limit"}
    assert [call.outcome for _, call in gateway.model_calls] == ["ok", "refused"]


def test_deadline_and_single_retry(server, tmp_path):
    server.delay_s = 0.5
    broker = _broker(server, tmp_path, profile=ProfileConfig("strict", deadline_ms=150, max_calls_per_round=4))
    result, gateway = _decide(broker, {"d2:codehub": NOUL})
    assert result["unavailable"] == {"d2:codehub": "decision_layer_unavailable"}
    assert gateway.model_calls[0][1].outcome == "timeout"
    server.mode, server.delay_s, server.requests = "error", 0.0, []
    result, gateway = _decide(_broker(server, tmp_path), {"d2:codehub": NOUL}, round_id="r2")
    assert len(server.requests) == 2                                   # one retry, then unavailable
    assert gateway.model_calls[0][1].outcome == "error"


def test_validate_answers_rules():
    asked = {"a": {"type": "noul"}, "b": {"type": "choice", "criteria": ["x", "y"]}}
    good = {"answers": {"a": {"type": "noul", "noul": 0.2},
                        "b": {"type": "choice", "choice": "y", "probabilities": {"x": 0.1, "y": 0.9}}}}
    assert validate_answers(asked, good) is None
    missing = {"answers": {"a": {"type": "noul", "noul": 0.2}}}
    assert validate_answers(asked, missing) == "invalid_output"
    wrong_type = {"answers": {**good["answers"], "a": {"type": "score", "score": 1}}}
    assert validate_answers(asked, wrong_type) == "invalid_output"


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
            out["ok"] = await proxy.dispatch(DECIDE_TOOL, {"round": "r1", "questions": {"d2:codehub": NOUL}},
                                             "req-p", caller)
            out["forged"] = await proxy.dispatch(DECIDE_TOOL, {"questions": {"d2:codehub": NOUL}},
                                                 "req-p", "forged-token")
        proxy.unbind("req-p", handle)
        out["trace"] = gateway.trace("req-p")
        out["anomalies"] = proxy.anomalies()


def test_proxy_tool_observes_model_calls_apart_from_sources(scenario_world, server, tmp_path, monkeypatch):  # noqa: F811
    monkeypatch.setenv("SYSTEMONE_TEST_KEY", KEY)
    out = {}
    anyio.run(_through_proxy, scenario_world, _broker(server, tmp_path), out)
    assert DECIDE_TOOL in out["tools"]
    assert set(out["ok"]["answers"]) == {"d2:codehub"}
    assert out["forged"]["error"]["code"] == "denied_or_not_found" and len(server.requests) == 1
    assert [a["kind"] for a in out["anomalies"]] == ["proxy_call_outside_binding"]
    trace = out["trace"]
    assert trace.sources_attempted() == {"codehub"}                     # the model call is not a source
    assert [(c.provider, c.outcome) for c in trace.model_calls] == [("local-test", "ok")]
    assert server.requests[0]["body"]["state"]["query"] == "How many retries?"   # from the binding


def test_key_stays_runner_side(server, tmp_path, monkeypatch):
    monkeypatch.setenv("SYSTEMONE_TEST_KEY", KEY)
    assert load_secret("SYSTEMONE_TEST_KEY") == KEY
    assert KEY not in child_environment().values()
    assert "SYSTEMONE_TEST_KEY" not in child_environment()
    env_file = tmp_path / ".env"
    env_file.write_text(f"OTHER=1\nSYSTEMONE_FILE_KEY='{KEY}'\n")
    monkeypatch.delenv("SYSTEMONE_FILE_KEY", raising=False)
    assert load_secret("SYSTEMONE_FILE_KEY", env_file) == KEY
    _decide(_broker(server, tmp_path), {"d2:codehub": NOUL})
    _decide(_broker(server, tmp_path), {"d2:incidenthub": NOUL})
    for path in (tmp_path / "system_one").rglob("*"):
        if path.is_file():
            assert KEY not in path.read_text(), path


# ---- runner, provenance and report ---------------------------------------------------------------
def test_runner_records_provider_and_keeps_key_out_of_outputs(scenario_world, server, tmp_path, monkeypatch):  # noqa: F811
    import yaml
    from sanctum_eval.provenance import effective_configuration, record_effective
    from sanctum_run.runner import DEFAULT_M0_PRINCIPAL_ALIASES, RunConfig, load_principal_aliases, run
    from sanctum_run.sut import StubSUTAdapter, load_call_plan

    root = Path(__file__).resolve().parents[1]
    providers = tmp_path / "providers.yaml"
    providers.write_text(yaml.safe_dump({
        "providers": {"local-test": {"base_url": server.url, "model": "jev-test", "credential_env": "SYSTEMONE_TEST_KEY",
                                     "capabilities": {"primitives": ["noul"], "data_classes_allowed": ["synthetic"]}}},
        "profiles": {"strict": {"deadline_ms": 400, "max_calls_per_round": 2},
                     "relaxed": {"deadline_ms": 5000, "max_calls_per_round": 4}}}))
    monkeypatch.setenv("SYSTEMONE_TEST_KEY", KEY)
    result = run(StubSUTAdapter(load_call_plan(root / "tests" / "fixtures" / "m0" / "traces")), RunConfig(
        cases_dir=root / "gold" / "m0", out_dir=tmp_path / "run", seed=1, sut_name="stub", world_build_dir=scenario_world,
        principal_aliases=load_principal_aliases(DEFAULT_M0_PRINCIPAL_ALIASES), system_one_provider="local-test",
        system_one_profile="relaxed", system_one_providers_path=providers))
    assert result.manifest["system_one"] == {"provider": "local-test", "requested_model": "jev-test", "profile": "relaxed",
                                             "data_class": "synthetic", "resolved_models": [], "model_calls": 0}
    manifest = record_effective(result.out_dir, effective_configuration(
        sut="stub", config_id="stub", hubs=result.manifest["hubs"], cases_dir=root / "gold" / "m0"))
    assert manifest["effective"]["system_one"]["provider"] == "local-test"
    for path in result.out_dir.rglob("*"):
        if path.is_file():
            assert KEY not in path.read_text(), path


def test_report_section_counts_model_calls(tmp_path):
    from types import SimpleNamespace
    from tools.report import render_system_one

    run_dir = tmp_path / "C3"
    run_dir.mkdir()
    calls = [{"provider": "local-test", "model": "jev-test-1.0.0", "profile": "strict", "round": "r1",
              "questions": ["d2:codehub"], "outcome": outcome, "elapsed_ms": ms}
             for outcome, ms in (("ok", 40.0), ("ok", 60.0), ("timeout", 400.0))]
    (run_dir / "traces.jsonl").write_text(json.dumps({"request_id": "r", "calls": [], "model_calls": calls}) + "\n")
    view = SimpleNamespace(dir=run_dir, config_id="C3", manifest={"system_one": {
        "provider": "local-test", "resolved_models": ["jev-test-1.0.0"], "profile": "strict"}})
    text = "\n".join(render_system_one([view]))
    assert "## System One model calls (reported, not gated)" in text
    assert "| C3 | local-test | jev-test-1.0.0 | strict | 3 | ok 2, timeout 1 | 60.0 | 400.0 |" in text
    assert render_system_one([SimpleNamespace(dir=tmp_path, config_id="C2", manifest={})]) == []


def test_with_shared_test_server_and_provider_file(monkeypatch, tmp_path):
    from sanctum_run.system_one_broker import load_provider
    from tests.helpers.systemone_server import ServerBehavior, SystemOneTestServer

    with SystemOneTestServer(ServerBehavior(model_sequence=["test-model-1.2"])) as test_server:
        monkeypatch.setenv("SANCTUM_SYSTEMONE_TEST_URL", test_server.base_url)
        provider, profile = load_provider("local-test", "relaxed")
        assert (provider.max_questions_per_call, provider.max_options) == (3, 5)
        broker = SystemOneBroker(provider=provider, profile=profile, data_class="synthetic",
                                 allowed_sources=["codehub", "dochub", "skillhub"], descriptors={},
                                 store_dir=tmp_path / "system_one")
        questions = {f"d2:{hub}": NOUL for hub in ("codehub", "dochub", "skillhub")}
        questions["route"] = {"type": "choice", "instructions": "best source",
                              "criteria": {"codehub": "code first", "dochub": "docs first"}}
        result, gateway = _decide(broker, questions)
    assert result["unavailable"] == {} and set(result["answers"]) == set(questions)
    assert result["model"] == "test-model-1.2"
    assert [len(call.questions) for _, call in gateway.model_calls] == [3, 1]     # split at max_questions_per_call
    with pytest.raises(ValueError):
        load_provider("standin", "strict")                                         # in-SUT provider, not brokered
