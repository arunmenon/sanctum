"""Renderer: exact spans, hub-visible allowlist, determinism, scale, no leaks (M1 task 3)."""
import json
from pathlib import Path

import pytest

from sanctum_world.filler import load_filler
from sanctum_world.render import HUB_VISIBLE_KEYS, build, build_vocabulary
from sanctum_world.schema import PLANTED_KINDS, load_world

ROOT = Path(__file__).resolve().parents[1]
WORLD_DIR = ROOT / "world"
SEED = 20260930
OTHER_SEED = 11


@pytest.fixture(scope="module")
def builds(tmp_path_factory):
    base = tmp_path_factory.mktemp("world")
    build(WORLD_DIR, SEED, base / "first")
    build(WORLD_DIR, SEED, base / "second")
    build(WORLD_DIR, OTHER_SEED, base / "other")
    return base


@pytest.fixture(scope="module")
def out(builds) -> Path:
    return builds / "first"


@pytest.fixture(scope="module")
def world():
    return load_world(WORLD_DIR / "world.yaml")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines()]


def hub_rows(out_dir: Path) -> dict[str, list[dict]]:
    return {path.parent.name: read_jsonl(path) for path in sorted((out_dir / "hubs").glob("*/artifacts.jsonl"))}


def private(out_dir: Path, name: str):
    return json.loads((out_dir / "private" / name).read_text())


def test_provenance_spans_slice_exactly(out, world):
    rows = {(row["artifact_id"], row["version"]): row for rows in hub_rows(out).values() for row in rows}
    provenance = read_jsonl(out / "private" / "provenance.jsonl")
    assert provenance
    for record in provenance:
        text = rows[(record["artifact_id"], record["version"])]["text"]
        assert text[record["start"]:record["end"]] == record["value_text"] == str(record["value"])


def test_hub_rows_use_only_allowlisted_keys(out):
    for hub, rows in hub_rows(out).items():
        for row in rows:
            assert tuple(sorted(row)) == HUB_VISIBLE_KEYS, (hub, sorted(row))


def test_same_seed_builds_are_byte_identical(builds):
    first = (builds / "first" / "manifest.json").read_bytes()
    assert first == (builds / "second" / "manifest.json").read_bytes()
    for relative in json.loads(first)["files"]:
        assert (builds / "first" / relative).read_bytes() == (builds / "second" / relative).read_bytes()


def test_other_seed_changes_filler_but_not_core_provenance(builds):
    first, other = builds / "first", builds / "other"
    for name in ("provenance.jsonl", "entity_refs.json", "canaries.json", "planted_index.json",
                 "artifact_map.json"):
        assert (first / "private" / name).read_bytes() == (other / "private" / name).read_bytes(), name
    assert (first / "hubs" / "codehub" / "artifacts.jsonl").read_bytes() != \
        (other / "hubs" / "codehub" / "artifacts.jsonl").read_bytes()
    first_manifest = json.loads((first / "manifest.json").read_text())
    other_manifest = json.loads((other / "manifest.json").read_text())
    assert first_manifest["total_artifacts"] == other_manifest["total_artifacts"]


def test_scale_and_held_back_incidenthub(out):
    manifest = json.loads((out / "manifest.json").read_text())
    assert 2700 <= manifest["total_artifacts"] <= 3300
    assert manifest["held_back_hubs"] == ["incidenthub"]
    assert manifest["counts"]["incidenthub"]["held_back"] is True
    assert manifest["counts"]["incidenthub"]["artifacts"] > 0
    distinct = {hub: len({row["artifact_id"] for row in rows}) for hub, rows in hub_rows(out).items()}
    assert {hub: manifest["counts"][hub]["artifacts"] for hub in distinct} == distinct


def test_no_private_identifiers_in_hub_output(out, world):
    entity_refs = private(out, "entity_refs.json")
    planted = private(out, "planted_index.json")
    tokens = ({fact.id for fact in world.facts} | set(entity_refs) | set(entity_refs.values())
              | set(planted) | {artifact.id for artifact in world.artifacts})
    for path in sorted((out / "hubs").glob("*/artifacts.jsonl")):
        content = path.read_text()
        for token in tokens:
            assert token not in content, f"{token} leaked into {path.name} of {path.parent.name}"


