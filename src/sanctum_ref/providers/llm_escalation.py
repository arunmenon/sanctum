"""Tier 2 LLM escalation (design page §1): interface only in this spike.

TODO: wire a model once an LLM budget (calls and spend per request) is decided."""
from __future__ import annotations

from sanctum_systemone import ProviderCapabilities


class NotConfigured(RuntimeError):
    pass


class LLMEscalationProvider:
    name = "llm-escalation"
    capabilities = ProviderCapabilities(primitives=["noul", "choice", "score"], conformance="experimental")

    async def decide_batch(self, requests, port, deadline_ms):
        raise NotConfigured("Tier 2 LLM escalation is not configured in this spike (no LLM budget decided)")
