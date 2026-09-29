"""Seeded failure knobs (plan M2 decision 7)."""
from collections import Counter
from pathlib import Path

import pytest

from sanctum_hubs.failure import FailureProfileError, load_failure_injector
from sanctum_hubs.interfaces import FailureDraw, FailureInjector, FailureOutcome, HubError, ErrorCode

PROFILES = Path(__file__).resolve().parents[2] / "configs" / "failure_profiles.yaml"
DRAW_COUNT = 2000


def draws(injector, hub="codehub", tool="search", count=DRAW_COUNT):
    return [injector.draw(f"req-{index:05d}", hub, tool, index % 3) for index in range(count)]


def test_none_profile_never_fails():
    injector = load_failure_injector(PROFILES, "none", run_seed=7, time_scale=0)
    assert isinstance(injector, FailureInjector)
    outcomes = {draw.outcome for draw in draws(injector)}
    assert outcomes == {FailureOutcome.OK}
    assert all(draw.latency_ms == 0 for draw in draws(injector, count=50))


@pytest.mark.parametrize("profile,rates", [
    ("flaky", {"timeout": 0.05, "error": 0.05, "partial": 0.10}),
    ("degraded", {"timeout": 0.15, "error": 0.10, "partial": 0.20}),
])
def test_rates_within_tolerance(profile, rates):
    injector = load_failure_injector(PROFILES, profile, run_seed=20260930, time_scale=0)
    counts = Counter(draw.outcome.value for draw in draws(injector))
    for outcome, rate in rates.items():
        # Four binomial standard deviations around the configured rate.
        tolerance = 4 * (rate * (1 - rate) / DRAW_COUNT) ** 0.5
        assert abs(counts[outcome] / DRAW_COUNT - rate) <= tolerance, (outcome, counts)


def test_latency_median_and_p95():
    injector = load_failure_injector(PROFILES, "flaky", run_seed=3, time_scale=0)
    latencies = sorted(draw.latency_ms for draw in draws(injector))
    median = latencies[DRAW_COUNT // 2]
    p95 = latencies[int(DRAW_COUNT * 0.95)]
    assert 34 <= median <= 47
    assert 190 <= p95 <= 320


def test_same_seed_same_outcomes_and_order_independent():
    first = load_failure_injector(PROFILES, "flaky", run_seed=11, time_scale=0)
    second = load_failure_injector(PROFILES, "flaky", run_seed=11, time_scale=0)
    forward = draws(first)
    backward = [second.draw(f"req-{index:05d}", "codehub", "search", index % 3)
                for index in reversed(range(DRAW_COUNT))][::-1]
    assert forward == backward
    other_seed = draws(load_failure_injector(PROFILES, "flaky", run_seed=12, time_scale=0))
    assert forward != other_seed


def test_draw_varies_with_each_key_component():
    injector = load_failure_injector(PROFILES, "flaky", run_seed=5, time_scale=0)
    base = injector.draw("req-1", "codehub", "search", 0)
    variants = [injector.draw("req-2", "codehub", "search", 0), injector.draw("req-1", "dochub", "search", 0),
                injector.draw("req-1", "codehub", "fetch", 0), injector.draw("req-1", "codehub", "search", 1)]
    assert all(variant.latency_ms != base.latency_ms for variant in variants)


def test_hub_override_wins():
    injector = load_failure_injector(PROFILES, "skillhub_timeout", run_seed=1, time_scale=0)
    assert {draw.outcome for draw in draws(injector, hub="skillhub", count=200)} == {FailureOutcome.TIMEOUT}
    assert {draw.outcome for draw in draws(injector, hub="codehub", count=200)} == {FailureOutcome.OK}


def test_time_scale_default_and_override():
    assert load_failure_injector(PROFILES, "flaky", run_seed=1).time_scale == 1.0
    assert load_failure_injector(PROFILES, "flaky", run_seed=1, time_scale=0).time_scale == 0.0


def test_timeout_distinct_from_empty():
    injector = load_failure_injector(PROFILES, "skillhub_timeout", run_seed=1, time_scale=0)
    draw = injector.draw("req-1", "skillhub", "search", 0)
    assert draw.outcome is FailureOutcome.TIMEOUT
    timeout_body = HubError(ErrorCode.TIMEOUT).body()
    assert timeout_body["error"]["code"] == "timeout"
    assert timeout_body != {"results": []}


def test_partial_drops_at_least_one_row():
    injector = load_failure_injector(PROFILES, "degraded", run_seed=9, time_scale=0)
    partial = next(draw for draw in draws(injector) if draw.outcome is FailureOutcome.PARTIAL)
    assert partial.keep_fraction == 0.5
    assert partial.kept(10) == 5
    assert partial.kept(1) == 0
    assert partial.kept(0) == 0
    assert FailureDraw(FailureOutcome.OK).kept(10) == 10


def test_unknown_profile_and_bad_rates(tmp_path):
    with pytest.raises(FailureProfileError):
        load_failure_injector(PROFILES, "missing", run_seed=1)
    bad = tmp_path / "bad.yaml"
    bad.write_text("defaults: {partial_keep: 0.5}\nprofiles:\n  broken:\n    default: "
                   "{latency_ms: {median: 1, p95: 2}, timeout_rate: 0.7, error_rate: 0.5, partial_rate: 0}\n")
    with pytest.raises(FailureProfileError):
        load_failure_injector(bad, "broken", run_seed=1)
