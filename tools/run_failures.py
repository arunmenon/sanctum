"""Run arms x failure profiles over the dev and scenario cases (M6), one run dir per pair.

Usage: python tools/run_failures.py --arm C1-fair --arm C2 [--profile none --profile flaky ...]
       [--cases gold/dev --cases gold/scenarios] [--seed 20260930] [--out runs/failures]

Every run uses the same seed and the same combined case set, so profiles are paired within an
arm. Each run goes through tools/run_lab.py; the degradation report is written to
<out>/degradation.md.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sanctum_eval.load import load_gold  # noqa: E402
from tools.report import CAVEAT, render_degradation  # noqa: E402

PROFILES = ("none", "flaky", "degraded", "skillhub_timeout")
CASE_SETS = (ROOT / "gold" / "dev", ROOT / "gold" / "scenarios")
SEED = 20260930


def combine_cases(case_dirs: list[Path], target: Path) -> Path:
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    for case_dir in case_dirs:
        for path in sorted(Path(case_dir).glob("*.yaml")):
            if (target / path.name).exists():
                raise SystemExit(f"run_failures: duplicate case file {path.name}")
            shutil.copy2(path, target / path.name)
    return target


def run_matrix(arms: list[str], profiles: list[str], cases_dir: Path, out_root: Path, seed: int,
               run_one: Callable[[str, str, Path, Path, int], int]) -> list[Path]:
    run_dirs = []
    for arm in arms:
        for profile in profiles:
            run_dir = out_root / f"{arm}__{profile}"
            code = run_one(arm, profile, cases_dir, run_dir, seed)
            if code not in (0, 1) or not (run_dir / "manifest.json").exists():
                raise SystemExit(f"run_failures: {arm} x {profile} did not produce a run (exit {code})")
            run_dirs.append(run_dir)
    return run_dirs


def run_lab(arm: str, profile: str, cases_dir: Path, run_dir: Path, seed: int, sut: str = "ref") -> int:
    command = [sys.executable, str(ROOT / "tools" / "run_lab.py"), "--sut", sut, "--config", arm,
               "--failure-profile", profile, "--seed", str(seed), "--cases", str(cases_dir), "--out", str(run_dir)]
    return subprocess.run(command, cwd=ROOT).returncode


def write_degradation(run_dirs: list[Path], cases_dir: Path, out_path: Path) -> str:
    golds = {gold.case_id: gold for gold in (load_gold(p) for p in sorted(cases_dir.glob("*.yaml")))}
    text = "\n".join(["# Sanctum Lab failure runs", "", f"> {CAVEAT}", "",
                      *render_degradation(run_dirs, golds), f"> {CAVEAT}", ""])
    out_path.write_text(text, encoding="utf-8")
    return text


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--arm", action="append", required=True)
    parser.add_argument("--profile", action="append", choices=PROFILES, default=None)
    parser.add_argument("--cases", type=Path, action="append", default=None)
    parser.add_argument("--sut", default="ref")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--out", type=Path, default=ROOT / "runs" / "failures")
    arguments = parser.parse_args()
    cases_dir = combine_cases(arguments.cases or list(CASE_SETS), arguments.out / "_cases")
    run_dirs = run_matrix(arguments.arm, arguments.profile or list(PROFILES), cases_dir, arguments.out,
                          arguments.seed, lambda a, p, c, r, s: run_lab(a, p, c, r, s, sut=arguments.sut))
    write_degradation(run_dirs, cases_dir, arguments.out / "degradation.md")
    print(f"wrote {len(run_dirs)} runs and {arguments.out / 'degradation.md'}")
