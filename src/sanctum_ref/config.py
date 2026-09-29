"""Arm configuration from `configs/matrix.yaml` switches only (lab plan §7.2).

An arm is the shared switches plus its own. `sanctum_ref` implements the modules that C1-naive,
C1-fair, C2, C4, C4a-equivalent and C4a-label-only enable; any arm that switches on a module not
built yet (a decision provider: C3, C5) is refused rather than silently run as something else.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

IMPLEMENTED = {
    "routing": {"fanout_all", "rules"},
    "assembly": {"concatenate", "common"},
    "resolution": {"none", "denotes", "label_only"},
    "translation": {False, True},
    "procedures": {False, "registry_only", "memory"},
    "memory_store": {"none", "relations", "tables"},
    "decision_provider": {"none"},
}


class UnsupportedArm(ValueError):
    pass


@dataclass(frozen=True)
class ArmConfig:
    config_id: str
    routing: str
    assembly: str
    procedures: Any
    resolution: str
    translation: bool
    memory_store: str
    response_tokens: int
    candidates: int
    calls: int
    deadline_ms: int
    tokenizer: str
    exact_dedup: bool
    applicability_enforcement: bool
    conflict_extraction: str
    packing: str

    @property
    def rules_routing(self) -> bool:
        return self.routing == "rules"

    @property
    def registry_procedures(self) -> bool:
        return self.procedures == "registry_only"

    @property
    def uses_memory(self) -> bool:
        return self.memory_store != "none"

    @property
    def common_assembly(self) -> bool:
        return self.assembly == "common"


def load_arm(matrix_path: Path, config_id: str) -> ArmConfig:
    matrix = yaml.safe_load(Path(matrix_path).read_text(encoding="utf-8"))
    arms = matrix.get("arms") or {}
    if config_id not in arms:
        raise UnsupportedArm(f"unknown arm {config_id!r}")
    switches = arms[config_id]
    for switch, allowed in IMPLEMENTED.items():
        if switches.get(switch) not in allowed:
            raise UnsupportedArm(f"{config_id}: {switch}={switches.get(switch)!r} is not implemented by sanctum_ref")
    shared = matrix["shared"]
    budgets = shared["budgets"]
    return ArmConfig(
        config_id=config_id, routing=switches["routing"], assembly=switches["assembly"],
        procedures=switches["procedures"], resolution=switches["resolution"],
        translation=bool(switches["translation"]), memory_store=switches["memory_store"], response_tokens=int(budgets["response_tokens"]),
        candidates=int(budgets["candidates"]), calls=int(budgets["calls"]),
        deadline_ms=int(budgets["deadline_ms"]), tokenizer=str(shared["tokenizer"]),
        exact_dedup=bool(shared["exact_dedup"]),
        applicability_enforcement=bool(shared["applicability_enforcement"]),
        conflict_extraction=str(shared["conflict_extraction"]), packing=str(shared["packing"]))