def test_canaries_only_inside_their_restricted_artifacts(out):
    canaries = private(out, "canaries.json")
    assert canaries
    for hub, rows in hub_rows(out).items():
        for row in rows:
            blob = json.dumps(row)
            for entry in canaries:
                if entry["token"] in blob:
                    assert row["artifact_id"] == entry["artifact_id"]
                    assert row["acl"] == ["restricted-incidents"]


def test_hubs_only_use_their_own_vocabulary(out, world):
    vocabulary = build_vocabulary(world, load_filler(WORLD_DIR / "filler.yaml"))
    for hub, rows in hub_rows(out).items():
        foreign = vocabulary.undeclared_for(hub)
        for row in rows:
            visible = " ".join(str(row[key] or "") for key in ("text", "title", "path", "location"))
            for native in foreign:
                assert native not in visible, (hub, row["artifact_id"], native)


def test_planted_situations_are_all_realised(out):
    planted = private(out, "planted_index.json")
    assert sorted(entry["kind"] for entry in planted.values()) == sorted(set(PLANTED_KINDS) - {"rule_missed_relation"})
    for planted_id, entry in planted.items():
        if entry["kind"] == "coverage_gap":
            assert entry["details"]["gap_facts"]
        else:
            assert entry["artifact_ids"], planted_id


def _core_rows(out, world_artifact_id):
    artifact_map = private(out, "artifact_map.json")[world_artifact_id]
    rows = hub_rows(out)[artifact_map["hub"]]
    return [row for row in rows if row["artifact_id"] == artifact_map["artifact_id"]]


def test_version_branching_values(out):
    provenance = read_jsonl(out / "private" / "provenance.jsonl")
    values = {record["version"]: record["value"] for record in provenance
              if record["world_artifact_id"] == "a.code.retryconfig"}
    assert values == {"R40": 3, "R41": 3, "R42": 5, "exp-branch": 7}
    exp_row = [row for row in _core_rows(out, "a.code.retryconfig") if row["version"] == "exp-branch"][0]
    assert exp_row["environment"] == "experiment"
    assert exp_row["metadata"]["revision"] == 4          # newer than the applicable R42 row


def test_exact_duplicate_is_byte_identical_across_hubs(out):
    doc_rows = _core_rows(out, "a.doc.retry-policy")
    code_rows = _core_rows(out, "a.code.retry-policy-copy")
    assert len(doc_rows) == len(code_rows) == 1
    assert doc_rows[0]["text"] == code_rows[0]["text"]
    assert doc_rows[0]["artifact_id"] != code_rows[0]["artifact_id"]


def test_space_without_version_reads_has_one_current_version(out):
    rows = [row for row in hub_rows(out)["dochub"] if row["location"] == "space:PA"]
    assert rows
    assert all(row["version"] == "current" for row in rows)
    assert len({row["artifact_id"] for row in rows}) == len(rows)


def test_injection_and_coverage_gap(out, world):
    planted = private(out, "planted_index.json")
    instruction = planted["p.dochub-injection"]["details"]["instruction"]
    assert instruction in _core_rows(out, "a.doc.injection")[0]["text"]
    provenance = read_jsonl(out / "private" / "provenance.jsonl")
    assert not [record for record in provenance if record["entity_id"] == "svc.fx-quote"]


def test_only_core_artifacts_assert_facts(out, world):
    core = {artifact.id for artifact in world.artifacts}
    provenance = read_jsonl(out / "private" / "provenance.jsonl")
    assert {record["world_artifact_id"] for record in provenance} <= core
    asserted = {record["fact_id"] for record in provenance}
    gap_entities = {planted.entity for planted in world.planted if planted.kind == "coverage_gap"}
    for fact in world.facts:
        assert (fact.id in asserted) != (fact.entity in gap_entities), fact.id
