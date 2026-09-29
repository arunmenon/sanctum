"""M5 evaluator side: leak scanner, paired stats, config pairing check, report, holdout protocol."""
import json
import shutil
from pathlib import Path

import pytest

from sanctum_eval.leak_scan import LeakScanner, scan_run_dir
from sanctum_eval.load import load_gold
from sanctum_eval.stats import cluster_key, paired_delta, per_family_deltas
from sanctum_run.runner import DEFAULT_M0_PRINCIPAL_ALIASES, RunConfig, load_principal_aliases, run
from sanctum_run.sut import StubSUTAdapter, load_call_plan
from sanctum_world.render import build
from tools.config_diff import check_runs, load as load_matrix
from tools import report
from tools.report import CAVEAT, build_report
from sanctum_eval.provenance import effective_configuration, tree_sha256
from tools.run_holdout import HoldoutRefused, check_passthrough, read_log, run_once

ROOT = Path(__file__).resolve().parents[1]
GOLD_M0 = ROOT / "gold" / "m0"
GOLD_DEV = ROOT / "gold" / "dev"
M0_TRACES = ROOT / "tests" / "fixtures" / "m0" / "traces"
SEED = 20260930


@pytest.fixture(scope="module")
def world_build(tmp_path_factory) -> Path:
    out_dir = tmp_path_factory.mktemp("m5-build") / "world"
    build(ROOT / "world", SEED, out_dir)
    return out_dir


@pytest.fixture(scope="module")
def scanner(world_build):
    return LeakScanner(world_build)


@pytest.fixture(scope="module")
def aliases():
    return load_principal_aliases(DEFAULT_M0_PRINCIPAL_ALIASES)


@pytest.fixture(scope="module")
def runs(world_build, aliases, tmp_path_factory):
    base = tmp_path_factory.mktemp("m5-runs")
    out = {}
    for config_id in ("C1-fair", "C2"):
        out[config_id] = run(StubSUTAdapter(load_call_plan(M0_TRACES)), RunConfig(
            cases_dir=GOLD_M0, out_dir=base / config_id, seed=SEED, sut_name="stub", config_id=config_id,
            world_build_dir=world_build, principal_aliases=aliases)).out_dir
    return out


def _plant(run_dir: Path, target: Path, text: str) -> Path:
    shutil.copytree(run_dir, target)
    path = target / "responses.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[0]["planted"] = text         # the scanner reads raw output text, not the parsed contract
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    return target


# ---- leak scanner -----------------------------------------------------------------------
def test_clean_run_has_no_leaks(runs, world_build, aliases):
    assert scan_run_dir(runs["C2"], GOLD_M0, world_build, aliases) == []


def test_planted_canary_is_caught(runs, world_build, aliases, tmp_path):
    leaky = _plant(runs["C2"], tmp_path / "leaky", "see CANARY-INC-4417")
    leaks = scan_run_dir(leaky, GOLD_M0, world_build, aliases)
    assert [(leak.file, leak.line, leak.kind, leak.token) for leak in leaks] == [
        ("responses.jsonl", 1, "canary", "CANARY-INC-4417")]


def test_restricted_text_title_and_count(scanner):
    text = "INC-2291 postmortem says: Root cause: retry storm amplified by gateway timeouts. 2 restricted results"
    kinds = {kind for kind, _ in scanner.scan_text(text, "kestrel-payments")}
    assert kinds == {"restricted_title", "restricted_text", "restricted_count"}
    assert scanner.scan_text(text, "admin-probe") == []        # admin-probe may read space:Incidents
    assert {kind for kind, _ in scanner.scan_text(text, None)} == kinds   # rows with no principal: strictest


def test_filler_noise_in_restricted_page_is_not_a_leak(scanner):
    # shared filler noise from world/filler.yaml, rendered into ~470 artifacts including INC-2291
    noise = "Load tests ran in the staging cluster overnight. Staging mirrors production configuration where possible."
    assert scanner.scan_text(json.dumps({"text": noise}), "kestrel-payments") == []
    assert scanner.scan_text(noise, None) == []
    restricted = [a for a in scanner.artifacts if a.restricted]
    assert all(line.strip() and "Load tests ran" not in line for a in restricted for line in a.lines)
    assert any("Root cause: retry storm amplified by gateway timeouts." in a.lines for a in restricted)


def test_unreadable_artifact_ids_and_foreign_memory(scanner):
    identity_code = next(a for a in scanner.artifacts if a.hub == "codehub" and a.acl == {"identity-eng"})
    assert ("artifact_id", identity_code.artifact_id) in scanner.scan_text(identity_code.artifact_id, "kestrel-payments")
    assert scanner.scan_text(identity_code.artifact_id, "kestrel-identity") == []
    foreign = next(a for a in scanner.artifacts if a.owner == "kestrel-both")
    assert scanner.scan_text(foreign.artifact_id, "kestrel-payments")    # someone else's session memory
    assert scanner.scan_text(foreign.artifact_id, "kestrel-both") == []


# ---- stats ------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def dev_golds():
    return {gold.case_id: gold for gold in (load_gold(p) for p in sorted(GOLD_DEV.glob("*.yaml")))}


