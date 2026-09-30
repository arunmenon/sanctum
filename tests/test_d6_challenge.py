"""D6 challenge slice (prompt review, measurement changes): rule-missed relations and hard
negatives in the overlay world/challenge-d6.yaml (built into its own build dir, never build/world). Evaluator side: gold is derived and frozen here, and a
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
from sanctum_world.render import build

ROOT = Path(__file__).resolve().parents[1]
SPECS = ROOT / "questions" / "specs" / "challenge-d6"
OVERLAY = ROOT / "world" / "challenge-d6.yaml"
GOLD = ROOT / "gold" / "challenge-d6"


def _golds():
    return {gold.case_id: gold for gold in (load_gold(p) for p in sorted(GOLD.glob("*.yaml")))}


def _pair(relation):
    return frozenset({relation.witness_a.spans[0].artifact_id, relation.witness_b.spans[0].artifact_id})


@pytest.fixture(scope="module")
def challenge_world(tmp_path_factory):
    """The base world plus the challenge overlay, built apart from build/world."""
    out = tmp_path_factory.mktemp("world-challenge") / "world"
    build(ROOT / "world", 20260930, out, overlays=(OVERLAY,))
    return out


def test_overlay_leaves_existing_gold_identical(challenge_world):
    world, index = load_world(ROOT / "world" / "world.yaml", (OVERLAY,)), BuildIndex(challenge_world)
    for directory in ("sample", "dev", "scenarios"):
        gold_dir = {"sample": "m1"}.get(directory, directory)
        for path in sorted((ROOT / "questions" / "specs" / directory).glob("*.yaml")):
            spec = QuestionSpec.model_validate(yaml.safe_load(path.read_text()))
            assert load_gold(ROOT / "gold" / gold_dir / f"{spec.id}.yaml") == derive(world, challenge_world, spec,
                                                                                    index=index), spec.id


def test_slice_gold_is_frozen_and_counts(challenge_world):
    world, index = load_world(ROOT / "world" / "world.yaml", (OVERLAY,)), BuildIndex(challenge_world)
    golds = _golds()
    for path in sorted(SPECS.glob("*.yaml")):
        spec = QuestionSpec.model_validate(yaml.safe_load(path.read_text()))
        assert load_gold(GOLD / f"{spec.id}.yaml") == derive(world, challenge_world, spec, index=index)
    positives = {_pair(r) for g in golds.values() for r in g.relations}
    assert len(golds) == 12 and len(positives) == 20
    assert any(p.kind == "rule_missed_relation" for p in world.planted)


@pytest.fixture(scope="module")
def shadow_run(challenge_world, tmp_path_factory):
    with SystemOneTestServer(ServerBehavior()) as server:
        previous = os.environ.get("SANCTUM_SYSTEMONE_TEST_URL")
        os.environ["SANCTUM_SYSTEMONE_TEST_URL"] = server.base_url
        try:
            result = run(ProcessSUT(["--config", "C4", "--round3", "d6", "--round3-provider", "local-test"]), RunConfig(
                cases_dir=GOLD, out_dir=tmp_path_factory.mktemp("d6-challenge") / "run", seed=20260930, sut_name="ref",
                config_id="C4+D6", world_build_dir=challenge_world, system_one_provider="local-test",
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


def test_overlay_only_adds_challenge_artifacts(challenge_world, tmp_path):
    """The challenge build equals a build of the pre-slice world (fd19e4f's world.yaml) plus the
    overlay's own artifacts: every existing row (id, text, version, metadata) is byte-identical."""
    import shutil
    import subprocess

    base_dir = tmp_path / "world-pre"
    shutil.copytree(ROOT / "world", base_dir, ignore=shutil.ignore_patterns("challenge-d6.yaml"))
    (base_dir / "world.yaml").write_bytes(subprocess.run(
        ["git", "show", "fd19e4f:world/world.yaml"], cwd=ROOT, capture_output=True, check=True).stdout)
    base_build = tmp_path / "base"
    build(base_dir, 20260930, base_build)

    def rows(build_dir):
        out = {}
        for path in sorted((build_dir / "hubs").glob("*/artifacts.jsonl")):
            for line in path.read_text().splitlines():
                row = json.loads(line)
                out[(path.parent.name, row["artifact_id"], row["version"])] = line
        return out

    base_rows, challenge_rows = rows(base_build), rows(challenge_world)
    assert all(challenge_rows.get(key) == line for key, line in base_rows.items())
    added = {artifact_id for _, artifact_id, _ in set(challenge_rows) - set(base_rows)}
    artifact_map = json.loads((challenge_world / "private" / "artifact_map.json").read_text())
    overlay_ids = {row["artifact_id"] for world_id, row in artifact_map.items() if world_id.startswith("a.ch.")}
    assert added == overlay_ids and len(overlay_ids) == 24
