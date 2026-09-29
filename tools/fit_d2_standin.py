"""Fit the D2 stand-in's logistic calibration on dev runs only (lab plan §7.3).

Labels come from scores of counterfactual runs, never from gold contents: C1-fair is run on the
dev cases once with every hub and once per hub with that hub's manifest removed (so the SUT
never calls it). A hub is useful for a case when removing it lowers the case's recall. The
feature is the TF-IDF cosine between the public query and the hub's pinned descriptor. Writes
`calibration` and `provenance` into configs/d2_standin.yaml; descriptors and bands are kept.
"""
import argparse
import datetime
import math
import shutil
import tempfile
from pathlib import Path

import yaml

from sanctum_run.process_sut import ProcessSUT
from sanctum_run.runner import DEFAULT_WORLD_BUILD, RunConfig, git_state, load_cases, public_request, run
from sanctum_ref.decision import tfidf_cosine

ROOT = Path(__file__).resolve().parents[1]
MANIFESTS = ROOT / "owners" / "manifests"


def recalls(cases: Path, out: Path, registry: Path, world: Path) -> dict[str, float]:
    result = run(ProcessSUT(["--config", "C1-fair", "--registry", str(registry)]),
                 RunConfig(cases_dir=cases, out_dir=out, seed=20260930, sut_name="ref", config_id="C1-fair",
                           world_build_dir=world))
    return {score.case_id: score.recall for score in result.scores if score.recall is not None}


def fit(points: list[tuple[float, int]], steps: int = 4000, rate: float = 0.5) -> tuple[float, float]:
    a = b = 0.0
    for _ in range(steps):
        grad_a = grad_b = 0.0
        for x, y in points:
            p = 1 / (1 + math.exp(-(a * x + b)))
            grad_a += (p - y) * x
            grad_b += p - y
        a -= rate * grad_a / len(points)
        b -= rate * grad_b / len(points)
    return a, b


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=ROOT / "gold" / "dev")
    parser.add_argument("--params", type=Path, default=ROOT / "configs" / "d2_standin.yaml")
    parser.add_argument("--world-build", type=Path, default=DEFAULT_WORLD_BUILD)
    arguments = parser.parse_args()
    if "holdout" in str(arguments.cases.resolve()):
        raise SystemExit("fit on dev cases only")
    params = yaml.safe_load(arguments.params.read_text())
    queries = {gold.case_id: public_request(gold).query for gold in load_cases(arguments.cases)}
    with tempfile.TemporaryDirectory() as scratch:
        scratch = Path(scratch)
        full = recalls(arguments.cases, scratch / "full", MANIFESTS, arguments.world_build)
        points = []
        for hub_id in params["descriptors"]:
            registry = scratch / f"without-{hub_id}"
            shutil.copytree(MANIFESTS, registry)
            (registry / f"{hub_id}.yaml").unlink()
            without = recalls(arguments.cases, scratch / f"run-{hub_id}", registry, arguments.world_build)
            for case_id, recall in full.items():
                useful = int(without.get(case_id, recall) < recall - 1e-9)
                similarity = tfidf_cosine(queries[case_id], params["descriptors"][hub_id], params["descriptors"])
                points.append((similarity, useful))
    a, b = fit(points)
    params["calibration"] = {"a": round(a, 4), "b": round(b, 4)}
    params["provenance"] = {
        "fitted_on": "dev", "cases": str(arguments.cases.relative_to(ROOT)), "points": len(points),
        "positives": sum(y for _, y in points), "label": "recall drop when the hub is removed (C1-fair runs)",
        "fitted_at": datetime.date.today().isoformat(), "git_commit": git_state()["git_commit"]}
    arguments.params.write_text("# D2 stand-in provider (lab plan §7.3). Descriptors are pinned (HLD §9.7) and written from\n"
                                "# hub-visible structure; calibration is fitted by tools/fit_d2_standin.py on dev runs only.\n"
                                + yaml.safe_dump(params, sort_keys=False, width=120))
    print(params["calibration"], params["provenance"])
