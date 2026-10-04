# PDLC design-document corpus workstream

Status: authorized preparation, 3 October 2026. Separate from harness implementation and task repair. Existing corpus: 102 synthetic development records, including 31 DocHub documents. New documents must not be presented as already accepted, loaded or approved.

Execution order clarified by the owner: receive current corpus/routing-memory review, fix document/source issues, regenerate and verify tasks against the expanded candidate, then resume the remaining harness implementation. Corpus draft acceptance is distinct from operational memory activation and final benchmark freeze.

## Coverage inventory

Author one repo-level HLD and two module-level LLDs per synthetic repo (18 new documents). Modules are evidence groupings from actual code paths, not newly invented runtime components.

| Repo | HLD scope | LLD modules grounded in existing paths |
|---|---|---|
| payment-authorization | Request processing, fraud boundary and historical/current/proposed distinctions | Handler/client flow; feature flag and regression seams |
| identity-provisioning | Provisioning and request-context artifacts, with unproven integration links explicit | Provisioning transport/invite storage; evaluation-context schema |
| ledger-reconciliation | Batch reconciliation and authorization-event posting as distinct paths | Batch reader/reconciler/tests; posting consumer/guard |
| gateway-routing | Selection, transport and diagnostic artifacts; no invented production topology | Route selection; HTTP transport/probe |
| fraud-batch-client | Batch-screening client evidence, distinct from payment authorization's client | Client/settings; timeout tests and maintenance boundaries |
| shared-engineering-testing | Shared tooling collection, without pretending it is one deployed service | Snapshot-fetch tooling; scope-guard test tooling |

## Authoring and document semantics

Use the owner-selected GPT-6 Luna and existing preparation ledger. Supply full selected code and relevant existing documents, exact public source IDs, versions/hashes and repo/module scope. Do not author from clipped code. If a packet cannot fit the generator's input bound, split it or reduce contextual documents while preserving complete relevant code; keep omitted context explicit and audit against the full corpus.

Each document retains native engineering style and realistic incompleteness. Separate observed/source-described behavior, historical design and new proposals. New design decisions remain draft recommendations and cannot imply implementation, measured behavior, approval or deployment. Do not resolve absent schema bindings, producer transforms, deduplication guarantees, capacity/duration or service links by invention. Preserve authentic conflicts and terminology. Do not include evaluation questions or gold hints in public document bodies.

Every document carries type (HLD/LLD), repo ID, module key when applicable, draft version/review status, public source references and private quote-backed audit claims. LLDs refer to their repo HLD through a stable local document key; HLDs point to their module LLDs. Navigation is explicit, not an inference that every artifact is about every service in a repo. Attach domain/service associations only where supported; synthetic module groupings are labeled accordingly.

## Checklist

- [x] Record dedicated workstream, six-repo coverage and eighteen-document target.
- [x] Prepare bounded source-grounded authoring packets with full code: six packets cover all 25 CodeHub records without clipping; contextual document omissions are recorded privately.
- [x] Generate six HLDs and twelve LLDs with GPT-6 Luna (six completed calls, estimated $0.0177071). Normalized packet-bound repo placeholders and one misplaced document into a private draft candidate; raw responses/hashes preserved. Semantic acceptance is pending.
- [x] Developer source audit completed; seven reference mismatches, timeout/deadline wording and navigation issues corrected. All 102 literal references resolve; independent acceptance remains pending. See [audit record](pdlc-design-corpus-audit.md).
- [x] Map repo, doc space, modules, domains and source relationships; validate cross-links.
- [x] Ingest reviewed read-only drafts into DocHub, preserving unapproved status; verify all 120 records via MCP reads/search and corpus manifest.
- [x] Refresh ontology candidate from 120 artifacts: 661 proposed assertions, five quarantined quotes; release `pilot-memory-178bbbb2fc81` remains inactive.
- [x] Prepare a [routing-memory review prompt](pdlc-routing-memory-review-prompt-astra-low.md) for one owner-requested Astra low pass.
- [x] Receive [one-pass corpus/routing-memory review](pdlc-routing-memory-review-astra-low.md); retain candidate inactive. Source wording correction, runtime subject wiring and projected navigation findings recorded; prior activation blockers remain open.
- [x] Correct RM-02 in Identity HLD/LLD: outer request configuration distinguished from nested subject; two draft-2 documents reloaded, review hashes updated. No independent recheck or activation claimed.
- [x] Recheck affected task gold and bounded scope/absence records; regenerate/repair the thirty-task development set and pin the corrected 120-record manifest. Independent task/gold acceptance and freeze remain pending.

Draft design documents add knowledge but not authoritative runtime policy. Corpus expansion invalidates the prior task corpus pin; original task drafts and Astra review remain preserved historical evidence. Harness-independent task/gold acceptance and any benchmark budget stay pending.
