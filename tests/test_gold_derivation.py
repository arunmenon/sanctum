"""Gold derivation (M1 task 5): every sample spec derives a valid M0 GoldCase with the
family-specific expectations, and checked-in gold/m1 matches a fresh derivation."""
import json
from pathlib import Path

import pytest
import yaml

from sanctum_eval.gold import GoldCase, InterpretationPolicy
from sanctum_eval.load import load_gold
from sanctum_world.gold import BuildIndex, QuestionSpec, derive
from sanctum_world.render import build
from sanctum_world.schema import load_world

ROOT = Path(__file__).resolve().parents[1]
WORLD_DIR = ROOT / "world"
SPECS = ROOT / "questions" / "specs" / "sample"
GOLD_M1 = ROOT / "gold" / "m1"
SEED = 20260930


@pytest.fixture(scope="module")
def world():
    return load_world(WORLD_DIR / "world.yaml")


@pytest.fixture(scope="module")
def build_dir(tmp_path_factory) -> Path:
    out_dir = tmp_path_factory.mktemp("gold") / "world"
    build(WORLD_DIR, SEED, out_dir)
    return out_dir


@pytest.fixture(scope="module")
def index(build_dir):
    return BuildIndex(build_dir)


@pytest.fixture(scope="module")
def specs() -> dict[str, QuestionSpec]:
    loaded = [QuestionSpec.model_validate(yaml.safe_load(path.read_text()))
              for path in sorted(SPECS.glob("*.yaml"))]
    return {spec.family: spec for spec in loaded}


@pytest.fixture(scope="module")
def golds(world, build_dir, index, specs) -> dict[str, GoldCase]:
    return {family: derive(world, build_dir, spec, index=index) for family, spec in specs.items()}


@pytest.fixture(scope="module")
def hub_text(build_dir):
    """(artifact_id, version) -> rendered hub text."""
    texts = {}
    for path in (build_dir / "hubs").glob("*/artifacts.jsonl"):
        for line in path.read_text().splitlines():
            row = json.loads(line)
            texts[(row["artifact_id"], row.get("version"))] = row["text"]
    return texts


def _provenance(index, span):
    return next(row for row in index.provenance
                if (row["artifact_id"], row["version"], row["start"], row["end"])
                == (span.artifact_id, span.version, span.start, span.end))


def _values(index, gold, fact_kind=None):
    return {_provenance(index, span)["value"]
            for obligation in gold.obligations for bundle in obligation.bundles for span in bundle.spans
            if fact_kind is None or _provenance(index, span)["fact_kind"] == fact_kind}


def test_ten_specs_cover_every_family(specs):
    assert len(list(SPECS.glob("*.yaml"))) == 10
    assert set(specs) == {
        "named_service", "hub_specific_name", "same_name_two_meanings", "historical",
        "conflicting_sources", "verify_claim", "vague", "no_source", "multi_hub", "restricted_content"}


def test_every_case_validates_and_request_id_is_opaque(golds):
    for family, gold in golds.items():
        GoldCase.model_validate(gold.model_dump(mode="json"))
        request_id = gold.request.request_id
        assert gold.case_id not in request_id and family not in request_id
        assert request_id.startswith("req-") and len(request_id) == 20


def test_every_span_renders_its_value(golds, index, hub_text):
    for gold in golds.values():
        spans = [span for obligation in gold.obligations for bundle in obligation.bundles for span in bundle.spans]
        spans += [span for relation in gold.relations
                  for span in relation.witness_a.spans + relation.witness_b.spans]
        for span in spans:
            text = hub_text[(span.artifact_id, span.version)]
            assert text[span.start:span.end] == _provenance(index, span)["value_text"]


def test_checked_in_gold_matches_derivation(golds):
    for gold in golds.values():
        stored = load_gold(GOLD_M1 / f"{gold.case_id}.yaml")
        assert stored == gold


def test_homonym_separates_alternatives(golds, index):
    gold = golds["same_name_two_meanings"]
    assert gold.interpretation_policy == InterpretationPolicy.separate_alternatives
    assert len(gold.interpretations) == 2
    covered = {obligation.interpretation_id for obligation in gold.obligations}
    assert covered == {interpretation.interpretation_id for interpretation in gold.interpretations}


def test_hub_specific_name_excludes_homonym_sibling(golds, index):
    gold = golds["hub_specific_name"]
    identity_ref = index.entity_refs["svc.identity-auth"]
    assert gold.interpretation_policy == InterpretationPolicy.unique
    assert gold.forbidden.wrong_entities == [identity_ref]
    assert gold.interpretations[0].entity_ref == index.entity_refs["svc.payment-auth"]


def test_historical_r40_yields_three(golds, index):
    gold = golds["historical"]
    assert _values(index, gold, "implemented") == {3}
    # one version_difference per code artifact asserting the value at both R40 and R42
    assert gold.relations
    assert {relation.relation_type.value for relation in gold.relations} == {"version_difference"}
    capability_gaps = {source.source_id for source in gold.source_obligations
                       if source.expected.value == "capability_gap"}
    assert "dochub" in capability_gaps


def test_conflict_is_policy_implementation_divergence(golds, index):
    gold = golds["conflicting_sources"]
    assert _values(index, gold, "implemented") == {5}
    assert _values(index, gold, "procedure") == {3}
    assert [relation.relation_type.value for relation in gold.relations] == ["policy_implementation_divergence"]
    assert any(source.source_id == "skillhub" and source.mandatory for source in gold.source_obligations)


