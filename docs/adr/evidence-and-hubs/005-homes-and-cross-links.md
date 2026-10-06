# ADR-005: Give artifacts a home and separate cross-domain associations

- **Bucket:** [Evidence and hubs](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

Repositories, services, domains and teams overlap; a single ownership tree loses those relationships. For example, a code file lives in one repository, while a design document lives in a document space and links to that repository. Both may concern several services or teams.

## Decision

- Give code a repository/path home and documents a document-space/path home.
- Attach domain, service, repository and team associations as cross-links.
- Preserve artifact versions and draft/review status during ingestion.

## Why this approach?

*Retrospective explanation based on the linked implementation and records; not a new approval.*

Readers can navigate a hierarchy without mistaking location for subject or authority.

## Tradeoffs and limits

- Many-to-many associations need explicit validation.
- A document linked to a repository does not automatically establish current code behavior.

## Evidence

- [map_pdlc_hierarchy.py](../../../tools/map_pdlc_hierarchy.py)
- [ingest_pdlc_corpus.py](../../../tools/ingest_pdlc_corpus.py)
- [corpus-and-hubs.md](../../lab/corpus-and-hubs.md)

*Documentation reviewed and clarified on 2026-10-06; runtime choices unchanged.*

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
