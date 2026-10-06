# ADR-006: Audit LLM-authored synthetic evidence before ingestion

- **Bucket:** [Evidence and hubs](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

Uniform perfect fixtures would hide ambiguity, stale knowledge and incomplete engineering evidence.

## Decision

- Author from role-specific local evidence packets through the provider-independent generation workflow.
- Retain realistic differences in vocabulary, knowledge, proposals and unresolved hypotheses.
- Audit introduced claims, repair accidental contradictions, attach mappings and verify MCP retrieval.

## Why this approach?

*Retrospective explanation based on the linked implementation and records; not a new approval.*

Synthetic messiness should challenge retrieval while remaining traceable to an inspectable scenario.

## Tradeoffs and limits

- Generating drafts does not remove the work of checking their claims, versions and consistency.
- Models can propose content; they cannot invent reviewed status or real production observations.
- The historical public-repository importer idea is outside the synthetic pilot’s implemented preparation path.

## Evidence

- [generate_pdlc_corpus.py](../../../tools/generate_pdlc_corpus.py)
- [pdlc-corpus-spec.md](../../experiments/pdlc-corpus-spec.md)
- [pdlc-design-corpus-audit.md](../../experiments/pdlc-design-corpus-audit.md)

*Documentation reviewed and clarified on 2026-10-06; runtime choices unchanged.*

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
