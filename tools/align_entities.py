"""Align SUT memory entity ids onto world entity refs (evaluator side; see sanctum_eval.alignment)."""
import argparse
import json
from pathlib import Path

from sanctum_eval.alignment import load_alignment
from sanctum_world.schema import load_world

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entities", type=Path, required=True, help="owners/memory_seed/<release>/entities.yaml")
    parser.add_argument("--world", type=Path, default=ROOT / "world" / "world.yaml")
    parser.add_argument("--build", type=Path, default=ROOT / "build" / "world")
    parser.add_argument("--out", type=Path, default=None, help="write the alignment table as JSON")
    arguments = parser.parse_args()
    aligned, unaligned = load_alignment(arguments.entities, load_world(arguments.world), arguments.build)
    table = json.dumps({"aligned": aligned, "unaligned": unaligned}, indent=1, sort_keys=True)
    if arguments.out:
        arguments.out.write_text(table + "\n", encoding="utf-8")
    print(table)
