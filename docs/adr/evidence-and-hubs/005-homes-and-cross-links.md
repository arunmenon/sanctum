# ADR-005: Give artifacts a home and separate cross-domain associations

- **Bucket:** [Evidence and hubs](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

Repositories, services, domains and teams overlap; a single ownership tree loses those relationships.

## Decision

- Give code a repository/path home and documents a document-space/path home.
- Attach domain, service, repository and team associations as cross-links.
- Preserve artifact versions and draft/review status during ingestion.

## Why this approach?

Readers can navigate a hierarchy without mistaking location for subject or authority.

## Tradeoffs and limits

- Many-to-many associations need explicit validation.
- A document linked to a repository does not automatically establish current code behavior.

## Evidence

- [map_pdlc_hierarchy.py](../../../tools/map_pdlc_hierarchy.py)
- [ingest_pdlc_corpus.py](../../../tools/ingest_pdlc_corpus.py)
- [corpus-and-hubs.md](../../lab/corpus-and-hubs.md)

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
