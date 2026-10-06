# ADR-018: Separate citation validation, semantic judgment and human acceptance

- **Bucket:** [Evaluation](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

Exact text matching cannot fairly grade explanations or designs, and valid citation IDs do not prove support.

## Decision

- Mechanically check answer format, delivered evidence identity and citation bindings.
- Use semantic reviews for meaning, support, uncertainty and task-specific 0/1/2 plan checklists.
- Inspect the whole answer, not only declared claims.
- Separate provisional completion from registered human acceptance.

## Why this approach?

Multiple sound designs can earn credit while unsupported claims remain penalized.

## Tradeoffs and limits

- Semantic judging can disagree or share model bias.
- Invalid agent protocol earns zero; missing judge grades remain unknown rather than becoming agent-quality zeros.

## Evidence

- [agent_score.py](../../../src/sanctum_run/agent_score.py)
- [quality_policy.py](../../../src/sanctum_run/quality_policy.py)
- [test_agent_score.py](../../../tests/test_agent_score.py)
- [scoring.md](../../lab/scoring.md)

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
