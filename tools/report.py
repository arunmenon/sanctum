"""Markdown report for a set of runs over the same cases (lab plan §9.3).

Usage: python tools/report.py --run runs/c1-fair --run runs/c2 --cases gold/dev --out report.md
"""
import argparse
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Optional

from sanctum_eval.budget import serialized_evidence_tokens
from sanctum_eval.degradation import deltas_vs_none, percentile, summarize_run
from sanctum_eval.gold import GoldCase
from sanctum_eval.leak_scan import LeakScanner, principals_for, request_texts_for
from sanctum_eval.load import load_gold
from sanctum_eval.stats import DEFAULT_SEED, metric_value, per_family_deltas
from tools.config_diff import check_runs, load as load_matrix

ROOT = Path(__file__).resolve().parents[1]
CAVEAT = ("SYNTHETIC, NOT PRODUCTION EVIDENCE. 60 dev + 40 holdout questions support directional "
          "results and debugging only, not population estimates.")
PAIRED_METRICS = ("safe_grounded_success", "recall", "sources_attempted", "wrong_entity")
# Hard gates, pass/fail per run, never averaged. Scope: no gateway anomaly (out-of-scope or
# unauthorised call) and no token audience failure. Budget: the evaluator's own cl100k recount of
# every response's serialized evidence is within the request's budget_tokens.
GATES = ("leakage", "scope", "wrong_entity", "budget")


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class RunView:
    def __init__(self, run_dir: Path, golds: dict[str, GoldCase], scanner: LeakScanner,
                 aliases: Optional[dict[str, str]]):
        self.dir = Path(run_dir)
        self.manifest = json.loads((self.dir / "manifest.json").read_text())
        self.config_id = self.manifest["config_id"]
        self.scores = {row["case_id"]: row for row in _read_jsonl(self.dir / "scores.jsonl")}
        self.receipt_lines = {row["request_id"]: number for number, row in
                              enumerate(_read_jsonl(self.dir / "receipts.jsonl"), start=1)}
        self.releases = sorted({row.get("memory_release_id") or "none"
                                for row in _read_jsonl(self.dir / "responses.jsonl")})
        self.anomalies = _read_jsonl(self.dir / "anomalies.jsonl")
        self.leaks = scanner.scan_run(self.dir, principals_for(golds.values(), aliases),
                                      request_texts_for(golds.values()))
        budgets = {gold.request.request_id: gold.request.budget_tokens for gold in golds.values()}
        recounts = [(row["request_id"], serialized_evidence_tokens(row.get("evidence", [])))
                    for row in _read_jsonl(self.dir / "responses.jsonl") if row["request_id"] in budgets]
        self.over_budget = sorted((request_id, used, budgets[request_id]) for request_id, used in recounts
                                  if used > budgets[request_id])
        self.gates = {
            "leakage": not self.leaks and not any(s["leaks"] for s in self.scores.values()),
            "scope": not self.anomalies and not any("audience" in s["gates_failed"] for s in self.scores.values()),
            "wrong_entity": not any(s["wrong_entity"] for s in self.scores.values()),
            "budget": not self.over_budget and not any("budget" in s["gates_failed"] for s in self.scores.values()),
        }


def _fmt(value, digits: int = 2) -> str:
    return "-" if value is None else f"{value:.{digits}f}"


def _link(report_dir: Path, run: RunView, request_id: str) -> str:
    target = os.path.relpath(run.dir / "receipts.jsonl", report_dir)
    return f"[receipt]({target}#L{run.receipt_lines.get(request_id, 1)})"


