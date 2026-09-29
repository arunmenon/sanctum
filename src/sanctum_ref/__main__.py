"""`python -m sanctum_ref --config C2 --proxy-read-fd N --proxy-write-fd M`

Serves `sanctum.retrieve` on stdio. Hubs are reachable only through the gateway proxy on the two
inherited descriptors. Takes no secrets: none are accepted on argv or read from the environment.
"""
import argparse
import sys
from pathlib import Path

import anyio

from .config import UnsupportedArm, load_arm
from .server import serve

ROOT = Path(__file__).resolve().parents[2]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m sanctum_ref", description=__doc__)
    parser.add_argument("--config", required=True, help="arm id from configs/matrix.yaml")
    parser.add_argument("--matrix", type=Path, default=ROOT / "configs" / "matrix.yaml")
    parser.add_argument("--registry", type=Path, default=ROOT / "owners" / "manifests")
    parser.add_argument("--proxy-read-fd", type=int, required=True)
    parser.add_argument("--proxy-write-fd", type=int, required=True)
    arguments = parser.parse_args(argv)
    try:
        arm = load_arm(arguments.matrix, arguments.config)
    except UnsupportedArm as error:
        print(f"sanctum_ref: {error}", file=sys.stderr)
        return 2
    anyio.run(serve, arm, arguments.registry, arguments.proxy_read_fd, arguments.proxy_write_fd)
    return 0


if __name__ == "__main__":
    sys.exit(main())
