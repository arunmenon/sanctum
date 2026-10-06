# Lab ADR catalog review prompt

Reviewer: Astra, medium effort. One independent pass, authorized 6 October 2026. Review only; implementation changes are handled afterward.

## Scope and reader

Review the catalog index, catalog plan, seven bucket indexes and all 22 ADRs under `docs/adr/`. Check supporting code, architecture documents, decision records and experiment reports where needed.

The intended reader is an engineer with no prior Sanctum context. Readability and understandable decisions are the highest priorities. This is a retrospective catalog of a research reference implementation, not approved production architecture.

## Review dimensions

1. **Readability and context:** Can a newcomer understand the problem, choice and consequences? Explain unfamiliar terms before use. Flag dense language, cryptic shorthand, repetition and unnecessary detail. Recommend short paragraphs, bullets, tables and examples where useful, with concrete rewrites.
2. **Bucket structure and navigation:** Are the seven groups intuitive and distinct? Check placement, overlap, missing categories, split/merge needs and finding decisions without knowing their IDs.
3. **Decision quality:** Each record must express an actual choice, not just describe a component. Check context, rationale, tradeoffs and consequences. Alternatives need historical evidence; flag invented history and unrelated decisions combined in a record.
4. **Grounding and accuracy:** Verify important claims against linked code and records. Distinguish observed implementation, design intent and reconstructed rationale. Flag unsupported claims, stale evidence, misleading links and fabricated approval.
5. **Coverage:** Check consequential choices in hubs, corpus organization, routing memory, System One, harness, scoring, reproducibility and operations. Support omissions with evidence; do not demand an ADR for every implementation detail.
6. **Status and history:** Check implemented, historical, experimental and deferred distinctions. Follow shadow/guarded/unconstrained Jev evolution and relationships between records. Preserve unpromoted experiments and pending acceptance.
7. **Architecture versus findings:** Keep setup and choices separate from numerical findings. Check links and interpretation; exploratory benefits must not be presented as proven. Future findings should not require rewriting historical decisions.
8. **Maintainability and presentation:** Check IDs, links, terminology, consistent sections, amendment/supersession rules and useful visualizations. Assess engineering handover readiness.

## Output

- Verdict: ready, ready with corrections, or needs restructuring.
- Bucket-level assessment and compact assessment of every ADR.
- Prioritized findings with location, evidence, reader impact and concrete fix.
- Representative plain-language rewrites for dense passages.
- Claims that could not be verified.

Do not edit files, delegate, rerun experiments or initiate another review. Prioritize clarity and correctness over documentation volume.