def test_verify_claim_prod_not_experiment(golds, index):
    gold = golds["verify_claim"]
    assert _values(index, gold) == {5}
    relation = gold.relations[0]
    assert relation.relation_type.value == "environment_difference"
    assert _provenance(index, relation.witness_b.spans[0])["value"] == 7


def test_vague_asks_for_clarification(golds):
    gold = golds["vague"]
    assert gold.interpretation_policy == InterpretationPolicy.clarify
    assert "ambiguous_term" in gold.expected.required_reasons


def test_coverage_gap_is_unanswerable(golds):
    gold = golds["no_source"]
    assert gold.answerable is False
    assert gold.obligations == []
    assert gold.expected.evidence_status.value == "insufficient"


def test_multi_hub_needs_code_and_doc(golds):
    gold = golds["multi_hub"]
    hubs_per_obligation = [{span.source_id for bundle in obligation.bundles for span in bundle.spans}
                           for obligation in gold.obligations]
    assert any("codehub" in hubs for hubs in hubs_per_obligation)
    assert any(hubs == {"dochub"} for hubs in hubs_per_obligation)


def test_restricted_has_canaries_and_no_restricted_spans(golds, index):
    gold = golds["restricted_content"]
    assert set(gold.forbidden.canaries) == {"CANARY-INC-4417", "CANARY-INC-9023"}
    assert gold.answerable is False
    restricted_ids = {canary["artifact_id"] for canary in index.canaries}
    for case in golds.values():
        for obligation in case.obligations:
            for bundle in obligation.bundles:
                assert not {span.artifact_id for span in bundle.spans} & restricted_ids


def test_exact_duplicates_are_alternative_bundles(world, build_dir, index):
    spec = QuestionSpec(id="t-dup", family="named_service", principal="kestrel-payments",
                        text="What is the payment auth backoff schedule?",
                        entities=["svc.payment-auth"], attributes=["backoff_schedule_ms"])
    gold = derive(world, build_dir, spec, index=index)
    assert len(gold.obligations) == 1
    bundle_hubs = sorted(bundle.spans[0].source_id for bundle in gold.obligations[0].bundles)
    assert bundle_hubs == ["codehub", "dochub"]


def test_denied_source_makes_obligation_unobtainable(world, build_dir, index):
    spec = QuestionSpec(id="t-denied", family="named_service", principal="kestrel-identity",
                        text="How many retries does the payment auth procedure allow?",
                        entities=["svc.payment-auth"], attributes=["max_retries"])
    gold = derive(world, build_dir, spec, index=index)
    # the shared composite skill is readable, so the procedure stays obtainable; code is denied
    implemented = [o for o in gold.obligations if _provenance(index, o.bundles[0].spans[0])["fact_kind"] == "implemented"]
    assert implemented and not implemented[0].obtainable
    assert gold.expected.evidence_status.value == "partial"
    assert "required_source_denied" in gold.expected.required_reasons


def _spec(**fields) -> QuestionSpec:
    base = {"id": "t-adhoc", "family": "named_service", "text": "ad hoc question"}
    return QuestionSpec(**{**base, **fields})


def test_relations_only_cite_obtainable_witnesses(world, build_dir, index):
    gold = derive(world, build_dir, _spec(principal="kestrel-identity", entities=["svc.payment-auth"],
                                          attributes=["max_retries"]), index=index)
    assert any(not obligation.obtainable for obligation in gold.obligations)
    assert gold.relations == []
    assert "required_source_denied" in gold.expected.required_reasons


def test_partially_covered_query_is_partial(world, build_dir, index):
    gold = derive(world, build_dir, _spec(principal="kestrel-both",
                                          entities=["svc.gateway-edge", "svc.fx-quote"],
                                          attributes=["upstream_timeout_ms", "quote_ttl_seconds"],
                                          expected_ambiguity="unique"), index=index)
    assert gold.answerable is True
    assert gold.expected.evidence_status.value == "partial"
    assert "no_coverage" in gold.expected.required_reasons


def test_historical_ignores_sources_without_version_reads(world, build_dir, index):
    gold = derive(world, build_dir, _spec(principal="kestrel-payments", as_of="R41",
                                          entities=["svc.ledger-post"], attributes=["batch_size"]),
                  index=index)
    hubs = {span.source_id for obligation in gold.obligations
            for bundle in obligation.bundles for span in bundle.spans}
    assert "memoryhub" not in hubs and "codehub" in hubs
    gaps = {source.source_id for source in gold.source_obligations if source.expected.value == "capability_gap"}
    assert "memoryhub" in gaps


def test_restricted_reader_gets_restricted_evidence(world, build_dir, index):
    gold = derive(world, build_dir, _spec(principal="admin-probe", entities=["svc.payment-auth"],
                                          attributes=["root_cause"], fact_kinds=["incident"]), index=index)
    assert gold.answerable is True
    assert gold.expected.evidence_status.value == "sufficient"
    assert gold.forbidden.canaries == []


def test_fact_not_yet_applicable_is_skipped(world, build_dir, index):
    gold = derive(world, build_dir, _spec(principal="kestrel-identity", as_of="R40",
                                          entities=["svc.identity-auth"], attributes=["max_retries"]),
                  index=index)
    kinds = {_provenance(index, o.bundles[0].spans[0])["fact_kind"] for o in gold.obligations}
    assert kinds == {"implemented"}
    assert gold.expected.evidence_status.value == "sufficient"
