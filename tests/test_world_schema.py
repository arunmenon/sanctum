"""World schema: minimal worlds load, dangling references fail with their path (M1 task 1)."""
import copy
from pathlib import Path

import pytest
from pydantic import ValidationError

from sanctum_world.rng import opaque_id, sub_rng
from sanctum_world.schema import PLANTED_KINDS, World, load_world, parse_assertion

ROOT = Path(__file__).resolve().parents[1]


def minimal_world() -> dict:
    return {
        "world_version": 1,
        "seed": 7,
        "principals": [{"id": "p1", "groups": ["team-a"]}],
        "entities": [{"id": "svc.one", "type": "service"}, {"id": "svc.two", "type": "service"}],
        "releases": ["R1", "R2"],
        "environments": ["prod"],
        "facts": [{"id": "f.limit", "entity": "svc.one", "fact_kind": "implemented",
                   "attribute": "limit", "values": [{"value": 3, "from": "R1", "env": "prod"}]}],
        "hubs": {
            "codehub": {"places": [{"native": "repo:one", "selects_for": "svc.one", "acl": ["team-a"]}],
                        "capabilities": {"version_reads": True}},
            "skillhub": {"names": [{"native": "One", "denotes": "svc.one"},
                                   {"native": "One", "namespace": "B", "denotes": "svc.two"}],
                         "capabilities": {"version_reads": True}},
        },
        "artifacts": [{"id": "a.code", "hub": "codehub", "kind": "java_class", "title": "One.java",
                       "place": "repo:one", "body": "LIMIT = {{fact:f.limit}};",
                       "versions": [{"ref": "R1", "env": "prod", "asserts": ["f.limit@R1/prod"]}]}],
        "planted": [{"id": "p.homonym", "kind": "homonym", "name": "One", "hub": "skillhub",
                     "entities": ["svc.one", "svc.two"]}],
    }


def test_minimal_world_loads():
    world = World.model_validate(minimal_world())
    assert world.resolve_value(parse_assertion("f.limit@R2/prod")).value == 3


def _mutated(path: list, value):
    data = copy.deepcopy(minimal_world())
    target = data
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    return data


@pytest.mark.parametrize("path,value,expected", [
    (["facts", 0, "entity"], "svc.missing", "facts[0].entity"),
    (["entities", 0, "member_of"], "domain.missing", "entities[0].member_of"),
    (["facts", 0, "values", 0, "from"], "R9", "facts[0].values[0].from"),
    (["artifacts", 0, "versions", 0, "asserts"], ["f.missing@R1"], "unknown fact"),
    (["artifacts", 0, "versions", 0, "asserts"], ["f.limit@R9"], "unknown release"),
    (["artifacts", 0, "versions", 0, "ref"], "R9", "versions[0].ref"),
    (["artifacts", 0, "hub"], "nohub", "unknown hub"),
    (["artifacts", 0, "place"], "repo:other", "not declared by codehub"),
    (["artifacts", 0, "about"], ["svc.missing"], "about"),
    (["hubs", "codehub", "places", 0, "acl"], ["team-missing"], "unknown group"),
    (["hubs", "skillhub", "names", 0, "denotes"], "svc.missing", "names[0].denotes"),
    (["planted", 0, "hub"], "dochub", "unknown hub"),
    (["planted", 0, "entities"], ["svc.one", "svc.missing"], "unknown entity"),
    (["artifacts", 0, "body"], "LIMIT = 3;", "do not match body slots"),
])
def test_dangling_reference_fails_with_path(path, value, expected):
    with pytest.raises(ValidationError) as error:
        World.model_validate(_mutated(path, value))
    assert expected in str(error.value)


def test_dangling_artifact_and_principal_fail():
    data = minimal_world()
    data["artifacts"].append({"id": "a.copy", "hub": "codehub", "kind": "java_class", "title": "x",
                              "copy_of": "a.missing", "versions": [{"ref": "R1"}]})
    with pytest.raises(ValidationError, match="unknown artifact"):
        World.model_validate(data)
    data = minimal_world()
    data["artifacts"][0]["principal"] = "p-missing"
    with pytest.raises(ValidationError, match="unknown principal"):
        World.model_validate(data)
    data = minimal_world()
    data["planted"].append({"id": "p.inj", "kind": "injection", "artifact": "a.missing", "instruction": "x"})
    with pytest.raises(ValidationError, match="unknown artifact"):
        World.model_validate(data)


def test_real_world_loads_with_required_shape():
    world = load_world(ROOT / "world" / "world.yaml")
    services = [entity for entity in world.entities if entity.type == "service"]
    assert 4 <= len(services) <= 10      # 5 core + 4 D6 challenge-slice services (register row 25)
    assert world.releases == ["R40", "R41", "R42"] and [b.id for b in world.branches] == ["exp-branch"]
    assert 3 <= len(world.principals) <= 5
    assert sorted(planted.kind for planted in world.planted) == sorted(PLANTED_KINDS)


def test_value_resolution_follows_releases_and_environments():
    world = load_world(ROOT / "world" / "world.yaml")
    value = lambda text: world.resolve_value(parse_assertion(text)).value
    assert value("f.retry-limit.impl@R40/prod") == 3
    assert value("f.retry-limit.impl@R41/prod") == 3
    assert value("f.retry-limit.impl@R42/prod") == 5
    assert value("f.retry-limit.impl@R42/experiment") == 7
    assert value("f.retry-limit.procedure@R42") == 3


def test_rng_helpers_are_stable_and_label_scoped():
    assert opaque_id(1, "art", "x") == opaque_id(1, "art", "x")
    assert opaque_id(1, "art", "x") != opaque_id(2, "art", "x")
    assert opaque_id(1, "ent", "x").startswith("ent-")
    assert sub_rng(1, "a").random() == sub_rng(1, "a").random()
    assert sub_rng(1, "a").random() != sub_rng(1, "b").random()
