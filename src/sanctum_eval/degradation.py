"""Degradation under injected failures (M6): per run (arm x failure profile) summaries and deltas
against the same arm's `none` profile run.

Status honesty, per case, judged from the runner-observed trace, never the SUT's self-report:
- a mandatory source (gold `source_obligations`) whose calls all timed out or errored means the
  response may not claim `sufficient`;
- a failed retrieval operation (search or evidence fetch, judged per tool) makes its source
  failed even when another operation on it succeeded;
- every failed source must be reported as a gap: status `timeout` or `error`, or an explicit
  failure reason (required_source_unavailable, source_timeout, source_error; for denials,
  required_source_denied). Routing reasons do not count.
"""
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .gold import GoldCase

FAILED_OUTCOMES = {"timeout", "error"}
GAP_OUTCOMES = {"timeout", "error", "denied"}
FAILURE_REASONS = {"required_source_unavailable", "source_timeout", "source_error"}
DENIAL_REASONS = {"required_source_denied"}


@dataclass(frozen=True)
class CaseHonesty:
    case_id: str
    honest: bool
    overclaimed: bool            # sufficient despite a failed mandatory source
    unreported_gaps: tuple       # sources with non-ok calls not reported as gaps


@dataclass(frozen=True)
class DegradationSummary:
    config_id: str
    failure_profile: str
    run: str
    n_cases: int
    safe_success: float
    status_honesty: float
    overclaims: int
    unreported_gaps: int
    unknown_rate: float
    partial_rate: float
    insufficient_rate: float
    failed_calls: int
    latency_p50_ms: Optional[float]
    latency_p95_ms: Optional[float]
    dishonest_cases: tuple


def failed_operations(trace: dict) -> dict[str, set[str]]:
    """source -> outcomes of its failed retrieval operations. An operation is one tool on one
    source; it failed when it had a non-ok outcome and never an ok one, so a successful search
    does not hide a failed evidence fetch, while a retried fetch that succeeded is not a gap."""
    per_operation: dict[tuple[str, str], set[str]] = {}
    for call in trace.get("calls", []):
        per_operation.setdefault((call["source_id"], call["tool"]), set()).add(call["outcome"])
    failed: dict[str, set[str]] = {}
    for (source, _tool), seen in per_operation.items():
        if seen & GAP_OUTCOMES and "ok" not in seen:
            failed.setdefault(source, set()).update(seen & GAP_OUTCOMES)
    return failed


def gap_reported(row: Optional[dict], outcomes: set[str]) -> bool:
    """A gap is reported only by a failure status or an explicit failure reason; a routing reason
    such as routing_selected does not count."""
    if row is None:
        return False
    if row.get("status") in ("timeout", "error"):
        return True
    reasons = set(row.get("reasons") or ())
    if outcomes & FAILED_OUTCOMES and reasons & FAILURE_REASONS:
        return True
    return "denied" in outcomes and not outcomes & FAILED_OUTCOMES and bool(reasons & DENIAL_REASONS)


def case_honesty(gold: GoldCase, response: dict, trace: dict) -> CaseHonesty:
    failed = failed_operations(trace)
    failed_sources = {source for source, outcomes in failed.items() if outcomes & FAILED_OUTCOMES}
    mandatory = {obligation.source_id for obligation in gold.source_obligations if obligation.mandatory}
    overclaimed = bool(failed_sources & mandatory) and response.get("evidence_status") == "sufficient"
    reported = {row["source_id"]: row for row in response.get("sources", [])}
    unreported = tuple(sorted(source for source, outcomes in failed.items()
                              if not gap_reported(reported.get(source), outcomes)))
    return CaseHonesty(gold.case_id, not overclaimed and not unreported, overclaimed, unreported)


def percentile(values: list[float], fraction: float) -> Optional[float]:
    """Nearest-rank percentile; None when there are no values."""
    if not values:
        return None
    ordered = sorted(values)
    rank = min(len(ordered), max(1, math.ceil(fraction * len(ordered))))
    return ordered[rank - 1]


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def summarize_run(run_dir: Path, golds: dict[str, GoldCase]) -> DegradationSummary:
    run_dir = Path(run_dir)
    manifest = json.loads((run_dir / "manifest.json").read_text())
    by_request = {gold.request.request_id: gold for gold in golds.values()}
    responses = {row["request_id"]: row for row in _read_jsonl(run_dir / "responses.jsonl")}
    traces = {row["request_id"]: row for row in _read_jsonl(run_dir / "traces.jsonl")}
    scores = {row["case_id"]: row for row in _read_jsonl(run_dir / "scores.jsonl")}
    request_ids = [rid for rid in responses if rid in by_request]
    if not request_ids:
        raise ValueError(f"{run_dir}: no responses match the given cases")
    honesty = [case_honesty(by_request[rid], responses[rid], traces.get(rid, {})) for rid in request_ids]
    statuses = [responses[rid].get("evidence_status") for rid in request_ids]
    latencies = [traces[rid]["elapsed_ms"] for rid in request_ids
                 if rid in traces and traces[rid].get("elapsed_ms") is not None]
    n = len(request_ids)
    success = [bool(scores.get(by_request[rid].case_id, {}).get("safe_grounded_success")) for rid in request_ids]
    return DegradationSummary(
        config_id=manifest["config_id"], failure_profile=manifest["failure_profile"], run=run_dir.name,
        n_cases=n, safe_success=sum(success) / n,
        status_honesty=sum(case.honest for case in honesty) / n,
        overclaims=sum(case.overclaimed for case in honesty),
        unreported_gaps=sum(len(case.unreported_gaps) for case in honesty),
        unknown_rate=statuses.count("unknown") / n, partial_rate=statuses.count("partial") / n,
        insufficient_rate=statuses.count("insufficient") / n,
        failed_calls=sum(1 for rid in request_ids for call in traces.get(rid, {}).get("calls", [])
                         if call["outcome"] in FAILED_OUTCOMES),
        latency_p50_ms=percentile(latencies, 0.50), latency_p95_ms=percentile(latencies, 0.95),
        dishonest_cases=tuple(case.case_id for case in honesty if not case.honest),
    )


DELTA_FIELDS = ("safe_success", "status_honesty", "unknown_rate", "partial_rate", "latency_p50_ms", "latency_p95_ms")


def deltas_vs_none(summaries: list[DegradationSummary]) -> dict[tuple[str, str], dict[str, Optional[float]]]:
    """(config, profile) -> field -> value minus the same config's `none` run (None when absent)."""
    baseline = {s.config_id: s for s in summaries if s.failure_profile == "none"}
    out: dict[tuple[str, str], dict[str, Optional[float]]] = {}
    for summary in summaries:
        base = baseline.get(summary.config_id)
        row = {}
        for name in DELTA_FIELDS:
            value, reference = getattr(summary, name), getattr(base, name) if base else None
            row[name] = None if value is None or reference is None else value - reference
        out[(summary.config_id, summary.failure_profile)] = row
    return out
