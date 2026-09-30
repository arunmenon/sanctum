"""D4 order-sensitive measurement and the predefined budget stress (prompt review §4)."""
import json
from pathlib import Path

import yaml

from sanctum_contracts import EvidenceResponse
from sanctum_eval.metrics import necessary_evidence_recall
from sanctum_eval.order_metrics import first_support_rank, order_metrics_for_run, prefix_coverage
from sanctum_run.runner import DEFAULT_M0_PRINCIPAL_ALIASES, RunConfig, load_principal_aliases, run
from sanctum_run.sut import StubSUTAdapter, load_call_plan
from tests.scenarios.conftest import scenario_world  # noqa: F401
from tools.run_budget_stress import arm_arguments, render, run_stress

ROOT = Path(__file__).resolve().parents[1]


def test_prefix_coverage_and_rank_follow_response_order(case):
    gold, response, _, _ = case("m0-001")
    resp = EvidenceResponse.model_validate(response)
    assert prefix_coverage(gold, resp, 100000) == necessary_evidence_recall(gold, resp)   # whole response
    assert prefix_coverage(gold, resp, 1) == 0.0                                   # nothing fits in one token
    reversed_resp = EvidenceResponse.model_validate({**response, "evidence": list(reversed(response["evidence"]))})
    ranks = (first_support_rank(gold, resp), first_support_rank(gold, reversed_resp))
    assert all(r is not None for r in ranks)
    padding = {**response["evidence"][0], "evidence_id": "ev-pad", "artifact_id": "art-pad",
               "native_ref": "codehub:art-pad@R42#0-10"}
    demoted = EvidenceResponse.model_validate({**response, "evidence": [padding] + response["evidence"]})
    assert first_support_rank(gold, demoted) == first_support_rank(gold, resp) + 1


def test_budget_stress_config_is_predeclared():
    config = yaml.safe_load((ROOT / "configs" / "budget_stress.yaml").read_text())
    assert config["budgets"] == [1000, 2000, 4000] and config["prefix_k"] == [1000, 2000, 4000]
    assert arm_arguments("C4+D4", "local-test") == ["--sut", "ref", "--config", "C4", "--round3", "d4",
                                                    "--round3-provider", "local-test",
                                                    "--system-one-provider", "local-test"]
    assert arm_arguments("C4", "x") == ["--sut", "ref", "--config", "C4"]


def test_budget_override_reaches_scoring_and_manifest(scenario_world, tmp_path):  # noqa: F811
    result = run(StubSUTAdapter(load_call_plan(ROOT / "tests" / "fixtures" / "m0" / "traces")), RunConfig(
        cases_dir=ROOT / "gold" / "m0", out_dir=tmp_path / "run", seed=1, sut_name="stub",
        world_build_dir=scenario_world, principal_aliases=load_principal_aliases(DEFAULT_M0_PRINCIPAL_ALIASES),
        budget_tokens=10))
    assert result.manifest["budget_tokens"] == 10
    assert all("budget" in score.gates_failed for score in result.scores if score.tokens_recounted > 10)


def test_stress_driver_and_offline_report(case, tmp_path):
    config = {"budgets": [1000, 2000], "prefix_k": [1000, 2000], "arms": ["C4", "C4+D4"]}
    gold, response, _, _ = case("m0-001")
    cases = tmp_path / "cases"
    cases.mkdir()
    (cases / "m0-001.yaml").write_text((ROOT / "gold" / "m0" / "m0-001.yaml").read_text())
    seen = []

    def fake(args, run_dir):
        seen.append(args)
        run_dir.mkdir(parents=True)
        (run_dir / "manifest.json").write_text("{}")
        (run_dir / "responses.jsonl").write_text(json.dumps(response) + "\n")
        return 0

    runs = run_stress(config, cases, tmp_path / "out", 7, "local-test", fake)
    assert [(arm, budget) for arm, budget, _ in runs] == [("C4", 1000), ("C4+D4", 1000), ("C4", 2000), ("C4+D4", 2000)]
    assert all("--budget-tokens" in args and "7" in args for args in seen)
    text = render(config, runs, cases)
    assert "| C4+D4 | 2000 |" in text and "SYNTHETIC" in text
    assert order_metrics_for_run(runs[0][2], cases, [1000])["coverage"][1000]["n"] == 1
