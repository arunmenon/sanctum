"""Render world/world.yaml into hub corpora and the private provenance index."""
import argparse
import json
from pathlib import Path

from sanctum_world.render import build

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=None, help="filler seed (default: world seed)")
    parser.add_argument("--out", type=Path, default=ROOT / "build" / "world")
    parser.add_argument("--world", type=Path, default=ROOT / "world")
    parser.add_argument("--overlay", type=Path, action="append", default=[],
                        help="world overlay merged at build time (world/challenge-d6.yaml -> build/world-challenge)")
    arguments = parser.parse_args()
    if arguments.overlay and arguments.out.resolve() == (ROOT / "build" / "world").resolve():
        raise SystemExit("build_world: overlays build elsewhere (e.g. --out build/world-challenge); build/world is the base world")
    manifest = build(arguments.world, arguments.seed, arguments.out, overlays=tuple(arguments.overlay))
    print(json.dumps({"out": str(arguments.out), "seed": manifest["seed"],
                      "total_artifacts": manifest["total_artifacts"],
                      "counts": manifest["counts"]}, indent=1, sort_keys=True))
