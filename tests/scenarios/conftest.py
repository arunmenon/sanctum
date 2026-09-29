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


def run_ref(world: Path, out_dir: Path, config_id: str = "C2", failure_profile: str = "none",
            registry: Path | None = None, time_scale: float | None = None, cases_dir: Path = SCENARIO_GOLD):
    arguments = ["--config", config_id]
    if registry is not None:
        arguments += ["--registry", str(registry)]
    return run(ProcessSUT(arguments), RunConfig(
        cases_dir=cases_dir, out_dir=out_dir, seed=SEED, sut_name="ref", config_id=config_id,
        failure_profile=failure_profile, world_build_dir=world, time_scale=time_scale))


@pytest.fixture(scope="session")
def c2_run(scenario_world, tmp_path_factory):
    return run_ref(scenario_world, tmp_path_factory.mktemp("c2-scenarios"))
