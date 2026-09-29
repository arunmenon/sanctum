"""Evaluator-side alignment of SUT memory entity ids onto world entity refs.

A memory-backed SUT (C4) names entities with its own opaque ids; gold names them with world
refs the SUT never sees. A memory entity is aligned to a world ref only when every place it
declares (`selects_for`) selects exactly one world entity and they all agree. Ambiguous,
conflicting, unknown or placeless entities stay unaligned, so their ids pass through unchanged
and a wrong or invented entity still scores as wrong.
"""
import json
from pathlib import Path
from typing import Optional

import yaml

from sanctum_contracts import EvidenceResponse, Receipt
from sanctum_world.schema import World


def load_memory_entities(path: Path) -> list[dict]:
    """entities.yaml: `entities: [{id, selects_for: [place, ...]}]` or a top-level list."""
    data = yaml.safe_load(Path(path).read_text())
    rows = data.get("entities", []) if isinstance(data, dict) else data or []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            raise ValueError(f"{path}: every entity needs a string id")
    return rows


def place_selections(world: World) -> dict[str, set[str]]:
    """Native place -> world entity ids it selects (empty for places that select none)."""
    selections: dict[str, set[str]] = {}
    for hub in world.hubs.values():
        for place in hub.places:
            selected = selections.setdefault(place.native, set())
            if place.selects_for:
                selected.add(place.selects_for)
    return selections


def align_entities(memory_entities: list[dict], world: World, entity_refs: dict[str, str]
                   ) -> tuple[dict[str, str], dict[str, str]]:
    """Returns (aligned: memory id -> world ref, unaligned: memory id -> reason)."""
    selections = place_selections(world)
    aligned: dict[str, str] = {}
    unaligned: dict[str, str] = {}
    for row in memory_entities:
        entity_id, places = row["id"], list(row.get("selects_for") or [])
        if not places:
            unaligned[entity_id] = "no_places"
            continue
        targets: set[str] = set()
        reason: Optional[str] = None
        for place in places:
            if place not in selections:
                reason = f"unknown_place:{place}"
                break
            if len(selections[place]) != 1:
                reason = f"ambiguous_place:{place}"
                break
            targets |= selections[place]
        if reason is None and len(targets) != 1:
            reason = "conflicting_places"
        if reason is None:
            aligned[entity_id] = entity_refs[targets.pop()]
        else:
            unaligned[entity_id] = reason
    return aligned, unaligned


def load_alignment(entities_path: Path, world: World, world_build_dir: Path
                   ) -> tuple[dict[str, str], dict[str, str]]:
    entity_refs = json.loads((Path(world_build_dir) / "private" / "entity_refs.json").read_text())
    return align_entities(load_memory_entities(entities_path), world, entity_refs)


def apply_alignment(response: EvidenceResponse, receipt: Receipt, alignment: dict[str, str]
                    ) -> tuple[EvidenceResponse, Receipt]:
    """Aligned copies; the inputs are not modified. Unaligned ids pass through unchanged."""
    def ref(value: str) -> str:
        return alignment.get(value, value)

    aligned_response = response.model_copy(update={"interpretations": [
        interpretation.model_copy(update={"entity_ref": ref(interpretation.entity_ref)})
        for interpretation in response.interpretations]})
    aligned_receipt = receipt.model_copy(update={
        "resolutions": [resolution.model_copy(update={
            "candidates": [ref(value) for value in resolution.candidates],
            "chosen": [ref(value) for value in resolution.chosen]})
            for resolution in receipt.resolutions],
        "activations": [activation.model_copy(update={"entity_ref": ref(activation.entity_ref)})
                        for activation in receipt.activations],
    })
    return aligned_response, aligned_receipt
