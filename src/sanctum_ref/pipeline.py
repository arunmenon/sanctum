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
from pathlib import Path
from typing import Any, Optional

import anyio

from sanctum_contracts import (
    CONTRACT_REVISION, Budget, EvidenceResponse, EvidenceStatus, Interpretation, Receipt,
    RetrieveRequest, SourceOutcome,
)
from sanctum_contracts.receipt import QueryPlan, SelfReportedCall

from .adapters import Candidate, HubPort, evidence_unit, fetch_arguments, search_arguments
from .assembly import finish, prepare
from .config import ArmConfig
from .intent import analyze
from .registry import Registry, RegistryUnavailable
from .providers import d2_request, unavailable
from .providers.http_systemone import decide_items
from .memory import LabelTable, MemoryUnavailable, build_store, load_release
from .resolution import resolve, resolve_label_only
from .routing import SourcePlan, apply_memory, plan_sources
from .text import stem, words

FETCH_PER_SOURCE = 5
UNCOVERED_SHARE = 0.25
MEMORY_RELEASE = "none"                      # no memory store in C1/C2
INVALIDATING_CHANGES = {"place_unshared", "path_renamed"}
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


def _invalidations(events: list[dict[str, Any]]) -> frozenset[str]:
    return frozenset(str(event.get("subject")) for event in events if event.get("kind") in INVALIDATING_CHANGES)


class MemoryState:
    """Process-lifetime memory state: pinned release cache and the change-feed cursor.

    Invalidations are consumed from the proxy's per-reader change feed before each request:
    an unshared or renamed place stops being used as a selector (HLD §9.5 "stale": uncertain,
    no exclusive filter) until a new release re-binds it."""

    def __init__(self, seed_dir: Optional[Path], release_id: Optional[str] = None):
        self.seed_dir = seed_dir
        self.release_id = release_id           # explicit release for this process; else ACTIVE
        # change-feed sequence numbers are per reader, so cursors and invalidations are too
        self._readers: dict[str, tuple[int, frozenset[str]]] = {}
        self._locks: dict[str, anyio.Lock] = {}
        self._stores: dict[tuple[str, str], Any] = {}

    def pin(self, backend: str):
        """(release, store) for the release active now; raises MemoryUnavailable."""
        if self.seed_dir is None:
            raise MemoryUnavailable("no memory seed configured")
        release = load_release(self.seed_dir, self.release_id)
        key = (release.release_id, backend)
        if key not in self._stores:
            self._stores[key] = (release, build_store(release, backend))
        return self._stores[key]

    async def consume_changes(self, port: HubPort, reader: Optional[str]) -> frozenset[str]:
        """This reader's invalidated places after reading its feed past its own cursor. A caller
        with no reader id reads its whole feed every time and shares nothing."""
        if reader is None:
            return _invalidations(await port.change_events(0) or [])
        lock = self._locks.setdefault(reader, anyio.Lock())
        async with lock:
            cursor, invalidated = self._readers.get(reader, (0, frozenset()))
            events = await port.change_events(cursor) or []
            cursor = max([cursor, *(int(event.get("reader_seq", 0)) for event in events)])
            invalidated = invalidated | _invalidations(events)
            self._readers[reader] = (cursor, invalidated)
            return invalidated


