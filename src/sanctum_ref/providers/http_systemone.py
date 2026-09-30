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

TEMPLATE_VERSION = "d2-noul-v1"
D2_INSTRUCTIONS = ("Answer true if searching the source named in the question is likely to return evidence "
                   "necessary to answer the query in the state, judged from the source's description.")
BROKER_TOOL = "system_one.decide"


def d2_questions(requests: list[DecisionRequest]) -> dict[str, dict[str, Any]]:
    return {f"d2:{request.candidate_ids[0]}": {
        "type": "noul",
        "instructions": f"{D2_INSTRUCTIONS} Source: {request.candidate_ids[0]}."} for request in requests}


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


class Calibration:
    def __init__(self, path: Path):
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        self.binding = data["binding"]
        self.a, self.b = float(data["platt"]["a"]), float(data["platt"]["b"])
        self.use, self.skip = float(data["bands"]["use"]), float(data["bands"]["skip"])

    def matches(self, provider: str, model: Optional[str], descriptor_release: Optional[str]) -> bool:
        binding = self.binding
        return (binding.get("provider") == provider and binding.get("model") == model
                and binding.get("template") == TEMPLATE_VERSION
                and binding.get("descriptor_release") in (None, descriptor_release))

    def apply(self, p_raw: float) -> float:
        p = min(max(p_raw, 1e-6), 1 - 1e-6)
        return 1 / (1 + math.exp(-(self.a * math.log(p / (1 - p)) + self.b)))


class SystemOneHttpAdapter:
    def __init__(self, spec: ProviderSpec, calibration_dir: Path, transport=None, max_calls_per_round: int = 3):
        self.name = spec.name
        self.capabilities = spec.capabilities
        self._calibration_dir = Path(calibration_dir)
        self._transport = transport or BrokerTransport()
        self._max_calls = max_calls_per_round

    def _calibration(self, model: Optional[str]) -> Optional[Calibration]:
        path = self._calibration_dir / f"{self.name}@{model}.yaml"
        try:
            return Calibration(path) if model and path.exists() else None
        except (OSError, KeyError, TypeError, ValueError, yaml.YAMLError):
            return None

    async def decide_batch(self, requests: list[DecisionRequest], port: Any,
                           deadline_ms: int) -> list[DecisionResult]:
        started = time.monotonic()
        if not requests:
            return []
        query = requests[0].bounded_state["query"]
        questions = d2_questions(requests)
        payload = {"round": "d2", "query": query, "questions": questions,
                   "candidate_source_ids": [request.candidate_ids[0] for request in requests],
                   "max_calls": self._max_calls}
        outcome = await self._transport.send(port, payload, deadline_ms)
        digest = request_hash("d2", query, questions)
        if outcome.unavailable_reason is not None:
            return [unavailable(self.name, started, outcome.model) for _ in requests]
        calibration = self._calibration(outcome.model)
        descriptor_release = outcome.descriptor_release
        shadow = calibration is None or not calibration.matches(self.name, outcome.model, descriptor_release)
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
                     "template": TEMPLATE_VERSION}
            if shadow:
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
                calibration=None if shadow else {"method": "platt_on_logit", "binding": f"{self.name}@{outcome.model}"},
                disposition=disposition, provider=self.name, model_version=outcome.model,
                policy_version=POLICY_VERSION, latency_ms=outcome.latency_ms, cost=0))
        return results
