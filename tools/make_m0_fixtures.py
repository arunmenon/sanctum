"""Writes the M0 gold cases, stub responses and hand-written observed traces.

Gold and traces are evaluator-side; stub responses are SUT-side. They are written
by one script only because M0 is a hand-authored bootstrap. From M1 on, gold comes
from the world generator plus an independent audit, and traces come from the runner.
"""
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "gold" / "m0"
STUB = ROOT / "src" / "sanctum_stub" / "responses"
TRACE = ROOT / "tests" / "fixtures" / "m0" / "traces"
TOK = "cl100k_base"
NOW = "2026-10-01T09:00:00Z"
REV = "lab-contract-0.1.0+hld-v5.1"


def unit(eid, src, art, ver, start, end, text, kind, role, toks, app=None, dups=()):
    return {
        "evidence_id": eid, "source_id": src, "artifact_id": art, "source_version": ver,
        "native_ref": f"{src}:{art}@{ver}#{start}-{end}", "span": {"start": start, "end": end},
        "content_hash": f"h-{art}-{ver}-{start}", "text": text, "kind": kind, "role": role,
        "applicability": app or {"applicability_status": "unknown"},
        "retrieved_at": NOW, "exact_token_count": toks, "tokenizer_id": TOK,
        "duplicates": list(dups),
    }


def span(src, art, ver, s, e):
    return {"source_id": src, "artifact_id": art, "version": ver, "start": s, "end": e}


def write(case_id, gold, response, receipt, trace):
    GOLD.mkdir(parents=True, exist_ok=True)
    TRACE.mkdir(parents=True, exist_ok=True)
    (GOLD / f"{case_id}.yaml").write_text(yaml.safe_dump(gold, sort_keys=False))
    rid = gold["request"]["request_id"]
    (STUB / f"{rid}.json").write_text(json.dumps({"response": response, "receipt": receipt}, indent=2))
    (TRACE / f"{rid}.json").write_text(json.dumps(trace, indent=2))


IMPL = unit("ev-a1", "codehub", "art-rc", "R42", 100, 200,
            "static final int MAX_RETRIES = 5; // gateway timeout path", "code", "implemented_behavior", 40,
            app={"branch": "main", "environment": "prod", "effective_from": "R42", "applicability_status": "known"})
PROC = unit("ev-b1", "skillhub", "art-sk", "v3", 0, 120,
            "Auth Service retries: retry at most 3 times on gateway timeout.", "skill", "intended_procedure", 30)
IDP = unit("ev-c1", "skillhub", "art-sk-id", "v2", 0, 110,
           "Identity Auth Service retries: at most 2 attempts.", "skill", "intended_procedure", 25)


