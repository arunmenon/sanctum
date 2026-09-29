"""Round 3 (HLD §7.3-7.5): exact dedup, lexical ranking, typed conflict rules, packing.

- Ranking: one lexical relevance score (BM25-style over the candidate pool), normalized within
  each source so no hub wins by corpus statistics alone. Authority is only a tie-break.
- Dedup: identical text (content hash) keeps one unit; the other copies stay listed under
  `duplicates` and in `omitted`, each with its own provenance. Authority is never transferred.
- Conflicts: same attribute (query terms on a line with a number), different value, in two units
  from different sources or versions. Typed by roles, versions and environments.
- Packing: whole units only; both witnesses of every conflict are reserved first; the rest fill
  in rank order. The budget counts the serialized evidence list with the declared tokenizer.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from typing import Optional

from sanctum_contracts import Conflict, ConflictStatus, EvidenceRole, EvidenceUnit, Omitted, RelationType

from .adapters import Candidate
from .text import STOPWORDS, stem, term_counts, token_count, words

NUMBER = re.compile(r"(?<![A-Za-z0-9.])\d+(?:\.\d+)?(?![A-Za-z0-9])")
RELEVANT_COVERAGE = 0.4
HEADER_LINE = re.compile(r"^\s*(#|//|/\*|\*|---|name:|namespace:)")
MAX_CONFLICT_UNITS = 8
CONFLICT_COVERAGE = 0.3
FRONT_MATTER_NAME = re.compile(r"^name:\s*(.+)$", re.MULTILINE)
PLACE_WORDS = frozenset({"repo", "space", "skill", "queue", "md", "yaml", "java", "src", "main", "com"})
MAX_CONFLICTS = 6
BM25_K1, BM25_B = 1.2, 0.75


@dataclass
class Ranked:
    candidate: Candidate
    score: float = 0.0              # normalized within source, 0..1
    coverage: float = 0.0           # share of query terms present
    duplicates: list[str] = field(default_factory=list)

    @property
    def unit(self) -> EvidenceUnit:
        return self.candidate.unit

    @property
    def relevant(self) -> bool:
        return self.coverage >= RELEVANT_COVERAGE


@dataclass
class Assembled:
    evidence: list[EvidenceUnit]
    conflicts: list[Conflict]
    omitted: list[Omitted]
    used_tokens: int
    truncated_relevant: bool
    relevant_packed: int
    uncovered_terms: list[str] = field(default_factory=list)
    subject_terms: int = 0
    relevant_ids: list[str] = field(default_factory=list)

    @property
    def uncovered_share(self) -> float:
        return len(self.uncovered_terms) / self.subject_terms if self.subject_terms else 0.0


def score(candidates: list[Candidate], terms: tuple[str, ...]) -> list[Ranked]:
    counts = [term_counts(candidate.text) for candidate in candidates]
    lengths = [sum(count.values()) or 1 for count in counts]
    average = (sum(lengths) / len(lengths)) if lengths else 1.0
    pool = len(candidates)
    frequency = {term: sum(1 for count in counts if term in count) for term in terms}
    ranked = []
    for candidate, count, length in zip(candidates, counts, lengths):
        raw = 0.0
        for term in terms:
            tf = count.get(term, 0)
            if not tf:
                continue
            idf = math.log(1 + (pool - frequency[term] + 0.5) / (frequency[term] + 0.5))
            raw += idf * tf * (BM25_K1 + 1) / (tf + BM25_K1 * (1 - BM25_B + BM25_B * length / average))
        # coverage over terms some candidate contains; terms no candidate has are reported
        # separately (`uncovered_terms`) and never make a unit look relevant or irrelevant
        weights = {term: math.log(1 + (pool + 1) / (frequency[term] + 0.5)) for term in terms if frequency[term]}
        total = sum(weights.values())
        coverage = (sum(weight for term, weight in weights.items() if term in count) / total) if total else 0.0
        ranked.append(Ranked(candidate, raw, coverage))
    best_by_source: dict[str, float] = {}
    for item in ranked:
        best_by_source[item.unit.source_id] = max(best_by_source.get(item.unit.source_id, 0.0), item.score)
    for item in ranked:
        best = best_by_source[item.unit.source_id]
        item.score = item.score / best if best > 0 else 0.0
    return ranked


def order(ranked: list[Ranked], fact_kinds: frozenset[str], by_relevance: bool) -> list[Ranked]:
    if not by_relevance:
        return list(ranked)                   # concatenate: hub order, then hub rank
    def key(item: Ranked):
        authoritative = any(item.candidate.manifest.authoritative_for(kind) for kind in fact_kinds)
        return (-round(item.score * item.coverage, 6), -item.coverage, not authoritative,
                item.unit.source_id, item.candidate.hub_rank)
    return sorted(ranked, key=key)


def dedup(ranked: list[Ranked], fact_kinds: frozenset[str]) -> tuple[list[Ranked], list[Omitted]]:
    """Keep one unit per content hash: an authoritative source's copy first, else the best ranked."""
    kept: dict[str, Ranked] = {}
    omitted: list[Omitted] = []
    for item in ranked:
        existing = kept.get(item.unit.content_hash)
        if existing is None:
            kept[item.unit.content_hash] = item
            continue
        item_authoritative = any(item.candidate.manifest.authoritative_for(kind) for kind in fact_kinds)
        existing_authoritative = any(existing.candidate.manifest.authoritative_for(kind) for kind in fact_kinds)
        if item_authoritative and not existing_authoritative:
            kept[item.unit.content_hash] = item
            item.duplicates = existing.duplicates + [existing.unit.evidence_id]
            existing.duplicates = []
            omitted.append(Omitted(ref_id=existing.unit.evidence_id, reason="exact_duplicate"))
        else:
            existing.duplicates.append(item.unit.evidence_id)
            omitted.append(Omitted(ref_id=item.unit.evidence_id, reason="exact_duplicate"))
    survivors = set(id(item) for item in kept.values())
    return [item for item in ranked if id(item) in survivors], omitted


