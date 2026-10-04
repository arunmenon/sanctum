"""Validate task-bundle inputs offline; never launches an agent."""
import argparse
import json
from pathlib import Path

from sanctum_run.bundle import BundleError, validate_bundle


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    try:
        result = validate_bundle(args.config)
    except BundleError as exc:
        parser.exit(2, f"Bundle validation failed: {exc}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
