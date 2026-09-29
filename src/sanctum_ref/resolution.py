"""Name resolution (HLD §9.2) and per-source query plans (§9.3) for C4 and the C4a controls.

Resolution (`resolution: denotes`):
- Label lookup over accepted DENOTES names found in the query (longest match), restricted to
  entities the caller can see; an entity the caller cannot see is never named.
- Several candidates: request context (scope words, or a domain named in the query) may pick
  one namespace; otherwise the request is ambiguous and, for agents, every visible meaning
  becomes its own interpretation. Nothing is chosen by score, nothing is unioned.
- No candidate: bounded fallback on the original text; a name-like token that matched nothing
  is reported as `unresolved_term`.

`resolution: label_only` (C4a-label-only): one flat label -> entity table, first match wins, no
namespaces, no ambiguity handling, places count as names. Origin `alias_table`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from sanctum_contracts import RetrieveRequest
from sanctum_contracts.receipt import Activation, TermResolution

from .memory import LabelTable, MemoryStore, PlaceRecord, normalize_label
from .registry import Registry
from .text import words

# Hub-native names look like `PA-svc` or `fx-quote`: a hyphenated token that matched no label.
NAME_LIKE = re.compile(r"\b[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+\b")
MAX_LABEL_WORDS = 4
MAX_ALIASES = 2


@dataclass
class Interpretation:
    entity_id: str
    entity_ref: str
    origin: str                                  # denotes | request_context | alias_table
    term: str
    assertion_refs: list[str] = field(default_factory=list)


@dataclass
class Resolution:
    interpretations: list[Interpretation] = field(default_factory=list)
    ambiguous: bool = False
    unresolved: list[str] = field(default_factory=list)
    records: list[TermResolution] = field(default_factory=list)


def _spans(query_words: list[str], labels: set[tuple[str, ...]]) -> list[tuple[int, int, tuple[str, ...]]]:
    """Longest non-overlapping label matches, left to right."""
    found, index = [], 0
    while index < len(query_words):
        for size in range(min(MAX_LABEL_WORDS, len(query_words) - index), 0, -1):
            candidate = tuple(query_words[index:index + size])
            if candidate in labels:
                found.append((index, index + size, candidate))
                index += size
                break
        else:
            index += 1
    return found


def entity_visible(store: MemoryStore, registry: Registry, entity_id: str, groups: set[str]) -> bool:
    """Visible when the caller can read one of the entity's places in a hub whose places are
    access-scoped (a hub-wide place such as every doc space proves nothing)."""
    for place in store.places_for(entity_id):
        manifest = registry.manifest(place.source)
        if manifest is None:
            continue
        declared = next((p for p in manifest.places if place.place.startswith(p.prefix)), None)
        if declared is not None and declared.domain != "any" and groups & set(declared.groups):
            return True
    return False


def _context_domains(request: RetrieveRequest, store: MemoryStore, entity_ids: list[str]) -> set[str]:
    """The candidates' domains that trusted request context (scope) or the query text names."""
    context_words = set(words(request.scope or "")) | set(words(request.query))
    domains = {domain for entity_id in entity_ids for domain in store.member_of(entity_id)}
    return {domain for domain in domains
            if (entity := store.entity(domain)) is not None and entity.label in context_words}


def _unresolved(query: str, matched: list[tuple[int, int, tuple[str, ...]]], releases: set[str]) -> list[str]:
    matched_words = {word for _, _, label in matched for word in label}
    out = []
    for token in NAME_LIKE.findall(query):
        token_words = set(words(token))
        if token.lower() in releases or token_words <= matched_words:
            continue
        out.append(token)
    return out


