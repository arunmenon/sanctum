"""M6 evaluator side: status honesty and degradation summaries over synthetic run dirs."""
import json
from pathlib import Path

import pytest

from sanctum_eval.degradation import case_honesty, deltas_vs_none, percentile, summarize_run
from sanctum_eval.load import load_gold
from tools.run_failures import combine_cases, run_matrix, write_degradation

ROOT = Path(__file__).resolve().parents[1]
GOLD_DEV = ROOT / "gold" / "dev"


@pytest.fixture(scope="module")
def golds():
    return {gold.case_id: gold for gold in (load_gold(p) for p in sorted(GOLD_DEV.glob("*.yaml")))}


def _case_with_mandatory(golds, source="skillhub"):
    return next(g for g in golds.values()
                if any(o.mandatory and o.source_id == source for o in g.source_obligations))


def _response(gold, status, sources=()):
    return {"request_id": gold.request.request_id, "evidence_status": status, "sources": list(sources)}


def _trace(gold, calls, elapsed_ms=None):
    return {"request_id": gold.request.request_id, "elapsed_ms": elapsed_ms,
            "calls": [{"source_id": s, "tool": "t", "outcome": o, "audience_valid": True} for s, o in calls]}


def test_sufficient_after_mandatory_timeout_is_dishonest(golds):
    gold = _case_with_mandatory(golds)
    honesty = case_honesty(gold, _response(gold, "sufficient", [{"source_id": "skillhub", "status": "timeout"}]),
                           _trace(gold, [("skillhub", "timeout")]))
    assert honesty.overclaimed and not honesty.honest


def test_gap_must_be_reported_for_every_non_ok_call(golds):
    gold = _case_with_mandatory(golds)
    trace = _trace(gold, [("skillhub", "timeout"), ("dochub", "error"), ("codehub", "ok")])
    silent = case_honesty(gold, _response(gold, "partial", [{"source_id": "skillhub", "status": "timeout"},
                                                            {"source_id": "dochub", "status": "called"}]), trace)
    assert silent.unreported_gaps == ("dochub",) and not silent.overclaimed
    reported = case_honesty(gold, _response(gold, "partial", [
        {"source_id": "skillhub", "status": "timeout"},
        {"source_id": "dochub", "status": "called", "reasons": ["source_error"]}]), trace)
    assert reported.honest


def test_retry_that_succeeded_is_not_a_gap(golds):
    gold = _case_with_mandatory(golds)
    honesty = case_honesty(gold, _response(gold, "sufficient"),
                           _trace(gold, [("skillhub", "timeout"), ("skillhub", "ok")]))
    assert honesty.honest


def test_percentile_nearest_rank():
    assert percentile([], 0.5) is None
    assert percentile([5.0], 0.95) == 5.0
    values = [float(v) for v in range(1, 101)]
    assert (percentile(values, 0.5), percentile(values, 0.95)) == (50.0, 95.0)


def _write_run(run_dir: Path, golds, config_id, profile, status, outcome, elapsed, success):
    run_dir.mkdir(parents=True)
    (run_dir / "manifest.json").write_text(json.dumps({"config_id": config_id, "failure_profile": profile}))
    rows = {"responses": [], "traces": [], "scores": []}
    for n, gold in enumerate(golds.values()):
        rows["responses"].append(_response(gold, status, [{"source_id": "skillhub", "status": "timeout"}]
                                           if outcome == "timeout" else []))
        rows["traces"].append(_trace(gold, [("skillhub", outcome)], elapsed + n))
        rows["scores"].append({"case_id": gold.case_id, "safe_grounded_success": success})
    for name, data in rows.items():
        (run_dir / f"{name}.jsonl").write_text("".join(json.dumps(row) + "\n" for row in data))
    return run_dir


def test_summaries_and_deltas_vs_none(golds, tmp_path):
    none = summarize_run(_write_run(tmp_path / "none", golds, "C2", "none", "sufficient", "ok", 10.0, True), golds)
    timeout = summarize_run(_write_run(tmp_path / "to", golds, "C2", "skillhub_timeout", "sufficient",
                                       "timeout", 100.0, False), golds)
    assert none.status_honesty == 1.0 and none.latency_p50_ms == 39.0 and none.failed_calls == 0
    mandatory = sum(1 for g in golds.values() if any(o.mandatory and o.source_id == "skillhub"
                                                     for o in g.source_obligations))
    assert timeout.overclaims == mandatory and timeout.failed_calls == 60
    assert timeout.status_honesty == pytest.approx(1 - mandatory / 60)
    delta = deltas_vs_none([none, timeout])[("C2", "skillhub_timeout")]
    assert delta["safe_success"] == -1.0 and delta["latency_p95_ms"] == 90.0
    assert deltas_vs_none([timeout])[("C2", "skillhub_timeout")]["safe_success"] is None


def test_run_matrix_and_degradation_report(golds, tmp_path):
    cases_dir = combine_cases([GOLD_DEV, ROOT / "gold" / "scenarios"], tmp_path / "_cases")
    assert len(list(cases_dir.glob("*.yaml"))) == 60 + len(list((ROOT / "gold" / "scenarios").glob("*.yaml")))
    calls = []

    def fake_run(arm, profile, cases, run_dir, seed):
        calls.append((arm, profile, seed))
        ok = profile == "none"
        _write_run(run_dir, golds, arm, profile, "sufficient" if ok else "partial",
                   "ok" if ok else "timeout", 5.0, ok)
        return 0

    dirs = run_matrix(["C1-fair", "C2"], ["none", "skillhub_timeout"], cases_dir, tmp_path / "out", 11, fake_run)
    assert [d.name for d in dirs] == ["C1-fair__none", "C1-fair__skillhub_timeout", "C2__none", "C2__skillhub_timeout"]
    assert {seed for _, _, seed in calls} == {11}
    text = write_degradation(dirs, GOLD_DEV, tmp_path / "degradation.md")
    assert "## Degradation under injected failures" in text and "SYNTHETIC" in text
    assert "| C2 | skillhub_timeout | 60 | 0.00 | -1.00 | 1.00 |" in text


def test_missing_run_is_refused(tmp_path):
    with pytest.raises(SystemExit):
        run_matrix(["C2"], ["none"], tmp_path, tmp_path / "out", 1, lambda *a: 2)
