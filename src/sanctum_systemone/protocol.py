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
    TRUNCATED = "truncated"                                # the provider dropped part of the state


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


PROBABILITY_SUM_TOLERANCE = 0.01          # choice probabilities must sum to 1 within this


def _score_range(question: dict[str, Any]) -> Optional[tuple[float, float]]:
    """(lowest, highest) declared score level: a list declares levels 0..n-1 (index = level), a
    mapping declares its integer keys. None when no levels are declared."""
    criteria = question.get("criteria")
    if isinstance(criteria, list) and criteria:
        return 0.0, float(len(criteria) - 1)
    if isinstance(criteria, dict) and criteria:
        try:
            levels = [int(level) for level in criteria]
        except (TypeError, ValueError):
            return None
        return float(min(levels)), float(max(levels))
    return None


def _score_in_range(question: dict[str, Any], score: float) -> bool:
    bounds = _score_range(question)
    return bounds is None or bounds[0] <= score <= bounds[1]


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
                    and all(_probability(p) for p in probabilities.values())
                    and abs(sum(float(p) for p in probabilities.values()) - 1.0) <= PROBABILITY_SUM_TOLERANCE):
                valid[qid] = {"type": "choice", "choice": answer["choice"], "probabilities": dict(probabilities),
                              "confidence": answer.get("confidence")}
            else:
                invalid.append(qid)
        elif kind == "score" and isinstance(answer.get("score"), (int, float)) and not isinstance(answer.get("score"), bool) \
                and _score_in_range(question, float(answer["score"])):
            valid[qid] = {"type": "score", "score": float(answer["score"])}
        else:
            invalid.append(qid)
    extra = set(answers) - set(asked)                       # ids never asked: the whole call is suspect
    if extra:
        return {}, sorted(asked)
    return valid, invalid


def truncation(response: Any) -> tuple[bool, list[str]]:
    """(state truncated, truncated question ids) from provider usage metadata. Laya reports
    `usage.truncated`, `state_tokens_dropped` and `truncated_questions`; a provider that reports
    nothing is guarded by the declared `max_state_chars` budget instead."""
    usage = response.get("usage") if isinstance(response, dict) else None
    if not isinstance(usage, dict):
        return False, []
    dropped = usage.get("state_tokens_dropped")
    state = bool(usage.get("truncated")) or (isinstance(dropped, (int, float)) and dropped > 0)
    questions = usage.get("truncated_questions")
    return state, [str(q) for q in questions] if isinstance(questions, list) else []


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


class CampaignBudget:
    """A hard campaign ceiling enforced before every HTTP attempt (review: pre-dispatch cap).

    Each attempt must fit in the remaining calls and reserve an input-token estimate for that
    exchange; the exchange's reported usage is then recorded once (or the reservation, when the
    provider reports none). Thread-safe; one per process (`set_campaign_budget`)."""

    def __init__(self, max_calls: int, max_input_tokens: int, max_output_tokens: Optional[int] = None):
        import threading
        self.max_calls, self.max_input_tokens, self.max_output_tokens = max_calls, max_input_tokens, max_output_tokens
        self.calls = self.input_tokens = self.output_tokens = 0
        self._lock = threading.Lock()
        self._reserved = 0

    def reserve(self, estimated_input_tokens: int) -> bool:
        with self._lock:
            if self.calls + 1 > self.max_calls:
                return False
            if self.input_tokens + self._reserved + estimated_input_tokens > self.max_input_tokens:
                return False
            if self.max_output_tokens is not None and self.output_tokens >= self.max_output_tokens:
                return False
            self.calls += 1
            self._reserved += estimated_input_tokens
            return True

    def settle(self, estimated_input_tokens: int, usage: Any) -> None:
        with self._lock:
            self._reserved -= estimated_input_tokens
            reported = usage.get("input_tokens") if isinstance(usage, dict) else None
            self.input_tokens += int(reported) if isinstance(reported, (int, float)) else estimated_input_tokens
            output = usage.get("output_tokens") if isinstance(usage, dict) else None
            self.output_tokens += int(output) if isinstance(output, (int, float)) else 0

    def summary(self) -> dict[str, int]:
        return {"calls": self.calls, "input_tokens": self.input_tokens, "output_tokens": self.output_tokens}


_CAMPAIGN: Optional[CampaignBudget] = None


def set_campaign_budget(budget: Optional[CampaignBudget]) -> None:
    global _CAMPAIGN
    _CAMPAIGN = budget


def estimate_input_tokens(body: dict[str, Any]) -> int:
    """Conservative reservation: about 3 characters per token over the serialized request."""
    import json as _json
    return len(_json.dumps(body)) // 3 + 64


