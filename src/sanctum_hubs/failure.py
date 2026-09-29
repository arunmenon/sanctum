"""Seeded failure knobs (plan M2 decision 7).

`load_failure_injector(profiles_path, profile, run_seed)` reads `configs/failure_profiles.yaml`
and returns a `FailureInjector`. Each draw is a pure function of
`(run_seed, request_id, hub, tool, call_index)`: the five values are hashed with SHA-256 and
seed a private `random.Random`, so draws never depend on call order or on other calls.

One uniform picks the outcome (timeout, then error, then partial, else ok); a second normal
variate gives a lognormal latency with the configured median and p95.
"""
from __future__ import annotations

import hashlib
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml

from .interfaces import FailureDraw, FailureOutcome

# z-score of the 95th percentile of a standard normal
P95_Z_SCORE = 1.6448536269514722
RULE_FIELDS = ("latency_ms", "timeout_rate", "error_rate", "partial_rate", "partial_keep")
DEFAULT_KEY = "default"


class FailureProfileError(ValueError):
    pass


@dataclass(frozen=True)
class FailureRule:
    latency_median_ms: float
    latency_p95_ms: float
    timeout_rate: float
    error_rate: float
    partial_rate: float
    partial_keep: float

    @classmethod
    def from_fields(cls, fields: dict[str, Any], where: str) -> "FailureRule":
        missing = [name for name in RULE_FIELDS if name not in fields]
        if missing:
            raise FailureProfileError(f"{where}: missing {', '.join(missing)}")
        latency = fields["latency_ms"] or {}
        rule = cls(latency_median_ms=float(latency.get("median", 0)),
                   latency_p95_ms=float(latency.get("p95", 0)),
                   timeout_rate=float(fields["timeout_rate"]), error_rate=float(fields["error_rate"]),
                   partial_rate=float(fields["partial_rate"]), partial_keep=float(fields["partial_keep"]))
        rates = (rule.timeout_rate, rule.error_rate, rule.partial_rate)
        if any(rate < 0 or rate > 1 for rate in rates) or sum(rates) > 1 + 1e-9:
            raise FailureProfileError(f"{where}: rates must be in [0, 1] and sum to at most 1")
        if rule.latency_median_ms < 0 or rule.latency_p95_ms < rule.latency_median_ms:
            raise FailureProfileError(f"{where}: latency needs 0 <= median <= p95")
        if not 0 <= rule.partial_keep < 1:
            raise FailureProfileError(f"{where}: partial_keep must be in [0, 1)")
        return rule

    def latency_from_normal(self, standard_normal: float) -> float:
        if self.latency_median_ms == 0:
            return 0.0
        sigma = math.log(self.latency_p95_ms / self.latency_median_ms) / P95_Z_SCORE
        return self.latency_median_ms * math.exp(sigma * standard_normal)


def _seed_for(run_seed: int, request_id: str, hub: str, tool: str, call_index: int) -> int:
    key = "\x1f".join((str(run_seed), request_id, hub, tool, str(call_index))).encode("utf-8")
    return int.from_bytes(hashlib.sha256(key).digest()[:8], "big")


class SeededFailureInjector:
    """Satisfies `FailureInjector`."""

    def __init__(self, profile_name: str, profile: dict[str, Any], defaults: dict[str, Any],
                 run_seed: int, time_scale: float):
        self.profile_name = profile_name
        self.run_seed = int(run_seed)
        self.time_scale = float(time_scale)
        self._profile = profile
        self._defaults = defaults
        self._rules: dict[tuple[str, str], FailureRule] = {}
        # Validate the profile-wide default eagerly so a bad file fails at load time.
        self.rule_for("", "")

    def rule_for(self, hub: str, tool: str) -> FailureRule:
        cached = self._rules.get((hub, tool))
        if cached:
            return cached
        fields: dict[str, Any] = {name: value for name, value in self._defaults.items()
                                  if name in RULE_FIELDS}
        fields.update(self._profile.get(DEFAULT_KEY) or {})
        hub_section = self._profile.get(hub) or {}
        fields.update(hub_section.get(DEFAULT_KEY) or {})
        fields.update(hub_section.get(tool) or {})
        rule = FailureRule.from_fields(fields, f"{self.profile_name}.{hub or '*'}.{tool or '*'}")
        self._rules[(hub, tool)] = rule
        return rule

    def draw(self, request_id: str, hub: str, tool: str, call_index: int) -> FailureDraw:
        rule = self.rule_for(hub, tool)
        generator = random.Random(_seed_for(self.run_seed, request_id, hub, tool, call_index))
        outcome_uniform = generator.random()
        latency_ms = rule.latency_from_normal(generator.gauss(0.0, 1.0))
        if outcome_uniform < rule.timeout_rate:
            outcome = FailureOutcome.TIMEOUT
        elif outcome_uniform < rule.timeout_rate + rule.error_rate:
            outcome = FailureOutcome.ERROR
        elif outcome_uniform < rule.timeout_rate + rule.error_rate + rule.partial_rate:
            outcome = FailureOutcome.PARTIAL
        else:
            outcome = FailureOutcome.OK
        keep_fraction = rule.partial_keep if outcome is FailureOutcome.PARTIAL else 1.0
        return FailureDraw(outcome=outcome, latency_ms=latency_ms, keep_fraction=keep_fraction)


def load_failure_injector(profiles_path: Path, profile: str, run_seed: int,
                          time_scale: Optional[float] = None) -> SeededFailureInjector:
    document = yaml.safe_load(Path(profiles_path).read_text(encoding="utf-8")) or {}
    profiles = document.get("profiles") or {}
    if profile not in profiles:
        raise FailureProfileError(f"unknown failure profile {profile!r}; known: {sorted(profiles)}")
    defaults = document.get("defaults") or {}
    resolved_time_scale = defaults.get("time_scale", 1.0) if time_scale is None else time_scale
    if resolved_time_scale < 0:
        raise FailureProfileError("time_scale must be non-negative")
    return SeededFailureInjector(profile, profiles[profile] or {}, defaults, run_seed,
                                 resolved_time_scale)
