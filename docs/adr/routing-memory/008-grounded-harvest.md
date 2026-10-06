# ADR-008: Propose ontology links from versioned hub evidence

- **Bucket:** [Routing memory](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

Routing knowledge should be collected consistently from hubs rather than maintained as unrelated manual fragments. For example, a passage naming the payment-authorization service can support a proposed link saying that the artifact is about that service. The proposal must retain the exact passage that supports it.

## Decision

- Use a source-neutral connector for paginated inventory and versioned fetch.
- Validate stable snapshots, source identity and content hashes.
- Require exact supporting spans for proposals and set unsupported proposals aside.

## Why this approach?

*Retrospective explanation based on the linked implementation and records; not a new approval.*

Provenance lets a reviewer distinguish a supported relationship from plausible model output.

## Tradeoffs and limits

- Collection failures cannot prove artifact deletion.
- An LLM proposal is not an owner declaration or automatic routing policy.

## Evidence

- [harvest.py](../../../src/sanctum_ref/harvest.py)
- [harvest_pdlc_memory.py](../../../tools/harvest_pdlc_memory.py)
- [test_memory_harvest.py](../../../tests/test_memory_harvest.py)

*Documentation reviewed and clarified on 2026-10-06; runtime choices unchanged.*

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
