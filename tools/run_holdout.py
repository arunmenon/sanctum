"""Run the holdout set once per milestone and config, and log it (lab plan §8.3; milestones M5).

Usage: python tools/run_holdout.py --milestone M5 --config C2 [--force --reason "..."] [-- run_lab args]

Every attempt is appended to holdout/runs.log (one JSON object per line). A second successful
run for the same milestone and config is refused unless --force is given with a reason, which
is logged. Failed attempts are logged and do not block a retry. This tool never reads holdout
questions or gold itself; tools/run_lab.py scores them.
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).resolve().parents[1]
HOLDOUT_LOG = ROOT / "holdout" / "runs.log"
HOLDOUT_GOLD = ROOT / "holdout" / "gold"


class HoldoutRefused(Exception):
    pass


def read_log(log_path: Path) -> list[dict]:
    if not log_path.exists():
        return []
    return [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]


def prior_runs(log_path: Path, milestone: str, config_id: str) -> list[dict]:
    return [row for row in read_log(log_path)
            if row["milestone"] == milestone and row["config"] == config_id and row["status"] == "ok"]


def run_once(milestone: str, config_id: str, runner: Callable[[Path], int], out_dir: Path,
             log_path: Path = HOLDOUT_LOG, force: bool = False, reason: Optional[str] = None,
             git_commit: Optional[str] = None) -> dict:
    if force and not (reason and reason.strip()):
        raise HoldoutRefused("--force needs --reason")
    previous = prior_runs(log_path, milestone, config_id)
    if previous and not force:
        raise HoldoutRefused(f"holdout already run for {milestone} {config_id} at {previous[-1]['at']}; "
                             "use --force --reason to run again")
    exit_code = runner(out_dir)
    entry = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "milestone": milestone,
             "config": config_id, "out": str(out_dir), "git_commit": git_commit,
             "status": "ok" if exit_code == 0 else f"failed:{exit_code}",
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
