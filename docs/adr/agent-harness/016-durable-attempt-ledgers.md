# ADR-016: Freeze schedules and preserve durable attempt outcomes

- **Bucket:** [Agent harness](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

An interrupted run can leave a request sent to a model but no saved answer. Starting it again immediately could duplicate work or conceal an unfavorable outcome. The harness therefore records when each attempt starts and when its final outcome is saved.

## Decision

- Record seeded task/arm/repetition schedules and input hashes.
- Keep a dispatch/terminal ledger plus native events, original answers and delivery receipts.
- Resume never-started attempts; reconcile unresolved dispatches before replay.

## Why this approach?

*Retrospective explanation based on the linked implementation and records; not a new approval.*

Durable records support recovery without selectively rerunning poor answers.

## Tradeoffs and limits

- Recovery is more deliberate than deleting an output directory.
- Changed inputs require a new validated experiment; a terminal result cannot be silently replaced.

## Evidence

- [agent_schedule.py](../../../src/sanctum_run/agent_schedule.py)
- [agent_runner.py](../../../src/sanctum_run/agent_runner.py)
- [runbook.md](../../lab/runbook.md)

*Documentation reviewed and clarified on 2026-10-06; runtime choices unchanged.*

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
