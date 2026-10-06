# Plan for the lab ADR catalog

Recorded 6 October 2026 against lab source baseline `848da1f`. This plan groups existing choices before documenting individual architecture decision records (ADRs).

## What belongs in this catalog?

An ADR explains a choice that shapes the lab: the problem, chosen approach, tradeoffs and supporting evidence. A component description alone is not an ADR. A measured improvement belongs in an experiment record; an ADR may link to it when it explains a subsequent choice.

This is a retrospective catalog. Creating it does not create new owner approvals, change the HLD, or promote experimental configurations.

## Buckets and planned records

| Bucket | Question | ADRs |
|---|---|---|
| Scope and contracts | What is the lab for, and what boundaries must it preserve? | 001 reference scope; 002 private-gold isolation; 003 executable wire contracts |
| Evidence and hubs | How do we represent, organize and prepare evidence? | 004 local simulated hubs; 005 homes and cross-links; 006 audited synthetic authoring |
| Routing memory | How does source evidence become routing knowledge? | 007 local graph; 008 grounded harvest; 009 reviewed and pinned releases |
| System One | How are decision models called and their advice applied? | 010 broker and provider pins; 011 shadow/guarded controls; 012 unconstrained experimental selection |
| Agent harness | How can experiments run reproducibly across scenarios? | 013 scenario bundles; 014 fresh evidence-only sessions; 015 normalized evidence and limits; 016 durable attempt records |
| Evaluation | How do we create tasks and assess results honestly? | 017 task diversity and boundaries; 018 mechanical/semantic scoring; 019 versioned scoring repair; 020 paired exploratory comparisons |
| Operations and documentation | How do we store, reproduce and explain the lab? | 021 local generated inputs and fixture; 022 separate guides, method and findings |

## Evidence to use

- Owning design: `design/intelligence-layer/`, plus the existing owner-decision register.
- Implementation: the source entry points and tests listed in the codebase map.
- Execution choices: harness specification, corpus specifications and dated experiment plans.
- Observations: current corrected result records, with superseded reports labeled as history.

Historical status text in a plan is not evidence of current runtime state. Check code and current closure/results records before assigning a status.

## Format and reading order

1. Catalog index: buckets, status meanings and unresolved ownership.
2. Bucket index: a short explanation and links to its ADRs.
3. Individual ADR: context, decision, reason, tradeoffs, consequences and evidence links.

Use short paragraphs and bullets. Record the documentation date separately from any evidenced original decision date. Do not invent meeting dates, rejected alternatives or formal approval.

## Completion checks

- [x] All 22 planned decisions have unique IDs and evidence links.
- [x] Each is labeled implemented, experimental or historical within the lab scope.
- [x] Experimental Jev selection and unpromoted follow-up variations remain explicit.
- [x] Every relative link and Markdown fence validates.
- [x] The lab entry point and owner-decision register link to the catalog.
- [x] Publish on the existing lab branch; no runtime or evaluation changes.

## Verification record

- 22 unique ADR IDs and filenames agree; all required record sections and status labels are present.
- Seven bucket indexes link to their records; each record links back to the catalog.
- Thirty-three Markdown files and 207 relative links checked, including the two entry points.
- Repaired one pre-existing broken provider-design link in the owner register.
- No code, runtime configuration, judgments or experiment inputs changed; no model calls made.

- Catalog published in commit `ed5df10` on `lab/pdlc-harness-docs-20261004`.
