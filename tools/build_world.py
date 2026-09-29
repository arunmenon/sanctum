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
    arguments = parser.parse_args()
    manifest = build(arguments.world, arguments.seed, arguments.out)
    print(json.dumps({"out": str(arguments.out), "seed": manifest["seed"],
                      "total_artifacts": manifest["total_artifacts"],
                      "counts": manifest["counts"]}, indent=1, sort_keys=True))
