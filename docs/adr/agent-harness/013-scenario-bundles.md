# ADR-013: Separate reusable harness logic from scenario bundles

- **Bucket:** [Agent harness](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

A scenario bundle is the experiment kit: source versions, questions, private grading criteria and run settings. A harness hard-coded to the product-development repositories could not assess unrelated scenarios.

## Decision

- Use bundle-relative manifests, public tasks, private criteria, connections, runtime pins and limits.
- Validate path containment, input hashes, task linkage and declared diversity.
- Keep agent adapters separate from scenario data; Claude Code is the current native adapter.

## Why this approach?

*Retrospective explanation based on the linked implementation and records; not a new approval.*

The same scheduling and scoring contracts can operate on another evidence corpus.

## Tradeoffs and limits

- A generic bundle does not implement a Codex/Pi adapter or coding workspace.
- Pilot preparation and judging scripts retain local/scenario assumptions; not every tool is portable.

## Evidence

- [bundle.py](../../../src/sanctum_run/bundle.py)
- [agent_contract.py](../../../src/sanctum_run/agent_contract.py)
- [experiment.yaml](../../../examples/agent-bundles/shipping/experiment.yaml)
- [extending.md](../../lab/extending.md)

*Documentation reviewed and clarified on 2026-10-06; runtime choices unchanged.*

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
