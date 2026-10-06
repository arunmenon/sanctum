# ADR-009: Review and pin routing-memory releases before use

- **Bucket:** [Routing memory](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

A harvested candidate is a collection of proposed links. Some may be weak or unsupported, so it cannot automatically become the map Sanctum uses to route requests.

## Decision

- Record reviewer scope and explicit owner-policy declarations.
- Build the runtime memory file from links with supporting evidence and an authorized review; unspecified proposals remain unreviewed.
- Select exact release and review/policy inputs for the experiment. Harvesting does not change ACTIVE, the pointer to the default memory release.

## Why this approach?

*Retrospective explanation based on the linked implementation and records; not a new approval.*

Review, release assembly and runtime selection are separate actions with separate evidence.

## Tradeoffs and limits

- A full candidate graph does not imply that every proposed link is operational.
- Global ACTIVE affects unpinned reference runs; explicit release selection makes experiments easier to reproduce.

## Evidence

- [harvest.py](../../../src/sanctum_ref/harvest.py)
- [agent_runtime.py](../../../src/sanctum_run/agent_runtime.py)
- [routing-memory.md](../../lab/routing-memory.md)

*Documentation reviewed and clarified on 2026-10-06; runtime choices unchanged.*

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
