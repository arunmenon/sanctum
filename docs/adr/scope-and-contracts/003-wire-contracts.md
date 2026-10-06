# ADR-003: Keep executable contracts synchronized with committed schemas

- **Bucket:** [Scope and contracts](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

Multiple processes need the same meaning for requests, evidence and decision receipts.

## Decision

- Define the request and response data formats in `sanctum_contracts` and export JSON schemas, which describe the fields other processes must send and receive.
- Keep committed schemas synchronized with those models.
- Make contract changes deliberate through schema export and diff review.

## Why this approach?

*Retrospective explanation based on the linked implementation and records; not a new approval.*

Executable contracts catch drift between components and make responses independently checkable.

## Tradeoffs and limits

- Schema agreement does not prove semantic correctness.
- Contract changes require coordinated review; the ADR records the existing schema-freeze choice, not a new version policy.

## Evidence

- [RetrieveRequest.json](../../../src/sanctum_contracts/schema/RetrieveRequest.json)
- [export_schemas.py](../../../tools/export_schemas.py)
- [test_schema_freeze.py](../../../tests/test_schema_freeze.py)
- [decisions.md](../../decisions.md)

*Documentation reviewed and clarified on 2026-10-06; runtime choices unchanged.*

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