def _scores(golds, success):
    return {case_id: {"safe_grounded_success": success(case_id), "recall": 0.5} for case_id in golds}


def test_identical_arms_have_zero_delta(dev_golds):
    scores = _scores(dev_golds, lambda c: int(c[-1]) % 2 == 0)
    row = paired_delta(scores, scores, dev_golds, "safe_grounded_success")
    assert (row.delta, row.low, row.high, row.b_better, row.a_better) == (0.0, 0.0, 0.0, 0, 0)
    assert row.n_cases == 60 and row.n_clusters == len({cluster_key(g) for g in dev_golds.values()})


def test_bootstrap_is_seeded_and_clustered(dev_golds):
    a = _scores(dev_golds, lambda c: False)
    b = _scores(dev_golds, lambda c: dev_golds[c].family in ("named_service", "multi_hub"))
    first = paired_delta(a, b, dev_golds, "safe_grounded_success", resamples=500, seed=7)
    again = paired_delta(a, b, dev_golds, "safe_grounded_success", resamples=500, seed=7)
    assert first == again
    assert first.delta == pytest.approx(16 / 60) and first.low <= first.delta <= first.high
    assert first.low > 0          # every improvement is in the same direction
    rows = {row.scope: row for row in per_family_deltas(a, b, dev_golds, "safe_grounded_success", resamples=200)}
    assert rows["named_service"].delta == 1.0 and rows["vague"].delta == 0.0
    assert set(rows) == {"pooled"} | {g.family for g in dev_golds.values()}


def test_unpaired_arms_are_refused(dev_golds):
    a = _scores(dev_golds, lambda c: True)
    b = dict(list(a.items())[1:])
    with pytest.raises(ValueError):
        paired_delta(a, b, dev_golds, "safe_grounded_success")


# ---- config pairing ---------------------------------------------------------------------
def _effective(config_id, **overrides):
    effective = effective_configuration(sut="ref", config_id=config_id, hubs=["codehub", "skillhub"],
                                        cases_dir=GOLD_DEV, registry=ROOT / "owners" / "manifests",
                                        memory_release="r1" if config_id.startswith("C4") else None,
                                        memory_seed=ROOT / "owners" / "memory_seed")
    return {**effective, **overrides}


def test_check_runs_requires_matching_arms_and_pairing():
    matrix = load_matrix()
    base = {"world_manifest_sha256": "w", "seed": 1, "failure_profile": "none", "metrics_revision": "m",
            "cases": ["x"]}
    ok = lambda config_id, **kw: {**base, "config_id": config_id, "effective": _effective(config_id, **kw)}
    assert check_runs(matrix, "Q2_routing", ok("C1-fair"), ok("C2")) == []
    wrong = check_runs(matrix, "Q2_routing", ok("C1-fair"), {**ok("C4"), "cases": ["x", "y"]})
    assert "cases differs between runs" in wrong and any("C4" in problem for problem in wrong)
    for name in ("Q2_routing", "Q3a_memory_package", "Q3a_semantics_ablation", "Q3b_storage_equivalence"):
        c = matrix["comparisons"][name]
        assert check_runs(matrix, name, ok(c["a"]), ok(c["b"])) == [], name


@pytest.mark.parametrize("override,expected", [
    ({"released_hubs": ["codehub", "incidenthub", "skillhub"]}, "recorded released_hubs differs"),
    ({"sut_code_sha256": "other"}, "recorded sut_code_sha256 differs"),
    ({"registry_sha256": "other"}, "recorded registry_sha256 differs"),
    ({"memory_release": "r2"}, "recorded memory_release differs"),
    ({"decision_provider": "rules"}, "recorded decision_provider differs"),
])
def test_check_runs_validates_recorded_conditions(override, expected):
    matrix = load_matrix()
    base = {"world_manifest_sha256": "w", "seed": 1, "failure_profile": "none", "metrics_revision": "m", "cases": ["x"]}
    a = {**base, "config_id": "C4", "effective": _effective("C4")}
    b = {**base, "config_id": "C4a-equivalent", "effective": _effective("C4a-equivalent", **override)}
    problems = check_runs(matrix, "Q3b_storage_equivalence", a, b)
    assert any(expected in problem for problem in problems), problems


def test_check_runs_refuses_manifests_without_effective_configuration():
    matrix = load_matrix()
    base = {"world_manifest_sha256": "w", "seed": 1, "failure_profile": "none", "metrics_revision": "m", "cases": ["x"]}
    problems = check_runs(matrix, "Q2_routing", {**base, "config_id": "C1-fair"}, {**base, "config_id": "C2"})
    assert problems and "effective configuration" in problems[0]


