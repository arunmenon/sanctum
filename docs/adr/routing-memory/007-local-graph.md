# ADR-007: Use local graph and table lookups for routing memory

- **Bucket:** [Routing memory](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

Routing memory is a map of subjects, names and search locations, rather than a store of session evidence. Its ontology defines those things and their relationships. The lab needs to test this map before selecting an external database.

## Decision

- Load reviewed releases into an in-memory RelationStore with dictionary and adjacency-style lookups.
- Retain TableStore, a flat-table implementation that answers the same routing queries, for comparison.
- Look up artifact subjects using source, artifact ID, version and content hash.

## Why this approach?

*Retrospective explanation based on the linked implementation and records; not a new approval.*

This makes ontology behavior directly testable without introducing graph-database infrastructure.

## Tradeoffs and limits

- Candidate assertions and runtime lookup structures have different shapes.
- Not every harvested relationship is traversed operationally; RELATES_TO remains unused.
- External graph storage is future work, not a selected production architecture.

## Evidence

- [memory.py](../../../src/sanctum_ref/memory.py)
- [test_sanctum_ref_memory.py](../../../tests/test_sanctum_ref_memory.py)
- [routing-memory.md](../../lab/routing-memory.md)

*Documentation reviewed and clarified on 2026-10-06; runtime choices unchanged.*

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
