"""Run the holdout set once per milestone and config, and log it (lab plan §8.3; milestones M5).

Usage: python tools/run_holdout.py --milestone M5 --config C2 [--force --reason "..."] [-- run_lab args]

Every attempt is appended to holdout/runs.log (one JSON object per line). A second successful
run for the same milestone and config is refused unless --force is given with a reason, which
is logged. Extra run_lab arguments may not override --config, --cases, --sut or --out, and a run
counts as ok only when its manifest shows the reserved config over exactly the holdout case set.
Failed or rejected attempts are logged and do not block a retry. This tool never parses holdout
questions or gold (it lists their file names and hashes them); tools/run_lab.py scores them.
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sanctum_eval.provenance import tree_sha256  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
HOLDOUT_LOG = ROOT / "holdout" / "runs.log"
HOLDOUT_GOLD = ROOT / "holdout" / "gold"


PROTECTED_OPTIONS = ("--config", "--config-id", "--cases", "--sut", "--out")


class HoldoutRefused(Exception):
    pass


def check_passthrough(arguments: list[str]) -> list[str]:
    """Extra run_lab arguments may not override the options that define the reserved run."""
    for argument in arguments:
        option = argument.split("=", 1)[0]
        if any(option == protected or (len(option) > 2 and protected.startswith(option))
               for protected in PROTECTED_OPTIONS):
            raise HoldoutRefused(f"passthrough argument {argument!r} would override a protected option")
    return arguments


def manifest_problems(out_dir: Path, config_id: str, cases_dir: Path) -> list[str]:
    """The produced run must be the reserved one: this config over exactly the holdout case set."""
    path = Path(out_dir) / "manifest.json"
    if not path.exists():
        return ["run produced no manifest"]
    manifest = json.loads(path.read_text())
    problems = []
    if manifest.get("config_id") != config_id:
        problems.append(f"manifest config {manifest.get('config_id')!r} is not {config_id!r}")
    expected_cases = sorted(p.stem for p in Path(cases_dir).glob("*.yaml"))
    if sorted(manifest.get("cases", [])) != expected_cases:
        problems.append("manifest cases are not the holdout set")
    recorded = (manifest.get("effective") or {}).get("cases_sha256")
    if recorded != tree_sha256(cases_dir, "*.yaml"):
        problems.append("manifest cases hash does not match the holdout set")
    return problems


def read_log(log_path: Path) -> list[dict]:
    if not log_path.exists():
        return []
    return [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]


def prior_runs(log_path: Path, milestone: str, config_id: str) -> list[dict]:
    return [row for row in read_log(log_path)
            if row["milestone"] == milestone and row["config"] == config_id and row["status"] == "ok"]


def run_once(milestone: str, config_id: str, runner: Callable[[Path], int], out_dir: Path,
             log_path: Path = HOLDOUT_LOG, force: bool = False, reason: Optional[str] = None,
             git_commit: Optional[str] = None, cases_dir: Path = HOLDOUT_GOLD) -> dict:
    if force and not (reason and reason.strip()):
        raise HoldoutRefused("--force needs --reason")
    previous = prior_runs(log_path, milestone, config_id)
    if previous and not force:
        raise HoldoutRefused(f"holdout already run for {milestone} {config_id} at {previous[-1]['at']}; "
                             "use --force --reason to run again")
    exit_code = runner(out_dir)
    problems = manifest_problems(out_dir, config_id, cases_dir) if exit_code == 0 else []
    status = "ok" if exit_code == 0 and not problems else (
        f"failed:{exit_code}" if exit_code != 0 else "rejected:" + "; ".join(problems))
    entry = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "milestone": milestone,
             "config": config_id, "out": str(out_dir), "git_commit": git_commit,
             "status": status,
             "forced": bool(previous) and force, "reason": reason if force else None,
             "prior_runs": len(previous)}
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry


def _git_commit() -> Optional[str]:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return result.stdout.strip() or None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--milestone", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--sut", default="ref")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--reason", default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("run_lab_args", nargs=argparse.REMAINDER)
    arguments = parser.parse_args()
    out_dir = arguments.out or ROOT / "runs" / "holdout" / f"{arguments.milestone}-{arguments.config}"
    extra = [a for a in arguments.run_lab_args if a != "--"]
    try:
        check_passthrough(extra)
    except HoldoutRefused as error:
        raise SystemExit(f"run_holdout: {error}") from None

    def run_lab(target: Path) -> int:
        command = [sys.executable, str(ROOT / "tools" / "run_lab.py"), "--sut", arguments.sut,
                   "--config", arguments.config, "--cases", str(HOLDOUT_GOLD), "--out", str(target), *extra]
        return subprocess.run(command, cwd=ROOT).returncode

    try:
        entry = run_once(arguments.milestone, arguments.config, run_lab, out_dir, force=arguments.force,
                         reason=arguments.reason, git_commit=_git_commit())
    except HoldoutRefused as error:
        raise SystemExit(f"run_holdout: {error}") from None
    print(json.dumps(entry, sort_keys=True))
    sys.exit(0 if entry["status"] == "ok" else 1)
