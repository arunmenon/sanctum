"""Sanctum memory v0 (HLD §8.5-§8.7, §9.6): releases, and two storage backends with one meaning.

- `load_release` reads `owners/memory_seed/<release>/release.yaml` (the release named by `ACTIVE`
  when none is given) and validates it. Only `accepted` assertions are usable (§8.7); anything
  else is loaded and kept out of every operational use. `RELATES_TO` is stored and disabled.
- `RelationStore` (C4, `memory_store: relations`) keeps typed edges and answers by traversal.
- `TableStore` (C4a, `memory_store: tables`) keeps flat per-relation tables; same queries,
  same answers (checked by the Q3b test).
- `LabelTable` (C4a-label-only resolution) is one flat label -> entity map: no namespaces, no
  ambiguity handling, and places count as names.

No inference: nothing computes closure over identity; two DENOTES edges never imply a third.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Protocol

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .text import words

ACCEPTED = "accepted"


class MemoryUnavailable(RuntimeError):
    pass


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class EntityRecord(_Model):
    id: str
    ref: str
    type: str
    label: str
    member_of: list[str] = Field(default_factory=list)
    descriptor: Optional[str] = None


class TermRecord(_Model):
    source: str
    namespace: str
    native_id: str
    label: str
    kind: str
    denotes: str
    status: str
    version: int
    reviewed_by: str


class PlaceRecord(_Model):
    source: str
    filter: str
    value: str
    place: str
    selects_for: str
    status: str
    version: int
    reviewed_by: str


class ContextRecord(_Model):
    scope: str
    selects_for: str
    status: str
    version: int
    reviewed_by: str


class MemoryTrigger(_Model):
    entity_member_of: str
    fact_kind_needed: str


class MemoryAction(_Model):
    must_consult: str
    selector: dict[str, str] = Field(default_factory=dict)


class MemoryProcedure(_Model):
    procedure_id: str
    version: int
    status: str
    owner: str
    attested_by: str
    trigger: MemoryTrigger
    action: MemoryAction


class RelationRecord(_Model):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)
    from_: str = Field(alias="from")
    type: str
    qualifier: Optional[str] = None
    to: str
    status: str


class Release(_Model):
    release_id: str
    schema_version: int
    status: str
    note: Optional[str] = None
    entities: list[EntityRecord]
    terms: list[TermRecord]
    places: list[PlaceRecord]
    contexts: list[ContextRecord] = Field(default_factory=list)
    procedures: list[MemoryProcedure] = Field(default_factory=list)
    relations: list[RelationRecord] = Field(default_factory=list)
    descriptors: dict[str, dict[str, str]] = Field(default_factory=dict)


def normalize_label(label: str) -> tuple[str, ...]:
    return tuple(words(label))


def load_release(seed_dir: Path, release_id: Optional[str] = None) -> Release:
    seed_dir = Path(seed_dir)
    try:
        release_id = release_id or (seed_dir / "ACTIVE").read_text(encoding="utf-8").strip()
        data: Any = yaml.safe_load((seed_dir / release_id / "release.yaml").read_text(encoding="utf-8"))
        release = Release.model_validate(data)
    except (OSError, yaml.YAMLError, ValidationError) as error:
        raise MemoryUnavailable(f"memory release unreadable: {type(error).__name__}") from None
    if release.release_id != release_id:
        raise MemoryUnavailable("release id does not match its directory")
    ids = {entity.id for entity in release.entities}
    dangling = [t.denotes for t in release.terms if t.denotes not in ids] + \
               [p.selects_for for p in release.places if p.selects_for not in ids] + \
               [m for e in release.entities for m in e.member_of if m not in ids] + \
               [c.selects_for for c in release.contexts if c.selects_for not in ids]
    if dangling:
        raise MemoryUnavailable("release references unknown entities")
    return release


@dataclass(frozen=True)
class Denotation:
    """One accepted DENOTES candidate for a label."""
    entity_id: str
    source: str
    namespace: str
    label: str
    assertion_ref: str


class MemoryStore(Protocol):
    release_id: str

    def entity(self, entity_id: str) -> Optional[EntityRecord]: ...
    def labels(self) -> list[tuple[str, ...]]: ...
    def denotes(self, label: tuple[str, ...]) -> list[Denotation]: ...
    def places_for(self, entity_id: str) -> list[PlaceRecord]: ...
    def member_of(self, entity_id: str) -> list[str]: ...
    def procedures(self) -> list[MemoryProcedure]: ...
    def preferred_label(self, entity_id: str, source: str) -> Optional[str]: ...
    def context_entity(self, scope: str) -> Optional[tuple[str, str]]: ...


def _term_ref(term: TermRecord, release_id: str) -> str:
    """Assertion refs carry the release they were read from, so a receipt shows no mixing."""
    return f"DENOTES:{term.source}:{term.namespace}:{term.native_id}@v{term.version}@{release_id}"


class RelationStore:
    """Typed edges keyed by subject (C4)."""

    def __init__(self, release: Release):
        self.release_id = release.release_id
        self._entities = {entity.id: entity for entity in release.entities}
        self._edges: dict[tuple[str, str], list[tuple[str, Any]]] = {}
        for term in release.terms:
            if term.status == ACCEPTED and term.kind == "name":
                self._edge(("label", "DENOTES"), normalize_label(term.label), term)
        for place in release.places:
            if place.status == ACCEPTED:
                self._edge((place.selects_for, "SELECTS_FOR"), None, place)
        for entity in release.entities:
            for parent in entity.member_of:
                self._edge((entity.id, "MEMBER_OF"), None, parent)
        self._procedures = [procedure for procedure in release.procedures if procedure.status == ACCEPTED]
        for context in release.contexts:
            if context.status == ACCEPTED:
                self._edge(("scope", "SELECTS_FOR"), context.scope, context)
        # RELATES_TO is stored for review and never read by any operational path (HLD §8.7)
        self._disabled = list(release.relations)

    def _edge(self, key, qualifier, value) -> None:
        self._edges.setdefault(key, []).append((qualifier, value))

    def entity(self, entity_id):
        return self._entities.get(entity_id)

    def labels(self):
        return sorted({qualifier for qualifier, _ in self._edges.get(("label", "DENOTES"), [])})

    def denotes(self, label):
        return [Denotation(term.denotes, term.source, term.namespace, term.label, _term_ref(term, self.release_id))
                for qualifier, term in self._edges.get(("label", "DENOTES"), []) if qualifier == label]

    def places_for(self, entity_id):
        return [place for _, place in self._edges.get((entity_id, "SELECTS_FOR"), [])]

    def member_of(self, entity_id):
        return [parent for _, parent in self._edges.get((entity_id, "MEMBER_OF"), [])]

    def procedures(self):
        return list(self._procedures)

    def preferred_label(self, entity_id, source):
        return next((term.label for _, term in self._edges.get(("label", "DENOTES"), [])
                     if term.denotes == entity_id and term.source == source), None)

    def context_entity(self, scope):
        return next(((c.selects_for, f"CONTEXT:{c.scope}@v{c.version}@{self.release_id}")
                     for qualifier, c in self._edges.get(("scope", "SELECTS_FOR"), []) if qualifier == scope), None)


class TableStore:
    """Flat tables, one per relation (C4a-equivalent storage)."""

    def __init__(self, release: Release):
        self.release_id = release.release_id
        self._entity_table = {entity.id: entity for entity in release.entities}
        self._name_table = [(normalize_label(t.label), t) for t in release.terms if t.status == ACCEPTED and t.kind == "name"]
        self._place_table = [p for p in release.places if p.status == ACCEPTED]
        self._membership_table = [(entity.id, parent) for entity in release.entities for parent in entity.member_of]
        self._procedure_table = [p for p in release.procedures if p.status == ACCEPTED]
        self._context_table = [c for c in release.contexts if c.status == ACCEPTED]

    def entity(self, entity_id):
        return self._entity_table.get(entity_id)

    def labels(self):
        return sorted({label for label, _ in self._name_table})

    def denotes(self, label):
        return [Denotation(t.denotes, t.source, t.namespace, t.label, _term_ref(t, self.release_id)) for key, t in self._name_table if key == label]

    def places_for(self, entity_id):
        return [place for place in self._place_table if place.selects_for == entity_id]

    def member_of(self, entity_id):
        return [parent for child, parent in self._membership_table if child == entity_id]

    def procedures(self):
        return list(self._procedure_table)

    def preferred_label(self, entity_id, source):
        return next((t.label for _, t in self._name_table if t.denotes == entity_id and t.source == source), None)

    def context_entity(self, scope):
        return next(((c.selects_for, f"CONTEXT:{c.scope}@v{c.version}@{self.release_id}") for c in self._context_table if c.scope == scope), None)


class LabelTable:
    """C4a-label-only: label -> one entity, first assertion wins. No namespaces, no ambiguity,
    and places are treated as names (no SELECTS_FOR distinction)."""

    def __init__(self, release: Release):
        self.table: dict[tuple[str, ...], tuple[str, str]] = {}
        for term in release.terms:
            if term.status == ACCEPTED:
                self.table.setdefault(normalize_label(term.label), (term.denotes, f"alias:{term.label}"))
        for place in release.places:
            if place.status == ACCEPTED:
                self.table.setdefault(normalize_label(place.value.split("/")[-1]), (place.selects_for, f"alias:{place.value}"))


def build_store(release: Release, backend: str) -> MemoryStore:
    if backend == "relations":
        return RelationStore(release)
    if backend == "tables":
        return TableStore(release)
    raise MemoryUnavailable(f"unknown memory_store {backend!r}")
