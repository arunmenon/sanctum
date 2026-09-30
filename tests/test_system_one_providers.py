"""System One providers (design page §2-§9): conformance, batching, deadlines, validation,
calibration binding and key isolation.

The conformance suite runs against the local test server always, and against `typesafe-jev` and
`laya-local` only when SANCTUM_SYSTEMONE_LIVE=1 (live calls cost money; never in CI)."""
import json
import os
from pathlib import Path

import anyio
import pytest
import yaml

from sanctum_ref.providers import build_provider, d2_request
from sanctum_ref.providers.http_systemone import TEMPLATE_VERSION, DirectTransport, SystemOneHttpAdapter
from sanctum_run.process_sut import child_environment
from sanctum_systemone import SystemOneClient, load_provider_specs, split_questions, validate_answers
from tests.helpers.systemone_server import ServerBehavior, SystemOneTestServer

ROOT = Path(__file__).resolve().parents[1]
SPECS = load_provider_specs(ROOT / "configs" / "system_one_providers.yaml")
LIVE = os.environ.get("SANCTUM_SYSTEMONE_LIVE") == "1"
NOUL = {"type": "noul", "instructions": "Is the sky blue in the state?"}
CHOICE = {"type": "choice", "instructions": "Pick one.", "criteria": {"a": "first", "b": "second", "c": "third"}}
SCORE = {"type": "score", "instructions": "Rate it.", "criteria": {"1": "low", "2": "mid", "3": "high"}}


def _dotenv() -> dict[str, str]:
    path = ROOT / ".env"
    if not path.exists():
        return {}
    pairs = (line.split("=", 1) for line in path.read_text().splitlines() if "=" in line and not line.startswith("#"))
    return {key.strip(): value.strip().strip('"') for key, value in pairs}


@pytest.fixture
def backend(request):
    """(client, spec, server-or-None) for one provider name."""
    name = request.param
    spec = SPECS[name]
    if name == "local-test":
        with SystemOneTestServer(ServerBehavior(require_key="test-key")) as server:
            yield SystemOneClient(spec, server.base_url, spec.model, api_key="test-key"), spec, server
        return
    if not LIVE:
        pytest.skip("live provider: set SANCTUM_SYSTEMONE_LIVE=1")
    environment = {**_dotenv(), **os.environ}
    base_url = spec.resolved_base_url(environment) or "https://api.typesafe.ai"
    key = environment.get(spec.api_key_env) if spec.api_key_env else None
    yield SystemOneClient(spec, base_url, spec.requested_model(environment), api_key=key), spec, None


PROVIDERS = ["local-test", "typesafe-jev", "laya-local"]


# ---- the eight conformance checks (design page §9) ------------------------------------------
@pytest.mark.parametrize("backend", PROVIDERS, indirect=True)
def test_conformance_shape_fidelity_usage_version(backend):
    client, spec, _server = backend
    questions = {"q1": NOUL, "q2": CHOICE} if "choice" in spec.capabilities.primitives else {"q1": NOUL}
    outcome = client.decide({"query": "conformance"}, questions, deadline_s=30, max_calls=2)
    assert outcome.unavailable_reason is None and outcome.model                   # 1 shape, 7 version
    assert set(outcome.answers) == set(questions) and not outcome.invalid_ids
    assert 0.0 <= outcome.answers["q1"]["noul"] <= 1.0                             # 2 fidelity
    if "q2" in outcome.answers:
        probabilities = outcome.answers["q2"]["probabilities"]
        assert outcome.answers["q2"]["choice"] in CHOICE["criteria"]
        assert abs(sum(probabilities.values()) - 1.0) <= 0.01
    assert (outcome.usage is not None) == spec.capabilities.reports_usage          # 8 usage
    again = client.decide({"query": "conformance"}, questions, deadline_s=30, max_calls=2)
    assert again.model == outcome.model                                              # 7 stable version
    assert abs(again.answers["q1"]["noul"] - outcome.answers["q1"]["noul"]) <= 0.05  # 6 determinism


