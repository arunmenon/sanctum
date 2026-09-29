"""Metric implementations (lab-plan review §3.2). One frozen implementation for all arms."""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from sanctum_contracts import EvidenceResponse, Receipt

from .budget import evidence_tokens
from .gold import Bundle, ExpectedSourceOutcome, GoldCase, InterpretationPolicy
from .trace import ObservedTrace


# ---------- evidence satisfaction ----------

def _within_budget(resp: EvidenceResponse, gold: GoldCase | None = None) -> bool:
    """Declared use within the declared budget, and the evaluator's own recount of the serialized
    evidence within the request's budget (the SUT's `budget.used` is not trusted alone)."""
    if resp.budget.used > resp.budget.requested:
        return False
    limit = gold.request.budget_tokens if gold is not None else resp.budget.requested
    return evidence_tokens(resp) <= limit


def _credited_units(resp: EvidenceResponse, gold: GoldCase):
    """E_q: evidence actually present, within the hard budget, not forbidden."""
    if not _within_budget(resp, gold):
        return []
    out = []
    for e in resp.evidence:
        if not e.text.strip():
            continue  # IDs-only / empty text earns nothing
        if any(c in e.text for c in gold.forbidden.canaries):
            continue
        out.append(e)
    return out


def _span_covered(span, units) -> bool:
    for e in units:
        if (e.source_id == span.source_id and e.artifact_id == span.artifact_id
                and e.source_version == span.version
                and e.span.start <= span.start and e.span.end >= span.end):
            return True
    return False


def bundle_satisfied(bundle: Bundle, units) -> bool:
    return all(_span_covered(s, units) for s in bundle.spans)


def _units_for_interpretation(resp, gold, interp_id, units):
    """Under separate_alternatives, only credit evidence listed under the matching branch."""
    if gold.interpretation_policy != InterpretationPolicy.separate_alternatives:
        return units
    gi = next(i for i in gold.interpretations if i.interpretation_id == interp_id)
    branch = next((i for i in resp.interpretations if i.entity_ref == gi.entity_ref), None)
    if branch is None:
        return []
    ids = set(branch.evidence_ids)
    return [u for u in units if u.evidence_id in ids]


def obligation_sat(resp, gold, ob, units) -> bool:
    scoped = _units_for_interpretation(resp, gold, ob.interpretation_id, units)
    return any(bundle_satisfied(b, scoped) for b in ob.bundles)


# ---------- metrics ----------

def necessary_evidence_recall(gold, resp) -> float | None:
    if not gold.answerable or not gold.obligations:
        return None
    units = _credited_units(resp, gold)
    total = sum(o.weight for o in gold.obligations)
    got = sum(o.weight for o in gold.obligations if obligation_sat(resp, gold, o, units))
    return got / total


def missing_obligations(gold, resp):
    units = _credited_units(resp, gold)
    return [o for o in gold.obligations if not obligation_sat(resp, gold, o, units)]


def harmful_omission(gold, resp) -> bool | None:
    if not gold.answerable:
        return None
    return len(missing_obligations(gold, resp)) > 0


def silent_omission(gold, resp) -> bool:
    """A missing obligation with no specific, declared gap reason. Generic gaps match nothing."""
    declared = set(resp.reasons)
    for s in resp.sources:
        declared |= set(s.reasons)
    for i in resp.interpretations:
        declared |= set(i.reasons)
    for o in missing_obligations(gold, resp):
        if not (set(o.acceptable_gap_reasons) & declared):
            return True
    return False


def conflict_witnesses_kept(gold, resp) -> float | None:
    if not gold.relations:
        return None
    units = _credited_units(resp, gold)
    by_id = {u.evidence_id: u for u in units}
    kept = 0
    for rel in gold.relations:
        if not (bundle_satisfied(rel.witness_a, units) and bundle_satisfied(rel.witness_b, units)):
            continue
        a_ids = {u.evidence_id for u in units if bundle_satisfied(Bundle(spans=rel.witness_a.spans), [u])}
        b_ids = {u.evidence_id for u in units if bundle_satisfied(Bundle(spans=rel.witness_b.spans), [u])}
        flagged = any(
            c.relation_type == rel.relation_type
            and ({c.a, c.b} & a_ids) and ({c.a, c.b} & b_ids)
            and c.a in by_id and c.b in by_id
            for c in resp.conflicts
        )
        kept += flagged
    return kept / len(gold.relations)


def false_conflict_flags(gold, resp) -> int:
    return len(resp.conflicts) if not gold.relations else 0


def wrong_entity_activations(gold, receipt: Receipt) -> list[str]:
    allowed = gold.allowed_entities
    bad = [a.ref for a in receipt.activations if a.entity_ref not in allowed]
    bad += [a.ref for a in receipt.activations if a.ref in gold.forbidden.prohibited_activations]
    return bad


def ambiguity_handled(gold, resp, receipt) -> bool | None:
    policy = gold.interpretation_policy
    got = {i.entity_ref for i in resp.interpretations}
    if policy == InterpretationPolicy.separate_alternatives:
        if gold.request.caller_profile.value == "agent" and "clarification_requested" in resp.reasons and not got:
            return False  # an agent default cannot be satisfied by clarification alone (HLD §9.2)
        if got != gold.allowed_entities:
            return False
        # no blending: evidence for one interpretation's obligations must not sit only in another branch
        units = _credited_units(resp, gold)
        for o in gold.obligations:
            if any(bundle_satisfied(b, units) for b in o.bundles) and not obligation_sat(resp, gold, o, units):
                return False
        return not wrong_entity_activations(gold, receipt)
    if policy == InterpretationPolicy.clarify:
        return "clarification_requested" in resp.reasons
    return None


