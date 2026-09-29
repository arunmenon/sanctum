"""Round-1 intent rules (HLD §6.3): which kinds of fact a query needs, which domains it names,
and whether it is too vague to promise a complete answer. Pure lexical rules; no model.

These rules read the query only. They never read evidence text, so a document cannot steer
routing or must-consult (HLD §10 Ex10)."""
from __future__ import annotations

from dataclasses import dataclass

from .text import STOPWORDS, stem, subject_terms, words

FACT_KIND_CUES = {
    "implementation": {"config", "configur", "configuration", "code", "value", "set", "implement",
                       "implementation", "batch", "size", "timeout", "limit", "pool", "retry", "max",
                       "default", "class", "constant", "setting", "parameter", "production", "prod",
                       "release", "deploy", "worker", "count", "interval", "threshold", "use"},
    "procedure": {"how", "step", "procedure", "runbook", "checklist", "should", "must", "supposed",
                  "process", "policy", "rule", "guideline", "cutover", "rollback", "drain", "failover",
                  "allow", "allowed", "intend", "wait", "restart",
                  # retry limits and backoff are governed settings: owners publish the intended value
                  "retry", "limit", "backoff"},
    "reference": {"doc", "documentation", "page", "wiki", "sla", "overview", "describe", "explain",
                  "policy", "backoff", "schedule", "document"},
    "session_history": {"session", "earlier", "previous", "previously", "note", "we", "i", "my",
                        "yesterday", "remember", "discuss", "follow"},
}
DEFAULT_FACT_KINDS = frozenset({"implementation", "procedure", "reference"})
VAGUE_CUES = {"why", "slow", "slower", "recently", "lately", "week", "anything", "something", "overall",
              "general", "happen", "wrong", "issue", "problem"}
MIN_SPECIFIC_TERMS = 3


ENVIRONMENT_CUES = {"experiment": {"experiment", "experimental"}}


@dataclass(frozen=True)
class Intent:
    terms: tuple[str, ...]              # stemmed content terms of the query
    fact_kinds: frozenset[str]
    detected_fact_kinds: frozenset[str]
    domains: frozenset[str]
    vague: bool
    releases: tuple[str, ...] = ()      # release names written in the query (HLD §10 Ex4 step 1)
    environments: frozenset[str] = frozenset()   # non-default environments the query names


def analyze(query: str, domains: dict[str, set[str]], releases: set[str] = frozenset(),
            verify: bool = False) -> Intent:
    raw = {stem(token) for token in words(query)} | set(words(query))
    detected = frozenset(kind for kind, cues in FACT_KIND_CUES.items()
                         if raw & {stem(cue) for cue in cues} | (raw & cues))
    if verify:
        # a claim is checked against every kind of authority: implemented, intended, reference
        detected = detected | DEFAULT_FACT_KINDS
    release_lookup = {release.lower(): release for release in releases}
    mentioned = tuple(dict.fromkeys(release_lookup[token] for token in words(query) if token in release_lookup))
    environments = frozenset(name for name, cues in ENVIRONMENT_CUES.items() if raw & cues)
    if verify:
        # evidence for and against a claim includes other environments, labelled by applicability
        environments = environments | frozenset(ENVIRONMENT_CUES)
    named_domains = frozenset(domain for domain, cue_terms in domains.items()
                              if raw & ({stem(term) for term in cue_terms} | cue_terms))
    terms = tuple(subject_terms(query, {release.lower() for release in releases}))
    specific = [term for term in terms if term not in VAGUE_CUES and term not in STOPWORDS]
    vague = bool(raw & VAGUE_CUES) and not named_domains and len(specific) < MIN_SPECIFIC_TERMS + 1
    return Intent(terms=terms, fact_kinds=detected or DEFAULT_FACT_KINDS, detected_fact_kinds=detected,
                  domains=named_domains, vague=vague or len(specific) < 2, releases=mentioned,
                  environments=environments)