def test_conformance_limits_errors_auth():
    spec = SPECS["local-test"]
    with SystemOneTestServer(ServerBehavior(require_key="k", max_questions_per_call=3, max_options=5)) as server:
        # 3 declared limits: the server rejects oversize batches (422) rather than truncating
        oversize = SystemOneClient(spec.model_copy(update={"capabilities": spec.capabilities.model_copy(
            update={"max_questions_per_call": 10})}), server.base_url, spec.model, api_key="k")
        rejected = oversize.decide({}, {f"q{i}": NOUL for i in range(5)}, deadline_s=5, max_calls=1)
        assert rejected.unavailable_reason == "error" and not rejected.answers
        # 5 auth: a missing or wrong key is refused
        for key in (None, "wrong"):
            assert SystemOneClient(spec, server.base_url, spec.model, api_key=key).decide(
                {}, {"q": NOUL}, deadline_s=5, max_calls=1).unavailable_reason == "error"
    # 4 errors: timeout and 5xx are distinguishable from a low probability
    with SystemOneTestServer(ServerBehavior(delay_ms=600)) as server:
        slow = SystemOneClient(spec, server.base_url, spec.model).decide({}, {"q": NOUL}, deadline_s=0.3, max_calls=1)
        assert slow.unavailable_reason == "timeout" and slow.calls <= 2
    with SystemOneTestServer(ServerBehavior(fail_times=5)) as server:
        broken = SystemOneClient(spec, server.base_url, spec.model).decide({}, {"q": NOUL}, deadline_s=5, max_calls=1)
        assert broken.unavailable_reason == "error"


# ---- batching, retries, validation ------------------------------------------------------------
def test_split_and_merge_on_declared_limits():
    spec = SPECS["local-test"]                        # max_questions_per_call 3
    with SystemOneTestServer() as server:
        questions = {f"d2:s{i}": NOUL for i in range(7)}
        outcome = SystemOneClient(spec, server.base_url, spec.model).decide({"query": "q"}, questions, 5, max_calls=3)
        assert outcome.calls == 3 and set(outcome.answers) == set(questions)
        assert [len(r["questions"]) for r in server.behavior.requests] == [3, 3, 1]
        assert outcome.usage == {"input_tokens": 3 * 50 + 70, "output_tokens": 35}   # merged
        over = SystemOneClient(spec, server.base_url, spec.model).decide({"query": "q"}, questions, 5, max_calls=2)
        assert over.unavailable_reason == "over_budget" and over.calls == 0      # per-round call limit


def test_one_retry_only_within_deadline():
    spec = SPECS["local-test"]
    with SystemOneTestServer(ServerBehavior(fail_times=1)) as server:
        outcome = SystemOneClient(spec, server.base_url, spec.model).decide({}, {"q": NOUL}, 5, max_calls=2)
        assert outcome.unavailable_reason is None and outcome.calls == 2
    with SystemOneTestServer(ServerBehavior(fail_times=2)) as server:
        outcome = SystemOneClient(spec, server.base_url, spec.model).decide({}, {"q": NOUL}, 5, max_calls=3)
        assert outcome.unavailable_reason == "error" and outcome.calls == 2          # never a third attempt


def test_max_calls_bounds_http_attempts_including_retries():
    """Holistic review: a one-call limit produced two HTTP attempts. The limit counts retries."""
    spec = SPECS["local-test"]
    with SystemOneTestServer(ServerBehavior(fail_times=1)) as server:
        outcome = SystemOneClient(spec, server.base_url, spec.model).decide({}, {"q": NOUL}, 5, max_calls=1)
        assert outcome.unavailable_reason == "error" and outcome.calls == 1
        assert len(server.behavior.requests) == 1
    with SystemOneTestServer(ServerBehavior(fail_times=1)) as server:     # a retry uses the second batch's call
        questions = {f"q{i}": NOUL for i in range(6)}                     # two batches of 3
        outcome = SystemOneClient(spec, server.base_url, spec.model).decide({}, questions, 5, max_calls=2)
        assert outcome.calls == 2 and len(server.behavior.requests) == 2
        assert outcome.unavailable_reason == "over_budget"


