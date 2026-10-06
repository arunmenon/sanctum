# ADR-019: Version scoring corrections and rescore immutable saved judgments

- **Bucket:** [Evaluation](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

Two mechanical rules withheld legitimate completion or boundary credit in the earlier scoring.

## Decision

- Report evidence-delivery limits separately rather than automatically failing completion.
- Allow supported factual premises to establish a relevant boundary diagnosis under the v3 rules.
- Rescore saved judgments in new output directories and preserve original bindings and reports.

## Why this approach?

A grading correction should not masquerade as a new product improvement or require selective agent reruns.

## Tradeoffs and limits

- Coverage changes caused by corrected grading are not runtime gains.
- The recorded direct-judgment recovery and narrow follow-up format repair are separate exceptions with preserved originals.
- Remaining grading disagreements require individual investigation, not automatic credit changes.

## Evidence

- [rescore_saved_quality.py](../../../tools/rescore_saved_quality.py)
- [pdlc-scorer-v3-audit.md](../../experiments/pdlc-scorer-v3-audit.md)
- [pdlc-rubric-followup-results.md](../../experiments/pdlc-rubric-followup-results.md)

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
