# ADR-020: Compare task pairs and keep conclusions exploratory

- **Bucket:** [Evaluation](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

Several facts in one answer and repeated answers to one task are related observations, not independent samples. A high refusal score can also hide weak answers to supported questions. Compare the same tasks across setups and keep those categories separate.

## Decision

- First average repeated attempts for each task and setup; then compare the setups on the same tasks.
- Estimate descriptive uncertainty by resampling tasks, keeping each task’s repeated attempts together. Report supported, partial and out-of-scope tasks separately.
- Disclose historical timing, same-model judging, scoring repairs and pending acceptance.
- Test memory and descriptor changes separately and together before considering promotion.

## Why this approach?

*Retrospective explanation based on the linked implementation and records; not a new approval.*

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

*Documentation reviewed and clarified on 2026-10-06; runtime choices unchanged.*

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
