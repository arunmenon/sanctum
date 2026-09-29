"""Paired comparisons across arms (lab plan §9.2).

Every arm answers every case, so each case contributes one paired difference (b minus a).
Intervals come from a cluster bootstrap: clusters are (family, primary entity), because questions
about the same entity are correlated; clusters are resampled whole and never split. Seeded and
deterministic. With 60 + 40 questions the intervals support directional reading only.
"""
import random
from dataclasses import dataclass
from typing import Callable, Iterable, Optional

from .gold import GoldCase

DEFAULT_RESAMPLES = 2000
DEFAULT_SEED = 20260930


def metric_value(score: dict, metric: str) -> Optional[float]:
    value = score.get(metric)
    if value is None:
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, list):         # gates_failed, wrong_entity, leaks: 1 when any
        return 1.0 if value else 0.0
    raise TypeError(f"metric {metric!r} is not numeric")


def cluster_key(gold: GoldCase) -> str:
    entity = gold.interpretations[0].entity_ref if gold.interpretations else "none"
    return f"{gold.family}|{entity}"


@dataclass(frozen=True)
class PairedDelta:
    scope: str                    # "pooled" or a family name
    metric: str
    n_cases: int
    n_clusters: int
    mean_a: Optional[float]
    mean_b: Optional[float]
    delta: Optional[float]        # mean of (b - a)
    low: Optional[float]
    high: Optional[float]
    b_better: int
    a_better: int


def paired_delta(scores_a: dict[str, dict], scores_b: dict[str, dict], golds: dict[str, GoldCase],
                 metric: str, scope: str = "pooled", case_ids: Optional[Iterable[str]] = None,
                 resamples: int = DEFAULT_RESAMPLES, seed: int = DEFAULT_SEED,
                 level: float = 0.95) -> PairedDelta:
    if set(scores_a) != set(scores_b):
        raise ValueError("paired comparison needs both arms to answer the same cases")
    ids = sorted(case_ids if case_ids is not None else scores_a)
    pairs: dict[str, list[float]] = {}
    values_a, values_b, b_better, a_better = [], [], 0, 0
    for case_id in ids:
        a, b = metric_value(scores_a[case_id], metric), metric_value(scores_b[case_id], metric)
        if a is None or b is None:
            continue
        values_a.append(a)
        values_b.append(b)
        b_better += b > a
        a_better += a > b
        pairs.setdefault(cluster_key(golds[case_id]), []).append(b - a)
    if not pairs:
        return PairedDelta(scope, metric, 0, 0, None, None, None, None, None, 0, 0)
    clusters = [pairs[key] for key in sorted(pairs)]
    delta = _mean([d for cluster in clusters for d in cluster])
    low, high = cluster_bootstrap(clusters, _mean_of_clusters, resamples, seed, level)
    return PairedDelta(scope, metric, len(values_a), len(clusters), _mean(values_a), _mean(values_b),
                       delta, low, high, b_better, a_better)


def per_family_deltas(scores_a, scores_b, golds, metric, **kwargs) -> list[PairedDelta]:
    families = sorted({golds[case_id].family for case_id in scores_a})
    rows = [paired_delta(scores_a, scores_b, golds, metric, scope="pooled", **kwargs)]
    for family in families:
        ids = [case_id for case_id in scores_a if golds[case_id].family == family]
        rows.append(paired_delta(scores_a, scores_b, golds, metric, scope=family, case_ids=ids, **kwargs))
    return rows


def cluster_bootstrap(clusters: list[list[float]], statistic: Callable[[list[list[float]]], float],
                      resamples: int, seed: int, level: float) -> tuple[float, float]:
    generator = random.Random(seed)
    draws = sorted(statistic([clusters[generator.randrange(len(clusters))] for _ in clusters])
                   for _ in range(resamples))
    tail = (1.0 - level) / 2.0
    return draws[int(tail * (resamples - 1))], draws[int((1.0 - tail) * (resamples - 1))]


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _mean_of_clusters(clusters: list[list[float]]) -> float:
    return _mean([value for cluster in clusters for value in cluster])