class SystemOneClient:
    """One `/v1/systemone` endpoint. The API key is passed in by the caller (the runner's broker
    or a lab tool); this module never reads the environment for it."""

    def __init__(self, spec: ProviderSpec, base_url: str, model: Optional[str], api_key: Optional[str] = None,
                 transport: Optional[httpx.BaseTransport] = None, campaign_budget: Optional[CampaignBudget] = None):
        self.spec = spec
        self.model = model
        self.campaign_budget = campaign_budget
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        self._http = httpx.Client(base_url=base_url, headers=headers, transport=transport)

    def close(self) -> None:
        self._http.close()

    def decide(self, state: Any, questions: dict[str, dict[str, Any]], deadline_s: float,
               max_calls: int, state_for=None) -> CallOutcome:
        """`state_for(batch_qids) -> state` (Round 3): each batch carries only its own items, and
        batches are split further until each state fits `max_state_chars`. A single question whose
        own state is still too large is refused, never truncated."""
        started = time.monotonic()
        outcome = CallOutcome(provider=self.spec.name)
        limit = self.spec.capabilities.max_state_chars
        batches, refused = split_questions(questions, self.spec.capabilities)
        outcome.invalid_ids.extend(refused)
        if state_for is None:
            if len(repr(state)) > limit:
                outcome.unavailable_reason = UnavailableReason.OVER_BUDGET   # refuse rather than risk truncation
                return outcome
            states = [state] * len(batches)
        else:
            sized: list[dict[str, dict[str, Any]]] = []
            for batch in batches:
                current: dict[str, dict[str, Any]] = {}
                for qid, question in batch.items():
                    if len(repr(state_for([qid]))) > limit:
                        outcome.invalid_ids.append(qid)             # too large on its own
                        continue
                    if current and len(repr(state_for([*current, qid]))) > limit:
                        sized.append(current)
                        current = {}
                    current[qid] = question
                if current:
                    sized.append(current)
            batches, states = sized, [state_for(list(batch)) for batch in sized]
        if len(batches) > max_calls:
            outcome.unavailable_reason = UnavailableReason.OVER_BUDGET
            return outcome
        for batch, batch_state in zip(batches, states):
            response, reason = self._post(batch_state, batch, started, deadline_s, outcome, max_calls)
            if reason is not None:
                outcome.unavailable_reason = reason
                break
            truncated_state, truncated_ids = truncation(response)
            if truncated_state:
                outcome.unavailable_reason = UnavailableReason.TRUNCATED   # never trust a truncated read
                outcome.answers.clear()
                break
            valid, invalid = validate_answers(batch, response)
            for qid in truncated_ids:
                if valid.pop(qid, None) is not None:
                    invalid.append(qid)
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

    def _post(self, state, batch, started, deadline_s, outcome,
              max_calls: Optional[int] = None) -> tuple[Optional[dict], Optional[UnavailableReason]]:
        """One exchange with retries. `max_calls` bounds HTTP attempts for the whole round,
        retries included: a retry that would exceed it is not sent."""
        body = build_request(state, self.model, batch)
        campaign = self.campaign_budget if self.campaign_budget is not None else _CAMPAIGN
        reason = UnavailableReason.TIMEOUT
        for attempt in range(1 + self.spec.timeout_retry):
            if max_calls is not None and outcome.calls >= max_calls:
                return None, reason if attempt else UnavailableReason.OVER_BUDGET
            remaining = deadline_s - (time.monotonic() - started)
            if remaining <= 0.01:
                return None, UnavailableReason.TIMEOUT
            estimate = estimate_input_tokens(body)
            if campaign is not None and not campaign.reserve(estimate):
                return None, UnavailableReason.OVER_BUDGET          # refused before dispatch
            outcome.calls += 1
            usage_seen: Any = None
            try:
                response = self._http.post(ENDPOINT, json=body, timeout=remaining)
                if response.status_code == 200:
                    try:
                        parsed = response.json()
                        usage_seen = parsed.get("usage") if isinstance(parsed, dict) else None
                    except ValueError:
                        usage_seen = None
            except httpx.TimeoutException:
                if campaign is not None:
                    campaign.settle(estimate, None)
                reason = UnavailableReason.TIMEOUT
                continue
            except httpx.HTTPError:
                if campaign is not None:
                    campaign.settle(estimate, None)
                reason = UnavailableReason.ERROR
                continue
            if campaign is not None:
                campaign.settle(estimate, usage_seen)             # counted once per exchange
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
