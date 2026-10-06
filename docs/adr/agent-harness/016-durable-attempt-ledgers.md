# ADR-016: Freeze schedules and preserve durable attempt outcomes

- **Bucket:** [Agent harness](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

Retries after a partial dispatch could duplicate model work or conceal an unfavorable outcome.

## Decision

- Record seeded task/arm/repetition schedules and input hashes.
- Keep a dispatch/terminal ledger plus native events, original answers and delivery receipts.
- Resume never-started attempts; reconcile unresolved dispatches before replay.

## Why this approach?

Durable records support recovery without selectively rerunning poor answers.

## Tradeoffs and limits

- Recovery is more deliberate than deleting an output directory.
- Changed inputs require a new validated experiment; a terminal result cannot be silently replaced.

## Evidence

- [agent_schedule.py](../../../src/sanctum_run/agent_schedule.py)
- [agent_runner.py](../../../src/sanctum_run/agent_runner.py)
- [runbook.md](../../lab/runbook.md)

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
