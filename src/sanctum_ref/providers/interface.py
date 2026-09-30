"""System One provider interface (design page §2) and shared D2 helpers.

`decide_batch(requests, port, deadline_ms)` answers one decision round: one `DecisionResult` per
request, in order (HLD §6.6). Every provider degrades the same way: anything it cannot answer
cleanly is `unavailable` with no value, and the router keeps the candidate."""
from __future__ import annotations

import time
from typing import Any, Optional, Protocol

from sanctum_contracts import DecisionRequest, DecisionResult
from sanctum_systemone import ProviderCapabilities

TARGET = "P(source returns necessary supporting evidence | query, authorized source)"
POLICY_VERSION = "d2-policy-1"
RUBRIC_VERSION = "d2-rubric-1"


class ProviderNotApproved(RuntimeError):
    pass


class DecisionUnavailable(RuntimeError):
    pass


class SystemOneProvider(Protocol):
    name: str
    capabilities: ProviderCapabilities

    async def decide_batch(self, requests: list[DecisionRequest], port: Any,
                           deadline_ms: int) -> list[DecisionResult]: ...


def d2_request(source_id: str, query: str, deadline_ms: int) -> DecisionRequest:
    return DecisionRequest(decision_type="D2", rubric_version=RUBRIC_VERSION, candidate_ids=[source_id],
                           bounded_state={"query": query, "source_id": source_id}, deadline_ms=deadline_ms,
                           provider_policy_version=POLICY_VERSION)


def unavailable(provider: str, started: float, model_version: Optional[str] = None) -> DecisionResult:
    return DecisionResult(status="unavailable", target=TARGET, disposition="preserve_candidate", provider=provider,
                          model_version=model_version, policy_version=POLICY_VERSION,
                          latency_ms=int((time.monotonic() - started) * 1000), cost=0)


class PerRequestProvider:
    """Adapts a provider with a synchronous per-request `decide` to the batch interface."""

    async def decide_batch(self, requests, port, deadline_ms):
        return [self.decide(request) for request in requests]
