"""Protocol core: specs, request building, split/merge, strict validation, one HTTP client.

Handshake points (design page §5): bearer auth with a key the caller supplies (never read here);
the resolved `model` from each response is kept; batches split only on declared provider limits
under one shared deadline and a total-call limit; at most one retry, only if time remains; any
answer that is not exactly what was asked is invalid; `score` and `choice` are never converted.
"""
from __future__ import annotations

import time
from enum import StrEnum
from pathlib import Path
from typing import Any, Optional

import httpx
import yaml
from pydantic import BaseModel, ConfigDict, Field

PRIMITIVES = ("noul", "choice", "score")
ENDPOINT = "/v1/systemone"


class UnavailableReason(StrEnum):
    TIMEOUT = "timeout"
    ERROR = "error"
    INVALID_OUTPUT = "invalid_output"
    DATA_CLASS_REFUSED = "data_class_refused"
    NOT_CONFIGURED = "not_configured"
    OVER_BUDGET = "over_budget"


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ProviderCapabilities(_Model):
    primitives: list[str] = Field(default_factory=lambda: ["noul"])
    max_questions_per_call: int = Field(default=20, gt=0)
    max_options: int = Field(default=20, gt=0)
    max_state_chars: int = Field(default=20000, gt=0)     # refuse, never truncate (Laya note)
    batching: bool = True
    reports_usage: bool = False
    hosted: bool = False
    data_classes_allowed: list[str] = Field(default_factory=lambda: ["synthetic"])
    conformance: str = "experimental"                     # supported | experimental
    confidence_thresholdable: bool = False                # bands never use `confidence`


class ProviderSpec(_Model):
    model_config = ConfigDict(extra="forbid", frozen=True, protected_namespaces=())
    name: str
    kind: str                                             # http | standin | llm
    base_url_env: Optional[str] = None                    # env var NAMES only
    base_url: Optional[str] = None                        # a fixed local URL (no secret)
    model_env: Optional[str] = None
    model: Optional[str] = None
    api_key_env: Optional[str] = None                     # read by the broker or a tool, never the SUT
    timeout_retry: int = Field(default=1, ge=0, le=1)
    capabilities: ProviderCapabilities = ProviderCapabilities()
    notes: Optional[str] = None

    def resolved_base_url(self, environment: dict[str, str]) -> Optional[str]:
        return environment.get(self.base_url_env) if self.base_url_env else self.base_url

    def requested_model(self, environment: dict[str, str]) -> Optional[str]:
        return environment.get(self.model_env, self.model) if self.model_env else self.model


def load_provider_specs(path: Path) -> dict[str, ProviderSpec]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return {name: ProviderSpec(name=name, **body) for name, body in (data.get("providers") or {}).items()}