def test_choice_probabilities_must_sum_to_one_and_scores_stay_in_declared_levels():
    """Holistic review: answers outside the declared distribution or levels are invalid."""
    good_choice = {"type": "choice", "choice": "a", "probabilities": {"a": 0.5, "b": 0.3, "c": 0.2}}
    loose_choice = {"type": "choice", "choice": "a", "probabilities": {"a": 0.9, "b": 0.9}}
    valid, invalid = validate_answers({"c1": CHOICE, "c2": CHOICE}, {"answers": {"c1": good_choice, "c2": loose_choice}})
    assert set(valid) == {"c1"} and invalid == ["c2"]
    listed = {"type": "score", "instructions": "Rate it.", "criteria": ["none", "some", "most", "all"]}
    answers = {"s1": {"type": "score", "score": 2.4}, "s2": {"type": "score", "score": 3.5},
               "s3": {"type": "score", "score": 3.0}, "s4": {"type": "score", "score": 0.5}}
    valid, invalid = validate_answers({"s1": listed, "s2": listed, "s3": SCORE, "s4": SCORE}, {"answers": answers})
    assert set(valid) == {"s1", "s3"} and sorted(invalid) == ["s2", "s4"]


@pytest.mark.parametrize("invalid", ["wrong_type", "unknown_id", "bad_probability", "not_json"])
def test_invalid_output_is_never_partially_trusted(invalid):
    spec = SPECS["local-test"]
    with SystemOneTestServer(ServerBehavior(invalid=invalid)) as server:
        outcome = SystemOneClient(spec, server.base_url, spec.model).decide({}, {"a": NOUL, "b": NOUL}, 5, max_calls=1)
    if invalid in ("unknown_id", "not_json"):
        assert outcome.unavailable_reason == "invalid_output" and not outcome.answers
    else:
        assert outcome.invalid_ids == ["a"] and set(outcome.answers) == {"b"}


def test_model_change_mid_round_is_invalid():
    spec = SPECS["local-test"]
    with SystemOneTestServer(ServerBehavior(model_sequence=["m-1", "m-2"])) as server:
        outcome = SystemOneClient(spec, server.base_url, spec.model).decide(
            {}, {f"q{i}": NOUL for i in range(5)}, 5, max_calls=2)
    assert outcome.unavailable_reason == "invalid_output"


def test_no_automatic_score_or_choice_conversion():
    capabilities = SPECS["local-test"].capabilities.model_copy(update={"primitives": ["noul", "choice"]})
    batches, refused = split_questions({"s": SCORE, "c": CHOICE, "n": NOUL}, capabilities)
    assert refused == ["s"] and all("s" not in batch for batch in batches)
    valid, invalid = validate_answers({"c": CHOICE}, {"answers": {"c": {"type": "score", "score": 2}}})
    assert not valid and invalid == ["c"]
    too_many = {**CHOICE, "criteria": {str(i): str(i) for i in range(9)}}
    assert split_questions({"x": too_many}, SPECS["local-test"].capabilities)[1] == ["x"]  # max_options 5


# ---- the SUT-side adapter: shadow-only, calibration binding, safe default ---------------------
def _adapter(server, calibration_dir):
    spec = SPECS["local-test"]
    client = SystemOneClient(spec, server.base_url, spec.model)
    return SystemOneHttpAdapter(spec, calibration_dir, transport=DirectTransport(client, lambda p: {"query": p["query"]}))


def _decide(adapter, sources=("codehub", "dochub", "memoryhub")):
    requests = [d2_request(source, "what is the retry limit", 3000) for source in sources]
    return anyio.run(adapter.decide_batch, requests, None, 3000)


def test_no_matching_calibration_runs_shadow_only(tmp_path):
    with SystemOneTestServer() as server:
        results = _decide(_adapter(server, tmp_path))
    assert all(r.status.value == "answered" and r.value["shadow"] and r.value["call"] for r in results)
    assert all(r.disposition.value == "preserve_candidate" and r.model_version == "test-model-1" for r in results)
    assert all(r.value["request_hash"].startswith("sha256:") and r.value["usage"] for r in results)


def test_matching_calibration_applies_bands_and_wrong_version_does_not(tmp_path):
    binding = {"provider": "local-test", "model": "test-model-1", "template": TEMPLATE_VERSION}
    (tmp_path / "local-test@test-model-1.yaml").write_text(yaml.safe_dump(
        {"binding": binding, "platt": {"a": 1.0, "b": 0.0}, "bands": {"use": 0.99, "skip": 0.999}}))
    with SystemOneTestServer() as server:
        calibrated = _decide(_adapter(server, tmp_path))
    assert all(not r.value["shadow"] and "p" in r.value for r in calibrated)
    assert all(r.value["call"] is (r.value["p"] >= 0.99) for r in calibrated)    # skip band above use: all skip unless use
    with SystemOneTestServer(ServerBehavior(model_sequence=["test-model-2"])) as server:
        other_version = _decide(_adapter(server, tmp_path))
    assert all(r.value["shadow"] for r in other_version)                          # bound to the resolved version


