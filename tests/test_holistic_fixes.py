"""Regression tests for the defects reproduced in docs/reviews/hld-holistic-review.md.
(Protocol validation and the call limit are in tests/test_system_one_providers.py.)"""
from pathlib import Path
from types import SimpleNamespace

import yaml

from sanctum_contracts import EvidenceStatus
from sanctum_ref.assembly import WITNESS_OMITTED, assemble, finish
from sanctum_ref.pipeline import Retriever
from sanctum_ref.registry import HubManifest, SearchSpec, load_registry
from sanctum_ref.resolution import compatible
from tests.test_round3_decisions import _prepared
from tests.test_sanctum_ref import _candidate

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = load_registry(ROOT / "owners" / "manifests")


def _ids(pair):
    a, b, _ = pair
    return frozenset((a.unit.evidence_id, b.unit.evidence_id))


def test_conflict_record_kept_when_witnesses_do_not_fit():
    """A rule-flagged pair keeps its record at every budget; each witness is packed or omitted
    with an explicit reason, and a missing witness marks the response truncated."""
    prepared = _prepared()
    flagged = {_ids(pair) for pair in prepared.flagged}
    partial_seen = False
    for budget in range(40, 900, 10):
        assembled = finish(prepared, budget, "cl100k_base")
        records = {frozenset((c.a, c.b)) for c in assembled.conflicts}
        assert flagged <= records, budget
        packed = {unit.evidence_id for unit in assembled.evidence}
        omitted = {entry.ref_id: entry.reason for entry in assembled.omitted}
        for pair in flagged:
            for witness in pair:
                assert witness in packed or omitted.get(witness) == WITNESS_OMITTED, (budget, witness)
            if not pair <= packed:
                partial_seen = True
                assert assembled.truncated_relevant
    assert partial_seen, "fixture must include a budget where a witness does not fit"


def test_d6_promotion_never_displaces_a_rules_packed_unit():
    prepared = _prepared()
    for budget in range(40, 900, 10):
        rules = {unit.evidence_id for unit in finish(prepared, budget, "cl100k_base").evidence}
        promoted = finish(prepared, budget, "cl100k_base", list(prepared.pair_candidates))
        assert rules <= {unit.evidence_id for unit in promoted.evidence}, budget
        records = {frozenset((c.a, c.b)) for c in promoted.conflicts}
        assert {_ids(pair) for pair in prepared.pair_candidates} <= records


def test_selector_values_compare_by_equality_unless_prefix_declared():
    assert compatible("1", "10") is None and compatible("10", "1") is None       # was merged to "10"
    assert compatible("payments", "payments") == "payments"
    assert compatible("skills/payments/", "skills/", prefix=True) == "skills/payments/"
    assert compatible("skills/a/", "skills/b/", prefix=True) is None
    assert SearchSpec(tool="t").filter_semantics == "equality"


def test_only_skillhub_declares_prefix_filters():
    manifests = ROOT / "owners" / "manifests"
    semantics = {path.stem: HubManifest.model_validate(yaml.safe_load(path.read_text())).search.filter_semantics
                 for path in manifests.glob("*.yaml")}
    assert semantics["skillhub"] == "prefix"
    assert all(value == "equality" for hub, value in semantics.items() if hub != "skillhub")


def _status_with_gap(units, needed):
    assembled = assemble(units, ("retry", "payment"), needed, 4000, "cl100k_base", common=True, dedup_exact=True)
    covered = Retriever._gap_covered(SimpleNamespace(registry=REGISTRY), assembled, {"skillhub"}, needed)
    return Retriever._status(assembled, False, True, gap_covered=covered)


def test_missing_required_source_is_insufficient_without_evidence_for_the_requested_facts():
    """Ex. 9 / Q16: SkillHub (procedure) is missing. Reference material alone leaves nothing
    obtainable for the requested facts: insufficient. Implementation evidence for a requested
    fact remains: partial (FX-20)."""
    reference = _candidate("dochub", "d1", "Retry payment calls at most 7 times.\n", version="v1", location="space:RISK")
    code = _candidate("codehub", "c1", "// repo:payments\nclass PaymentRetry { MAX_RETRIES = 5; }\n")
    assert _status_with_gap([reference], frozenset({"procedure"})) == EvidenceStatus.insufficient
    assert _status_with_gap([reference, code], frozenset({"procedure", "implementation"})) == EvidenceStatus.partial


def test_absent_version_stays_null_not_the_string_none():
    from sanctum_ref.adapters import evidence_unit, native_ref
    manifest = REGISTRY.manifest("incidenthub")
    artifact = {"artifact_id": "inc-1", "text": "Retry storm on payments.", "location": "queue:PAY"}
    unit = evidence_unit(manifest, artifact, "ev-1", "2026-01-01T00:00:00Z", "cl100k_base", frozenset())
    assert unit.source_version is None and native_ref(artifact) == "queue:PAY"
    assert "None" not in unit.model_dump_json()
    versioned = evidence_unit(manifest, {**artifact, "version": 3}, "ev-2", "2026-01-01T00:00:00Z", "cl100k_base",
                              frozenset())
    assert versioned.source_version == "3" and versioned.native_ref == "queue:PAY@3"


def test_name_visibility_checks_the_terms_own_permission_before_places():
    """A skillhub term in the Payments namespace is not visible to a caller without a payments
    group, even when the entity is readable through another hub's places; a term whose source
    declares no places for its namespace (catalog) falls back to places."""
    from sanctum_ref.memory import Denotation
    from sanctum_ref.resolution import entity_visible, term_permission
    assert term_permission(REGISTRY, "skillhub", "Payments", {"payments-eng"}) is True
    assert term_permission(REGISTRY, "skillhub", "Payments", {"identity-eng"}) is False
    assert term_permission(REGISTRY, "catalog", "payments", {"identity-eng"}) is None

    class Store:
        def places_for(self, entity_id):
            from sanctum_ref.memory import PlaceRecord
            return [PlaceRecord(source="codehub", filter="repo", value="payments/auth", place="repo:payments/auth",
                                selects_for=entity_id, status="accepted", version=1, reviewed_by="x")]

    skill_term = Denotation("ent-1", "skillhub", "Payments", "payment auth", "ref")
    catalog_term = Denotation("ent-1", "catalog", "payments", "payment auth", "ref")
    code_reader = {"payments-code"}                  # reads repo:payments/, holds no skillhub group
    assert entity_visible(Store(), REGISTRY, "ent-1", code_reader) is True             # places, as before
    assert entity_visible(Store(), REGISTRY, "ent-1", code_reader, skill_term) is False
    assert entity_visible(Store(), REGISTRY, "ent-1", code_reader, catalog_term) is True


def test_round3_binding_none_matches_only_the_v1_layout(tmp_path):
    """Design §8: a Round 3 binding with descriptor_release "none" was fitted on the v1 pointer
    layout and must not apply to answers read on any other layout."""
    from sanctum_ref.providers.http_systemone import Calibration
    binding = {"provider": "p", "model": "m", "decision": "d6", "template": "t", "descriptor_release": "none"}
    path = tmp_path / "c.yaml"
    path.write_text(yaml.safe_dump({"binding": binding, "platt": {"a": 1.0, "b": 0.0},
                                    "bands": {"use": 0.6, "skip": 0.0}}))
    calibration = Calibration(path)
    assert calibration.matches("p", "m", "none", "t") and calibration.matches("p", "m", None, "t")
    assert not calibration.matches("p", "m", "r3-state-v2", "t")
    assert not calibration.matches("p", "m", "r3-state-v2-compact-150", "t")