def render(runs: list[RunView], golds: dict[str, GoldCase], report_dir: Path,
           seed: int = DEFAULT_SEED) -> str:
    matrix = load_matrix()
    out = ["# Sanctum Lab report", "", f"> {CAVEAT}", "",
           f"Ranker: `{matrix['shared']['ranker']}` in every arm; the B* cross-encoder profile is deferred "
           "(discrepancy register 18), so these are lexical-ranker results.", ""]

    out += ["## Runs and provenance", "",
            "| config | run | world sha256 | seed | memory release | failure profile | git commit | dirty | integrity |",
            "|---|---|---|---|---|---|---|---|---|"]
    for run in runs:
        m = run.manifest
        out.append(f"| {run.config_id} | `{run.dir.name}` | `{m['world_manifest_sha256'][:12]}` | {m['seed']} | "
                   f"{', '.join(run.releases)} | {m['failure_profile']} | `{str(m.get('git_commit'))[:10]}` | "
                   f"{m.get('git_dirty')} | {m['integrity']['ok']} |")

    switches = list(next(iter(matrix["arms"].values())))
    out += ["", "## Config matrix", "", "| config | " + " | ".join(switches) + " |",
            "|---|" + "---|" * len(switches)]
    for run in runs:
        arm = matrix["arms"].get(run.config_id, {})
        out.append(f"| {run.config_id} | " + " | ".join(str(arm.get(k, "-")) for k in switches) + " |")

    out += ["", "## Gates (pass/fail, never averaged)", "", "| config | " + " | ".join(GATES) + " |",
            "|---|" + "---|" * len(GATES)]
    for run in runs:
        out.append(f"| {run.config_id} | " + " | ".join("PASS" if run.gates[g] else "**FAIL**" for g in GATES) + " |")
    for run in runs:
        for request_id, used, budget in run.over_budget:
            out.append(f"- {run.config_id} over budget: {request_id} recounted {used} > {budget} tokens")
        for leak in run.leaks[:20]:
            out.append(f"- {run.config_id} leak: {leak.kind} `{leak.token[:60]}` in {leak.file}:{leak.line}")

    out += ["", "## Per-family results", ""]
    families = sorted({gold.family for gold in golds.values()})
    header = "| family | n | " + " | ".join(f"{run.config_id} success | {run.config_id} recall" for run in runs) + " |"
    out += [header, "|---|---|" + "---|---|" * len(runs)]
    for family in families + ["all"]:
        ids = [c for c, g in golds.items() if family in ("all", g.family)]
        cells = []
        for run in runs:
            success = [metric_value(run.scores[c], "safe_grounded_success") for c in ids if c in run.scores]
            recall = [v for v in (metric_value(run.scores[c], "recall") for c in ids if c in run.scores) if v is not None]
            cells += [_fmt(sum(success) / len(success) if success else None),
                      _fmt(sum(recall) / len(recall) if recall else None)]
        out.append(f"| {family} | {len(ids)} | " + " | ".join(cells) + " |")

    out += ["", "## Paired comparisons (b minus a, 95% cluster bootstrap by family and entity)", ""]
    by_config = {run.config_id: run for run in runs}
    compared = False
    for name, comparison in matrix["comparisons"].items():
        a, b = by_config.get(comparison["a"]), by_config.get(comparison["b"])
        if not (a and b):
            continue
        compared = True
        out += [f"### {name}: {comparison['a']} vs {comparison['b']}", ""]
        problems = check_runs(matrix, name, a.manifest, b.manifest)
        if problems:
            out += [f"Not comparable: {'; '.join(problems)}", ""]
            continue
        out += ["| metric | scope | n | clusters | a | b | delta | interval | b better | a better |",
                "|---|---|---|---|---|---|---|---|---|---|"]
        for metric in PAIRED_METRICS:
            for row in per_family_deltas(a.scores, b.scores, golds, metric, seed=seed):
                if row.n_cases:
                    out.append(f"| {metric} | {row.scope} | {row.n_cases} | {row.n_clusters} | {_fmt(row.mean_a)} | "
                               f"{_fmt(row.mean_b)} | {_fmt(row.delta)} | [{_fmt(row.low)}, {_fmt(row.high)}] | "
                               f"{row.b_better} | {row.a_better} |")
        out.append("")
    if not compared:
        out += ["No matrix comparison has both arms in this run set.", ""]

    out += render_system_one(runs)
    if any(run.manifest["failure_profile"] != "none" for run in runs):
        out += render_degradation([run.dir for run in runs], golds)
    out += ["## Failures", ""]
    for run in runs:
        failing = [c for c, s in sorted(run.scores.items()) if not s["safe_grounded_success"]]
        out.append(f"**{run.config_id}**: {len(failing)} of {len(run.scores)} cases not safe-grounded-successful")
        for case_id in failing:
            gold = golds[case_id]
            gates = ", ".join(run.scores[case_id]["gates_failed"]) or "quality"
            out.append(f"- {case_id} ({gold.family}): {gates} {_link(report_dir, run, gold.request.request_id)}")
        out.append("")
    out += [f"> {CAVEAT}", ""]
    return "\n".join(out)


