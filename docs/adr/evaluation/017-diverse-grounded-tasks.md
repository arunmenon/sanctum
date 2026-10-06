# ADR-017: Ground a diverse PDLC task mix in pinned evidence

- **Bucket:** [Evaluation](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

Repeated planning questions or false absence labels would make a benchmark uninformative.

## Decision

- Author task evidence packets from audited corpus versions, then verify model-drafted questions and facts.
- Cover six task families: understand behavior; trace dependencies/change impact; plan implementation; design testing; plan rollout/recovery; resolve uncertainty.
- Track separately whether evidence fully supports, partially supports or cannot support the requested answer.
- Include explicit high-level and low-level design (HLD/LLD) demands and task-specific design criteria.
- Require independent acceptance before a frozen evaluation claim.

## Why this approach?

*Retrospective explanation based on the linked implementation and records; not a new approval.*

Diversity must cover different evidence and reasoning demands, not just different wording.

## Tradeoffs and limits

- Metadata quotas and exact duplicate checks do not establish semantic diversity.
- Independent acceptance of boundary gold remains pending; developer-verified tasks are not automatically accepted benchmarks.

## Evidence

- [claude-code-harness-spec.md](../../experiments/claude-code-harness-spec.md)
- [bundle.py](../../../src/sanctum_run/bundle.py)
- [pdlc-task-review-astra-low.md](../../experiments/pdlc-task-review-astra-low.md)
- [README.md](../../experiments/method/README.md)

*Documentation reviewed and clarified on 2026-10-06; runtime choices unchanged.*

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
