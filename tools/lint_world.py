"""Lint the authored world against a rendered build; exits non-zero on any finding."""
import argparse
import sys
from pathlib import Path

from sanctum_world.lint import lint
from sanctum_world.schema import load_world

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, default=ROOT / "build" / "world")
    parser.add_argument("--world", type=Path, default=ROOT / "world")
    arguments = parser.parse_args()
    findings = lint(load_world(arguments.world / "world.yaml"), arguments.build, arguments.world)
    for finding in findings:
        print(finding)
    print(f"{len(findings)} finding(s)")
    sys.exit(1 if findings else 0)
