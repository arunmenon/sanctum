"""Show and check config diffs. Usage: python tools/config_diff.py [comparison]"""
import sys
from pathlib import Path

import yaml

MATRIX = Path(__file__).resolve().parents[1] / "configs" / "matrix.yaml"


def load():
    return yaml.safe_load(MATRIX.read_text())


def diff(m, a, b):
    A, B = m["arms"][a], m["arms"][b]
    if set(A) != set(B):
        raise ValueError(f"{a} and {b} declare different switches")
    return {k: (A[k], B[k]) for k in A if A[k] != B[k]}


def check_comparison(m, name):
    c = m["comparisons"][name]
    d = diff(m, c["a"], c["b"])
    extra = set(d) - set(c["may_differ"])
    return d, extra


PAIRED_MANIFEST_KEYS = ("world_manifest_sha256", "seed", "failure_profile", "metrics_revision", "cases")


def check_runs(m, name, manifest_a, manifest_b):
    """Problems that make two runs unfit for comparison `name`; empty when they are paired."""
    c = m["comparisons"][name]
    problems = []
    if (manifest_a.get("config_id"), manifest_b.get("config_id")) != (c["a"], c["b"]):
        problems.append(f"runs are {manifest_a.get('config_id')} vs {manifest_b.get('config_id')}, "
                        f"comparison needs {c['a']} vs {c['b']}")
    _, extra = check_comparison(m, name)
    if extra:
        problems.append(f"switches outside may_differ: {sorted(extra)}")
    for key in PAIRED_MANIFEST_KEYS:
        if manifest_a.get(key) != manifest_b.get(key):
            problems.append(f"{key} differs between runs")
    return problems


if __name__ == "__main__":
    m = load()
    names = sys.argv[1:] or list(m["comparisons"])
    bad = False
    for n in names:
        d, extra = check_comparison(m, n)
        print(f"{n}: {d}" + (f"  !! unexpected: {sorted(extra)}" if extra else ""))
        bad |= bool(extra)
    sys.exit(1 if bad else 0)
