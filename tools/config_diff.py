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


if __name__ == "__main__":
    m = load()
    names = sys.argv[1:] or list(m["comparisons"])
    bad = False
    for n in names:
        d, extra = check_comparison(m, n)
        print(f"{n}: {d}" + (f"  !! unexpected: {sorted(extra)}" if extra else ""))
        bad |= bool(extra)
    sys.exit(1 if bad else 0)
