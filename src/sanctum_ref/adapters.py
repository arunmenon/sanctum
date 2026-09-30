"""Per-hub adapters (HLD §12.3): build search and fetch arguments from a hub's manifest, and turn
a fetched artifact into an `EvidenceUnit` whose span, artifact id and version come from the hub.

The evidence span is the whole fetched text (offsets 0..len(text)), so a unit covers any span of
that artifact version. Hub text is data: nothing here interprets it."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol

from sanctum_contracts import Applicability, ApplicabilityStatus, EvidenceUnit, Span

from .registry import HubManifest
from .text import search_query, token_count

SEARCH_TOP_K = 10


class HubPort(Protocol):
    """The SUT's only route to hubs (the runner's gateway proxy, or a test double of it)."""

    async def call(self, hub_id: str, tool: str, arguments: dict[str, Any]) -> dict[str, Any]: ...

    reader: Optional[str]          # opaque per-caller id, set by caller_groups (None if unknown)

    async def caller_groups(self) -> Optional[list[str]]: ...

    async def capabilities(self) -> Optional[dict[str, Any]]: ...

    async def change_events(self, after_seq: int) -> list[dict[str, Any]]: ...


def search_arguments(manifest: HubManifest, query: str, selectors: dict[str, str],
                     version_ref: Optional[str]) -> dict[str, Any]:
    arguments: dict[str, Any] = {"query": search_query(query), "top_k": SEARCH_TOP_K}
    place_filter = manifest.search.place_filter
    if place_filter and place_filter in selectors:
        arguments[place_filter] = selectors[place_filter]
    if version_ref and manifest.search.version_filter:
        arguments[manifest.search.version_filter] = version_ref
    return arguments


def fetch_arguments(manifest: HubManifest, hit: dict[str, Any], version_ref: Optional[str]) -> Optional[dict[str, Any]]:
    identifier = hit.get(manifest.fetch.id_field)
    if not identifier:
        return None
    arguments: dict[str, Any] = {manifest.fetch.id_argument: identifier}
    if version_ref and manifest.fetch.version_argument:
        arguments[manifest.fetch.version_argument] = version_ref
    return arguments


@dataclass
class Candidate:
    """A fetched artifact before assembly."""
    source_id: str
    hub_rank: int
    manifest: HubManifest
    artifact: dict[str, Any]
    unit: EvidenceUnit
    interpretations: set[int] = field(default_factory=set)   # which interpretations' plans found it

    @property
    def text(self) -> str:
        return self.unit.text


def artifact_version(artifact: dict[str, Any]) -> Optional[str]:
    """The hub's version as a string, or None when the hub returned none (no version read);
    never the string "None"."""
    version = artifact.get("version")
    return None if version is None else str(version)


def native_ref(artifact: dict[str, Any]) -> str:
    place = artifact.get("path") or artifact.get("location") or artifact.get("title") or artifact["artifact_id"]
    version = artifact_version(artifact)
    return place if version is None else f"{place}@{version}"


def applicability(manifest: HubManifest, artifact: dict[str, Any]) -> Applicability:
    environment = artifact.get("environment")
    branch = manifest.versions.branch_by_environment.get(environment or "")
    if manifest.versions.semantics == "release" and environment and branch:
        return Applicability(branch=branch, environment=environment, effective_from=artifact.get("version"),
                             applicability_status=ApplicabilityStatus.known)
    return Applicability()


def evidence_unit(manifest: HubManifest, artifact: dict[str, Any], evidence_id: str,
                  retrieved_at: str, tokenizer_id: str, fact_kinds: frozenset[str]) -> EvidenceUnit:
    text = artifact.get("text") or ""
    authority = next((f"{manifest.hub_id}:authority:{kind}" for kind in sorted(fact_kinds)
                      if manifest.authoritative_for(kind)), None)
    return EvidenceUnit(
        evidence_id=evidence_id, source_id=manifest.hub_id, artifact_id=artifact["artifact_id"],
        source_version=artifact_version(artifact), native_ref=native_ref(artifact),
        span=Span(start=0, end=len(text)), content_hash="sha256:" + hashlib.sha256(text.encode()).hexdigest(),
        text=text, kind=manifest.evidence_kind, role=manifest.role,
        applicability=applicability(manifest, artifact), retrieved_at=retrieved_at,
        authority_assertion_ref=authority, exact_token_count=token_count(text, tokenizer_id),
        tokenizer_id=tokenizer_id)
