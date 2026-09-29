"""Regression tests for the M3-M8 review items on the evaluator side (degradation honesty per
retrieval operation, leak fingerprints for all caller-unreadable content, independent budget
recount)."""
import json
from pathlib import Path

import pytest

from sanctum_contracts import EvidenceResponse, Receipt
from sanctum_eval.budget import evidence_tokens
from sanctum_eval.degradation import case_honesty
from sanctum_eval.leak_scan import LeakScanner
from sanctum_eval.load import load_gold
from sanctum_eval.metrics import score_case
from sanctum_world.render import build

ROOT = Path(__file__).resolve().parents[1]
GOLD_DEV = ROOT / "gold" / "dev"
SEED = 20260930


# ---- item 2: honesty per retrieval operation ---------------------------------------------
@pytest.fixture(scope="module")
def codehub_mandatory():
    golds = [load_gold(path) for path in sorted(GOLD_DEV.glob("*.yaml"))]
    return next(g for g in golds if any(o.mandatory and o.source_id == "codehub" for o in g.source_obligations))


def _trace(gold, calls):
    return {"request_id": gold.request.request_id,
            "calls": [{"source_id": s, "tool": t, "outcome": o, "audience_valid": True} for s, t, o in calls]}


def _response(gold, status, source_row):
    return {"request_id": gold.request.request_id, "evidence_status": status, "sources": [source_row]}


SEARCH_OK_FETCH_TIMEOUT = [("codehub", "search_code", "ok"), ("codehub", "read_file", "timeout")]


def test_failed_fetch_after_ok_search_is_a_failure(codehub_mandatory):
    gold = codehub_mandatory
    honesty = case_honesty(gold, _response(gold, "sufficient", {"source_id": "codehub", "status": "called"}),
                           _trace(gold, SEARCH_OK_FETCH_TIMEOUT))
    assert honesty.overclaimed and honesty.unreported_gaps == ("codehub",)


def test_routing_reason_is_not_a_reported_gap(codehub_mandatory):
    gold = codehub_mandatory
    row = {"source_id": "codehub", "status": "called", "reasons": ["routing_selected"]}
    assert case_honesty(gold, _response(gold, "partial", row), _trace(gold, SEARCH_OK_FETCH_TIMEOUT)).unreported_gaps
    row = {"source_id": "codehub", "status": "called", "reasons": ["routing_selected", "required_source_unavailable"]}
    assert case_honesty(gold, _response(gold, "partial", row), _trace(gold, SEARCH_OK_FETCH_TIMEOUT)).honest


def test_retried_fetch_that_succeeded_is_not_a_gap(codehub_mandatory):
    gold = codehub_mandatory
    calls = SEARCH_OK_FETCH_TIMEOUT + [("codehub", "read_file", "ok")]
    row = {"source_id": "codehub", "status": "called"}
    assert case_honesty(gold, _response(gold, "sufficient", row), _trace(gold, calls)).honest


# ---- item 3: leak fingerprints for all caller-unreadable content ----------------------------
@pytest.fixture(scope="module")
def world_build(tmp_path_factory):
    out_dir = tmp_path_factory.mktemp("review-build") / "world"
    build(ROOT / "world", SEED, out_dir)
    return out_dir


@pytest.fixture(scope="module")
def scanner(world_build):
    return LeakScanner(world_build)


def _hub_row(world_build, hub, needle):
    for line in (world_build / "hubs" / hub / "artifacts.jsonl").read_text().splitlines():
        if needle in line:
            return json.loads(line)
    raise AssertionError(needle)


def test_foreign_session_memory_text_is_a_leak(scanner, world_build):
    note = _hub_row(world_build, "memoryhub", "billsync drain follow-up")
    assert note["metadata"]["principal"] == "kestrel-both"
    body = note["text"].split("\n", 2)[2]          # text only: no header, title or artifact id
    kinds = {kind for kind, _ in scanner.scan_text(body, "kestrel-payments")}
    assert "private_text" in kinds
    assert scanner.scan_text(note["text"], "kestrel-both") == []


def test_cross_acl_text_is_a_leak_but_shared_fragments_are_not(scanner):
    identity_only = next(a for a in scanner.artifacts
                         if a.hub == "codehub" and a.acl == {"identity-eng"} and a.owner is None
                         and any(("private_text", line) in scanner.fingerprints("kestrel-payments") for line in a.lines))
    line = next(l for l in identity_only.lines if ("private_text", l) in scanner.fingerprints("kestrel-payments"))
    assert ("private_text", line) in scanner.scan_text(f"answer: {line}", "kestrel-payments")
    assert scanner.scan_text(line, "kestrel-identity") == []
    # a hidden line that is a fragment of readable text is not a fingerprint for that caller
    readable = "\n".join(l for a in scanner.artifacts if scanner.can_read("kestrel-payments", a) for l in a.lines)
    assert all(token not in readable for kind, token in scanner.fingerprints("kestrel-payments") if kind.endswith("_text"))


# ---- item 4: independent budget recount -----------------------------------------------------
def test_budget_gate_recounts_evidence(case):
    gold, response, receipt, trace = case("m0-001")
    assert score_case(gold, EvidenceResponse.model_validate(response), Receipt.model_validate(receipt),
                      trace).within_budget
    response["evidence"][0]["text"] = "retry " * (gold.request.budget_tokens + 50)
    response["budget"]["used"] = 10                                        # the SUT under-reports
    padded = EvidenceResponse.model_validate(response)
    assert evidence_tokens(padded) > gold.request.budget_tokens
    score = score_case(gold, padded, Receipt.model_validate(receipt), trace)
    assert not score.within_budget and "budget" in score.gates_failed and not score.safe_grounded_success
    assert score.tokens_recounted == evidence_tokens(padded)