def attribute_values(text: str, terms: set[str]) -> dict[str, str]:
    """{query term: first number on the first body line that mentions it}. Header lines (paths,
    titles, front matter) name places, not settings, and are skipped."""
    found: dict[str, str] = {}
    for line in text.splitlines():
        if HEADER_LINE.match(line):
            continue
        numbers = NUMBER.findall(line)
        if not numbers:
            continue
        for term in {stem(token) for token in words(line) if not token.isdigit()} & terms:
            found.setdefault(term, numbers[0])
    return found


def relation_type(a: EvidenceUnit, b: EvidenceUnit) -> RelationType:
    roles = {a.role, b.role}
    if roles == {EvidenceRole.implemented_behavior, EvidenceRole.intended_procedure}:
        return RelationType.policy_implementation_divergence
    if a.applicability.environment and b.applicability.environment and a.applicability.environment != b.applicability.environment:
        return RelationType.environment_difference
    if a.source_id == b.source_id and a.artifact_id == b.artifact_id and a.source_version != b.source_version:
        return RelationType.version_difference
    return RelationType.contradiction


def identity_signature(candidate: Candidate, domain_terms: set[str]) -> set[str]:
    """Words naming what a unit is about, from hub-visible identity fields only: the place's
    last segment (repo, space) and a front-matter `name:`. Multi-word names also contribute
    their acronym (payment-auth -> pa). Domain words (payments) and place words are dropped."""
    names = []
    location = candidate.artifact.get("location") or ""
    if location:
        names.append(location.split(":", 1)[-1].rstrip("/").split("/")[-1])
    front_matter = FRONT_MATTER_NAME.search(candidate.text[:300])
    if front_matter:
        names.append(front_matter.group(1))
    signature: set[str] = set()
    for name in names:
        tokens = [token for token in words(name) if token not in STOPWORDS]
        if len(tokens) > 1:
            signature.add("".join(token[0] for token in tokens))
        signature |= {stem(token) for token in tokens}
    return {word for word in signature if word not in domain_terms and word not in PLACE_WORDS}


def same_subject(a: Candidate, b: Candidate, domain_terms: set[str]) -> bool:
    """Conflict rule precondition (same entity): identity signatures overlap, or one unit has
    no identity fields at all (a session note)."""
    signature_a, signature_b = identity_signature(a, domain_terms), identity_signature(b, domain_terms)
    return not signature_a or not signature_b or bool(signature_a & signature_b)


