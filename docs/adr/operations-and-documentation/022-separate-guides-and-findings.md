# ADR-022: Separate readable implementation guides, experiment setup and findings

- **Bucket:** [Operations and documentation](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

A monolithic write-up and mixed status/results pages made the lab difficult to hand over.

## Decision

- Use a top-down walkthrough and focused component guides with short explanations, tables and diagrams.
- Keep experiment method separate from result records and maintain a results index.
- Put corrected scores first; label preserved original reports as superseded history.
- Keep ADRs separate from implementation tutorials and numerical findings.

## Why this approach?

*Retrospective explanation based on the linked implementation and records; not a new approval.*

Readers can understand the system before its contracts and find new findings without rewriting architecture pages.

## Tradeoffs and limits

- Indexes and links need maintenance when experiments or decisions change.
- Historical plans remain linked at stable paths; their progress statements are not current readiness claims.

## Evidence

- [README.md](../../lab/README.md)
- [README.md](../../experiments/README.md)
- [README.md](../../experiments/method/README.md)
- [lab-docs-handover-dispositions-20261005.md](../../reviews/lab-docs-handover-dispositions-20261005.md)

*Documentation reviewed and clarified on 2026-10-06; runtime choices unchanged.*

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
