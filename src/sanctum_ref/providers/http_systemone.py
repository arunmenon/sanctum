"""`SystemOneHttpAdapter`: any `/v1/systemone` backend (design page §2, §5).

In a run the adapter never talks HTTP itself: it sends one round's questions through the
runner's broker tool `system_one.decide` (`BrokerTransport`), which holds the key, builds the
state from the gateway's own view, splits on provider limits, validates and records the call.
Lab tools and tests use `DirectTransport` over `sanctum_systemone.SystemOneClient`.

Calibration binding (§8): a file `configs/calibration/<provider>@<model>.yaml` applies only when
its binding matches the resolved model and the current template; otherwise the provider runs
shadow-only (raw answers recorded, every candidate kept). Bands use calibrated `noul` only;
`confidence` is never thresholded.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any, Optional

import yaml

from sanctum_contracts import DecisionRequest, DecisionResult
from sanctum_systemone import CallOutcome, ProviderSpec, SystemOneClient

from .interface import POLICY_VERSION, TARGET, unavailable
from .templates import DEFAULT_TEMPLATES, Template, TemplateRegistry

TEMPLATE_VERSION = "d2-noul-v1"
TEMPLATES = {"d2": TEMPLATE_VERSION, "d6": "d6-noul-v1", "d4": "d4-noul-v1"}
ROUND3_INSTRUCTIONS = {
    "d6": "Answer true if the two evidence units listed under this question's id in state.items assert "
          "incompatible values for the same fact, scope and version.",
    "d4": "Answer true if the evidence unit listed under this question's id in state.items supports an "
          "answer to the query in the state.",
}
D2_INSTRUCTIONS = ("Answer true if searching the source named in the question is likely to return evidence "
                   "necessary to answer the query in the state, judged from the source's description.")
BROKER_TOOL = "system_one.decide"
ROUND3_MAX_CALLS = 24


def d2_questions(requests: list[DecisionRequest], template: Optional[Template] = None) -> dict[str, dict[str, Any]]:
    template = template or TemplateRegistry(DEFAULT_TEMPLATES).resolve("d2")
    questions: dict[str, dict[str, Any]] = {}
    for request in requests:
        source = request.candidate_ids[0]
        questions.update(template.questions(f"d2:{source}", source=source))
    return questions


def request_hash(round_name: str, query: str, questions: dict[str, Any]) -> str:
    material = json.dumps({"round": round_name, "query": query, "questions": questions}, sort_keys=True)
    return "sha256:" + hashlib.sha256(material.encode()).hexdigest()[:24]


# The runner's broker reports per-question refusals with its own reason names; the SUT only needs
# to know that a question was not answered (keep the candidate) and, for the whole call, why.
BROKER_REASONS = {
    "not_allowed": "invalid_output", "invalid_request": "invalid_output", "primitive_unsupported": "invalid_output",
    "invalid_output": "invalid_output", "data_class_ineligible": "data_class_refused",
    "over_budget": "over_budget", "call_limit": "over_budget", "decision_layer_unavailable": "error",
}


def outcome_from_broker(body: Any) -> CallOutcome:
    """The broker's tool result (`system_one.decide`, runner side) as a `CallOutcome`. Anything
    unexpected is unavailable: the SUT never partially trusts a result it cannot read."""
    if not isinstance(body, dict) or "provider" not in body:
        return CallOutcome(provider="unknown", unavailable_reason="not_configured")
    try:
        return CallOutcome.model_validate(body)                  # already in the core's shape
    except ValueError:
        pass
    model = body.get("model")
    answers = body.get("answers") if isinstance(body.get("answers"), dict) else {}
    refused = body.get("unavailable") if isinstance(body.get("unavailable"), dict) else {}
    release = body.get("descriptor_release")
    outcome = CallOutcome(provider=str(body["provider"]), usage=body.get("usage") if isinstance(body.get("usage"), dict) else None,
                          latency_ms=int(float(body.get("elapsed_ms") or 0)),
                          descriptor_release=release if isinstance(release, str) else None)
    if isinstance(model, list):                                  # batches resolved to different versions
        outcome.unavailable_reason = "invalid_output"
        return outcome
    outcome.model = model if isinstance(model, str) else None
    outcome.answers = {qid: answer for qid, answer in answers.items() if qid not in refused and isinstance(answer, dict)}
    outcome.invalid_ids = sorted(refused)
    if refused and not outcome.answers:
        reasons = {BROKER_REASONS.get(str(reason), "error") for reason in refused.values()}
        outcome.unavailable_reason = sorted(reasons)[0] if len(reasons) == 1 else "error"
    elif not outcome.answers:
        outcome.unavailable_reason = "invalid_output"
    return outcome


class BrokerTransport:
    """Sends a round to the runner's broker through the SUT's proxy port."""

    async def send(self, port: Any, payload: dict[str, Any], deadline_ms: int) -> CallOutcome:
        call = getattr(port, "system_one_decide", None)
        if call is None:
            return CallOutcome(provider="unknown", unavailable_reason="not_configured")
        return outcome_from_broker(await call(payload))


class DirectTransport:
    """Lab tools and tests only: a direct client with a caller-supplied key."""

    def __init__(self, client: SystemOneClient, state_builder):
        self._client = client
        self._state_builder = state_builder

    async def send(self, port: Any, payload: dict[str, Any], deadline_ms: int) -> CallOutcome:
        state = self._state_builder(payload)
        return await asyncio.to_thread(self._client.decide, state, payload["questions"], deadline_ms / 1000.0,
                                       payload.get("max_calls", 3))


ROUND3_DECISIONS = frozenset({"d6", "d4"})


class Calibration:
    def __init__(self, path: Path):
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        self.binding = data["binding"]
        self.a, self.b = float(data["platt"]["a"]), float(data["platt"]["b"])
        self.use, self.skip = float(data["bands"]["use"]), float(data["bands"]["skip"])
        if not 0.0 < self.use < 1.0:
            # a calibration that cannot promote is not a calibration: shadow mode comes from the
            # absence of a usable binding, never from a sentinel band
            raise ValueError("use band must be strictly between 0 and 1")

    def matches(self, provider: str, model: Optional[str], descriptor_release: Optional[str],
                template: str = TEMPLATE_VERSION) -> bool:
        binding = self.binding
        bound = binding.get("descriptor_release")
        if binding.get("decision") in ROUND3_DECISIONS:
            # design §8: a Round 3 binding names its state layout; "none" is the v1 pointer layout
            # (the broker reports "none" for it) and matches no other layout
            layout_ok = (bound or "none") == (descriptor_release or "none")
        else:
            layout_ok = bound in (None, "none", descriptor_release)
        return (binding.get("provider") == provider and binding.get("model") == model
                and binding.get("template") == template and layout_ok)

    def apply(self, p_raw: float) -> float:
        p = min(max(p_raw, 1e-6), 1 - 1e-6)
        return 1 / (1 + math.exp(-(self.a * math.log(p / (1 - p)) + self.b)))


class SystemOneHttpAdapter:
    def __init__(self, spec: ProviderSpec, calibration_dir: Path, transport=None, max_calls_per_round: int = 3,
                 templates: Optional[TemplateRegistry] = None, template_ids: Optional[dict[str, str]] = None):
        self.name = spec.name
        self.capabilities = spec.capabilities
        self._calibration_dir = Path(calibration_dir)
        self._transport = transport or BrokerTransport()
        self._max_calls = max_calls_per_round
        self._templates = templates or TemplateRegistry(DEFAULT_TEMPLATES)
        self._template_ids = dict(template_ids or {})

    def template(self, decision: str) -> Template:
        return self._templates.resolve(decision, self.name, self._template_ids.get(decision))

    def _calibration(self, model: Optional[str], decision: str = "d2") -> Optional[Calibration]:
        suffix = "" if decision == "d2" else f".{decision}"
        path = self._calibration_dir / f"{self.name}@{model}{suffix}.yaml"
        try:
            return Calibration(path) if model and path.exists() else None
        except (OSError, KeyError, TypeError, ValueError, yaml.YAMLError):
            return None

    async def decide_batch(self, requests: list[DecisionRequest], port: Any,
                           deadline_ms: int, *, raw_selection: bool = False) -> list[DecisionResult]:
        started = time.monotonic()
        if not requests:
            return []
        query = requests[0].bounded_state["query"]
        template = self.template("d2")
        questions = d2_questions(requests, template)
        payload = {"round": "d2", "query": query, "questions": questions, "template": template.id,
                   "candidate_source_ids": [request.candidate_ids[0] for request in requests],
                   "max_calls": self._max_calls}
        outcome = await self._transport.send(port, payload, deadline_ms)
        digest = request_hash("d2", query, questions)
        if outcome.unavailable_reason is not None:
            return [unavailable(self.name, started, outcome.model) for _ in requests]
        calibration = self._calibration(outcome.model)
        descriptor_release = outcome.descriptor_release
        shadow = (template.diagnostic or calibration is None
                  or not calibration.matches(self.name, outcome.model, descriptor_release, template.id))
        results = []
        for request in requests:
            source_id = request.candidate_ids[0]
            answer = outcome.answers.get(f"d2:{source_id}")
            if answer is None:                               # invalid or missing: keep the candidate
                results.append(unavailable(self.name, started, outcome.model))
                continue
            p_raw = answer["noul"]
            value = {"source": source_id, "p_raw": round(p_raw, 4), "call": True, "shadow": shadow,
                     "request_hash": digest, "usage": outcome.usage, "calls": outcome.calls,
                     "template": template.id}
            if raw_selection:
                # Experimental binary decision: choose the more likely raw label, with no calibration gate.
                value.update(call=p_raw >= 0.5, shadow=False, selection_policy="raw_argmax")
                disposition = "use"
            elif shadow:
                disposition = "preserve_candidate"
            else:
                p = calibration.apply(p_raw)
                value["p"] = round(p, 4)
                if p >= calibration.use:
                    disposition = "use"
                elif p < calibration.skip:
                    disposition, value["call"] = "use", False
                else:
                    disposition = "preserve_candidate"
            results.append(DecisionResult(
                status="answered", value=value, target=TARGET,
                distribution={"useful": round(p_raw, 4), "not_useful": round(1 - p_raw, 4)},
                calibration=None if shadow or raw_selection else {"method": "platt_on_logit", "binding": f"{self.name}@{outcome.model}"},
                disposition=disposition, provider=self.name, model_version=outcome.model,
                policy_version=POLICY_VERSION, latency_ms=outcome.latency_ms, cost=0))
        return results


class ItemJudgement:
    """One Round 3 answer: raw and calibrated p (None when shadow or unavailable)."""

    def __init__(self, qid: str, p_raw: Optional[float], p: Optional[float], shadow: bool):
        self.qid, self.p_raw, self.p, self.shadow = qid, p_raw, p, shadow


async def decide_items(adapter: "SystemOneHttpAdapter", round_name: str, items: dict[str, list[dict[str, Any]]],
                       query: str, port: Any, deadline_ms: int,
                       item_meta: Optional[dict[str, dict[str, Any]]] = None) -> tuple[dict[str, ItemJudgement], list[DecisionResult], Optional[Calibration]]:
    """A Round 3 round (design page §14): the resolved template's question(s) per item; items carry
    provenance refs only and the broker reads the text. Returns judgements, receipt DecisionResults
    and the calibration used. Diagnostic templates and templates without a matching calibration
    are shadow-only: recorded, never applied."""
    started = time.monotonic()
    template = adapter.template(round_name)
    questions: dict[str, dict[str, Any]] = {}
    item_payload: dict[str, dict[str, Any]] = {}
    for qid, refs in items.items():
        for question_id, question in template.questions(qid).items():
            questions[question_id] = question
            item_payload[question_id] = {"refs": refs}
    payload = {"round": round_name, "query": query, "questions": questions, "items": item_payload,
               "template": template.id, "state_kind": template.state,
               # Round 3 may need about one call per item on small-context providers; the broker
               # still caps calls by the run profile
               "max_calls": ROUND3_MAX_CALLS}
    outcome = await adapter._transport.send(port, payload, deadline_ms)
    digest = request_hash(round_name, query, questions)
    judgements: dict[str, ItemJudgement] = {}
    results: list[DecisionResult] = []
    calibration = None if outcome.unavailable_reason or template.diagnostic else adapter._calibration(outcome.model, round_name)
    shadow = (template.diagnostic or calibration is None
              or not calibration.matches(adapter.name, outcome.model, outcome.descriptor_release, template.id))
    for qid, refs in items.items():
        own = [question_id for question_id in questions if question_id == qid or question_id.startswith(qid + "#")]
        answers = {} if outcome.unavailable_reason else {q: outcome.answers[q] for q in own if q in outcome.answers}
        if len(answers) != len(own):                   # any missing part: the item is unavailable
            judgements[qid] = ItemJudgement(qid, None, None, True)
            result = unavailable(adapter.name, started, outcome.model)
            results.append(result.model_copy(update={"target": f"{round_name}:{qid}"}))
            continue
        single = answers.get(qid)
        p_raw = single["noul"] if single is not None and single.get("type") == "noul" else None
        p = None if shadow or p_raw is None else calibration.apply(p_raw)
        judgements[qid] = ItemJudgement(qid, None if template.diagnostic else p_raw, p, shadow)
        value = {"item": qid, "shadow": shadow, "refs": refs, "request_hash": digest, "usage": outcome.usage,
                 "calls": outcome.calls, "template": template.id, "diagnostic": template.diagnostic,
                 "answers": answers, **((item_meta or {}).get(qid) or {})}
        if p_raw is not None:
            value["p_raw"] = round(p_raw, 4)
            if template.polarity == "negative":
                value["p_signal"] = round(1 - p_raw, 4)          # diagnostic signal only
        if p is not None:
            value["p"] = round(p, 4)
        # the evaluator's label reader (sanctum_eval.calibration_labels) keys on these names
        if round_name == "d6":
            value.update({"pair": qid, "a": refs[0], "b": refs[1]})
        elif round_name == "d4":
            value.update({"unit": qid, "ref": refs[0]})
        results.append(DecisionResult(
            status="answered", value=value, target=f"{round_name}: template {template.id}",
            distribution=None if p_raw is None else {"true": round(p_raw, 4), "false": round(1 - p_raw, 4)},
            calibration=None if shadow else {"method": "platt_on_logit", "binding": f"{adapter.name}@{outcome.model}.{round_name}"},
            disposition="use" if (p is not None and p >= calibration.use) else "preserve_candidate",
            provider=adapter.name, model_version=outcome.model, policy_version=POLICY_VERSION,
            latency_ms=outcome.latency_ms, cost=0))
    return judgements, results, (None if shadow else calibration)
