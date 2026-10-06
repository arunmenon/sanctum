# ADR-004: Serve synthetic evidence through working local MCP hubs

- **Bucket:** [Evidence and hubs](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

The reference needs real search/fetch behavior without requiring enterprise connectors.

## Decision

- Load versioned JSONL artifacts into local hub services backed by an SQLite FTS5 index.
- Expose evidence through source-specific MCP search and fetch tools.
- Preserve source access checks and supported version reads.

## Why this approach?

This exercises tool protocols, retrieval and access behavior in a controlled corpus.

## Tradeoffs and limits

- Local text search and capability declarations do not prove real-adapter behavior.
- CodeHub, DocHub, SkillHub and MemoryHub are the PDLC evidence types; IncidentHub is outside this pilot.

## Evidence

- [corpus.py](../../../src/sanctum_hubs/corpus.py)
- [index.py](../../../src/sanctum_hubs/index.py)
- [servers.py](../../../src/sanctum_hubs/servers.py)
- [corpus-and-hubs.md](../../lab/corpus-and-hubs.md)

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