def test_unavailable_and_invalid_keep_every_candidate(tmp_path):
    with SystemOneTestServer(ServerBehavior(fail_times=5)) as server:
        failed = _decide(_adapter(server, tmp_path))
    assert all(r.status.value == "unavailable" and r.value is None for r in failed)
    with SystemOneTestServer(ServerBehavior(invalid="wrong_type")) as server:
        partly = _decide(_adapter(server, tmp_path))
    assert partly[0].status.value == "unavailable" and all(r.value is None or r.value["call"] for r in partly)


def test_registry_builds_every_declared_provider():
    params = ROOT / "configs" / "d2_standin.yaml"
    for name in ("rules", "standin", "typesafe-jev", "laya-local", "local-test"):
        provider = build_provider(name, params, ROOT / "configs" / "system_one_providers.yaml", tmp_dir := ROOT / "configs" / "calibration")
        assert provider.name == name and provider.capabilities.primitives
    assert SPECS["laya-local"].capabilities.confidence_thresholdable is False
    assert "api_key_env" not in SPECS["laya-local"].model_fields_set


def test_provider_key_never_reaches_the_sut(monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "sk-test-value-that-must-not-leak")
    environment = child_environment()
    assert "TYPESAFE_API_KEY" not in environment
    assert "sk-test-value-that-must-not-leak" not in json.dumps(environment)


def test_configured_key_value_appears_in_no_file():
    """Value scan, not a prefix scan: the key configured in .env is in no file of the repo,
    including run outputs and reports (.env itself and VCS internals excepted)."""
    key = _dotenv().get("TYPESAFE_API_KEY")
    if not key or len(key) < 12:
        pytest.skip("no provider key configured")
    needle = key.encode()
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.name == ".env" or ".git" in path.parts or path.stat().st_size > 20_000_000:
            continue
        assert needle not in path.read_bytes(), f"provider key found in {path.relative_to(ROOT)}"


def test_bad_choice_is_invalid():
    spec = SPECS["local-test"]
    with SystemOneTestServer(ServerBehavior(invalid="bad_choice")) as server:
        outcome = SystemOneClient(spec, server.base_url, spec.model).decide({}, {"c": CHOICE, "n": NOUL}, 5, max_calls=1)
    assert outcome.invalid_ids == ["c"] and set(outcome.answers) == {"n"}


def test_broker_result_translation():
    from sanctum_ref.providers.http_systemone import outcome_from_broker
    ok = outcome_from_broker({"provider": "p", "model": "m-1", "answers": {"d2:a": {"type": "noul", "noul": 0.4},
                              "d2:b": {"type": "noul", "noul": 0.9}}, "unavailable": {"d2:b": "not_allowed"},
                              "elapsed_ms": 12.5, "usage": {"input_tokens": 3}, "descriptor_release": "sha256:abc"})
    assert ok.descriptor_release == "sha256:abc"
    assert ok.model == "m-1" and set(ok.answers) == {"d2:a"} and ok.invalid_ids == ["d2:b"]
    assert ok.unavailable_reason is None and ok.latency_ms == 12
    refused = outcome_from_broker({"provider": "p", "model": None, "answers": {},
                                   "unavailable": {"d2:a": "data_class_ineligible"}})
    assert refused.unavailable_reason == "data_class_refused"
    mixed_versions = outcome_from_broker({"provider": "p", "model": ["m-1", "m-2"], "answers": {"d2:a": {"type": "noul", "noul": 0.4}}})
    assert mixed_versions.unavailable_reason == "invalid_output"
    assert outcome_from_broker({"error": {"code": "x"}}).unavailable_reason == "not_configured"


