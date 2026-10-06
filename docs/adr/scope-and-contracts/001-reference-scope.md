# ADR-001: Treat Sanctum as a research reference implementation

- **Bucket:** [Scope and contracts](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

Sanctum helps an agent find evidence across knowledge sources. This lab investigates whether that retrieval improves answers, before making deployment claims.

## Decision

- Use a disposable reference implementation with synthetic evidence.
- Separate evidence that a real slice can be built from evidence of superiority.
- Treat production connectors, other agent adapters and local coding workflows as separate work.

## Why this approach?

*Retrospective explanation based on the linked implementation and records; not a new approval.*

This keeps experiments concrete while exposing the limits of their conclusions.

## Tradeoffs and limits

- Synthetic scenarios make facts inspectable, but do not establish enterprise realism.
- The existing D-REF and D-GOAL entries are working assumptions; this record does not invent an owner ratification.

## Evidence

- [decisions.md](../../decisions.md)
- [extending.md](../../lab/extending.md)
- [walkthrough.md](../../lab/walkthrough.md)

*Documentation reviewed and clarified on 2026-10-06; runtime choices unchanged.*

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
