# ADR-003: Version and check executable request, evidence and receipt contracts

- **Bucket:** [Scope and contracts](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

Multiple processes need the same meaning for requests, evidence and decision receipts.

## Decision

- Define public wire models in sanctum_contracts and export their JSON schemas.
- Keep committed schemas synchronized with those models.
- Make contract changes deliberate through schema export and diff review.

## Why this approach?

Executable contracts catch drift between components and make responses independently checkable.

## Tradeoffs and limits

- Schema agreement does not prove semantic correctness.
- Contract changes require coordinated review; the ADR records the existing schema-freeze choice, not a new version policy.

## Evidence

- [RetrieveRequest.json](../../../src/sanctum_contracts/schema/RetrieveRequest.json)
- [export_schemas.py](../../../tools/export_schemas.py)
- [test_schema_freeze.py](../../../tests/test_schema_freeze.py)
- [decisions.md](../../decisions.md)

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