# --- m0-001: unique name, policy/implementation divergence, mandatory source ---
g1 = {
    "case_id": "m0-001", "bundle_id": "b-01", "family": "hub_specific_name",
    "request": {"request_id": "req-4c1e", "query": "What are the PA-svc retry limits on a gateway timeout?",
                "mode": "scoped", "scope": "project:proj-a", "budget_tokens": 4000, "deadline_ms": 3000,
                "caller_profile": "agent"},
    "principal": "p-payments", "answerable": True, "interpretation_policy": "unique",
    "interpretations": [{"interpretation_id": "i1", "entity_ref": "ent-17"}],
    "obligations": [
        {"obligation_id": "o-impl", "interpretation_id": "i1", "weight": 1.0,
         "bundles": [{"spans": [span("codehub", "art-rc", "R42", 120, 180)]}]},
        {"obligation_id": "o-proc", "interpretation_id": "i1", "weight": 1.0,
         "bundles": [{"spans": [span("skillhub", "art-sk", "v3", 10, 90)]}]},
    ],
    "source_obligations": [{"source_id": "skillhub", "mandatory": True, "expected": "attempted"}],
    "relations": [{"relation_id": "r1", "relation_type": "policy_implementation_divergence",
                   "witness_a": {"spans": [span("codehub", "art-rc", "R42", 120, 180)]},
                   "witness_b": {"spans": [span("skillhub", "art-sk", "v3", 10, 90)]}}],
    "forbidden": {"canaries": ["CANARY-7731"], "wrong_entities": ["ent-23"], "prohibited_activations": []},
    "expected": {"evidence_status": "sufficient", "required_reasons": [],
                 "source_status": {"codehub": "called", "skillhub": "called", "memoryhub": "skipped"}},
}
r1 = {
    "request_id": "req-4c1e", "receipt_id": "rc-01", "memory_release_id": "r1",
    "effective_scope_ref": "scope-x1", "replay_level": "recompute_on_candidates",
    "interpretations": [{"interpretation_id": "x1", "entity_ref": "ent-17", "resolution_origin": "denotes",
                         "evidence_ids": ["ev-a1", "ev-b1"], "conflict_ids": ["c1"], "evidence_status": "sufficient"}],
    "evidence": [IMPL, PROC],
    "conflicts": [{"conflict_id": "c1", "a": "ev-a1", "b": "ev-b1",
                   "relation_type": "policy_implementation_divergence", "status": "possible_conflict"}],
    "sources": [{"source_id": "codehub", "status": "called", "reasons": ["routing_selected"]},
                {"source_id": "skillhub", "status": "called", "reasons": ["must_consult"]},
                {"source_id": "memoryhub", "status": "skipped", "reasons": ["not_selected"]}],
    "evidence_status": "sufficient", "budget": {"requested": 4000, "used": 310, "tokenizer_id": TOK},
}
rc1 = {"receipt_id": "rc-01", "request_id": "req-4c1e", "config_id": "stub", "contract_revision": REV,
       "memory_release_id": "r1",
       "resolutions": [{"term": "PA-svc", "candidates": ["ent-17"], "chosen": ["ent-17"], "origin": "denotes",
                        "assertion_refs": ["DENOTES:memoryhub/PA-svc@v1"]}],
       "activations": [{"kind": "procedure", "ref": "proc-must-consult-skillhub@v3", "entity_ref": "ent-17",
                        "source_id": "skillhub"},
                       {"kind": "selector", "ref": "repo:payments/pa", "entity_ref": "ent-17", "source_id": "codehub"}],
       "calls": [{"source_id": "codehub", "tool": "search_code", "status": "ok", "started_ms": 5, "ended_ms": 60},
                 {"source_id": "skillhub", "tool": "search_skills", "status": "ok", "started_ms": 5, "ended_ms": 70}]}
t1 = {"request_id": "req-4c1e", "calls": [{"source_id": "codehub", "tool": "search_code", "outcome": "ok"},
                                          {"source_id": "skillhub", "tool": "search_skills", "outcome": "ok"}]}
write("m0-001", g1, r1, rc1, t1)


# --- m0-002: homonym, agent caller -> separated interpretations ---
g2 = {
    "case_id": "m0-002", "bundle_id": "b-02", "family": "same_name_two_meanings",
    "request": {"request_id": "req-9b27", "query": "How many retries does Auth Service allow?",
                "mode": "explore", "budget_tokens": 4000, "deadline_ms": 3000, "caller_profile": "agent"},
    "principal": "p-both", "answerable": True, "interpretation_policy": "separate_alternatives",
    "interpretations": [{"interpretation_id": "iA", "entity_ref": "ent-17"},
                        {"interpretation_id": "iB", "entity_ref": "ent-23"}],
    "obligations": [
        {"obligation_id": "oA", "interpretation_id": "iA", "weight": 1.0,
         "bundles": [{"spans": [span("skillhub", "art-sk", "v3", 10, 90)]}]},
        {"obligation_id": "oB", "interpretation_id": "iB", "weight": 1.0,
         "bundles": [{"spans": [span("skillhub", "art-sk-id", "v2", 0, 60)]}]},
    ],
    "forbidden": {"canaries": ["CANARY-7731"]},
    "expected": {"evidence_status": "sufficient", "required_reasons": ["ambiguous_term"]},
}
r2 = {
    "request_id": "req-9b27", "receipt_id": "rc-02", "memory_release_id": "r1",
    "effective_scope_ref": "scope-x2", "replay_level": "recompute_on_candidates",
    "interpretations": [
        {"interpretation_id": "x1", "entity_ref": "ent-17", "resolution_origin": "denotes",
         "evidence_ids": ["ev-b1"], "evidence_status": "sufficient"},
        {"interpretation_id": "x2", "entity_ref": "ent-23", "resolution_origin": "denotes",
         "evidence_ids": ["ev-c1"], "evidence_status": "sufficient"}],
    "evidence": [PROC, IDP],
    "sources": [{"source_id": "skillhub", "status": "called", "reasons": ["routing_selected"]}],
    "evidence_status": "sufficient", "reasons": ["ambiguous_term"],
    "budget": {"requested": 4000, "used": 240, "tokenizer_id": TOK},
}
rc2 = {"receipt_id": "rc-02", "request_id": "req-9b27", "config_id": "stub", "contract_revision": REV,
       "memory_release_id": "r1",
       "resolutions": [{"term": "Auth Service", "candidates": ["ent-17", "ent-23"], "chosen": ["ent-17", "ent-23"],
                        "origin": "denotes"}],
       "calls": [{"source_id": "skillhub", "tool": "search_skills", "status": "ok", "started_ms": 3, "ended_ms": 50}]}