# ---- report -----------------------------------------------------------------------------
def test_report_sections_gates_and_links(runs, world_build, aliases, tmp_path):
    leaky = _plant(runs["C2"], tmp_path / "C2-leaky", "CANARY-INC-9023")
    out = tmp_path / "report.md"
    text = report.render(
        [report.RunView(runs["C1-fair"], _m0(), LeakScanner(world_build), aliases),
         report.RunView(leaky, _m0(), LeakScanner(world_build), aliases)], _m0(), tmp_path)
    for heading in ("## Runs and provenance", "## Config matrix", "## Gates", "## Per-family results",
                    "### Q2_routing: C1-fair vs C2", "## Failures"):
        assert heading in text
    assert text.count(CAVEAT) == 2 and "SYNTHETIC" in text
    assert "| C1-fair | PASS | PASS | PASS | PASS |" in text and "| C2 | **FAIL** | PASS | PASS | PASS |" in text
    assert "CANARY-INC-9023" in text
    build_report([runs["C1-fair"], runs["C2"]], GOLD_M0, world_build, out, aliases=aliases)
    written = out.read_text()
    assert "| C2 | PASS | PASS | PASS | PASS |" in written and "not safe-grounded-successful" in written


def _m0():
    return {gold.case_id: gold for gold in (load_gold(p) for p in sorted(GOLD_M0.glob("*.yaml")))}


# ---- holdout protocol -------------------------------------------------------------------
@pytest.fixture
def holdout_cases(tmp_path):
    cases = tmp_path / "holdout-gold"
    cases.mkdir()
    for case_id in ("h-001", "h-002"):
        (cases / f"{case_id}.yaml").write_text(f"case_id: {case_id}\n")
    return cases


def _fake_run(cases, config_id="C2", case_ids=None, code=0, calls=None):
    def runner(out):
        if calls is not None:
            calls.append(out)
        out.mkdir(parents=True, exist_ok=True)
        ids = case_ids if case_ids is not None else sorted(p.stem for p in cases.glob("*.yaml"))
        (out / "manifest.json").write_text(json.dumps({
            "config_id": config_id, "cases": ids,
            "effective": {"cases_sha256": tree_sha256(cases, "*.yaml")}}))
        return code
    return runner


def test_holdout_runs_once_per_milestone_and_config(tmp_path, holdout_cases):
    log = tmp_path / "runs.log"
    calls = []
    kwargs = dict(log_path=log, cases_dir=holdout_cases)
    first = run_once("M5", "C2", _fake_run(holdout_cases, calls=calls), tmp_path / "a", git_commit="abc", **kwargs)
    assert first["status"] == "ok" and not first["forced"]
    with pytest.raises(HoldoutRefused):
        run_once("M5", "C2", _fake_run(holdout_cases, calls=calls), tmp_path / "b", **kwargs)
    with pytest.raises(HoldoutRefused):
        run_once("M5", "C2", _fake_run(holdout_cases, calls=calls), tmp_path / "b", force=True, **kwargs)
    forced = run_once("M5", "C2", _fake_run(holdout_cases, calls=calls), tmp_path / "b", force=True,
                      reason="gateway bug fixed", **kwargs)
    assert forced["forced"] and forced["reason"] == "gateway bug fixed" and forced["prior_runs"] == 1
    run_once("M5", "C4", _fake_run(holdout_cases, "C4", calls=calls), tmp_path / "c", **kwargs)
    run_once("M6", "C2", _fake_run(holdout_cases, calls=calls), tmp_path / "d", **kwargs)
    assert len(calls) == 4 and len(read_log(log)) == 4


def test_failed_holdout_attempt_is_logged_but_does_not_block(tmp_path, holdout_cases):
    log = tmp_path / "runs.log"
    run_once("M5", "C2", _fake_run(holdout_cases, code=3), tmp_path / "a", log_path=log, cases_dir=holdout_cases)
    assert read_log(log)[0]["status"] == "failed:3"
    assert run_once("M5", "C2", _fake_run(holdout_cases), tmp_path / "b", log_path=log,
                    cases_dir=holdout_cases)["status"] == "ok"


@pytest.mark.parametrize("extra", [["--config", "C4"], ["--config=C4"], ["--cases", "gold/dev"], ["--conf", "C4"],
                                   ["--sut", "stub"], ["--out", "elsewhere"], ["--config-id", "C4"]])
def test_holdout_rejects_protected_passthrough(extra):
    with pytest.raises(HoldoutRefused):
        check_passthrough(extra)
    assert check_passthrough(["--failure-profile", "none", "--seed", "3"]) == ["--failure-profile", "none", "--seed", "3"]


def test_holdout_success_requires_the_reserved_manifest(tmp_path, holdout_cases):
    log = tmp_path / "runs.log"
    wrong_config = run_once("M5", "C2", _fake_run(holdout_cases, "C4"), tmp_path / "a",
                            log_path=log, cases_dir=holdout_cases)
    wrong_cases = run_once("M5", "C2", _fake_run(holdout_cases, case_ids=["d-001"]), tmp_path / "b",
                           log_path=log, cases_dir=holdout_cases)
    assert wrong_config["status"].startswith("rejected:") and "config" in wrong_config["status"]
    assert wrong_cases["status"].startswith("rejected:") and "holdout set" in wrong_cases["status"]
    assert run_once("M5", "C2", _fake_run(holdout_cases), tmp_path / "c", log_path=log,
                    cases_dir=holdout_cases)["status"] == "ok"      # rejected attempts do not block
