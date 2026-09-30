"""`python -m sanctum_ref --config C2 --proxy-read-fd N --proxy-write-fd M`

Serves `sanctum.retrieve` on stdio. Hubs are reachable only through the gateway proxy on the two
inherited descriptors. Takes no secrets: none are accepted on argv or read from the environment.
"""
import argparse
import dataclasses
import sys
from pathlib import Path

import anyio

from .config import UnsupportedArm, load_arm
from .providers import ProviderNotApproved, build_provider
from .server import serve

ROOT = Path(__file__).resolve().parents[2]


def round3_limits(path: Path) -> dict:
    """Per-request Round 3 bounds from the provider file (`round3:`), with the design defaults."""
    import yaml
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) if Path(path).exists() else {}
    return {"d4_max_units": 20, **((data or {}).get("round3") or {})}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m sanctum_ref", description=__doc__)
    parser.add_argument("--config", required=True, help="arm id from configs/matrix.yaml")
    parser.add_argument("--matrix", type=Path, default=ROOT / "configs" / "matrix.yaml")
    parser.add_argument("--registry", type=Path, default=ROOT / "owners" / "manifests")
    parser.add_argument("--memory-seed", type=Path, default=ROOT / "owners" / "memory_seed",
                        help="memory releases (used by memory arms only)")
    parser.add_argument("--memory-release", default=None,
                        help="pin this release for the whole process instead of reading ACTIVE per request")
    parser.add_argument("--decision-provider", default=None,
                        help="D2 provider name (configs/system_one_providers.yaml, or rules/standin); default: the arm's provider switch")
    parser.add_argument("--system-one-providers", type=Path, default=ROOT / "configs" / "system_one_providers.yaml")
    parser.add_argument("--calibration-dir", type=Path, default=ROOT / "configs" / "calibration")
    parser.add_argument("--decision-params", type=Path, default=ROOT / "configs" / "d2_standin.yaml")
    parser.add_argument("--round3", default="none", choices=["none", "d6", "d4"],
                        help="Round 3 System One decision (design page §14); the config id gains +D6 / +D4")
    parser.add_argument("--round3-provider", default=None, help="provider name for the Round 3 decision")
    parser.add_argument("--proxy-read-fd", type=int, required=True)
    parser.add_argument("--proxy-write-fd", type=int, required=True)
    arguments = parser.parse_args(argv)
    try:
        arm = load_arm(arguments.matrix, arguments.config)
    except UnsupportedArm as error:
        print(f"sanctum_ref: {error}", file=sys.stderr)
        return 2
    provider = None
    if arm.decision_provider == "named":
        try:
            provider = build_provider(arguments.decision_provider or arm.provider, arguments.decision_params,
                                      arguments.system_one_providers, arguments.calibration_dir)
        except (ProviderNotApproved, ValueError) as error:
            print(f"sanctum_ref: {error}", file=sys.stderr)
            return 2
    round3_provider = None
    if arguments.round3 != "none":
        if not arguments.round3_provider:
            print("sanctum_ref: --round3 needs --round3-provider", file=sys.stderr)
            return 2
        round3_provider = build_provider(arguments.round3_provider, arguments.decision_params,
                                         arguments.system_one_providers, arguments.calibration_dir)
        if not hasattr(round3_provider, "_transport"):
            print("sanctum_ref: Round 3 needs a System One HTTP provider", file=sys.stderr)
            return 2
        arm = dataclasses.replace(arm, config_id=f"{arm.config_id}+{arguments.round3.upper()}")
    anyio.run(serve, arm, arguments.registry, arguments.proxy_read_fd, arguments.proxy_write_fd,
              arguments.memory_seed if arm.uses_memory else None, provider, arguments.memory_release,
              arguments.round3, round3_provider, round3_limits(arguments.system_one_providers)["d4_max_units"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
