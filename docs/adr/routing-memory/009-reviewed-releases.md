# ADR-009: Review and pin routing-memory releases before use

- **Bucket:** [Routing memory](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

A harvested candidate may include weak assertions and cannot safely stand in for accepted routing knowledge.

## Decision

- Record reviewer scope and explicit owner-policy declarations.
- Project supported accepted records into a runtime release; unspecified proposals remain unreviewed.
- Pin release and review/policy inputs in the experiment; harvest does not switch ACTIVE.

## Why this approach?

Review, release assembly and runtime selection are separate actions with separate evidence.

## Tradeoffs and limits

- A full candidate graph does not imply that every proposed link is operational.
- Global ACTIVE affects unpinned reference runs; explicit release selection makes experiments easier to reproduce.

## Evidence

- [harvest.py](../../../src/sanctum_ref/harvest.py)
- [agent_runtime.py](../../../src/sanctum_run/agent_runtime.py)
- [routing-memory.md](../../lab/routing-memory.md)

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
