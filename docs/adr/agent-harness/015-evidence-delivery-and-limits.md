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

*Retrospective explanation based on the linked implementation and records; not a new approval.*

Citation credit and resource comparisons need a record of what the agent actually received.

## Tradeoffs and limits

- Selecting a hub does not guarantee that the needed passage is delivered.
- Limits are bundle settings, not universal defaults; unconstrained broker capacity differs from earlier campaigns.

## Related decisions

[ADR-023](../evidence-and-hubs/023-evidence-assembly.md) explains how Sanctum chooses whole passages within its own budget. This record covers what the harness observes and charges after delivery.

## Evidence

- [delivery.py](../../../src/sanctum_run/delivery.py)
- [agent_session.py](../../../src/sanctum_run/agent_session.py)
- [test_agent_delivery.py](../../../tests/test_agent_delivery.py)
- [README.md](../../experiments/method/README.md)

*Documentation reviewed and clarified on 2026-10-06; runtime choices unchanged.*

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
