# ADR-004: Serve synthetic evidence through working local MCP hubs

- **Bucket:** [Evidence and hubs](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

A hub serves searchable artifacts, such as code files or design documents. The reference needs working search and fetch tools without enterprise connectors. Agents call these tools through MCP (Model Context Protocol).

## Decision

- Load versioned JSONL artifacts into local hub services backed by an SQLite FTS5 index.
- Expose evidence through source-specific MCP search and fetch tools.
- Preserve source access checks and supported version reads.

## Why this approach?

*Retrospective explanation based on the linked implementation and records; not a new approval.*

This exercises tool protocols, retrieval and access behavior in a controlled corpus.

## Tradeoffs and limits

- Local text search and capability declarations do not prove real-adapter behavior.
- CodeHub, DocHub, SkillHub and MemoryHub are the PDLC evidence types; IncidentHub is outside this pilot.

## Evidence

- [corpus.py](../../../src/sanctum_hubs/corpus.py)
- [index.py](../../../src/sanctum_hubs/index.py)
- [servers.py](../../../src/sanctum_hubs/servers.py)
- [corpus-and-hubs.md](../../lab/corpus-and-hubs.md)

*Documentation reviewed and clarified on 2026-10-06; runtime choices unchanged.*

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
