"""Derive gold cases for every question spec from a rendered world build."""
import argparse
import sys
from pathlib import Path

import yaml

from sanctum_world.gold import BuildIndex, QuestionSpec, derive
from sanctum_world.schema import load_world

ROOT = Path(__file__).resolve().parents[1]


def derive_all(world_path: Path, build_dir: Path, specs_dir: Path, out_dir: Path) -> list[Path]:
    world = load_world(world_path)
    index = BuildIndex(build_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for spec_path in sorted(specs_dir.glob("*.yaml")):
        spec = QuestionSpec.model_validate(yaml.safe_load(spec_path.read_text()))
        gold = derive(world, build_dir, spec, index=index)
        out_path = out_dir / f"{spec.id}.yaml"
        out_path.write_text(yaml.safe_dump(gold.model_dump(mode="json", exclude_none=True), sort_keys=False))
        written.append(out_path)
    return written


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", type=Path, default=ROOT / "build" / "world")
    parser.add_argument("--specs", type=Path, default=ROOT / "questions" / "specs" / "sample")
    parser.add_argument("--out", type=Path, default=ROOT / "gold" / "m1")
    parser.add_argument("--world", type=Path, default=ROOT / "world" / "world.yaml")
    arguments = parser.parse_args()
    paths = derive_all(arguments.world, arguments.build, arguments.specs, arguments.out)
    if not paths:
        sys.exit(f"no specs found in {arguments.specs}")
    print(f"derived {len(paths)} gold cases into {arguments.out}")
