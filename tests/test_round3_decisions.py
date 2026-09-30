"""Round 3 System One decisions (design page §14): D6 invariants.

D6 judges only rule-produced pairs: a rule-flagged pair is always flagged whatever the provider
says; a candidate pair is promoted only with a matching calibration at or above the use band; with
no calibration, a failure or an invalid answer, assembly equals the rules-only result."""
from pathlib import Path

import anyio
import pytest
import yaml

from sanctum_ref.assembly import assemble, finish, prepare
from sanctum_ref.config import load_arm
from sanctum_ref.pipeline import Retriever
from sanctum_ref.providers.http_systemone import TEMPLATES, SystemOneHttpAdapter
from sanctum_systemone import CallOutcome, load_provider_specs
from tests.test_sanctum_ref import _candidate

ROOT = Path(__file__).resolve().parents[1]
SPEC = load_provider_specs(ROOT / "configs" / "system_one_providers.yaml")["local-test"]
TERMS = ("retry", "payment", "auth")


class ScriptedTransport:
    """Answers every asked item with a fixed p (or fails), like the broker would."""

    def __init__(self, p=None, reason=None, model="test-model-1"):
        self.p, self.reason, self.model, self.payloads = p, reason, model, []

    async def send(self, port, payload, deadline_ms):
        self.payloads.append(payload)
        if self.reason:
            return CallOutcome(provider=SPEC.name, unavailable_reason=self.reason)
        answers = {qid: {"type": "noul", "noul": self.p} for qid in payload["questions"]}
        return CallOutcome(provider=SPEC.name, model=self.model, answers=answers, descriptor_release="none")


def _units():
    code = _candidate("codehub", "a1", "// repo:payments/payment-auth\nclass RetryConfig {\n  MAX_RETRIES = 5;\n}\n")
    skill = _candidate("skillhub", "a2", "---\nname: Payment Auth\n---\nRetry at most 3 times on timeout.\n",
                       version="v3", location="skills/payments/")
    other = _candidate("dochub", "a3", "Retry payment auth calls at most 7 times.\n", version="v1", location="space:RISK")
    return [code, skill, other]


def _prepared():
    prepared = prepare(_units(), TERMS, frozenset({"implementation", "procedure"}), common=True, dedup_exact=True,
                       domain_terms={"payment"})
    assert prepared.flagged and prepared.pair_candidates, "fixture must produce both kinds of pair"
    return prepared


def _judge(tmp_path, transport, calibrate: bool):
    if calibrate:
        (tmp_path / "local-test@test-model-1.d6.yaml").write_text(yaml.safe_dump({
            "binding": {"provider": "local-test", "model": "test-model-1", "template": TEMPLATES["d6"]},
            "platt": {"a": 1.0, "b": 0.0}, "bands": {"use": 0.7, "skip": 0.0}}))
    adapter = SystemOneHttpAdapter(SPEC, tmp_path, transport=transport)
    retriever = Retriever(load_arm(ROOT / "configs" / "matrix.yaml", "C4"), None, round3="d6", round3_provider=adapter)
    from sanctum_contracts import RetrieveRequest
    request = RetrieveRequest(request_id="req-d6", query="payment auth retry limit", mode="scoped",
                              budget_tokens=4000, deadline_ms=3000)
    prepared = _prepared()
    promoted, results, failed = anyio.run(retriever._judge_conflicts, request, prepared, None)
    return prepared, finish(prepared, 4000, "cl100k_base", promoted), results, failed


def _pairs(assembled):
    return {frozenset((c.a, c.b)) for c in assembled.conflicts}


def _rules_only():
    return assemble(_units(), TERMS, frozenset({"implementation", "procedure"}), 4000, "cl100k_base",
                    common=True, dedup_exact=True, domain_terms={"payment"})


@pytest.mark.parametrize("p,reason,calibrate", [(0.0, None, True), (0.99, None, False), (None, "timeout", True),
                                                (None, "truncated", True), (0.5, None, True)])
def test_rule_flagged_pairs_always_stay_and_defaults_equal_rules(tmp_path, p, reason, calibrate):
    prepared, assembled, results, failed = _judge(tmp_path, ScriptedTransport(p, reason), calibrate)
    flagged = {frozenset((a.unit.evidence_id, b.unit.evidence_id)) for a, b, _ in prepared.flagged}
    assert flagged <= _pairs(assembled)                                   # never hidden
    assert _pairs(assembled) == _pairs(_rules_only())                    # below band, shadow or failed: rules-only
    assert [u.evidence_id for u in assembled.evidence] == [u.evidence_id for u in _rules_only().evidence]
    assert failed == (reason is not None)


def test_candidate_promoted_only_with_calibration_at_use_band(tmp_path):
    prepared, assembled, results, _ = _judge(tmp_path, ScriptedTransport(0.95), calibrate=True)
    candidate = {frozenset((a.unit.evidence_id, b.unit.evidence_id)) for a, b, _ in prepared.pair_candidates}
    assert candidate <= _pairs(assembled)                                 # promoted and both witnesses packed
    packed = {u.evidence_id for u in assembled.evidence}
    assert all(pair <= packed for pair in candidate)
    assert all(r.value["refs"] and r.value["template"] == "d6-noul-v1" for r in results if r.value)


def test_d6_sends_refs_not_text_and_cannot_create_pairs(tmp_path):
    transport = ScriptedTransport(0.95)
    prepared, assembled, _, _ = _judge(tmp_path, transport, calibrate=True)
    items = transport.payloads[0]["items"]
    assert all(set(ref) == {"source_id", "artifact_id", "version", "start", "end"}
               for item in items.values() for ref in item["refs"])
    produced = {frozenset((a.unit.evidence_id, b.unit.evidence_id)) for a, b, _ in prepared.flagged + prepared.pair_candidates}
    assert _pairs(assembled) <= produced
    stranger = (prepared.ranked[0], prepared.ranked[0], prepared.flagged[0][2])
    assert _pairs(finish(prepared, 4000, "cl100k_base", [stranger])) == _pairs(_rules_only())