t2 = {"request_id": "req-9b27", "calls": [{"source_id": "skillhub", "tool": "search_skills", "outcome": "ok"}]}
write("m0-002", g2, r2, rc2, t2)


# --- m0-003: mandatory source denied -> safe gap, no call ---
g3 = {
    "case_id": "m0-003", "bundle_id": "b-03", "family": "restricted_content",
    "request": {"request_id": "req-2d80", "query": "What is the retry procedure for PA-svc?",
                "mode": "scoped", "scope": "project:proj-a", "budget_tokens": 4000, "deadline_ms": 3000},
    "principal": "p-code-only", "answerable": True, "interpretation_policy": "unique",
    "interpretations": [{"interpretation_id": "i1", "entity_ref": "ent-17"}],
    "obligations": [
        {"obligation_id": "o-impl", "interpretation_id": "i1", "weight": 1.0,
         "bundles": [{"spans": [span("codehub", "art-rc", "R42", 120, 180)]}]},
        {"obligation_id": "o-proc", "interpretation_id": "i1", "weight": 1.0, "obtainable": False,
         "acceptable_gap_reasons": ["required_source_denied"],
         "bundles": [{"spans": [span("skillhub", "art-sk", "v3", 10, 90)]}]},
    ],
    "source_obligations": [{"source_id": "skillhub", "mandatory": True, "expected": "denied_gap"}],
    "forbidden": {"canaries": ["retry at most 3 times"]},
    "expected": {"evidence_status": "partial", "required_reasons": ["required_source_denied"],
                 "source_status": {"skillhub": "skipped"}},
}
r3 = {
    "request_id": "req-2d80", "receipt_id": "rc-03", "memory_release_id": "r1",
    "effective_scope_ref": "scope-x3", "replay_level": "recompute_on_candidates",
    "interpretations": [{"interpretation_id": "x1", "entity_ref": "ent-17", "resolution_origin": "denotes",
                         "evidence_ids": ["ev-a1"], "evidence_status": "partial",
                         "reasons": []}],
    "evidence": [IMPL],
    "sources": [{"source_id": "codehub", "status": "called", "reasons": ["routing_selected"]},
                {"source_id": "skillhub", "status": "skipped", "reasons": ["required_source_denied"]}],
    "evidence_status": "partial", "reasons": ["required_source_denied"],
    "budget": {"requested": 4000, "used": 150, "tokenizer_id": TOK},
}
rc3 = {"receipt_id": "rc-03", "request_id": "req-2d80", "config_id": "stub", "contract_revision": REV,
       "memory_release_id": "r1",
       "resolutions": [{"term": "PA-svc", "candidates": ["ent-17"], "chosen": ["ent-17"], "origin": "denotes"}],
       "activations": [{"kind": "procedure", "ref": "proc-must-consult-skillhub@v3", "entity_ref": "ent-17",
                        "source_id": "skillhub"}],
       "calls": [{"source_id": "codehub", "tool": "search_code", "status": "ok", "started_ms": 4, "ended_ms": 55}]}
t3 = {"request_id": "req-2d80", "calls": [{"source_id": "codehub", "tool": "search_code", "outcome": "ok"}]}
write("m0-003", g3, r3, rc3, t3)
print("fixtures written")
