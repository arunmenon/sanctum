# ADR-007: Use local graph and table lookups for routing memory

- **Bucket:** [Routing memory](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

The lab needs to resolve shared subjects and search scopes before choosing an external storage product.

## Decision

- Load reviewed releases into an in-memory RelationStore with dictionary and adjacency-style lookups.
- Retain TableStore as an equivalent query backend.
- Look up artifact subjects using source, artifact ID, version and content hash.

## Why this approach?

This makes ontology behavior directly testable without introducing graph-database infrastructure.

## Tradeoffs and limits

- Candidate assertions and runtime lookup structures have different shapes.
- Not every harvested relationship is traversed operationally; RELATES_TO remains unused.
- External graph storage is future work, not a selected production architecture.

## Evidence

- [memory.py](../../../src/sanctum_ref/memory.py)
- [test_sanctum_ref_memory.py](../../../tests/test_sanctum_ref_memory.py)
- [routing-memory.md](../../lab/routing-memory.md)

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
