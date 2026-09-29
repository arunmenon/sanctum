"""Evaluator-side alignment of SUT memory entity ids onto world entity refs (M4)."""
import json
from pathlib import Path

import pytest
import yaml

from sanctum_contracts import EvidenceResponse, Receipt
from sanctum_eval.alignment import align_entities, apply_alignment, load_alignment
from sanctum_run.runner import DEFAULT_M0_PRINCIPAL_ALIASES, RunConfig, load_principal_aliases, run
from sanctum_run.sut import StubSUTAdapter, load_call_plan
from sanctum_world.render import build
from sanctum_world.schema import load_world

ROOT = Path(__file__).resolve().parents[1]
GOLD_M0 = ROOT / "gold" / "m0"
M0_TRACES = ROOT / "tests" / "fixtures" / "m0" / "traces"
SEED = 20260930

# Same shape as owners/memory_seed/<release>/entities.yaml (contract from the sanctum_ref owner).
MEMORY_ENTITIES = {"entities": [
    {"id": "me-01", "selects_for": ["repo:payments/payment-auth", "space:PA"]},
    {"id": "me-02", "selects_for": ["repo:identity/auth"]},
    {"id": "me-03", "selects_for": ["repo:payments/ledger-post", "skills/payments/"]},   # ambiguous
    {"id": "me-04", "selects_for": ["repo:payments/payment-auth", "space:IDN"]},         # conflicting
    {"id": "me-05", "selects_for": ["repo:payments/checkout"]},                          # invented
    {"id": "me-06", "selects_for": []},
]}


@pytest.fixture(scope="module")
def world():
    return load_world(ROOT / "world" / "world.yaml")


@pytest.fixture(scope="module")
def world_build(tmp_path_factory) -> Path:
    out_dir = tmp_path_factory.mktemp("align-build") / "world"
    build(ROOT / "world", SEED, out_dir)
    return out_dir


@pytest.fixture(scope="module")
def refs(world_build):
    return json.loads((world_build / "private" / "entity_refs.json").read_text())


@pytest.fixture(scope="module")
def alignment(world, world_build, tmp_path_factory):
    path = tmp_path_factory.mktemp("memory-seed") / "entities.yaml"
    path.write_text(yaml.safe_dump(MEMORY_ENTITIES))
    return load_alignment(path, world, world_build)


def test_exact_alignment(alignment, refs):
    aligned, _ = alignment
    assert aligned == {"me-01": refs["svc.payment-auth"], "me-02": refs["svc.identity-auth"]}


def test_ambiguous_conflicting_invented_and_placeless_stay_unaligned(alignment):
    _, unaligned = alignment
    assert unaligned == {"me-03": "ambiguous_place:skills/payments/", "me-04": "conflicting_places",
                         "me-05": "unknown_place:repo:payments/checkout", "me-06": "no_places"}


def test_top_level_list_shape(world, refs):
    aligned, _ = align_entities([{"id": "me-x", "selects_for": ["space:EDGE"]}], world, refs)
    assert aligned == {"me-x": refs["svc.gateway-edge"]}


def _receipt(entity_ref: str) -> Receipt:
    return Receipt.model_validate({
        "receipt_id": "r", "request_id": "q", "config_id": "C4", "contract_revision": "1",
        "resolutions": [{"term": "Auth Service", "candidates": [entity_ref, "me-05"],
                         "chosen": [entity_ref], "origin": "denotes"}],
        "activations": [{"kind": "procedure", "ref": "proc-1", "entity_ref": entity_ref}]})


def test_invented_entity_passes_through_and_input_is_untouched(alignment, refs):
    aligned, _ = alignment
    receipt = _receipt("me-01")
    before = receipt.model_dump(mode="json")
    _, aligned_receipt = apply_alignment(EvidenceResponse.model_construct(interpretations=[]),
                                         receipt, aligned)
    assert receipt.model_dump(mode="json") == before
    assert aligned_receipt.resolutions[0].candidates == [refs["svc.payment-auth"], "me-05"]
    assert aligned_receipt.activations[0].entity_ref == refs["svc.payment-auth"]
    assert "me-05" not in set(refs.values())    # so it can never match a gold interpretation


class MemoryIdSUT(StubSUTAdapter):
    """The M0 stub, but naming entities with memory ids the way a C4 SUT would."""

    def __init__(self, call_plan, to_memory: dict[str, str]):
        super().__init__(call_plan)
        self.to_memory = to_memory

    async def retrieve(self, request, context):
        response, receipt = await super().retrieve(request, context)
        inverse = {world_ref: memory_id for memory_id, world_ref in self.to_memory.items()}
        return apply_alignment(response, receipt, inverse)


def _run(world_build, out_dir, sut, entity_alignment=None):
    return run(sut, RunConfig(cases_dir=GOLD_M0, out_dir=out_dir, seed=SEED, sut_name="stub",
                              world_build_dir=world_build, entity_alignment=entity_alignment,
                              principal_aliases=load_principal_aliases(DEFAULT_M0_PRINCIPAL_ALIASES)))


def test_runner_scores_aligned_copies_and_keeps_raw_outputs(world_build, tmp_path):
    call_plan = load_call_plan(M0_TRACES)
    baseline = _run(world_build, tmp_path / "baseline", StubSUTAdapter(call_plan))
    gold_refs = sorted({json.loads(line)["interpretations"][i]["entity_ref"]
                        for line in (baseline.out_dir / "responses.jsonl").read_text().splitlines()
                        for i in range(len(json.loads(line)["interpretations"]))})
    to_memory = {f"mem-{n}": ref for n, ref in enumerate(gold_refs)}
    sut = MemoryIdSUT(call_plan, to_memory)

    unaligned = _run(world_build, tmp_path / "unaligned", sut)
    aligned = _run(world_build, tmp_path / "aligned", sut, entity_alignment=to_memory)

    by_case = lambda result: {score.case_id: score.safe_grounded_success for score in result.scores}
    assert by_case(baseline)["m0-002"]          # separated interpretations (kestrel-both)
    assert not by_case(unaligned)["m0-002"]
    assert by_case(aligned) == by_case(baseline)

    raw = (aligned.out_dir / "responses.jsonl").read_text()
    assert "mem-" in raw and not any(ref in raw for ref in gold_refs)
    aligned_copy = (aligned.out_dir / "responses.aligned.jsonl").read_text()
    assert "mem-" not in aligned_copy
    assert json.loads((aligned.out_dir / "entity_alignment.json").read_text()) == to_memory
    assert aligned.manifest["entity_alignment"] == {"table": "entity_alignment.json", "aligned": len(to_memory)}
    assert unaligned.manifest["entity_alignment"] is None