def test_truncated_reads_are_never_trusted():
    """Laya reports truncation in usage; a truncated state voids the call, a truncated question
    voids that decision (design page §13)."""
    spec = SPECS["local-test"]
    with SystemOneTestServer(ServerBehavior(invalid="truncated_state")) as server:
        whole = SystemOneClient(spec, server.base_url, spec.model).decide({}, {"a": NOUL, "b": NOUL}, 5, max_calls=1)
    assert whole.unavailable_reason == "truncated" and not whole.answers
    with SystemOneTestServer(ServerBehavior(invalid="truncated_question")) as server:
        one = SystemOneClient(spec, server.base_url, spec.model).decide({}, {"a": NOUL, "b": NOUL}, 5, max_calls=1)
    assert one.unavailable_reason is None and one.invalid_ids == ["a"] and set(one.answers) == {"b"}


def test_per_batch_state_splits_on_state_size():
    """Round 3: each batch carries only its own items, and batches split until the state fits;
    a single oversize item is refused, never truncated."""
    spec = SPECS["local-test"].model_copy(update={"capabilities": SPECS["local-test"].capabilities.model_copy(
        update={"max_state_chars": 400, "max_questions_per_call": 10})})
    texts = {"a": "x" * 150, "b": "y" * 150, "c": "z" * 150, "huge": "w" * 900}
    state_for = lambda qids: {"items": {q: texts[q] for q in qids}}
    with SystemOneTestServer() as server:
        outcome = SystemOneClient(spec, server.base_url, spec.model).decide(
            {}, {q: NOUL for q in texts}, 5, max_calls=5, state_for=state_for)
        sent = [set(r["state"]["items"]) for r in server.behavior.requests]
    assert outcome.invalid_ids == ["huge"] and set(outcome.answers) == {"a", "b", "c"}
    assert sent == [{"a", "b"}, {"c"}] and all(len(repr(state_for(list(batch)))) <= 400 for batch in sent)


def test_campaign_budget_is_enforced_before_dispatch():
    """Review A1: the ceiling is checked before each HTTP attempt, retries count, and usage is
    recorded once per exchange; an exhausted budget makes no further request."""
    from sanctum_systemone import CampaignBudget, set_campaign_budget
    spec = SPECS["local-test"]
    budget = CampaignBudget(max_calls=3, max_input_tokens=10_000)
    set_campaign_budget(budget)
    try:
        with SystemOneTestServer(ServerBehavior(fail_times=1)) as server:
            client = SystemOneClient(spec, server.base_url, spec.model)
            first = client.decide({}, {"q": NOUL}, 5, max_calls=2)          # 503 then ok: 2 attempts
            second = client.decide({}, {"q": NOUL}, 5, max_calls=1)         # third attempt
            third = client.decide({}, {"q": NOUL}, 5, max_calls=1)          # refused before dispatch
            sent = len(server.behavior.requests)
        assert first.unavailable_reason is None and first.calls == 2
        assert second.unavailable_reason is None and third.unavailable_reason == "over_budget"
        assert third.calls == 0 and sent == 3 and budget.calls == 3
        from sanctum_systemone.protocol import build_request, estimate_input_tokens
        failed_attempt = estimate_input_tokens(build_request({}, spec.model, {"q": NOUL}))
        # two answered exchanges at their reported usage (60 each) plus the 503 at its reservation
        assert budget.input_tokens == 60 * 2 + failed_attempt
        tight = CampaignBudget(max_calls=10, max_input_tokens=50)       # below one reservation
        set_campaign_budget(tight)
        with SystemOneTestServer() as server:
            refused = SystemOneClient(spec, server.base_url, spec.model).decide({}, {"q": NOUL}, 5, max_calls=1)
            assert refused.unavailable_reason == "over_budget" and not server.behavior.requests
    finally:
        set_campaign_budget(None)


def test_shadow_comes_from_a_missing_binding_not_a_sentinel(tmp_path):
    """Review A2: a calibration whose use band is 1.0 (or missing) is not usable; the adapter runs
    shadow-only, exactly as when no calibration file exists."""
    binding = {"provider": "local-test", "model": "test-model-1", "template": TEMPLATE_VERSION}
    (tmp_path / "local-test@test-model-1.yaml").write_text(yaml.safe_dump(
        {"binding": binding, "platt": {"a": 1.0, "b": 0.0}, "bands": {"use": 1.0, "skip": 0.0}}))
    with SystemOneTestServer() as server:
        sentinel = _decide(_adapter(server, tmp_path))
    assert all(r.value["shadow"] and r.value["call"] and "p" not in r.value for r in sentinel)
    assert not list((ROOT / "configs" / "calibration").glob("*.yaml")) or all(
        yaml.safe_load(p.read_text())["bands"]["use"] < 1.0 for p in (ROOT / "configs" / "calibration").glob("*.yaml"))


