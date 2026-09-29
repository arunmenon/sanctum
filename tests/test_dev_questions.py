"""M3 dev question set and scenario cases: plan §8.2 family counts, every checked-in gold case
matches a fresh derivation and validates, request ids are opaque, and the family x principal
coverage the SUT will be scored on actually exists."""
import re
from collections import Counter
from pathlib import Path

import pytest
import yaml

from sanctum_eval.load import load_gold
from sanctum_world.gold import FAMILIES, BuildIndex, QuestionSpec, derive
from sanctum_world.render import build
from sanctum_world.schema import load_world

ROOT = Path(__file__).resolve().parents[1]
DEV_SPECS = ROOT / "questions" / "specs" / "dev"
SCENARIO_SPECS = ROOT / "questions" / "specs" / "scenarios"
GOLD_DEV = ROOT / "gold" / "dev"
GOLD_SCENARIOS = ROOT / "gold" / "scenarios"
SCENARIO_CASES = ROOT / "docs" / "scenario-cases.yaml"
SEED = 20260930

DEV_FAMILY_COUNTS = {
    "named_service": 10, "hub_specific_name": 8, "same_name_two_meanings": 6, "historical": 6,
    "conflicting_sources": 6, "verify_claim": 4, "vague": 4, "no_source": 6, "multi_hub": 6,
    "restricted_content": 4,
}
M3_SCENARIOS = {"EX-01", "EX-02", "EX-03", "EX-04", "EX-06", "EX-07", "EX-08", "EX-09", "EX-10", "FX-24"}
M4_SCENARIOS = {"EX-05", "EX-09b", "EX-15", "FX-16", "FX-17", "FX-18", "FX-19", "FX-20", "FX-21",
                "FX-22", "FX-23"}
SCRIPT_ONLY = {"FX-18", "FX-22"}
CODE_ONLY = "kestrel-codeonly"


def _load_specs(directory: Path) -> dict[str, QuestionSpec]:
    return {spec.id: spec for spec in (
        QuestionSpec.model_validate(yaml.safe_load(path.read_text()))
        for path in sorted(directory.glob("*.yaml")))}


@pytest.fixture(scope="module")
def world():
    return load_world(ROOT / "world" / "world.yaml")


@pytest.fixture(scope="module")
def index(tmp_path_factory):
    out_dir = tmp_path_factory.mktemp("dev") / "world"
    build(ROOT / "world", SEED, out_dir)
    return out_dir, BuildIndex(out_dir)


@pytest.fixture(scope="module")
def dev_specs():
    return _load_specs(DEV_SPECS)


@pytest.fixture(scope="module")
def scenario_specs():
    return _load_specs(SCENARIO_SPECS)


@pytest.fixture(scope="module")
def dev_golds(world, index, dev_specs):
    build_dir, build_index = index
    return {case_id: derive(world, build_dir, spec, index=build_index) for case_id, spec in dev_specs.items()}


def test_dev_set_size_and_family_counts(dev_specs):
    assert set(DEV_FAMILY_COUNTS) == set(FAMILIES)
    assert len(dev_specs) == 60
    assert Counter(spec.family for spec in dev_specs.values()) == Counter(DEV_FAMILY_COUNTS)


def test_spec_ids_match_file_names():
    for directory in (DEV_SPECS, SCENARIO_SPECS):
        for path in directory.glob("*.yaml"):
            assert yaml.safe_load(path.read_text())["id"] == path.stem


def test_checked_in_dev_gold_matches_derivation(dev_golds):
    assert {path.stem for path in GOLD_DEV.glob("*.yaml")} == set(dev_golds)
    for case_id, gold in dev_golds.items():
        assert load_gold(GOLD_DEV / f"{case_id}.yaml") == gold


def test_checked_in_scenario_gold_matches_derivation(world, index, scenario_specs):
    build_dir, build_index = index
    assert {path.stem for path in GOLD_SCENARIOS.glob("*.yaml")} == set(scenario_specs)
    for case_id, spec in scenario_specs.items():
        assert load_gold(GOLD_SCENARIOS / f"{case_id}.yaml") == derive(world, build_dir, spec, index=build_index)


def test_request_ids_are_opaque_and_unique(dev_golds, index):
    _, build_index = index
    private_terms = set(build_index.entity_refs) | set(build_index.artifact_map) | {
        gold.case_id for gold in dev_golds.values()}
    request_ids = [gold.request.request_id for gold in dev_golds.values()]
    assert len(set(request_ids)) == len(request_ids)
    for request_id in request_ids:
        assert re.fullmatch(r"req-[0-9a-f]{16}", request_id)
        assert not any(term in request_id for term in private_terms)


def test_dev_texts_are_varied(dev_specs):
    texts = [spec.text for spec in dev_specs.values()]
    assert len(set(texts)) == len(texts)


def test_every_family_has_mixed_principals(dev_specs):
    principals_by_family: dict[str, set[str]] = {}
    for spec in dev_specs.values():
        principals_by_family.setdefault(spec.family, set()).add(spec.principal)
    for family, principals in principals_by_family.items():
        assert len(principals) >= 2, family


def test_every_world_principal_asks_dev_questions(world, dev_specs):
    assert {spec.principal for spec in dev_specs.values()} == {principal.id for principal in world.principals}


def test_code_only_principal_gets_required_source_denied(dev_golds):
    code_only = [gold for gold in dev_golds.values() if gold.principal == CODE_ONLY]
    denied_families = {gold.family for gold in code_only
                       if "required_source_denied" in gold.expected.required_reasons}
    assert {"named_service", "hub_specific_name", "historical", "conflicting_sources"} <= denied_families
    for gold in code_only:
        if "required_source_denied" in gold.expected.required_reasons:
            assert any(not obligation.obtainable for obligation in gold.obligations)
            assert any(outcome.source_id == "skillhub" and outcome.expected.value == "denied_gap"
                       for outcome in gold.source_obligations)


def test_family_outcomes(dev_golds):
    by_family: dict[str, list] = {}
    for gold in dev_golds.values():
        by_family.setdefault(gold.family, []).append(gold)
    assert all(not gold.answerable for gold in by_family["no_source"])
    assert all("ambiguous_term" in gold.expected.required_reasons for gold in by_family["vague"])
    assert any(len(gold.interpretations) == 2 for gold in by_family["same_name_two_meanings"])
    assert all(gold.request.as_of for gold in by_family["historical"])
    restricted = by_family["restricted_content"]
    assert any(gold.answerable for gold in restricted) and any(not gold.answerable for gold in restricted)
    assert all(gold.forbidden.canaries for gold in restricted if not gold.answerable)


def test_scenario_mapping_covers_m3_and_m4_scenarios(scenario_specs):
    document = yaml.safe_load(SCENARIO_CASES.read_text())
    mapping = document["scenarios"]
    assert set(mapping) == M3_SCENARIOS | M4_SCENARIOS
    assert {scenario for scenario, case_ids in mapping.items() if not case_ids} == SCRIPT_ONLY
    assert M4_SCENARIOS <= set(document["scripts"])
    mapped = [case_id for case_ids in mapping.values() for case_id in case_ids]
    assert sorted(mapped) == sorted(scenario_specs)
