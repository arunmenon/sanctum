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


def _d4_units():
    relevant = _units()
    unrelated = [_candidate("dochub", f"z{i}", f"Quarterly offsite notes {i}. Lunch at noon.\n", version="v1",
                            location="space:OTHER", rank=i) for i in range(4)]
    return relevant + unrelated


def test_d4_never_removes_a_rules_packed_unit_under_any_scores():
    """Superset property (design page §14): for any D4 scores and use band, the packed set
    contains every unit the rules-only packer would pack, and the budget holds."""
    import random
    from sanctum_ref.text import token_count
    import json as _json
    rng = random.Random(7)
    units = _d4_units()
    fact_kinds = frozenset({"implementation", "procedure"})
    for trial in range(60):
        budget = rng.randint(120, 1400)
        prepared = prepare(units, TERMS, fact_kinds, common=True, dedup_exact=True, domain_terms={"payment"})
        rules = finish(prepared, budget, "cl100k_base")
        ids = [item.unit.evidence_id for item in prepared.ranked + prepared.excluded]
        scores = {evidence_id: rng.random() for evidence_id in ids}
        if trial % 3 == 0:
            scores = {evidence_id: 1.0 if evidence_id.startswith("ev-z") else 0.0 for evidence_id in ids}  # adversarial
        d4 = finish(prepared, budget, "cl100k_base", d4_scores=scores, d4_use=rng.choice([0.0, 0.5, 0.9]))
        rules_ids = {u.evidence_id for u in rules.evidence}
        d4_ids = {u.evidence_id for u in d4.evidence}
        assert rules_ids <= d4_ids, (trial, budget)
        assert set(d4.rules_packed) == rules_ids
        assert d4_ids - rules_ids <= {item.unit.evidence_id for item in prepared.excluded}
        wire = _json.dumps([u.model_dump(mode="json") for u in d4.evidence])
        assert d4.used_tokens <= budget and token_count(wire, "cl100k_base") <= budget


def test_d4_shadow_is_rules_only(tmp_path):
    adapter = SystemOneHttpAdapter(SPEC, tmp_path, transport=ScriptedTransport(0.99))   # no calibration file
    retriever = Retriever(load_arm(ROOT / "configs" / "matrix.yaml", "C4"), None, round3="d4", round3_provider=adapter)
    from sanctum_contracts import RetrieveRequest
    request = RetrieveRequest(request_id="req-d4", query="payment auth retry limit", mode="scoped",
                              budget_tokens=4000, deadline_ms=3000)
    prepared = prepare(_d4_units(), TERMS, frozenset({"implementation"}), common=True, dedup_exact=True, domain_terms={"payment"})
    scores, use, results, failed = anyio.run(retriever._judge_relevance, request, prepared, None)
    assert scores is None and use is None and not failed
    assert all(r.value["shadow"] and r.value["template"] == "d4-noul-v1" for r in results if r.value)


@pytest.mark.parametrize("budget", [1000, 1500, 2000])
def test_d4_superset_holds_at_tight_budgets_with_adversarial_scores(budget):
    """Review A3: at fixed tight budgets, adversarial D4 scores (irrelevant units first, rules
    units last, reversed rank) never remove a unit the rules-only packer includes."""
    many = _d4_units() + [_candidate("codehub", f"r{i}", f"// repo:payments/payment-auth\\nclass RetryConfig{i} {{\\n  "
                                     f"MAX_RETRIES = {i};\\n}}\\n" + "x " * (60 + 11 * i), rank=i) for i in range(8)]
    fact_kinds = frozenset({"implementation"})
    prepared = prepare(many, TERMS, fact_kinds, common=True, dedup_exact=True, domain_terms={"payment"})
    rules = {u.evidence_id for u in finish(prepared, budget, "cl100k_base").evidence}
    ids = [item.unit.evidence_id for item in prepared.ranked + prepared.excluded]
    adversaries = [
        {i: (1.0 if i in {x.unit.evidence_id for x in prepared.excluded} else 0.0) for i in ids},
        {i: position / len(ids) for position, i in enumerate(ids)},          # reversed rank
        {i: (0.0 if i in rules else 1.0) for i in ids},
    ]
    for scores in adversaries:
        for use in (0.0, 0.5):
            d4 = finish(prepared, budget, "cl100k_base", d4_scores=scores, d4_use=use)
            assert rules <= {u.evidence_id for u in d4.evidence}, (budget, use)
            assert d4.used_tokens <= budget


