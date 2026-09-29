"""Memory v0 units (HLD §8.5-§8.7, §9.2-§9.6): releases, backends, resolution, plans, procedures."""
import shutil
from pathlib import Path

import pytest
import yaml

from sanctum_contracts import RetrieveRequest
from sanctum_ref.config import load_arm
from sanctum_ref.intent import analyze
from sanctum_ref.memory import LabelTable, MemoryUnavailable, RelationStore, TableStore, load_release
from sanctum_ref.registry import load_registry
from sanctum_ref.resolution import resolve, resolve_label_only
from sanctum_ref.routing import apply_memory, plan_sources

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "owners" / "memory_seed"
MATRIX = ROOT / "configs" / "matrix.yaml"
REGISTRY = load_registry(ROOT / "owners" / "manifests")
RELEASES = {"R40", "R41", "R42"}
CAPABILITIES = {hub: {"contract": {"version_reads": hub != "memoryhub"}, "place_version_reads": {}}
                for hub in ("codehub", "skillhub", "dochub", "memoryhub")}
BOTH = {"payments-eng", "identity-eng"}
PAYMENTS = {"payments-eng", "platform-eng"}


def req(query, **fields):
    return RetrieveRequest(request_id="req-mem", query=query, mode=fields.pop("mode", "scoped"),
                           budget_tokens=4000, deadline_ms=3000, **fields)


@pytest.fixture(scope="module")
def release():
    return load_release(SEED)


def plans(query, groups, arm="C4", invalidated=frozenset(), **fields):
    release = load_release(SEED)
    arm_config = load_arm(MATRIX, arm)
    store = RelationStore(release) if arm_config.memory_store == "relations" else TableStore(release)
    request = req(query, **fields)
    intent = analyze(query, REGISTRY.domains, RELEASES)
    base = plan_sources(request, arm_config, REGISTRY, intent, CAPABILITIES, set(groups))
    resolution = (resolve_label_only(request, LabelTable(release), store, RELEASES) if arm_config.resolution == "label_only"
                  else resolve(request, store, REGISTRY, set(groups), RELEASES))
    return resolution, *apply_memory(base, resolution, store, REGISTRY, intent, set(groups), set(invalidated), query, arm_config)


def test_release_validates_and_is_incomplete(release):
    assert release.release_id == "r1" and (SEED / "ACTIVE").read_text().strip() == "r1"
    labels = {term.label for term in release.terms}
    assert {"Auth Service", "PA-svc"} <= labels
    namespaces = {term.namespace for term in release.terms if term.label == "Auth Service"}
    assert namespaces == {"Payments", "Identity"}
    assert "ledgerd" not in labels                                   # deliberately missing name
    assert all(place.place != term.label for place in release.places for term in release.terms)


def test_unreadable_or_dangling_release_is_unavailable(tmp_path):
    with pytest.raises(MemoryUnavailable):
        load_release(tmp_path)
    shutil.copytree(SEED, tmp_path / "seed")
    path = tmp_path / "seed" / "r1" / "release.yaml"
    data = yaml.safe_load(path.read_text())
    data["terms"][0]["denotes"] = "svc:nowhere"
    path.write_text(yaml.safe_dump(data))
    with pytest.raises(MemoryUnavailable):
        load_release(tmp_path / "seed")


def test_backends_answer_identically(release):
    relations, tables = RelationStore(release), TableStore(release)
    assert relations.labels() == tables.labels()
    for label in relations.labels():
        assert relations.denotes(label) == tables.denotes(label)
    for entity in release.entities:
        assert relations.places_for(entity.id) == tables.places_for(entity.id)
        assert relations.member_of(entity.id) == tables.member_of(entity.id)
    assert relations.procedures() == tables.procedures()


@pytest.mark.parametrize("query,groups,fields", [
    ("How many retries does Auth Service allow?", BOTH, {}),
    ("What are the PA-svc retry limits on a gateway timeout?", PAYMENTS, {"scope": "project:payments-auth-retry-fix"}),
    ("What was the retry limit for payment-auth in release R40?", PAYMENTS, {}),
])
def test_q3b_c4_and_c4a_equivalent_plan_identically(query, groups, fields):
    """Q3b: relations and tables storage give the same resolutions, activations and plans."""
    def summary(arm):
        resolution, planned, activations, reasons = plans(query, groups, arm=arm, **fields)
        return ([(r.term, r.candidates, r.chosen, r.origin, r.assertion_refs) for r in resolution.records],
                [(a.kind, a.ref, a.entity_ref, a.source_id) for a in activations],
                [(p.hub_id, p.call, p.status, p.reasons, p.selectors, p.aliases, p.version_refs, p.interpretation)
                 for p in planned], reasons)
    assert summary("C4") == summary("C4a-equivalent")


def test_two_accessible_meanings_are_separated_not_guessed():
    """FX-16: both "Auth Service" meanings visible -> two interpretations, each with its own plan
    and procedures; no union of authority."""
    resolution, planned, activations, _ = plans("How many retries does Auth Service allow?", BOTH)
    assert resolution.ambiguous and len(resolution.interpretations) == 2
    assert {i.origin for i in resolution.interpretations} == {"denotes"}
    by_interpretation = {}
    for plan in planned:
        by_interpretation.setdefault(plan.interpretation, {})[plan.hub_id] = plan
    repos = {index: hubs["codehub"].selectors.get("repo") for index, hubs in by_interpretation.items()}
    assert sorted(repos.values()) == ["identity/auth", "payments/payment-auth"]
    # the payments must-consult fires only for the payments meaning
    procedure_entities = {a.entity_ref for a in activations if a.kind == "procedure"}
    payments_ref = next(i.entity_ref for i in resolution.interpretations if i.entity_id == "svc:payments/payment-auth")
    assert procedure_entities == {payments_ref}


