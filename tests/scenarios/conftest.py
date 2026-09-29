"""Scenario tests run `sanctum_ref` out of process behind the gateway proxy, over the scenario
cases mapped in docs/scenario-cases.yaml. The runner (evaluator side) loads gold; the SUT only
ever sees the public request and hub tools."""
from pathlib import Path

import pytest
import yaml

from sanctum_run.process_sut import ProcessSUT
from sanctum_run.runner import RunConfig, run
from sanctum_world.render import build

ROOT = Path(__file__).resolve().parents[2]
SEED = 20260930
SCENARIO_GOLD = ROOT / "gold" / "scenarios"
SCENARIO_MAP = ROOT / "docs" / "scenario-cases.yaml"


def scenario_cases() -> dict[str, list[str]]:
    return {scenario: list(cases) for scenario, cases in
            (yaml.safe_load(SCENARIO_MAP.read_text(encoding="utf-8"))["scenarios"] or {}).items()}


@pytest.fixture(scope="session")
def scenario_world(tmp_path_factory) -> Path:
    out_dir = tmp_path_factory.mktemp("scenario-build") / "world"
    build(ROOT / "world", SEED, out_dir)
    return out_dir


def alignment_for(world: Path, config_id: str):
    """Evaluator side: memory entity refs -> world refs (src/sanctum_eval/alignment.py)."""
    if config_id not in ("C4", "C4a-equivalent", "C4a-label-only", "C5"):
        return None
    from sanctum_eval.alignment import load_alignment
    from sanctum_world.schema import load_world
    aligned, _unaligned = load_alignment(ROOT / "owners" / "memory_seed" / "r1" / "entities.yaml",
                                         load_world(ROOT / "world" / "world.yaml"), world)
    return aligned


def run_ref(world: Path, out_dir: Path, config_id: str = "C2", failure_profile: str = "none",
            registry: Path | None = None, time_scale: float | None = None, cases_dir: Path = SCENARIO_GOLD,
            memory_seed: Path | None = None, extra_arguments: tuple[str, ...] = ()):
    arguments = ["--config", config_id, *extra_arguments]
    if memory_seed is not None:
        arguments += ["--memory-seed", str(memory_seed)]
    if registry is not None:
        arguments += ["--registry", str(registry)]
    return run(ProcessSUT(arguments), RunConfig(
        cases_dir=cases_dir, out_dir=out_dir, seed=SEED, sut_name="ref", config_id=config_id,
        failure_profile=failure_profile, world_build_dir=world, time_scale=time_scale,
        entity_alignment=alignment_for(world, config_id)))


@pytest.fixture(scope="session")
def c2_run(scenario_world, tmp_path_factory):
    return run_ref(scenario_world, tmp_path_factory.mktemp("c2-scenarios"))


@pytest.fixture(scope="session")
def c4_run(scenario_world, tmp_path_factory):
    return run_ref(scenario_world, tmp_path_factory.mktemp("c4-scenarios"), config_id="C4")


@pytest.fixture(scope="session")
def label_only_run(scenario_world, tmp_path_factory):
    return run_ref(scenario_world, tmp_path_factory.mktemp("c4a-label-scenarios"), config_id="C4a-label-only")
