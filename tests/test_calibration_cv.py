"""Nested, case-grouped calibration validation (prompt review §7)."""
import random

import pytest

from sanctum_eval.calibration import (
    CALIBRATORS, Record, fit_intercept_only, fit_isotonic, fit_platt, fit_source_intercepts, group_folds, nested_cv,
    roc_auc, wilson,
)


def _records(n_cases=40, per_case=4, seed=3, shift=0.0):
    rng = random.Random(seed)
    out = []
    for case in range(n_cases):
        for unit in range(per_case):
            label = int(rng.random() < 0.3)
            p = min(max(0.2 + 0.5 * label + shift + rng.gauss(0, 0.15), 0.01), 0.99)
            out.append(Record(group=f"case-{case}", p_raw=p, label=label, source=["codehub", "skillhub"][unit % 2]))
    return out


def test_groups_never_split_across_folds():
    records = _records()
    folds = group_folds(records, 5, seed=1)
    owner = {}
    for k, fold in enumerate(folds):
        for r in fold:
            assert owner.setdefault(r.group, k) == k
    assert sum(len(f) for f in folds) == len(records)


def test_calibrators_fit_and_rank_sensibly():
    records = _records(shift=0.2)                     # raw p too high: calibration should pull it down
    for fit in (fit_platt, fit_intercept_only, fit_source_intercepts, fit_isotonic):
        model = fit(records)
        mean_p = sum(model(r) for r in records) / len(records)
        assert abs(mean_p - sum(r.label for r in records) / len(records)) < 0.08, fit.__name__
    platt = fit_platt(records)
    assert roc_auc([platt(r) for r in records], [r.label for r in records]) > 0.8


def test_nested_cv_selects_inside_and_reports_outer_with_denominators():
    records = _records()
    band_fit = lambda probs, labels: 0.5
    band_eval = lambda band, probs, labels: {"above": sum(p >= band for p in probs), "n": len(probs)}
    result = nested_cv(records, outer_folds=5, inner_folds=3, band_fit=band_fit, band_eval=band_eval)
    assert len(result.folds) == 5
    summary = result.summary()
    assert summary["n"] == len(records) and summary["positives"] == sum(r.label for r in records)
    assert summary["auc"]["folds"] == 5 and summary["auc"]["sd"] >= 0
    assert all(f.calibrator in CALIBRATORS and f.band_metrics["n"] == f.n for f in result.folds)
    assert set(result.diagnostic) == {"isotonic"}
    assert nested_cv(records, outer_folds=5, inner_folds=3).summary() == nested_cv(records, outer_folds=5, inner_folds=3).summary()


def test_isotonic_is_not_selectable():
    with pytest.raises(ValueError):
        nested_cv(_records(), calibrators=("platt", "isotonic"))


def test_wilson_interval_at_zero():
    low, high = wilson(0, 30)
    assert low == 0.0 and 0.08 < high < 0.13
    assert wilson(0, 0) is None


def test_records_from_fit_shapes():
    from sanctum_eval.calibration import records_from_fit

    raw = {("c1", "codehub"): 0.7, ("c1", "skillhub"): 0.2, ("c2", "codehub"): 0.4}
    labels = {("c1", "codehub"): 1, ("c2", "codehub"): 0, ("c3", "x"): 1}
    records = records_from_fit(raw, labels, source_of=lambda key: key[1])
    assert [(r.group, r.label, r.source) for r in records] == [("c1", 1, "codehub"), ("c2", 0, "codehub")]