def render_system_one(runs: list["RunView"]) -> list[str]:
    """Model calls observed by the runner-side broker, per run (provider, profile). Reported, never a
    gate: latency is dominated by the laptop-to-hosted network (design page, owner decision)."""
    rows = []
    for run in runs:
        calls = [call for trace in _read_jsonl(run.dir / "traces.jsonl") for call in trace.get("model_calls", [])]
        if not calls:
            continue
        system_one = run.manifest.get("system_one") or {}
        latencies = [call["elapsed_ms"] for call in calls if call.get("calls")]    # calls that reached the provider
        outcomes = defaultdict(int)
        for call in calls:
            outcomes[call.get("reason") or call["outcome"]] += 1
        rows.append(f"| {run.config_id} | {system_one.get('provider', calls[0]['provider'])} | "
                    f"{', '.join(system_one.get('resolved_models') or sorted({c['model'] for c in calls if c.get('model')})) or '-'} | "
                    f"{system_one.get('profile', calls[0]['profile'])} | {len(calls)} | "
                    f"{', '.join(f'{k} {v}' for k, v in sorted(outcomes.items()))} | "
                    f"{_fmt(percentile(latencies, 0.5), 1)} | {_fmt(percentile(latencies, 0.95), 1)} |")
    if not rows:
        return []
    return ["## System One model calls (reported, not gated)", "",
            "Runner-side broker observations, separate from source calls. Latency includes broker, network, "
            "validation, batching and retries; from a laptop to a hosted endpoint it is not evidence about the "
            "fast path.", "",
            "| config | provider | resolved model | profile | tool calls | outcomes | p50 ms | p95 ms |",
            "|---|---|---|---|---|---|---|---|", *rows, ""]


def render_degradation(run_dirs: list[Path], golds: dict[str, GoldCase]) -> list[str]:
    """Per arm and failure profile; deltas are against the same arm's `none` run."""
    summaries = sorted((summarize_run(run_dir, golds) for run_dir in run_dirs),
                       key=lambda s: (s.config_id, s.failure_profile != "none", s.failure_profile))
    deltas = deltas_vs_none(summaries)
    out = ["## Degradation under injected failures", "",
           "Status honesty: never `sufficient` when a retrieval operation (search or fetch, per tool) on a "
           "mandatory source timed out or errored without a successful retry (runner-observed trace), and every "
           "failed source reported as a gap with a failure status or explicit failure reason. Latency is the "
           "runner's wall clock around each request (simulated hub latency, scaled).", "",
           "| config | profile | n | success | d success | honesty | overclaims | unreported gaps | unknown | "
           "partial | failed calls | p50 ms | p95 ms | d p95 ms |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in summaries:
        d = deltas[(s.config_id, s.failure_profile)]
        out.append(f"| {s.config_id} | {s.failure_profile} | {s.n_cases} | {_fmt(s.safe_success)} | "
                   f"{_fmt(d['safe_success'])} | {_fmt(s.status_honesty)} | {s.overclaims} | {s.unreported_gaps} | "
                   f"{_fmt(s.unknown_rate)} | {_fmt(s.partial_rate)} | {s.failed_calls} | "
                   f"{_fmt(s.latency_p50_ms, 1)} | {_fmt(s.latency_p95_ms, 1)} | {_fmt(d['latency_p95_ms'], 1)} |")
    for s in summaries:
        if s.dishonest_cases:
            out.append(f"- {s.config_id} / {s.failure_profile} dishonest status: {', '.join(s.dishonest_cases)}")
    return out + [""]


def build_report(run_dirs: list[Path], cases_dir: Path, world_build: Path, out_path: Path,
                 aliases: Optional[dict[str, str]] = None, seed: int = DEFAULT_SEED) -> str:
    golds = {gold.case_id: gold for gold in (load_gold(p) for p in sorted(Path(cases_dir).glob("*.yaml")))}
    scanner = LeakScanner(world_build)
    runs = [RunView(run_dir, golds, scanner, aliases) for run_dir in run_dirs]
    text = render(runs, golds, Path(out_path).resolve().parent, seed)
    Path(out_path).write_text(text, encoding="utf-8")
    return text


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, action="append", required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--world-build", type=Path, default=ROOT / "build" / "world")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    build_report(arguments.run, arguments.cases, arguments.world_build, arguments.out, seed=arguments.seed)
    print(f"wrote {arguments.out}")
