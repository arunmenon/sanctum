"""The six stages of one request (HLD §5.1) for C1-naive, C1-fair and C2.

1. Who is asking: the proxy returns the verified caller's access groups (never the principal).
2. What is allowed: groups x registry places x hub capabilities.
3. What is worth asking: fan-out or intent rules, capability guards, must-consult.
4. Ask: searches in parallel, then fetches of the top hits, under one shared deadline.
5. Clean up: dedup, rank, conflict flags, pack (assembly.py).
6. Record and reply: the receipt is built before the response and carries the config id.

Fail closed: if the registry or the caller's verification is unavailable, no hub is called and
the response claims nothing (`evidence_status: unknown`, no sources, no evidence).
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import anyio

from sanctum_contracts import (
    CONTRACT_REVISION, Budget, EvidenceResponse, EvidenceStatus, Receipt, RetrieveRequest,
    SourceOutcome,
)
from sanctum_contracts.receipt import QueryPlan, SelfReportedCall

from .adapters import Candidate, HubPort, evidence_unit, fetch_arguments, search_arguments
from .assembly import assemble
from .config import ArmConfig
from .intent import analyze
from .registry import Registry, RegistryUnavailable
from .routing import SourcePlan, plan_sources
from .text import stem

FETCH_PER_SOURCE = 5
UNCOVERED_SHARE = 0.25
MEMORY_RELEASE = "none"                      # no memory store in C1/C2
TIMEOUT_CODES = {"timeout"}


@dataclass
class CallLog:
    started: float
    calls: list[SelfReportedCall] = field(default_factory=list)

    def record(self, source_id: str, tool: str, status: str, started: float) -> None:
        self.calls.append(SelfReportedCall(source_id=source_id, tool=tool, status=status,
                                           started_ms=int((started - self.started) * 1000),
                                           ended_ms=int((time.monotonic() - self.started) * 1000)))


def _status_of(payload: Optional[dict[str, Any]]) -> str:
    if payload is None:
        return "timeout"
    error = payload.get("error")
    if not error:
        return "ok"
    return "timeout" if error.get("code") in TIMEOUT_CODES else "error"


def _place_has_versions(capabilities: dict[str, Any], hit: dict[str, Any]) -> bool:
    """Under as_of, a hit from a place without version reads cannot stand for a past version
    (DocHub `space:PA`, discrepancy register 11): it is not used."""
    place_reads = capabilities.get("place_version_reads") or {}
    return place_reads.get(hit.get("location") or "", True)


class Retriever:
    def __init__(self, arm: ArmConfig, registry: Optional[Registry],
                 registry_error: Optional[str] = None):
        self.arm = arm
        self.registry = registry
        self.registry_error = registry_error

    # ---- entry point ---------------------------------------------------------------------------
    async def retrieve(self, request: RetrieveRequest, port: HubPort) -> tuple[EvidenceResponse, Receipt]:
        clock = CallLog(time.monotonic())
        receipt_id = "rc-" + hashlib.sha256(f"{self.arm.config_id}:{request.request_id}".encode()).hexdigest()[:16]
        if self.registry is None:
            return self._fail_closed(request, receipt_id, "registry")
        groups = await port.caller_groups()
        capabilities = await port.capabilities() if groups is not None else None
        if groups is None or capabilities is None:
            return self._fail_closed(request, receipt_id, "caller")
        releases = {release for manifest in self.registry.manifests.values() for release in manifest.versions.releases}
        intent = analyze(request.query, self.registry.domains, releases, verify=request.mode.value == "verify")
        plans = plan_sources(request, self.arm, self.registry, intent, capabilities, set(groups))
        deadline = time.monotonic() + min(request.deadline_ms, self.arm.deadline_ms) / 1000.0
        outcomes: dict[str, str] = {}
        candidates = await self._ask(request, plans, port, clock, deadline, intent.fact_kinds, outcomes,
                                     capabilities)
        assembled = assemble(candidates, intent.terms, intent.fact_kinds, request.budget_tokens,
                             self.arm.tokenizer, common=self.arm.common_assembly,
                             dedup_exact=self.arm.exact_dedup,
                             domain_terms={stem(term) for terms in self.registry.domains.values() for term in terms})
        sources, response_reasons, required_gap = self._sources(plans, outcomes)
        status = self._status(assembled, intent.vague, required_gap)
        if assembled.truncated_relevant:
            response_reasons.append("insufficient_budget")
        if status == EvidenceStatus.insufficient and not required_gap:
            response_reasons.append("no_coverage")
        receipt = Receipt(
            receipt_id=receipt_id, request_id=request.request_id, config_id=self.arm.config_id,
            contract_revision=CONTRACT_REVISION, memory_release_id=MEMORY_RELEASE,
            query_plans=[QueryPlan(source_id=plan.hub_id, original_query=request.query,
                                   selectors=[f"{key}={value}" for key, value in sorted(plan.selectors.items())],
                                   as_of=plan.as_of)
                         for plan in plans if plan.call],
            calls=clock.calls, complete=True,
            timings_ms={"total": int((time.monotonic() - clock.started) * 1000)})
        response = EvidenceResponse(
            request_id=request.request_id, receipt_id=receipt_id, memory_release_id=MEMORY_RELEASE,
            effective_scope_ref=self._scope_ref(request, groups),
            policy_versions={"registry": self.registry.version, "config": self.arm.config_id},
            replay_level="recompute_on_candidates", evidence=assembled.evidence,
            conflicts=assembled.conflicts, sources=sources, evidence_status=status,
            reasons=sorted(set(response_reasons)), omitted=assembled.omitted,
            budget=Budget(requested=request.budget_tokens, used=assembled.used_tokens,
                          tokenizer_id=self.arm.tokenizer),
            truncation=assembled.truncated_relevant)
        return response, receipt

    # ---- stage 4 -------------------------------------------------------------------------------
    async def _ask(self, request: RetrieveRequest, plans: list[SourcePlan], port: HubPort, clock: CallLog,
                   deadline: float, fact_kinds: frozenset[str], outcomes: dict[str, str],
                   capabilities: dict[str, Any]) -> list[Candidate]:
        hits: dict[str, list[tuple[Optional[str], dict[str, Any]]]] = {}

        async def call(plan: SourcePlan, tool: str, arguments: dict[str, Any]) -> Optional[dict[str, Any]]:
            started = time.monotonic()
            payload: Optional[dict[str, Any]] = None
            try:
                with anyio.move_on_after(max(0.0, deadline - time.monotonic())):
                    payload = await port.call(plan.hub_id, tool, arguments)
            finally:
                clock.record(plan.hub_id, tool, _status_of(payload), started)
            return payload

        async def search(plan: SourcePlan, ref: Optional[str]) -> None:
            payload = await call(plan, plan.manifest.search.tool,
                                 search_arguments(plan.manifest, request.query, plan.selectors, ref))
            status = _status_of(payload)
            # a source is "called" only if every search it needed succeeded
            if outcomes.get(plan.hub_id, "ok") == "ok":
                outcomes[plan.hub_id] = status
            if status == "ok":
                results = [hit for hit in payload.get("results") or []
                           if not plan.as_of or _place_has_versions(capabilities.get(plan.hub_id, {}), hit)]
                hits.setdefault(plan.hub_id, []).extend((ref, hit) for hit in results[:FETCH_PER_SOURCE])

        async with anyio.create_task_group() as group:
            for plan in plans:
                if plan.call:
                    for ref in plan.version_refs:
                        group.start_soon(search, plan, ref)

        fetched: list[Candidate] = []
        retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        by_hub = {plan.hub_id: plan for plan in plans}
        budget = self.arm.candidates

        async def fetch(plan: SourcePlan, rank: int, ref: Optional[str], hit: dict[str, Any]) -> None:
            arguments = fetch_arguments(plan.manifest, hit, ref)
            if arguments is None:
                return
            payload = await call(plan, plan.manifest.fetch.tool, arguments)
            if _status_of(payload) != "ok" or "artifact" not in payload:
                return
            artifact = payload["artifact"]
            fetched.append(Candidate(plan.hub_id, rank, plan.manifest, artifact,
                                     evidence_unit(plan.manifest, artifact, "", retrieved_at,
                                                   self.arm.tokenizer, fact_kinds)))

        async with anyio.create_task_group() as group:
            for hub_id in sorted(hits):
                seen: set[tuple[str, str]] = set()
                for rank, (ref, hit) in enumerate(hits[hub_id]):
                    key = (str(hit.get("artifact_id")), str(hit.get("version")))
                    if budget <= 0 or key in seen:
                        continue
                    seen.add(key)
                    budget -= 1
                    group.start_soon(fetch, by_hub[hub_id], rank, ref, hit)
        # deterministic evidence ids: hub order, then hub rank
        fetched.sort(key=lambda candidate: (candidate.source_id, candidate.hub_rank))
        for index, candidate in enumerate(fetched):
            candidate.unit = candidate.unit.model_copy(update={"evidence_id": f"ev-{index + 1}"})
        return fetched

    # ---- stage 6 helpers ---------------------------------------------------------------------------
    @staticmethod
    def _sources(plans: list[SourcePlan], outcomes: dict[str, str]) -> tuple[list[SourceOutcome], list[str], bool]:
        sources, reasons, required_gap = [], [], False
        for plan in plans:
            status, source_reasons = plan.status, list(plan.reasons)
            if plan.call:
                outcome = outcomes.get(plan.hub_id, "timeout")
                status = {"ok": "called", "timeout": "timeout"}.get(outcome, "error")
            gap = None
            if plan.required and "required_source_denied" in source_reasons:
                gap = "required_source_denied"
            elif plan.required and status in ("timeout", "error", "unsupported_for_mode"):
                gap = "required_source_unavailable"
                source_reasons.append(gap)
            if gap:
                required_gap = True
                reasons.append(gap)
            sources.append(SourceOutcome(source_id=plan.hub_id, status=status, reasons=sorted(set(source_reasons))))
        return sources, reasons, required_gap

    @staticmethod
    def _status(assembled, vague: bool, required_gap: bool) -> EvidenceStatus:
        # a large share of the subject that no source returned anything about (the asked-for
        # attribute of a service nobody documents, HLD §10 Ex8): the question is not covered
        if not assembled.relevant_packed or assembled.uncovered_share >= UNCOVERED_SHARE:
            return EvidenceStatus.insufficient
        if required_gap or vague or assembled.truncated_relevant:
            return EvidenceStatus.partial
        return EvidenceStatus.sufficient

    def _scope_ref(self, request: RetrieveRequest, groups: list[str]) -> str:
        material = f"{request.scope or 'default'}|{','.join(sorted(groups))}|{self.registry.version}"
        return "scope-" + hashlib.sha256(material.encode()).hexdigest()[:12]

    def _fail_closed(self, request: RetrieveRequest, receipt_id: str, cause: str) -> tuple[EvidenceResponse, Receipt]:
        """Registry or caller verification unavailable: no hub call, no evidence, no claim."""
        receipt = Receipt(receipt_id=receipt_id, request_id=request.request_id, config_id=self.arm.config_id,
                          contract_revision=CONTRACT_REVISION, memory_release_id=MEMORY_RELEASE,
                          complete=True, timings_ms={f"fail_closed_{cause}": 0})
        response = EvidenceResponse(
            request_id=request.request_id, receipt_id=receipt_id, memory_release_id=MEMORY_RELEASE,
            effective_scope_ref="scope-unavailable", replay_level="none",
            evidence_status=EvidenceStatus.unknown,
            budget=Budget(requested=request.budget_tokens, used=0, tokenizer_id=self.arm.tokenizer))
        return response, receipt


__all__ = ["Retriever", "RegistryUnavailable"]
