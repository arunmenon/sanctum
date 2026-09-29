"""M4 done-when: FX-16..23, EX-05, EX-15 on C4, plus EX-04 and EX-06 (docs/milestones.md).

Scored with evaluator-side entity alignment (src/sanctum_eval/alignment.py). Strict xfails
record what C4 does not do yet:
- EX-04: no scope, no service named; the question needs the payment-auth context C4 cannot infer.
- EX-06: r1 reviews "auth" as a name of identity-auth only, so the vague question resolves to one
  meaning where gold expects two (the seed would need a second reviewed "auth" name).
- FX-19 case 1: context resolution and the alias cap work, but half the obligations are missed.
- FX-21: needs the admin script (descriptor refresh, then unshare mid-run) and a SkillHub read.
FX-18, FX-22, FX-23 have no cases (script-only): FX-18 and FX-23 are covered by unit tests
(tests/test_sanctum_ref_memory.py); FX-22 (probe coverage) is not built.
EX-15 and FX-17 pass on the seed as authored; their governance scripts (proposal review) are not
run because the write and proposal path is post-pilot.
"""
import json

import pytest

from .conftest import scenario_cases

M4_SCENARIOS = {"EX-05", "EX-09b", "EX-15", "FX-16", "FX-17", "FX-19", "FX-20", "FX-21", "EX-04", "EX-06"}
EXPECTED_C4_FAIL = {
    "sc-ex-04-1": "no scope and no service named",
    "sc-ex-06-1": "r1 reviews 'auth' for identity-auth only",
    "sc-fx-19-1": "context resolves, half the obligations missed",
    "sc-fx-21-1": "admin script and SkillHub read not driven",
}


def _params():
    for scenario, cases in sorted(scenario_cases().items()):
        if scenario not in M4_SCENARIOS:
            continue
        for case_id in cases:
            marks = [pytest.mark.xfail(reason=EXPECTED_C4_FAIL[case_id], strict=True)] if case_id in EXPECTED_C4_FAIL else []
            yield pytest.param(case_id, marks=marks, id=f"{scenario}-{case_id}")


@pytest.mark.parametrize("case_id", list(_params()))
def test_scenario_on_c4(c4_run, case_id):
    score = next(score for score in c4_run.scores if score.case_id == case_id)
    assert not score.gates_failed, score.gates_failed
    assert score.safe_grounded_success, score


def test_c4_run_is_clean_and_pinned(c4_run):
    assert c4_run.integrity_ok and c4_run.manifest["config_id"] == "C4"
    receipts = [json.loads(line) for line in (c4_run.out_dir / "receipts.jsonl").read_text().splitlines()]
    assert {receipt["memory_release_id"] for receipt in receipts} == {"r1"}
    assert all(score.receipt_honest and not score.leaks and not score.wrong_entity for score in c4_run.scores)


def test_ex05_hub_name_translated(c4_run):
    case_id = scenario_cases()["EX-05"][0]
    index = c4_run.manifest["cases"].index(case_id)
    receipt = json.loads((c4_run.out_dir / "receipts.jsonl").read_text().splitlines()[index])
    assert [r["origin"] for r in receipt["resolutions"]] == ["denotes"]
    selectors = {plan["source_id"]: plan["selectors"] for plan in receipt["query_plans"]}
    assert selectors["codehub"] == ["repo=payments/payment-auth"] and selectors["dochub"] == ["space=PA"]


def test_fx16_label_only_control_cannot_separate(label_only_run, c4_run):
    """The C4a-label-only control picks one meaning where C4 separates two."""
    for case_id in scenario_cases()["FX-16"]:
        c4 = next(s for s in c4_run.scores if s.case_id == case_id)
        label_only = next(s for s in label_only_run.scores if s.case_id == case_id)
        if c4.ambiguity_handled is not None:
            assert c4.ambiguity_handled and not label_only.ambiguity_handled
