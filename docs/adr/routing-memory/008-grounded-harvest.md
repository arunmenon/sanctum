# ADR-008: Propose ontology links from versioned hub evidence

- **Bucket:** [Routing memory](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

Routing knowledge should be collected consistently from hubs rather than maintained as unrelated manual fragments.

## Decision

- Use a source-neutral connector for paginated inventory and versioned fetch.
- Validate stable snapshots, source identity and content hashes.
- Require exact supporting spans for proposals and set unsupported proposals aside.

## Why this approach?

Provenance lets a reviewer distinguish a supported relationship from plausible model output.

## Tradeoffs and limits

- Collection failures cannot prove artifact deletion.
- An LLM proposal is not an owner declaration or automatic routing policy.

## Evidence

- [harvest.py](../../../src/sanctum_ref/harvest.py)
- [harvest_pdlc_memory.py](../../../tools/harvest_pdlc_memory.py)
- [test_memory_harvest.py](../../../tests/test_memory_harvest.py)

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
