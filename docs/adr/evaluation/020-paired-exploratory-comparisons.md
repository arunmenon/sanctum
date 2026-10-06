# ADR-020: Compare task pairs and keep conclusions exploratory

- **Bucket:** [Evaluation](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

Fact counts and repeated answers are correlated; refusal success can hide poor supported answers.

## Decision

- Average repetitions within each task/setup and compare paired task differences.
- Resample whole tasks for descriptive intervals and report scope strata separately.
- Disclose historical timing, same-model judging, scoring repairs and pending acceptance.
- Test memory and descriptor changes separately and together before considering promotion.

## Why this approach?

This reports a directional signal with its limitations rather than a premature production winner.

## Tradeoffs and limits

- Thirty tasks in one scenario cannot establish a narrow quality margin.
- The twelve-question follow-up is a different cohort; its absolute scores are not directly comparable with earlier campaigns.
- Follow-up variations remain unpromoted because results are mixed and grading disputes remain.

## Evidence

- [agent_schedule.py](../../../src/sanctum_run/agent_schedule.py)
- [report_agent_run.py](../../../tools/report_agent_run.py)
- [pdlc-rubric-followup-results.md](../../experiments/pdlc-rubric-followup-results.md)
- [README.md](../../experiments/README.md)

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
