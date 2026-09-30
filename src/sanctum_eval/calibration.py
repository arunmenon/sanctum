"""Calibration discipline for System One decisions (prompt review §7), evaluator side.

Records are (group, raw_p, label, source). Validation is nested and grouped by case: outer folds
estimate generalization; inside each outer training split, inner folds select the calibrator and
fit the band on out-of-fold predictions only. Outer-fold results are reported with their
denominators and uncertainty and are never used to choose anything. No unit of one case is ever
split across folds.

Calibrators: Platt (logistic on logit p), regularized Platt (L2), intercept-only (slope fixed at
1), per-source intercepts with a shared slope (D2; L2 on the intercept offsets). Isotonic (PAV)
is diagnostic only: reported, never selectable.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence

EPS = 1e-6


@dataclass(frozen=True)
class Record:
    group: str          # case id; all of a case's records share a fold
    p_raw: float
    label: int
    source: str = ""    # D2 per-source intercepts


def logit(p: float) -> float:
    p = min(max(p, EPS), 1 - EPS)
    return math.log(p / (1 - p))


def sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x)) if x >= 0 else math.exp(x) / (1 + math.exp(x))


# ---- fitting ----------------------------------------------------------------------------------
def _solve(matrix: list[list[float]], vector: list[float]) -> list[float]:
    """Gaussian elimination with partial pivoting (small systems only)."""
    size = len(vector)
    augmented = [row[:] + [value] for row, value in zip(matrix, vector)]
    for col in range(size):
        pivot = max(range(col, size), key=lambda r: abs(augmented[r][col]))
        augmented[col], augmented[pivot] = augmented[pivot], augmented[col]
        if abs(augmented[col][col]) < 1e-12:
            augmented[col][col] = 1e-12
        for row in range(size):
            if row != col:
                factor = augmented[row][col] / augmented[col][col]
                augmented[row] = [a - factor * b for a, b in zip(augmented[row], augmented[col])]
    return [augmented[i][size] / augmented[i][i] for i in range(size)]


def _newton(features: list[list[float]], labels: list[int], penalty: list[float], offsets: list[float],
            iterations: int = 50) -> list[float]:
    """L2-penalized logistic regression: minimise log loss + sum(penalty_j * w_j^2 / 2)."""
    size = len(penalty)
    weights = [0.0] * size
    for _ in range(iterations):
        gradient = [penalty[j] * weights[j] for j in range(size)]
        hessian = [[penalty[j] if j == k else 0.0 for k in range(size)] for j in range(size)]
        for x, y, offset in zip(features, labels, offsets):
            p = sigmoid(offset + sum(w * v for w, v in zip(weights, x)))
            for j in range(size):
                gradient[j] += (p - y) * x[j]
                for k in range(size):
                    hessian[j][k] += p * (1 - p) * x[j] * x[k]
        step = _solve(hessian, gradient)
        weights = [w - s for w, s in zip(weights, step)]
        if max(abs(s) for s in step) < 1e-9:
            break
    return weights


Calibrator = Callable[[Record], float]


def fit_platt(records: Sequence[Record], l2: float = 0.0) -> Calibrator:
    a, b = _newton([[logit(r.p_raw), 1.0] for r in records], [r.label for r in records], [l2, l2 * 0.01],
                   [0.0] * len(records))
    return lambda r: sigmoid(a * logit(r.p_raw) + b)


def fit_intercept_only(records: Sequence[Record]) -> Calibrator:
    [b] = _newton([[1.0] for _ in records], [r.label for r in records], [1e-4], [logit(r.p_raw) for r in records])
    return lambda r: sigmoid(logit(r.p_raw) + b)


def fit_source_intercepts(records: Sequence[Record], l2: float = 1.0) -> Calibrator:
    sources = sorted({r.source for r in records})
    index = {s: i for i, s in enumerate(sources)}
    features = [[logit(r.p_raw), 1.0] + [1.0 if index[r.source] == i else 0.0 for i in range(len(sources))]
                for r in records]
    weights = _newton(features, [r.label for r in records], [1e-4, 1e-4] + [l2] * len(sources), [0.0] * len(records))
    a, b, offsets = weights[0], weights[1], dict(zip(sources, weights[2:]))
    return lambda r: sigmoid(a * logit(r.p_raw) + b + offsets.get(r.source, 0.0))


def fit_isotonic(records: Sequence[Record]) -> Calibrator:
    """Pool-adjacent-violators on raw p; diagnostic only."""
    ordered = sorted(records, key=lambda r: r.p_raw)
    blocks: list[list[float]] = []            # [upper p, sum labels, count]
    for r in ordered:
        blocks.append([r.p_raw, float(r.label), 1.0])
        while len(blocks) > 1 and blocks[-2][1] / blocks[-2][2] > blocks[-1][1] / blocks[-1][2]:
            upper, total, count = blocks.pop()
            blocks[-1] = [upper, blocks[-1][1] + total, blocks[-1][2] + count]
    uppers = [(block[0], block[1] / block[2]) for block in blocks]

    def predict(r: Record) -> float:
        for upper, value in uppers:
            if r.p_raw <= upper:
                return value
        return uppers[-1][1] if uppers else 0.5
    return predict


CALIBRATORS: dict[str, Callable[[Sequence[Record]], Calibrator]] = {
    "platt": fit_platt,
    "platt_l2": lambda records: fit_platt(records, l2=1.0),
    "intercept_only": fit_intercept_only,
    "source_intercepts": fit_source_intercepts,
}
DIAGNOSTIC = {"isotonic": fit_isotonic}


# ---- metrics ----------------------------------------------------------------------------------
def log_loss(probabilities: Sequence[float], labels: Sequence[int]) -> float:
    return -sum(y * math.log(max(p, EPS)) + (1 - y) * math.log(max(1 - p, EPS))
                for p, y in zip(probabilities, labels)) / max(len(labels), 1)


def brier(probabilities: Sequence[float], labels: Sequence[int]) -> float:
    return sum((p - y) ** 2 for p, y in zip(probabilities, labels)) / max(len(labels), 1)


def roc_auc(scores: Sequence[float], labels: Sequence[int]) -> Optional[float]:
    positives = [s for s, y in zip(scores, labels) if y]
    negatives = [s for s, y in zip(scores, labels) if not y]
    if not positives or not negatives:
        return None
    wins = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in positives for n in negatives)
    return wins / (len(positives) * len(negatives))


def wilson(successes: int, total: int, z: float = 1.96) -> Optional[tuple[float, float]]:
    """95% Wilson interval for a rate; defined at zero successes (e.g. "zero harmful skips")."""
    if total == 0:
        return None
    rate = successes / total
    centre = (rate + z * z / (2 * total)) / (1 + z * z / total)
    half = z * math.sqrt(rate * (1 - rate) / total + z * z / (4 * total * total)) / (1 + z * z / total)
    return max(0.0, centre - half), min(1.0, centre + half)


# ---- grouped, nested validation ------------------------------------------------------------------
def group_folds(records: Sequence[Record], folds: int, seed: int) -> list[list[Record]]:
    groups = sorted({r.group for r in records})
    random.Random(seed).shuffle(groups)
    fold_of = {group: n % folds for n, group in enumerate(groups)}
    return [[r for r in records if fold_of[r.group] == k] for k in range(folds)]


def _oof(records: Sequence[Record], fit: Callable, folds: int, seed: int) -> list[tuple[Record, float]]:
    out = []
    parts = group_folds(records, folds, seed)
    for k, held in enumerate(parts):
        train = [r for j, part in enumerate(parts) if j != k for r in part]
        if not held or not train or len({r.label for r in train}) < 2:
            out += [(r, sum(t.label for t in train) / len(train) if train else 0.5) for r in held]
            continue
        model = fit(train)
        out += [(r, model(r)) for r in held]
    return out


BandFit = Callable[[list[float], list[int]], object]           # (oof probabilities, labels) -> band
BandEval = Callable[[object, list[float], list[int]], dict]     # band applied to outer held-out


@dataclass
class OuterFold:
    fold: int
    n: int
    positives: int
    groups: int
    calibrator: str
    log_loss: float
    brier: float
    auc: Optional[float]
    band: object = None
    band_metrics: dict = field(default_factory=dict)


@dataclass
class NestedResult:
    folds: list[OuterFold]
    diagnostic: dict[str, dict]          # isotonic etc.: outer log loss / brier / auc, never selected

    def summary(self) -> dict:
        def spread(values):
            values = [v for v in values if v is not None]
            if not values:
                return None
            mean = sum(values) / len(values)
            sd = math.sqrt(sum((v - mean) ** 2 for v in values) / (len(values) - 1)) if len(values) > 1 else 0.0
            return {"mean": mean, "sd": sd, "folds": len(values)}
        return {"n": sum(f.n for f in self.folds), "positives": sum(f.positives for f in self.folds),
                "log_loss": spread([f.log_loss for f in self.folds]), "brier": spread([f.brier for f in self.folds]),
                "auc": spread([f.auc for f in self.folds]),
                "calibrators_selected": [f.calibrator for f in self.folds]}


def nested_cv(records: Sequence[Record], calibrators: Sequence[str] = ("platt", "platt_l2", "intercept_only"),
              outer_folds: int = 5, inner_folds: int = 4, seed: int = 20260930,
              band_fit: Optional[BandFit] = None, band_eval: Optional[BandEval] = None) -> NestedResult:
    unknown = set(calibrators) - set(CALIBRATORS)
    if unknown:
        raise ValueError(f"not selectable: {sorted(unknown)} (isotonic is diagnostic only)")
    results, diagnostic_preds = [], {name: [] for name in DIAGNOSTIC}
    parts = group_folds(records, outer_folds, seed)
    for k, held in enumerate(parts):
        train = [r for j, part in enumerate(parts) if j != k for r in part]
        if not held or len({r.label for r in train}) < 2:
            continue
        # inner: choose the calibrator by out-of-fold log loss inside the outer training split
        inner = {name: _oof(train, CALIBRATORS[name], inner_folds, seed + 1) for name in calibrators}
        chosen = min(calibrators, key=lambda name: log_loss([p for _, p in inner[name]], [r.label for r, _ in inner[name]]))
        band = band_fit([p for _, p in inner[chosen]], [r.label for r, _ in inner[chosen]]) if band_fit else None
        model = CALIBRATORS[chosen](train)
        probabilities, labels = [model(r) for r in held], [r.label for r in held]
        results.append(OuterFold(
            fold=k, n=len(held), positives=sum(labels), groups=len({r.group for r in held}), calibrator=chosen,
            log_loss=log_loss(probabilities, labels), brier=brier(probabilities, labels),
            auc=roc_auc(probabilities, labels), band=band,
            band_metrics=band_eval(band, probabilities, labels) if (band_eval and band is not None) else {}))
        for name, fit in DIAGNOSTIC.items():
            diagnostic_model = fit(train)
            diagnostic_preds[name] += [(diagnostic_model(r), r.label) for r in held]
    diagnostic = {name: {"log_loss": log_loss([p for p, _ in pairs], [y for _, y in pairs]),
                         "brier": brier([p for p, _ in pairs], [y for _, y in pairs]),
                         "auc": roc_auc([p for p, _ in pairs], [y for _, y in pairs]), "n": len(pairs)}
                  for name, pairs in diagnostic_preds.items() if pairs}
    return NestedResult(results, diagnostic)


def records_from_fit(raw: dict[tuple[str, str], float], labels: dict[tuple[str, str], int],
                     source_of: Optional[Callable[[tuple[str, str]], str]] = None) -> list[Record]:
    """tools/fit_system_one.py's shapes ({(case_id, key): p_raw}, {(case_id, key): label}) as records,
    grouped by case id; keys present in both only."""
    return [Record(group=key[0], p_raw=raw[key], label=int(labels[key]),
                   source=source_of(key) if source_of else "") for key in sorted(set(raw) & set(labels))]
