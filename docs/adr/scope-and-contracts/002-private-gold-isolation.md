# ADR-002: Keep evaluator gold outside the retrieval and agent runtimes

- **Bucket:** [Scope and contracts](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

An agent could appear accurate if private answer criteria leaked into its tools or evidence.

## Decision

- Keep public artifacts and questions separate from private gold.
- Run Sanctum across a process/transport boundary and expose hub operations through the trusted gateway.
- Observe actual hub calls rather than trusting self-reported retrieval receipts alone.

## Why this approach?

Independent scoring needs an answer path that cannot consult the evaluator’s answer key.

## Tradeoffs and limits

- The trusted runner has more responsibility for identity, transport and observations.
- Isolation controls reduce leakage; they do not constitute a hostile-code sandbox for future coding tasks.

## Evidence

- [process_sut.py](../../../src/sanctum_run/process_sut.py)
- [test_isolation_static.py](../../../tests/test_isolation_static.py)
- [architecture.md](../../lab/architecture.md)

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