def resolve(request: RetrieveRequest, store: MemoryStore, registry: Registry, groups: set[str],
            releases: set[str]) -> Resolution:
    query_words = words(request.query)
    matches = _spans(query_words, set(store.labels()))
    resolution = Resolution(unresolved=_unresolved(request.query, matches, {r.lower() for r in releases}))
    chosen: dict[str, Interpretation] = {}
    for _, _, label in matches:
        denotations = [d for d in store.denotes(label) if entity_visible(store, registry, d.entity_id, groups)]
        entity_ids = sorted({d.entity_id for d in denotations})
        term = " ".join(label)
        origin, picked = "denotes", entity_ids
        if len(entity_ids) > 1:
            context = _context_domains(request, store, entity_ids)
            narrowed = [e for e in entity_ids if set(store.member_of(e)) & context]
            if len(narrowed) == 1:
                origin, picked = "request_context", narrowed
            else:
                resolution.ambiguous = True
        refs = [store.entity(e).ref for e in entity_ids]
        resolution.records.append(TermResolution(
            term=term, candidates=refs, chosen=[store.entity(e).ref for e in picked],
            origin=origin if picked else "none",
            assertion_refs=sorted({d.assertion_ref for d in denotations if d.entity_id in picked})))
        for entity_id in picked:
            if entity_id not in chosen:
                chosen[entity_id] = Interpretation(entity_id, store.entity(entity_id).ref, origin, term,
                                                   sorted({d.assertion_ref for d in denotations if d.entity_id == entity_id}))
    resolution.interpretations = list(chosen.values())
    if not resolution.interpretations and request.scope:
        # no name resolved: reviewed request context may supply the entity (HLD §9.3, Fx19)
        bound = store.context_entity(request.scope)
        if bound and entity_visible(store, registry, bound[0], groups):
            entity = store.entity(bound[0])
            resolution.interpretations = [Interpretation(entity.id, entity.ref, "request_context", "", [bound[1]])]
            resolution.records.append(TermResolution(term=request.scope, candidates=[entity.ref], chosen=[entity.ref],
                                                     origin="request_context", assertion_refs=[bound[1]]))
    return resolution


def resolve_label_only(request: RetrieveRequest, table: LabelTable, store: MemoryStore,
                       releases: set[str]) -> Resolution:
    query_words = words(request.query)
    matches = _spans(query_words, set(table.table))
    resolution = Resolution(unresolved=_unresolved(request.query, matches, {r.lower() for r in releases}))
    if matches:
        _, _, label = matches[0]
        entity_id, assertion = table.table[label]
        entity = store.entity(entity_id)
        resolution.interpretations = [Interpretation(entity_id, entity.ref, "alias_table", " ".join(label), [assertion])]
        resolution.records.append(TermResolution(term=" ".join(label), candidates=[entity.ref], chosen=[entity.ref],
                                                 origin="alias_table", assertion_refs=[assertion]))
    return resolution


@dataclass
class EntityPlan:
    """What memory contributes to one source's plan for one interpretation."""
    selectors: dict[str, str] = field(default_factory=dict)
    aliases: list[str] = field(default_factory=list)
    selector_refs: list[str] = field(default_factory=list)
    procedure_conflict: bool = False


def compatible(first: str, second: str) -> Optional[str]:
    """AND of two prefix filters: the narrower one, or None when they cannot both hold."""
    if first.startswith(second):
        return first
    if second.startswith(first):
        return second
    return None


def entity_plan(store: MemoryStore, registry: Registry, entity_id: str, hub_id: str, groups: set[str],
                invalidated_places: set[str], request_query: str) -> EntityPlan:
    plan = EntityPlan()
    manifest = registry.manifest(hub_id)
    if manifest is None:
        return plan
    for place in store.places_for(entity_id):
        if place.source != hub_id or place.filter != manifest.search.place_filter:
            continue
        if place.place in invalidated_places or f"{place.filter}:{place.value}" in invalidated_places:
            continue                         # unshared or renamed since: uncertain, no exclusive filter
        if manifest.place_accessible(place.place, groups) is False:
            continue
        plan.selectors[place.filter] = place.value
        plan.selector_refs.append(f"SELECTS_FOR:{place.source}:{place.value}@v{place.version}@{store.release_id}")
        break
    query_words = set(words(request_query))
    for source in (hub_id, "catalog", "skillhub"):
        label = store.preferred_label(entity_id, source)
        if label and not set(words(label)) <= query_words and label not in plan.aliases:
            plan.aliases.append(label)
        if len(plan.aliases) >= MAX_ALIASES:
            break
    return plan


def procedure_activations(store: MemoryStore, entity_id: str, entity_ref: str,
                          fact_kinds: frozenset[str]) -> list[tuple[object, Activation]]:
    """Accepted procedures whose trigger holds for this entity via explicit MEMBER_OF (§9.4)."""
    domains = set(store.member_of(entity_id))
    out = []
    for procedure in store.procedures():
        if procedure.trigger.entity_member_of in domains and procedure.trigger.fact_kind_needed in fact_kinds:
            out.append((procedure, Activation(kind="procedure", ref=f"{procedure.procedure_id}@v{procedure.version}@{store.release_id}",
                                              entity_ref=entity_ref, source_id=procedure.action.must_consult)))
    return out
