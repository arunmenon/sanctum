"""D6 challenge slice (prompt review, measurement changes): rule-missed relations and hard
negatives added to the world after E3. Evaluator side: gold is derived and frozen here, and a
rules-only C4 run with D6 in shadow (local test provider) shows the slice is discriminative, i.e.
its positives reach D6 as promotable candidates rather than rule-flagged pairs."""
import json
import os
from pathlib import Path

import pytest
import yaml

from sanctum_eval.calibration_labels import d6_pair_label
from sanctum_eval.load import load_gold
from sanctum_run.process_sut import ProcessSUT
from sanctum_run.runner import RunConfig, run
from sanctum_world.gold import BuildIndex, QuestionSpec, derive
from sanctum_world.schema import load_world
from tests.helpers.systemone_server import ServerBehavior, SystemOneTestServer
from tests.scenarios.conftest import scenario_world  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
SPECS = ROOT / "questions" / "specs" / "challenge-d6"
GOLD = ROOT / "gold" / "challenge-d6"


def _golds():
    return {gold.case_id: gold for gold in (load_gold(p) for p in sorted(GOLD.glob("*.yaml")))}


def _pair(relation):
    return frozenset({relation.witness_a.spans[0].artifact_id, relation.witness_b.spans[0].artifact_id})


def test_slice_gold_is_frozen_and_counts(scenario_world):  # noqa: F811
    world, index = load_world(ROOT / "world" / "world.yaml"), BuildIndex(scenario_world)
    golds = _golds()
    for path in sorted(SPECS.glob("*.yaml")):
        spec = QuestionSpec.model_validate(yaml.safe_load(path.read_text()))
        assert load_gold(GOLD / f"{spec.id}.yaml") == derive(world, scenario_world, spec, index=index)
    positives = {_pair(r) for g in golds.values() for r in g.relations}
    assert len(golds) == 12 and len(positives) == 20
    assert any(p.kind == "rule_missed_relation" for p in world.planted)


@pytest.fixture(scope="module")
def shadow_run(scenario_world, tmp_path_factory):  # noqa: F811
    with SystemOneTestServer(ServerBehavior()) as server:
        previous = os.environ.get("SANCTUM_SYSTEMONE_TEST_URL")
        os.environ["SANCTUM_SYSTEMONE_TEST_URL"] = server.base_url
        try:
            result = run(ProcessSUT(["--config", "C4", "--round3", "d6", "--round3-provider", "local-test"]), RunConfig(
                cases_dir=GOLD, out_dir=tmp_path_factory.mktemp("d6-challenge") / "run", seed=20260930, sut_name="ref",
                config_id="C4+D6", world_build_dir=scenario_world, system_one_provider="local-test",
                system_one_profile="relaxed"))
        finally:
            if previous is None:
                os.environ.pop("SANCTUM_SYSTEMONE_TEST_URL", None)
            else:
                os.environ["SANCTUM_SYSTEMONE_TEST_URL"] = previous
    return result


def test_positives_reach_d6_as_candidates_not_rule_flags(shadow_run):
    golds = {g.request.request_id: g for g in _golds().values()}
    positives = {_pair(r) for g in golds.values() for r in g.relations}
    candidate_pos, flagged_pos, candidate_neg = set(), set(), set()
    for line in (shadow_run.out_dir / "receipts.jsonl").read_text().splitlines():
        receipt = json.loads(line)
        gold = golds[receipt["request_id"]]
        for decision in receipt["decisions"]:
            value = decision.get("value")
            if not isinstance(value, dict) or not str(value.get("item", "")).startswith("d6:"):
                continue
            refs = value.get("refs") or [value["a"], value["b"]]
            key = frozenset({refs[0]["artifact_id"], refs[1]["artifact_id"]})
            if d6_pair_label(gold, refs[0], refs[1]):
                (flagged_pos if value.get("rule_flagged") else candidate_pos).add(key)
            elif not value.get("rule_flagged"):
                candidate_neg.add(key)
    assert len(candidate_pos) * 2 >= len(positives)          # at least half exposed to D6 as candidates
    assert len(candidate_pos) > len(flagged_pos)              # the rules miss most of them
    assert len(candidate_neg) >= 15                           # hard negatives the rules also surface
