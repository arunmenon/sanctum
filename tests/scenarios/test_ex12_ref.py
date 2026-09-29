"""EX-12: a fifth backend onboarded by manifest and release only (M7). Case 1 runs with IncidentHub
released and must answer from it; case 2 is the same question with the hub held back and must say
insufficient (no guessed count)."""
import shutil

import pytest

from .conftest import SCENARIO_GOLD, run_ref, scenario_cases


@pytest.mark.parametrize("config_id", ["C2", "C4"])
def test_ex12_answers_only_when_released(scenario_world, tmp_path, config_id):
    released_case, held_case = scenario_cases()["EX-12"][:2]
    outcomes = {}
    for case_id, released in ((released_case, True), (held_case, False)):
        cases = tmp_path / case_id
        cases.mkdir()
        shutil.copy(SCENARIO_GOLD / f"{case_id}.yaml", cases)
        result = run_ref(scenario_world, tmp_path / f"run-{case_id}", config_id=config_id, cases_dir=cases,
                         include_held_back=released, extra_arguments=("--memory-release", "r2") if config_id == "C4" else ())
        assert result.integrity_ok and ("incidenthub" in result.manifest["hubs"]) == released
        outcomes[case_id] = result.scores[0]
    assert outcomes[released_case].safe_grounded_success, outcomes[released_case]
    assert outcomes[held_case].safe_grounded_success, outcomes[held_case]
