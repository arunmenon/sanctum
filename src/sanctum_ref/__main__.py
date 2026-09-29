"""`python -m sanctum_ref --config C2 --proxy-read-fd N --proxy-write-fd M`

Serves `sanctum.retrieve` on stdio. Hubs are reachable only through the gateway proxy on the two
inherited descriptors. Takes no secrets: none are accepted on argv or read from the environment.
"""
import argparse
import sys
from pathlib import Path

import anyio

from .config import UnsupportedArm, load_arm
from .decision import ProviderNotApproved, build_provider
from .server import serve

ROOT = Path(__file__).resolve().parents[2]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m sanctum_ref", description=__doc__)
    parser.add_argument("--config", required=True, help="arm id from configs/matrix.yaml")
    parser.add_argument("--matrix", type=Path, default=ROOT / "configs" / "matrix.yaml")
    parser.add_argument("--registry", type=Path, default=ROOT / "owners" / "manifests")
    parser.add_argument("--memory-seed", type=Path, default=ROOT / "owners" / "memory_seed",
                        help="memory releases (used by memory arms only)")
    parser.add_argument("--memory-release", default=None,
                        help="pin this release for the whole process instead of reading ACTIVE per request")
    parser.add_argument("--decision-provider", default="standin", choices=["rules", "standin", "jev"],
                        help="D2 provider for arms with decision_provider: named")
    parser.add_argument("--decision-params", type=Path, default=ROOT / "configs" / "d2_standin.yaml")
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
            provider = build_provider(arguments.decision_provider, arguments.decision_params)
        except ProviderNotApproved as error:
            print(f"sanctum_ref: {error}", file=sys.stderr)
            return 2
    anyio.run(serve, arm, arguments.registry, arguments.proxy_read_fd, arguments.proxy_write_fd,
              arguments.memory_seed if arm.uses_memory else None, provider, arguments.memory_release)
    return 0


if __name__ == "__main__":
    sys.exit(main())
