# ADR-018: Separate citation validation, semantic judgment and human acceptance

- **Bucket:** [Evaluation](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

Exact text matching cannot fairly grade explanations or designs, and valid citation IDs do not prove support.

## Decision

- Mechanically check answer format, delivered evidence identity and citation bindings.
- Judge meaning, source support and uncertainty, rather than requiring an exact wording match. Score each task-specific checklist: **0** absent or wrong; **1** partial; **2** all mandatory items met.
- Replace evidence IDs with neutral aliases and remove explicit setup, tool and cost identifiers from the judge packet.
- Inspect the whole answer, not only declared claims.
- Keep automated completion provisional. Independent acceptance of task gold checks the grading criteria; human acceptance of a particular answer checks that answer and its review. These are separate records, not interchangeable approvals.

## Why this approach?

*Retrospective explanation based on the linked implementation and records; not a new approval.*

Multiple sound designs can earn credit while unsupported claims remain penalized.

## Tradeoffs and limits

- Semantic judging can disagree or share model bias.
- Removing explicit setup identifiers does not guarantee complete blindness: answer content may reveal its setup, and the operational-metadata audit remains unresolved.
- Invalid agent protocol earns zero; missing judge grades remain unknown rather than becoming agent-quality zeros.

## Related decisions

- [ADR-017](017-diverse-grounded-tasks.md): task construction and independent gold acceptance.
- [ADR-020](020-paired-exploratory-comparisons.md): comparing the same tasks across setups.

## Evidence

- [agent_score.py](../../../src/sanctum_run/agent_score.py)
- [quality_policy.py](../../../src/sanctum_run/quality_policy.py)
- [test_agent_score.py](../../../tests/test_agent_score.py)
- [scoring.md](../../lab/scoring.md)

*Documentation reviewed and clarified on 2026-10-06; runtime choices unchanged.*

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