def test_templates_are_versioned_and_defaults_unchanged():
    """Review B: named, versioned templates; the default ids keep the exact texts the existing
    calibrations were fitted with; diagnostics are never live."""
    from sanctum_ref.providers.http_systemone import D2_INSTRUCTIONS, ROUND3_INSTRUCTIONS, d2_questions
    from sanctum_ref.providers.templates import DEFAULT_TEMPLATES, TemplateRegistry
    registry = TemplateRegistry(DEFAULT_TEMPLATES)
    assert registry.resolve("d2").questions("d2:codehub", source="codehub")["d2:codehub"]["instructions"] == \
        f"{D2_INSTRUCTIONS} Source: codehub."
    assert registry.resolve("d6").instructions == ROUND3_INSTRUCTIONS["d6"]
    assert registry.resolve("d4").instructions == ROUND3_INSTRUCTIONS["d4"]
    assert list(d2_questions([d2_request("dochub", "q", 3000)])) == ["d2:dochub"]
    for name in ("d6-noul-v2-relations", "d6-noul-v3-excerpts", "d6-laya-positive-v1", "d2-noul-v2-loss",
                 "d2-descriptors-v2", "d4-noul-v2-support"):
        assert not registry.templates[name].diagnostic
    for name in ("d6-laya-negative-v1", "d6-decomp-v1", "d6-choice-v1", "d4-score-v1"):
        assert registry.templates[name].diagnostic
    assert set(registry.resolve("d6", template_id="d6-decomp-v1").questions("d6:a|b")) == {"d6:a|b#same_subject", "d6:a|b#values_differ"}
    assert "no_conflict" in registry.resolve("d6", template_id="d6-choice-v1").questions("d6:a|b")["d6:a|b"]["criteria"]


def test_diagnostic_templates_never_drive_decisions(tmp_path):
    from sanctum_ref.providers.http_systemone import decide_items
    from sanctum_ref.providers.templates import DEFAULT_TEMPLATES, TemplateRegistry
    (tmp_path / "local-test@test-model-1.d6.yaml").write_text(yaml.safe_dump({
        "binding": {"provider": "local-test", "model": "test-model-1", "template": "d6-laya-negative-v1"},
        "platt": {"a": 1.0, "b": 0.0}, "bands": {"use": 0.5, "skip": 0.0}}))
    ref = {"source_id": "codehub", "artifact_id": "a", "version": "R42", "start": 0, "end": 5}
    for template_id in ("d6-laya-negative-v1", "d6-decomp-v1", "d6-choice-v1"):
        with SystemOneTestServer() as server:
            adapter = SystemOneHttpAdapter(SPECS["local-test"], tmp_path,
                                           transport=DirectTransport(SystemOneClient(SPECS["local-test"], server.base_url, "test-model-1"),
                                                                     lambda p: {"query": p["query"]}),
                                           templates=TemplateRegistry(DEFAULT_TEMPLATES), template_ids={"d6": template_id})
            judgements, results, calibration = anyio.run(decide_items, adapter, "d6", {"d6:a|b": [ref, ref]}, "q", None, 3000)
        assert calibration is None and all(j.p is None for j in judgements.values())
        assert results[0].value["template"] == template_id and results[0].value["diagnostic"] is True


def test_score_criteria_go_on_the_wire_as_an_ordered_list():
    """The hosted protocol takes score levels as a list (index = level); choice keeps a dict."""
    from sanctum_ref.providers.templates import DEFAULT_TEMPLATES, TemplateRegistry
    registry = TemplateRegistry(DEFAULT_TEMPLATES)
    score = registry.templates["d4-score-v1"].questions("d4:x")["d4:x"]["criteria"]
    assert isinstance(score, list) and len(score) == 4 and score[0].startswith("No substantive")
    assert isinstance(registry.templates["d6-choice-v1"].questions("d6:a|b")["d6:a|b"]["criteria"], dict)
