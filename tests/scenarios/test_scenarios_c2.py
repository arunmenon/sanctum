"""M3 done-when: scenario tests EX-01..04, 06..10, FX-24 on C2 (docs/milestones.md).

EX-04 and EX-06 are expected failures on C2 and are recorded as such (strict xfail), so a
change that makes them pass or breaks the others is visible:
- EX-04 asks for "the retry limit in release R40" with no scope and no service named. C2 has
  no name resolution or request context, and the release's retry artifact is not among the
  hub's lexical top results for that wording. Needs scope or memory context (C4, M4).
- EX-06 is an explore-mode question about "auth", which names two services; the gold policy
  expects separated interpretations, which need memory resolution (C4, M4).
"""
import json

import pytest

from .conftest import scenario_cases

PASS_ON_C2 = {"EX-01", "EX-02", "EX-03", "EX-07", "EX-08", "EX-09", "EX-10", "FX-24"}
EXPECTED_C2_FAIL = {
    "EX-04": "no scope and no service named; needs request context or memory (C4)",
    "EX-06": "ambiguous 'auth' needs separated interpretations (memory resolution, C4)",
}
M3_SCENARIOS = PASS_ON_C2 | set(EXPECTED_C2_FAIL)    # the mapping also holds M4 (C4) scenarios


M3_SCENARIOS = PASS_ON_C2 | set(EXPECTED_C2_FAIL)


def _params():
    for scenario, cases in sorted(scenario_cases().items()):
        if scenario not in M3_SCENARIOS:
            continue
        if scenario not in M3_SCENARIOS:
            continue
        for case_id in cases:
            marks = []
            if scenario in EXPECTED_C2_FAIL:
                marks.append(pytest.mark.xfail(reason=EXPECTED_C2_FAIL[scenario], strict=True))
            yield pytest.param(scenario, case_id, marks=marks, id=f"{scenario}-{case_id}")


def test_mapping_covers_the_m3_scenarios():
    assert M3_SCENARIOS <= set(scenario_cases())


@pytest.mark.parametrize("scenario,case_id", list(_params()))
def test_scenario_on_c2(c2_run, scenario, case_id):
    score = next(score for score in c2_run.scores if score.case_id == case_id)
    assert not score.gates_failed, score.gates_failed
    assert score.safe_grounded_success, score


def test_c2_run_is_out_of_process_and_clean(c2_run):
    assert c2_run.integrity_ok, c2_run.anomalies
    assert c2_run.manifest["config_id"] == "C2" and c2_run.manifest["sut"] == "ref"
    receipts = [json.loads(line) for line in (c2_run.out_dir / "receipts.jsonl").read_text().splitlines()]
    assert receipts and all(receipt["config_id"] == "C2" for receipt in receipts)
    assert all(score.receipt_honest and score.within_budget and not score.leaks for score in c2_run.scores)


def test_ex02_duplicates_keep_provenance(c2_run):
    """Every `duplicates` reference resolves (present or omitted with a reason)."""
    for line in (c2_run.out_dir / "responses.jsonl").read_text().splitlines():
        response = json.loads(line)
        present = {unit["evidence_id"] for unit in response["evidence"]}
        omitted = {entry["ref_id"]: entry["reason"] for entry in response["omitted"]}
        for unit in response["evidence"]:
            for ref in unit["duplicates"]:
                assert ref in present or omitted.get(ref) == "exact_duplicate"


def test_fx24_applicability_labels(c2_run):
    """Code evidence carries branch, environment and effective release; experiment-branch units
    are never labelled production."""
    for line in (c2_run.out_dir / "responses.jsonl").read_text().splitlines():
        for unit in json.loads(line)["evidence"]:
            if unit["source_id"] != "codehub":
                continue
            applicability = unit["applicability"]
            assert applicability["applicability_status"] == "known"
            assert applicability["effective_from"] == unit["source_version"]
            if unit["source_version"] == "exp-branch":
                assert applicability["environment"] == "experiment"
