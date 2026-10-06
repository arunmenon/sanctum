# ADR-021: Keep generated campaign inputs local and ship an offline fixture

- **Bucket:** [Operations and documentation](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

Code distribution, credentials, synthetic authoring outputs and experiment receipts have different lifecycles.

## Decision

- Check in source, guides and a small shipping example.
- Keep generated PDLC corpus, releases, private bundles and raw runs in ignored local build directories.
- Keep credentials outside bundles, evidence and versioned documentation.
- Provide an inference-free fixture for checkout validation.

## Why this approach?

*Retrospective explanation based on the linked implementation and records; not a new approval.*

An engineer can exercise the harness without obtaining the full local campaign or model credentials.

## Tradeoffs and limits

- A fresh clone cannot reproduce the larger PDLC campaign by itself.
- Portable quality-driver support remains incomplete; the runbook identifies local prerequisites.

## Evidence

- [.gitignore](../../../.gitignore)
- [README.md](../../../examples/agent-bundles/shipping/README.md)
- [quickstart.md](../../lab/quickstart.md)
- [runbook.md](../../lab/runbook.md)

*Documentation reviewed and clarified on 2026-10-06; runtime choices unchanged.*

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