def false_ambiguity(gold, resp) -> bool | None:
    if gold.interpretation_policy != InterpretationPolicy.unique:
        return None
    return len(resp.interpretations) > 1 or "ambiguous_term" in resp.reasons


def mandatory_source_compliance(gold, resp, trace: ObservedTrace) -> dict[str, bool]:
    attempted = trace.sources_attempted()
    by_src = {s.source_id: s for s in resp.sources}
    out = {}
    for so in gold.source_obligations:
        if not so.mandatory:
            continue
        s = by_src.get(so.source_id)
        reasons = set(s.reasons) if s else set()
        if so.expected == ExpectedSourceOutcome.attempted:
            ok = so.source_id in attempted
        elif so.expected == ExpectedSourceOutcome.denied_gap:
            ok = (so.source_id not in attempted) and ("required_source_denied" in reasons | set(resp.reasons))
        elif so.expected == ExpectedSourceOutcome.unavailable_gap:
            ok = (so.source_id in attempted) and ("required_source_unavailable" in reasons | set(resp.reasons))
        else:
            ok = s is not None and s.status.value == "unsupported_for_mode"
        out[so.source_id] = ok
    return out


def status_correctness(gold, resp) -> dict[str, bool]:
    exp = gold.expected
    got_reasons = set(resp.reasons)
    by_src = {s.source_id: s.status for s in resp.sources}
    res = {
        "evidence_status": resp.evidence_status == exp.evidence_status,
        "required_reasons": set(exp.required_reasons) <= got_reasons,
        "source_status": all(by_src.get(k) == v for k, v in exp.source_status.items()),
    }
    res["all"] = all(res.values())
    return res


def leakage(gold, resp, receipt) -> list[str]:
    surfaces = json.dumps(resp.model_dump(mode="json")) + json.dumps(receipt.model_dump(mode="json"))
    return [c for c in gold.forbidden.canaries if c in surfaces]


def receipt_honest(receipt, trace) -> bool:
    return {c.source_id for c in receipt.calls} == trace.sources_attempted()


def evidence_precision(gold, resp) -> float | None:
    """M0 approximation: tokens of units that cover any gold span / all returned evidence tokens."""
    total = sum(e.exact_token_count for e in resp.evidence)
    if total == 0:
        return None
    spans = [s for o in gold.obligations for b in o.bundles for s in b.spans]
    spans += [s for r in gold.relations for s in r.witness_a.spans + r.witness_b.spans]
    useful = sum(e.exact_token_count for e in resp.evidence if any(_span_covered(s, [e]) for s in spans))
    return useful / total


@dataclass
class CaseScore:
    case_id: str
    recall: float | None
    complete_support: bool | None
    harmful_omission: bool | None
    silent_omission: bool
    conflict_witnesses: float | None
    false_conflicts: int
    ambiguity_handled: bool | None
    false_ambiguity: bool | None
    mandatory: dict
    status: dict
    wrong_entity: list
    leaks: list
    within_budget: bool
    receipt_honest: bool
    precision: float | None
    sources_attempted: int
    tokens_used: int
    tokens_recounted: int | None = None
    gates_failed: list = field(default_factory=list)
    safe_grounded_success: bool = False


def score_case(gold: GoldCase, resp: EvidenceResponse, receipt: Receipt, trace: ObservedTrace) -> CaseScore:
    if resp.request_id != gold.request.request_id or trace.request_id != gold.request.request_id:
        raise ValueError("response/trace do not belong to this case")
    missing = missing_obligations(gold, resp) if gold.answerable else []
    s = CaseScore(
        case_id=gold.case_id,
        recall=necessary_evidence_recall(gold, resp),
        complete_support=(None if not gold.answerable else (not missing and (conflict_witnesses_kept(gold, resp) in (None, 1.0)))),
        harmful_omission=harmful_omission(gold, resp),
        silent_omission=silent_omission(gold, resp),
        conflict_witnesses=conflict_witnesses_kept(gold, resp),
        false_conflicts=false_conflict_flags(gold, resp),
        ambiguity_handled=ambiguity_handled(gold, resp, receipt),
        false_ambiguity=false_ambiguity(gold, resp),
        mandatory=mandatory_source_compliance(gold, resp, trace),
        status=status_correctness(gold, resp),
        wrong_entity=wrong_entity_activations(gold, receipt),
        leaks=leakage(gold, resp, receipt),
        within_budget=_within_budget(resp, gold),
        receipt_honest=receipt_honest(receipt, trace),
        precision=evidence_precision(gold, resp),
        sources_attempted=len(trace.sources_attempted()),
        tokens_used=resp.budget.used,
        tokens_recounted=evidence_tokens(resp),
    )
    # Safety/contract gates are pass/fail; never averaged away by quality.
    if s.leaks:
        s.gates_failed.append("confidentiality")
    if s.wrong_entity:
        s.gates_failed.append("wrong_entity_activation")
    if not s.within_budget:
        s.gates_failed.append("budget")
    if not s.receipt_honest:
        s.gates_failed.append("receipt_honesty")
    if not all(s.mandatory.values()):
        s.gates_failed.append("mandatory_source")
    if any(c.audience_valid is False for c in trace.calls):
        s.gates_failed.append("audience")

    ok = not s.gates_failed and s.status["all"] and not s.silent_omission
    if gold.interpretation_policy != InterpretationPolicy.unique:
        ok = ok and bool(s.ambiguity_handled)
    else:
        ok = ok and not s.false_ambiguity
    if gold.answerable:
        obtainable_missing = [o for o in missing if o.obtainable]
        ok = ok and not obtainable_missing and s.conflict_witnesses in (None, 1.0)
    s.safe_grounded_success = ok
    return s