def build_request(state: Any, model: Optional[str], questions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {"state": state, "model": model, "questions": questions}


def _options(question: dict[str, Any]) -> int:
    criteria = question.get("criteria") or {}
    return len(criteria) if isinstance(criteria, dict) else len(criteria or [])


def split_questions(questions: dict[str, dict[str, Any]],
                    capabilities: ProviderCapabilities) -> tuple[list[dict[str, dict[str, Any]]], list[str]]:
    """(batches, refused ids). A question with more options than declared, or a primitive the
    provider does not offer, is refused (never truncated, never converted)."""
    refused = [qid for qid, q in questions.items()
               if q.get("type") not in capabilities.primitives or _options(q) > capabilities.max_options]
    kept = [(qid, q) for qid, q in questions.items() if qid not in refused]
    size = capabilities.max_questions_per_call if capabilities.batching else 1
    return [dict(kept[i:i + size]) for i in range(0, len(kept), size)], refused


def _probability(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0.0 <= float(value) <= 1.0


def validate_answers(asked: dict[str, dict[str, Any]], response: Any) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """(valid answers, invalid ids). An answer counts only if it is exactly what was asked."""
    answers = (response or {}).get("answers") if isinstance(response, dict) else None
    if not isinstance(answers, dict):
        return {}, sorted(asked)
    valid, invalid = {}, []
    for qid, question in asked.items():
        answer = answers.get(qid)
        if not isinstance(answer, dict) or answer.get("type") != question.get("type"):
            invalid.append(qid)
            continue
        kind = question["type"]
        if kind == "noul" and _probability(answer.get("noul")):
            valid[qid] = {"type": "noul", "noul": float(answer["noul"])}
        elif kind == "choice":
            options = set((question.get("criteria") or {}).keys()) if isinstance(question.get("criteria"), dict) else set(question.get("criteria") or [])
            probabilities = answer.get("probabilities")
            if (answer.get("choice") in options and isinstance(probabilities, dict) and set(probabilities) <= options
                    and all(_probability(p) for p in probabilities.values())):
                valid[qid] = {"type": "choice", "choice": answer["choice"], "probabilities": dict(probabilities),
                              "confidence": answer.get("confidence")}
            else:
                invalid.append(qid)
        elif kind == "score" and isinstance(answer.get("score"), (int, float)) and not isinstance(answer.get("score"), bool):
            valid[qid] = {"type": "score", "score": float(answer["score"])}
        else:
            invalid.append(qid)
    extra = set(answers) - set(asked)                       # ids never asked: the whole call is suspect
    if extra:
        return {}, sorted(asked)
    return valid, invalid


class CallOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: str
    model: Optional[str] = None                             # resolved version from the response
    answers: dict[str, dict[str, Any]] = Field(default_factory=dict)
    usage: Optional[dict[str, Any]] = None
    latency_ms: int = 0
    calls: int = 0
    unavailable_reason: Optional[UnavailableReason] = None
    invalid_ids: list[str] = Field(default_factory=list)
    descriptor_release: Optional[str] = None                # which pinned descriptors the state used


def _add_usage(total: Optional[dict[str, Any]], usage: Any) -> Optional[dict[str, Any]]:
    if not isinstance(usage, dict):
        return total
    total = dict(total or {})
    for key, value in usage.items():
        if isinstance(value, (int, float)):
            total[key] = total.get(key, 0) + value
    return total


class SystemOneClient:
    """One `/v1/systemone` endpoint. The API key is passed in by the caller (the runner's broker
    or a lab tool); this module never reads the environment for it."""

    def __init__(self, spec: ProviderSpec, base_url: str, model: Optional[str], api_key: Optional[str] = None,
                 transport: Optional[httpx.BaseTransport] = None):
        self.spec = spec
        self.model = model
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._http = httpx.Client(base_url=base_url, headers=headers, transport=transport)

    def close(self) -> None:
        self._http.close()

    def decide(self, state: Any, questions: dict[str, dict[str, Any]], deadline_s: float,
               max_calls: int) -> CallOutcome:
        started = time.monotonic()
        outcome = CallOutcome(provider=self.spec.name)
        if len(repr(state)) > self.spec.capabilities.max_state_chars:
            outcome.unavailable_reason = UnavailableReason.OVER_BUDGET   # refuse rather than risk truncation
            return outcome
        batches, refused = split_questions(questions, self.spec.capabilities)
        outcome.invalid_ids.extend(refused)
        if len(batches) > max_calls:
            outcome.unavailable_reason = UnavailableReason.OVER_BUDGET
            return outcome
        for batch in batches:
            response, reason = self._post(state, batch, started, deadline_s, outcome)
            if reason is not None:
                outcome.unavailable_reason = reason
                break
            valid, invalid = validate_answers(batch, response)
            outcome.answers.update(valid)
            outcome.invalid_ids.extend(invalid)
            outcome.model = outcome.model or response.get("model")
            if response.get("model") and outcome.model != response.get("model"):
                outcome.unavailable_reason = UnavailableReason.INVALID_OUTPUT   # version changed mid-round
                break
            outcome.usage = _add_usage(outcome.usage, response.get("usage"))
        if outcome.unavailable_reason is None and questions and not outcome.answers:
            outcome.unavailable_reason = UnavailableReason.INVALID_OUTPUT
        outcome.latency_ms = int((time.monotonic() - started) * 1000)
        return outcome

    def _post(self, state, batch, started, deadline_s, outcome) -> tuple[Optional[dict], Optional[UnavailableReason]]:
        body = build_request(state, self.model, batch)
        reason = UnavailableReason.TIMEOUT
        for attempt in range(1 + self.spec.timeout_retry):
            remaining = deadline_s - (time.monotonic() - started)
            if remaining <= 0.01:
                return None, UnavailableReason.TIMEOUT
            outcome.calls += 1
            try:
                response = self._http.post(ENDPOINT, json=body, timeout=remaining)
            except httpx.TimeoutException:
                reason = UnavailableReason.TIMEOUT
                continue
            except httpx.HTTPError:
                reason = UnavailableReason.ERROR
                continue
            if response.status_code >= 500:
                reason = UnavailableReason.ERROR
                continue
            if response.status_code != 200:
                return None, UnavailableReason.ERROR      # 4xx is not retried
            try:
                payload = response.json()
            except ValueError:
                return None, UnavailableReason.INVALID_OUTPUT
            return (payload, None) if isinstance(payload, dict) else (None, UnavailableReason.INVALID_OUTPUT)
        return None, reason