def test_reorder_that_costs_more_never_removes_a_rules_packed_unit(monkeypatch):
    """Review A3, the exact risk: the D4 reorder changes serialization cost and pushes the list
    over budget after extras are exhausted. The packer must keep the fitting order, not drop a
    rules-packed unit."""
    import sanctum_ref.assembly as assembly
    prepared = prepare(_units(), TERMS, frozenset({"implementation", "procedure"}), common=True, dedup_exact=True,
                       domain_terms={"payment"})
    rank = [item.unit.evidence_id for item in prepared.ranked]
    real_cost = assembly.list_cost

    def order_sensitive_cost(items, tokenizer_id):
        ids = [item.unit.evidence_id for item in items]
        in_rank_order = ids == sorted(ids, key=lambda i: rank.index(i) if i in rank else len(rank))
        return real_cost(items, tokenizer_id) + (0 if in_rank_order else 50)

    monkeypatch.setattr(assembly, "list_cost", order_sensitive_cost)
    rules = finish(prepared, 4000, "cl100k_base")
    budget = rules.used_tokens                                  # exactly full under rules order
    rules = finish(prepared, budget, "cl100k_base")
    reversed_scores = {i: position / len(rank) for position, i in enumerate(rank)}
    d4 = finish(prepared, budget, "cl100k_base", d4_scores=reversed_scores, d4_use=0.99)
    assert {u.evidence_id for u in rules.evidence} <= {u.evidence_id for u in d4.evidence}
    assert d4.used_tokens <= budget


@pytest.mark.parametrize('decision', ['d4', 'd6'])
def test_raw_round3_applies_without_calibration_and_records_policy(tmp_path, decision):
    from sanctum_contracts import RetrieveRequest
    adapter = SystemOneHttpAdapter(SPEC, tmp_path, transport=ScriptedTransport(0.95))
    retriever = Retriever(load_arm(ROOT/'configs/matrix.yaml', 'C4'), None,
                          round3='both', round3_provider=adapter, round3_policy='raw')
    request = RetrieveRequest(request_id='raw-round3', query='payment auth retry limit',
                              mode='scoped', budget_tokens=4000, deadline_ms=3000)
    prepared = _prepared()
    if decision == 'd6':
        promoted, results, failed = anyio.run(retriever._judge_conflicts, request, prepared, None)
        assert promoted == prepared.pair_candidates
        assert _pairs(finish(prepared, 4000, 'cl100k_base', promoted)) > _pairs(_rules_only())
    else:
        scores, use, results, failed = anyio.run(retriever._judge_relevance, request, prepared, None)
        assert scores and set(scores.values()) == {0.95} and use == 0.5
    assert not failed
    assert all(r.value['shadow'] is False and r.value['application_policy'] == 'raw'
               and r.value['use_threshold'] == 0.5 and r.calibration is None for r in results)


def test_raw_relevance_changes_delivered_order_and_preserves_unavailable(tmp_path):
    from sanctum_contracts import RetrieveRequest
    class ReverseTransport(ScriptedTransport):
        async def send(self, port, payload, deadline_ms):
            self.payloads.append(payload)
            ids=list(payload['questions'])
            return CallOutcome(provider=SPEC.name, model=self.model, descriptor_release='none',
                answers={qid:{'type':'noul','noul':i/len(ids)} for i,qid in enumerate(ids)})
    request=RetrieveRequest(request_id='raw-order',query='payment auth retry limit',mode='scoped',
                            budget_tokens=4000,deadline_ms=3000)
    prepared=_prepared()
    adapter=SystemOneHttpAdapter(SPEC,tmp_path,transport=ReverseTransport())
    retriever=Retriever(load_arm(ROOT/'configs/matrix.yaml','C4'),None,round3='both',round3_provider=adapter,round3_policy='raw')
    scores,use,_,failed=anyio.run(retriever._judge_relevance,request,prepared,None)
    rules=finish(prepared,4000,'cl100k_base')
    changed=finish(prepared,4000,'cl100k_base',d4_scores=scores,d4_use=use)
    assert [e.evidence_id for e in changed.evidence] != [e.evidence_id for e in rules.evidence]
    assert not failed
    retriever.round3_provider=SystemOneHttpAdapter(SPEC,tmp_path,transport=ScriptedTransport(reason='timeout'))
    promoted,results,failed=anyio.run(retriever._judge_conflicts,request,prepared,None)
    assert not promoted and failed and all(r.status.value=='unavailable' for r in results)