def find_conflicts(ranked: list[Ranked], terms: tuple[str, ...],
                   domain_terms: set[str] = frozenset()) -> list[tuple[Ranked, Ranked, RelationType]]:
    pool = [item for item in ranked if item.coverage >= CONFLICT_COVERAGE][:MAX_CONFLICT_UNITS]
    values = [attribute_values(item.candidate.text, set(terms)) for item in pool]
    conflicts = []
    for i in range(len(pool)):
        for j in range(i + 1, len(pool)):
            a, b = pool[i].unit, pool[j].unit
            if a.source_id == b.source_id and a.source_version == b.source_version:
                continue
            if not same_subject(pool[i].candidate, pool[j].candidate, domain_terms):
                continue
            meanings_a, meanings_b = pool[i].candidate.interpretations, pool[j].candidate.interpretations
            if meanings_a and meanings_b and not meanings_a & meanings_b:
                continue                 # separated interpretations are never compared (no blending)
            clash = any(key in values[j] and values[j][key] != value for key, value in values[i].items())
            if clash:
                conflicts.append((pool[i], pool[j], relation_type(a, b)))
            if len(conflicts) >= MAX_CONFLICTS:
                return conflicts
    return conflicts


def unit_cost(unit: EvidenceUnit, tokenizer_id: str) -> int:
    return token_count(json.dumps(unit.model_dump(mode="json"), sort_keys=True), tokenizer_id)


def pack(ranked: list[Ranked], conflict_pairs: list[tuple[Ranked, Ranked, RelationType]],
         budget_tokens: int, tokenizer_id: str, reserve_witnesses: bool) -> Assembled:
    chosen: list[Ranked] = []
    used = 0

    def take(item: Ranked) -> bool:
        nonlocal used
        if any(item is other for other in chosen):
            return True
        cost = unit_cost(item.unit, tokenizer_id)
        if used + cost > budget_tokens:
            return False
        chosen.append(item)
        used += cost
        return True

    flagged: list[tuple[Ranked, Ranked, RelationType]] = []
    if reserve_witnesses:
        for a, b, relation in conflict_pairs:
            before = (list(chosen), used)
            if take(a) and take(b):
                flagged.append((a, b, relation))
            else:
                chosen[:], used = before       # never keep one side of a conflict alone by reservation
    # "needed" = the best-covered tier: a dropped unit that covers the question as well as the
    # best one found means needed evidence did not fit (HLD §7.4 check)
    top_coverage = max((item.coverage for item in ranked), default=0.0)
    truncated_relevant = False
    for item in ranked:
        if not take(item) and item.relevant and item.coverage >= top_coverage - 1e-9:
            truncated_relevant = True
    if not reserve_witnesses:
        flagged = [(a, b, r) for a, b, r in conflict_pairs
                   if any(a is c for c in chosen) and any(b is c for c in chosen)]
    chosen_order = {id(item): index for index, item in enumerate(ranked)}
    chosen.sort(key=lambda item: chosen_order[id(item)])
    evidence = [item.unit.model_copy(update={"duplicates": list(item.duplicates)}) for item in chosen]
    conflicts = [Conflict(conflict_id=f"cf-{index + 1}", a=a.unit.evidence_id, b=b.unit.evidence_id,
                          relation_type=relation, status=ConflictStatus.possible_conflict)
                 for index, (a, b, relation) in enumerate(flagged)]
    return Assembled(evidence=evidence, conflicts=conflicts, omitted=[], used_tokens=used,
                     truncated_relevant=truncated_relevant,
                     relevant_packed=sum(1 for item in chosen if item.relevant),
                     relevant_ids=[item.unit.evidence_id for item in chosen if item.relevant])


def assemble(candidates: list[Candidate], terms: tuple[str, ...], fact_kinds: frozenset[str],
             budget_tokens: int, tokenizer_id: str, common: bool, dedup_exact: bool,
             domain_terms: set[str] = frozenset()) -> Assembled:
    ranked = [item for item in score(candidates, terms) if item.coverage > 0 or not common]
    ranked = order(ranked, fact_kinds, by_relevance=common)
    omitted: list[Omitted] = []
    if dedup_exact:
        ranked, omitted = dedup(ranked, fact_kinds)
    pairs = find_conflicts(ranked, terms, domain_terms)
    assembled = pack(ranked, pairs, budget_tokens, tokenizer_id, reserve_witnesses=common)
    packed_ids = {unit.evidence_id for unit in assembled.evidence}
    duplicate_refs = {ref for unit in assembled.evidence for ref in unit.duplicates}
    # reference closure: keep an omitted entry only for copies a packed unit still points to
    assembled.subject_terms = len(terms)
    assembled.uncovered_terms = [term for term in terms
                                 if not any(term in term_counts(candidate.text) for candidate in candidates)]
    assembled.omitted = [entry for entry in omitted if entry.ref_id in duplicate_refs and entry.ref_id not in packed_ids]
    return assembled