def test_inaccessible_meaning_is_never_named():
    resolution, *_ = plans("How many retries does Auth Service allow?", PAYMENTS)
    assert not resolution.ambiguous and [i.entity_id for i in resolution.interpretations] == ["svc:payments/payment-auth"]
    assert len(resolution.records[0].candidates) == 1


def test_request_context_picks_the_namespace():
    resolution, *_ = plans("How many retries does Auth Service allow?", BOTH, scope="project:payments-auth-retry-fix")
    assert [(i.entity_id, i.origin) for i in resolution.interpretations] == [("svc:payments/payment-auth", "request_context")]


def test_hub_name_translates_to_selectors_and_aliases():
    """EX-05: PA-svc resolves by DENOTES; code gets the repo selector, docs the PA space, skills
    the procedure prefix narrowed by the entity selector; the space is a place, not a name."""
    resolution, planned, activations, reasons = plans("What are the PA-svc retry limits on a gateway timeout?", PAYMENTS)
    assert [i.entity_id for i in resolution.interpretations] == ["svc:payments/payment-auth"]
    by_hub = {p.hub_id: p for p in planned}
    assert by_hub["codehub"].selectors == {"repo": "payments/payment-auth"}
    assert by_hub["dochub"].selectors == {"space": "PA"}
    assert by_hub["skillhub"].selectors == {"path_prefix": "skills/payments/auth-service"}
    assert by_hub["skillhub"].required and "Auth Service" in by_hub["skillhub"].aliases
    assert {a.kind for a in activations} == {"procedure", "selector"} and not reasons


def test_missing_name_is_unresolved_not_invented():
    resolution, planned, activations, _ = plans("Why is ledgerd-worker slow?", PAYMENTS)
    assert not resolution.interpretations and resolution.unresolved == ["ledgerd-worker"]
    assert activations == []


def test_label_only_has_no_namespaces_or_ambiguity():
    """C4a-label-only: first flat match wins, even with two accessible meanings; places are names."""
    resolution, *_ = plans("How many retries does Auth Service allow?", BOTH, arm="C4a-label-only")
    assert len(resolution.interpretations) == 1 and not resolution.ambiguous
    assert resolution.interpretations[0].origin == "alias_table"
    space_as_name, *_ = plans("What does PA say about retries?", PAYMENTS, arm="C4a-label-only")
    assert space_as_name.interpretations                              # the space label resolved as a name
    c4, *_ = plans("What does PA say about retries?", PAYMENTS)
    assert not c4.interpretations                                     # C4: a place never resolves identity


def test_denied_must_consult_from_memory_is_a_gap():
    """FX-20: the procedure fires, but SkillHub payments is outside the caller's access."""
    _, planned, activations, _ = plans("How many retries does payment-auth allow?", {"payments-code"})
    skill = next(p for p in planned if p.hub_id == "skillhub")
    assert not skill.call and skill.required and skill.reasons == ["required_source_denied"]
    assert any(a.kind == "procedure" for a in activations)


def test_unshared_place_stops_being_a_selector():
    """FX-21: after `place_unshared` for space:PA the selector is uncertain and not applied."""
    _, planned, _, _ = plans("What are the PA-svc retry limits?", PAYMENTS, invalidated={"space:PA"})
    assert "space" not in next(p for p in planned if p.hub_id == "dochub").selectors


def test_disabled_relation_has_no_effect(release):
    """FX-18 / X-RELATION-USE: RELATES_TO is stored, never used for identity or procedures."""
    assert release.relations and all(r.status != "accepted" for r in release.relations)
    resolution, *_ = plans("How many retries does Auth Service allow?", {"identity-eng"})
    assert [i.entity_id for i in resolution.interpretations] == ["svc:identity/auth"]


def test_fx23_release_swap_and_rollback(tmp_path):
    """Each pin reads ACTIVE once; a request keeps its pinned release; a swap affects only later
    requests, and rollback is another pointer switch (old receipts keep the release they used)."""
    from sanctum_ref.pipeline import MemoryState
    seed = tmp_path / "seed"
    shutil.copytree(SEED, seed)
    shutil.copytree(seed / "r1", seed / "r2")
    release_file = seed / "r2" / "release.yaml"
    release_file.write_text(release_file.read_text().replace("release_id: r1", "release_id: r2"))
    state = MemoryState(seed)
    pinned_release, pinned_store = state.pin("relations")
    (seed / "ACTIVE").write_text("r2\n")
    assert pinned_release.release_id == "r1" and pinned_store.release_id == "r1"   # in-flight keeps r1
    assert state.pin("relations")[0].release_id == "r2"
    (seed / "ACTIVE").write_text("r1\n")                                            # rollback
    assert state.pin("relations")[0].release_id == "r1"
    (seed / "ACTIVE").write_text("r9\n")                                            # withdrawn / missing
    with pytest.raises(MemoryUnavailable):
        state.pin("relations")
