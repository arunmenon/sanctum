"""D4 budget stress (prompt review §4): run the arms of configs/budget_stress.yaml at each fixed
budget over the same cases, then measure order offline from the saved responses.

Usage: python tools/run_budget_stress.py --provider <p> [--out runs/budget-stress] [--seed 20260930]

Arm "C4+D4" runs run_lab with --round3 d4 --round3-provider <p> --system-one-provider <p>. The
reorder-only gate is part of scoring at every budget. Output: one run dir per (arm, budget) and
<out>/budget-stress.md with coverage@K and first-support rank per run.
"""
import argparse
import subprocess
import sys
from pathlib import Path
from typing import Callable

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sanctum_eval.order_metrics import order_metrics_for_run  # noqa: E402
from tools.report import CAVEAT  # noqa: E402
from tools.run_failures import combine_cases  # noqa: E402

CONFIG = ROOT / "configs" / "budget_stress.yaml"


def arm_arguments(arm: str, provider: str, profile: str = "strict") -> list[str]:
    base, _, round3 = arm.partition("+")
    arguments = ["--sut", "ref", "--config", base]
    if round3:
        arguments += ["--round3", round3.lower(), "--round3-provider", provider, "--system-one-provider", provider,
                      "--system-one-profile", profile]
    return arguments


def run_stress(config: dict, cases_dir: Path, out_root: Path, seed: int, provider: str,
               run_one: Callable[[list[str], Path], int], profile: str = "strict") -> list[tuple[str, int, Path]]:
    runs = []
    for budget in config["budgets"]:
        for arm in config["arms"]:
            run_dir = out_root / f"{arm.replace('+', '_')}__{budget}"
            code = run_one([*arm_arguments(arm, provider, profile), "--cases", str(cases_dir), "--seed", str(seed),
                            "--budget-tokens", str(budget), "--out", str(run_dir)], run_dir)
            if code not in (0, 1) or not (run_dir / "manifest.json").exists():
                raise SystemExit(f"run_budget_stress: {arm} at {budget} did not produce a run (exit {code})")
            runs.append((arm, budget, run_dir))
    return runs


def render(config: dict, runs: list[tuple[str, int, Path]], cases_dir: Path) -> str:
    ks = config["prefix_k"]
    lines = ["# D4 budget stress", "", f"> {CAVEAT}", "",
             "Budgets and K fixed in configs/budget_stress.yaml before outcomes were inspected. Coverage@K is "
             "over answerable cases (n); rank is over cases with any supporting unit.", "",
             "| arm | budget | " + " | ".join(f"coverage@{k}" for k in ks) + " | first support rank (mean, median, n) | "
             "answerable without support |", "|---|---|" + "---|" * len(ks) + "---|---|"]
    for arm, budget, run_dir in runs:
        metrics = order_metrics_for_run(run_dir, cases_dir, ks)
        cells = [f"{c['mean']:.2f} (n={c['n']})" if c["mean"] is not None else "-" for c in
                 (metrics["coverage"][k] for k in ks)]
        rank = metrics["first_support_rank"]
        rank_cell = f"{rank['mean']:.2f}, {rank['median']}, {rank['n']}" if rank["mean"] is not None else "-"
        lines.append(f"| {arm} | {budget} | " + " | ".join(cells) + f" | {rank_cell} | "
                     f"{metrics['answerable_without_support']} |")
    return "\n".join(lines + ["", f"> {CAVEAT}", ""])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--out", type=Path, default=ROOT / "runs" / "budget-stress")
    parser.add_argument("--seed", type=int, default=20260930)
    parser.add_argument("--system-one-profile", default="strict", choices=["strict", "relaxed"],
                        help="System One profile for the D4 arm (strict: 150 ms, 1 call; relaxed: 60 s, 24 calls)")
    arguments = parser.parse_args()
    config = yaml.safe_load(CONFIG.read_text())
    cases_dir = combine_cases([ROOT / c for c in config["cases"]], arguments.out / "_cases")
    runs = run_stress(config, cases_dir, arguments.out, arguments.seed, arguments.provider,
                      lambda args, _: subprocess.run([sys.executable, str(ROOT / "tools" / "run_lab.py"), *args],
                                                     cwd=ROOT).returncode, arguments.system_one_profile)
    (arguments.out / "budget-stress.md").write_text(render(config, runs, cases_dir), encoding="utf-8")
    print(f"wrote {arguments.out / 'budget-stress.md'}")