class Retriever:
    def __init__(self, arm: ArmConfig, registry: Optional[Registry],
                 registry_error: Optional[str] = None, memory: Optional[MemoryState] = None,
                 provider=None, round3: str = "none", round3_provider=None):
        self.arm = arm
        self.provider = provider
        self.round3 = round3                      # none | d6 | d4 (design page §14)
        self.round3_provider = round3_provider
        self.registry = registry
        self.registry_error = registry_error
        self.memory = memory

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

        # memory: pin one release for the whole request (HLD §9.6); failure degrades, never widens
        release_id, degraded, resolution, activations, memory_reasons = MEMORY_RELEASE, [], None, [], []
        pinned_at_ms = None
        if self.arm.uses_memory:
            try:
                invalidated = await self.memory.consume_changes(port, getattr(port, "reader", None))
                release, store = self.memory.pin(self.arm.memory_store)
                release_id = release.release_id
                pinned_at_ms = int((time.monotonic() - clock.started) * 1000)
                if self.arm.resolution == "label_only":
                    resolution = resolve_label_only(request, LabelTable(release), store, releases)
                else:
                    resolution = resolve(request, store, self.registry, set(groups), releases)
                plans, activations, memory_reasons = apply_memory(
                    plans, resolution, store, self.registry, intent, set(groups),
                    set(invalidated), request.query, self.arm)
            except MemoryUnavailable:
                degraded = ["memory_unavailable"]
                resolution = None

        decisions = []
        if self.arm.decision_provider == "named":
            decisions, decision_degraded = await self._judge_usefulness(request, plans, port)
            degraded += decision_degraded
        deadline = time.monotonic() + min(request.deadline_ms, self.arm.deadline_ms) / 1000.0
        outcomes: dict[str, str] = {}
        self._fetch_gaps: set[str] = set()
        candidates = await self._ask(request, plans, port, clock, deadline, intent.fact_kinds, outcomes,
                                     capabilities)
        prepared = prepare(candidates, intent.terms, intent.fact_kinds, common=self.arm.common_assembly,
                           dedup_exact=self.arm.exact_dedup,
                           domain_terms={stem(term) for terms in self.registry.domains.values() for term in terms})
        promoted: list = []
        if self.round3 == "d6" and self.round3_provider is not None and (prepared.flagged or prepared.pair_candidates):
            promoted, round3_decisions, round3_failed = await self._judge_conflicts(request, prepared, port)
            decisions = decisions + round3_decisions
            if round3_failed:
                degraded = sorted(set(degraded) | {"decision_layer_unavailable"})
        assembled = finish(prepared, request.budget_tokens, self.arm.tokenizer, promoted)
        sources, response_reasons, required_gap = self._sources(plans, outcomes,
                                                                intent.detected_fact_kinds or intent.fact_kinds,
                                                                self._fetch_gaps)
        response_reasons += memory_reasons
        resolved = resolution is not None and bool(resolution.interpretations)
        status = self._status(assembled, intent.vague, required_gap, lexical_coverage=not resolved)
        if resolved and status != EvidenceStatus.insufficient:
            # the entity is covered, but is what was asked about it covered? (HLD §10 Ex8) Only
            # when nothing returned mentions any of the non-name subject words is it not.
            name_terms = {stem(word) for i in resolution.interpretations for word in words(i.term)}
            asked = [term for term in intent.terms if term not in name_terms]
            if asked and set(asked) <= set(assembled.uncovered_terms):
                status = EvidenceStatus.insufficient
        interpretations = []
        if resolution is not None:
            interpretations, status = self._interpretations(resolution, candidates, assembled, status,
                                                            required_gap, response_reasons, request)
        if any(source.status.value in ("timeout", "error") for source in sources):
            # a source routing chose to ask failed: what it would have added is unknown, so no
            # answer (or interpretation) can be called complete (Ex. 9; dev-018, dev-052)
            if status == EvidenceStatus.sufficient:
                status = EvidenceStatus.partial
            interpretations = [i.model_copy(update={"evidence_status": EvidenceStatus.partial})
                               if i.evidence_status == EvidenceStatus.sufficient else i for i in interpretations]
        if assembled.truncated_relevant:
            response_reasons.append("insufficient_budget")
        if status == EvidenceStatus.insufficient and not required_gap:
            response_reasons.append("no_coverage")
        receipt = Receipt(
            receipt_id=receipt_id, request_id=request.request_id, config_id=self.arm.config_id,
            contract_revision=CONTRACT_REVISION, memory_release_id=release_id,
            resolutions=resolution.records if resolution else [], activations=activations, decisions=decisions,
            query_plans=[QueryPlan(source_id=plan.hub_id, original_query=request.query,
                                   selectors=[f"{key}={value}" for key, value in sorted(plan.selectors.items())],
                                   aliases=list(plan.aliases), as_of=plan.as_of)
                         for plan in plans if plan.call],
            calls=clock.calls, complete=True,
            timings_ms={"total": int((time.monotonic() - clock.started) * 1000),
                        # when the release was pinned (FX-23): everything after used this release
                        **({"memory_pinned": pinned_at_ms} if pinned_at_ms is not None else {})})
        response = EvidenceResponse(
            request_id=request.request_id, receipt_id=receipt_id, memory_release_id=release_id,
            effective_scope_ref=self._scope_ref(request, groups),
            policy_versions={"registry": self.registry.version, "config": self.arm.config_id},
            replay_level="recompute_on_candidates", interpretations=interpretations,
            evidence=assembled.evidence,
            conflicts=assembled.conflicts, sources=sources, evidence_status=status,
            reasons=sorted(set(response_reasons)), omitted=assembled.omitted,
            budget=Budget(requested=request.budget_tokens, used=assembled.used_tokens,
                          tokenizer_id=self.arm.tokenizer),
            truncation=assembled.truncated_relevant, degraded_reasons=degraded)
        return response, receipt

    async def _judge_conflicts(self, request: RetrieveRequest, prepared, port: HubPort):
        """D6 (design page §14): judge rule-produced pairs only. Flagged pairs stay flagged whatever
        the answer; a candidate pair is promoted only when its calibrated p reaches the use band."""
        def ref(item) -> dict:
            unit = item.unit
            return {"source_id": unit.source_id, "artifact_id": unit.artifact_id, "version": unit.source_version,
                    "start": unit.span.start, "end": unit.span.end}
        pairs = list(prepared.flagged) + list(prepared.pair_candidates)
        items = {f"d6:{a.unit.evidence_id}|{b.unit.evidence_id}": [ref(a), ref(b)] for a, b, _ in pairs}
        try:
            judgements, results, calibration = await decide_items(
                self.round3_provider, "d6", items, request.query, port, self.arm.deadline_ms)
        except Exception:                     # a provider failure is never a conflict decision
            return [], [unavailable(self.round3_provider.name, time.monotonic())], True
        promoted = []
        for a, b, relation in prepared.pair_candidates:
            judgement = judgements.get(f"d6:{a.unit.evidence_id}|{b.unit.evidence_id}")
            if calibration is not None and judgement and judgement.p is not None and judgement.p >= calibration.use:
                promoted.append((a, b, relation))
        failed = all(r.status.value != "answered" for r in results)
        return promoted, results, failed

    async def _judge_usefulness(self, request: RetrieveRequest, plans: list[SourcePlan], port: HubPort):
        """Round 2, D2 (HLD §6.3): one question per optional called source. A confident "not
        useful" skips it; uncertain keeps it; an unavailable layer keeps everything."""
        optional = sorted({plan.hub_id for plan in plans if plan.call and not plan.required}
                          - {plan.hub_id for plan in plans if plan.required})
        if self.provider is None:
            return [], ["decision_layer_unavailable"]
        requests = [d2_request(hub_id, request.query, self.arm.deadline_ms) for hub_id in optional]
        try:
            answered = await self.provider.decide_batch(requests, port, self.arm.deadline_ms) if requests else []
        except Exception:                      # a provider failure is never a routing decision
            answered = [unavailable(self.provider.name, time.monotonic()) for _ in requests]
        results = dict(zip(optional, answered))
        if any(result.status.value != "answered" for result in results.values()):
            return list(results.values()), ["decision_layer_unavailable"]
        skip = {hub_id for hub_id, result in results.items() if not result.value["call"]}
        if skip and not [p for p in plans if p.call and p.hub_id not in skip]:
            # never leave the request with no source: keep the two most likely (HLD §10 Ex8)
            keep = sorted(skip, key=lambda hub_id: -results[hub_id].value["p"])[:2]
            skip -= set(keep)
        for plan in plans:
            if plan.hub_id in skip:
                plan.call, plan.status, plan.reasons = False, "skipped", ["not_selected"]
        return list(results.values()), []

    def _interpretations(self, resolution, candidates, assembled, status, required_gap,
                         reasons: list[str], request: RetrieveRequest):
        """One interpretation per resolved meaning, each with only the evidence its own plans
        found (no blending), its own conflicts and status (HLD §9.2)."""
        if resolution.unresolved and not resolution.interpretations:
            reasons.append("unresolved_term")
            if status == EvidenceStatus.sufficient:
                status = EvidenceStatus.partial
        if resolution.ambiguous:
            reasons.append("ambiguous_term")
            if request.caller_profile.value == "interactive":
                reasons.append("clarification_requested")
        found_by = {candidate.unit.content_hash: set() for candidate in candidates}
        for candidate in candidates:
            found_by[candidate.unit.content_hash] |= candidate.interpretations
        out = []
        for index, interpretation in enumerate(resolution.interpretations):
            evidence_ids = [unit.evidence_id for unit in assembled.evidence if index in found_by.get(unit.content_hash, set())]
            conflict_ids = [c.conflict_id for c in assembled.conflicts if c.a in evidence_ids and c.b in evidence_ids]
            relevant = {item for item in assembled.relevant_ids} & set(evidence_ids)
            branch_status = EvidenceStatus.insufficient if not relevant else (
                EvidenceStatus.partial if required_gap else EvidenceStatus.sufficient)
            out.append(Interpretation(interpretation_id=f"in-{index + 1}", entity_ref=interpretation.entity_ref,
                                      resolution_origin=interpretation.origin, evidence_ids=evidence_ids,
                                      conflict_ids=conflict_ids, evidence_status=branch_status))
        if resolution.ambiguous and any(i.evidence_status != EvidenceStatus.sufficient for i in out):
            status = EvidenceStatus.partial          # some meaning is not fully answered
        elif resolution.ambiguous and out:
            status = EvidenceStatus.sufficient
        return out, status

    # ---- stage 4 -------------------------------------------------------------------------------
    async def _ask(self, request: RetrieveRequest, plans: list[SourcePlan], port: HubPort, clock: CallLog,
                   deadline: float, fact_kinds: frozenset[str], outcomes: dict[str, str],
                   capabilities: dict[str, Any]) -> list[Candidate]:
        hits: dict[str, list[tuple[Optional[str], dict[str, Any], Optional[int]]]] = {}
        manifests = {plan.hub_id: plan.manifest for plan in plans}

        async def call(hub_id: str, tool: str, arguments: dict[str, Any]) -> Optional[dict[str, Any]]:
            started = time.monotonic()
            payload: Optional[dict[str, Any]] = None
            try:
                with anyio.move_on_after(max(0.0, deadline - time.monotonic())):
                    payload = await port.call(hub_id, tool, arguments)
            finally:
                clock.record(hub_id, tool, _status_of(payload), started)
            return payload

        async def search(plan: SourcePlan, ref: Optional[str]) -> None:
            query = " ".join([request.query, *plan.aliases])      # the original question is always kept
            payload = await call(plan.hub_id, plan.manifest.search.tool,
                                 search_arguments(plan.manifest, query, plan.selectors, ref))
            status = _status_of(payload)
            # a source is "called" only if every search it needed succeeded
            if outcomes.get(plan.hub_id, "ok") == "ok":
                outcomes[plan.hub_id] = status
            if status == "ok":
                results = [hit for hit in payload.get("results") or []
                           if not plan.as_of or _place_has_versions(capabilities.get(plan.hub_id, {}), hit)]
                hits.setdefault(plan.hub_id, []).extend((ref, hit, plan.interpretation) for hit in results[:FETCH_PER_SOURCE])

        async with anyio.create_task_group() as group:
            for plan in plans:
                if plan.call:
                    for ref in plan.version_refs:
                        group.start_soon(search, plan, ref)

        fetched: list[Candidate] = []
        fetch_outcomes: dict[str, list[str]] = {}
        retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        budget = self.arm.candidates
        found_by: dict[tuple[str, str, str], set[int]] = {}

        async def fetch(hub_id: str, rank: int, ref: Optional[str], hit: dict[str, Any], key) -> None:
            manifest = manifests[hub_id]
            arguments = fetch_arguments(manifest, hit, ref)
            if arguments is None:
                return
            payload = await call(hub_id, manifest.fetch.tool, arguments)
            status = _status_of(payload)
            if status == "ok" and "artifact" not in payload:
                status = "error"
            fetch_outcomes.setdefault(hub_id, []).append(status)
            if status != "ok":
                return
            artifact = payload["artifact"]
            fetched.append(Candidate(hub_id, rank, manifest, artifact,
                                     evidence_unit(manifest, artifact, "", retrieved_at, self.arm.tokenizer, fact_kinds),
                                     found_by[key]))

        async with anyio.create_task_group() as group:
            for hub_id in sorted(hits):
                for rank, (ref, hit, interpretation) in enumerate(hits[hub_id]):
                    key = (hub_id, str(hit.get("artifact_id")), str(hit.get("version")))
                    if key in found_by:
                        if interpretation is not None:
                            found_by[key].add(interpretation)
                        continue
                    if budget <= 0:
                        continue
                    found_by[key] = {interpretation} if interpretation is not None else set()
                    budget -= 1
                    group.start_soon(fetch, hub_id, rank, ref, hit, key)
        # A search that found hits whose evidence could not be read is not a successful retrieval:
        # every fetch failed -> the source reports that failure; some failed -> `fetch_gaps`.
        for hub_id, statuses in fetch_outcomes.items():
            failed = [status for status in statuses if status != "ok"]
            if failed and len(failed) == len(statuses) and outcomes.get(hub_id) == "ok":
                outcomes[hub_id] = "timeout" if "timeout" in failed else "error"
            elif failed:
                self._fetch_gaps.add(hub_id)
        # deterministic evidence ids: hub order, then hub rank
        fetched.sort(key=lambda candidate: (candidate.source_id, candidate.hub_rank, candidate.unit.artifact_id))
        for index, candidate in enumerate(fetched):
            candidate.unit = candidate.unit.model_copy(update={"evidence_id": f"ev-{index + 1}"})
        return fetched

    # ---- stage 6 helpers ---------------------------------------------------------------------------
    @staticmethod
    def _sources(plans: list[SourcePlan], outcomes: dict[str, str],
                 needed_kinds: frozenset[str] = frozenset(),
                 fetch_gaps: set[str] = frozenset()) -> tuple[list[SourceOutcome], list[str], bool]:
        """One outcome per source; per-interpretation plans for the same source are merged.

        A called source that is authoritative for a kind of fact the question needs is required
        for that fact (HLD §10 Ex9d): if it times out or errors, that is a visible gap
        (`required_source_unavailable`), never a `sufficient` answer from other sources."""
        merged: dict[str, SourcePlan] = {}
        for plan in plans:
            current = merged.get(plan.hub_id)
            if current is None:
                merged[plan.hub_id] = SourcePlan(plan.hub_id, plan.manifest, plan.call, plan.status,
                                                 list(plan.reasons), plan.required)
                continue
            current.required = current.required or plan.required
            if plan.call and not current.call:
                current.call, current.status, current.reasons = True, plan.status, list(plan.reasons)
            elif plan.call == current.call:
                current.reasons = sorted(set(current.reasons) | set(plan.reasons))
        sources, reasons, required_gap = [], [], False
        for plan in (merged[hub_id] for hub_id in sorted(merged)):
            status, source_reasons = plan.status, list(plan.reasons)
            if plan.call:
                outcome = outcomes.get(plan.hub_id, "timeout")
                status = {"ok": "called", "timeout": "timeout"}.get(outcome, "error")
            authoritative = plan.manifest is not None and any(
                plan.manifest.authoritative_for(kind) for kind in needed_kinds)
            gap = None
            if plan.call and authoritative and (status in ("timeout", "error") or plan.hub_id in fetch_gaps):
                gap = "required_source_unavailable"
                source_reasons.append(gap)
            elif plan.required and "required_source_denied" in source_reasons:
                gap = "required_source_denied"
            elif plan.required and (status in ("timeout", "error", "unsupported_for_mode") or plan.hub_id in fetch_gaps):
                gap = "required_source_unavailable"
                source_reasons.append(gap)
            if gap:
                required_gap = True
                reasons.append(gap)
            sources.append(SourceOutcome(source_id=plan.hub_id, status=status, reasons=sorted(set(source_reasons))))
        return sources, reasons, required_gap

    @staticmethod
    def _status(assembled, vague: bool, required_gap: bool, lexical_coverage: bool = True) -> EvidenceStatus:
        # a large share of the subject that no source returned anything about (the asked-for
        # attribute of a service nobody documents, HLD §10 Ex8): the question is not covered.
        # With a resolved entity the pool is narrowed to its places, where this lexical signal
        # misfires, so it applies only to unresolved questions.
        uncovered = lexical_coverage and assembled.uncovered_share >= UNCOVERED_SHARE
        if not assembled.relevant_packed or uncovered:
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
