# ADR-015: Normalize delivered evidence and enforce shared attempt limits

- **Bucket:** [Agent harness](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

Tool paths return different forms of text; unlimited evidence or turns would confound comparisons.

## Decision

- Normalize direct and Sanctum results into observed citable passages.
- Charge displayed evidence and metadata against configured evidence limits.
- Enforce rounds, tool calls and deadlines; account nested System One calls separately.

## Why this approach?

Citation credit and resource comparisons need a record of what the agent actually received.

## Tradeoffs and limits

- Selecting a hub does not guarantee that the needed passage is delivered.
- Limits are bundle settings, not universal defaults; unconstrained broker capacity differs from earlier campaigns.

## Evidence

- [delivery.py](../../../src/sanctum_run/delivery.py)
- [agent_session.py](../../../src/sanctum_run/agent_session.py)
- [test_agent_delivery.py](../../../tests/test_agent_delivery.py)
- [README.md](../../experiments/method/README.md)

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
