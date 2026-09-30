# Sanctum intelligence layer: overview and reading guide

## Purpose and relationship to the team's proposal

This document set expands the engineering team's initial Sanctum proposal. It develops an evidence router that works inside a given allowed set of sources, a System One decision interface, and governed memory about knowledge sources. The accompanying lab is a spike to investigate the underlying hypotheses. Its findings will inform design choices and possible follow-on work.

Add the initial team proposal's Confluence link here when publishing; compatibility with its contract remains open. The architectural expansion and lab do not imply approval or replacement of that proposal.

**Version v5.3.1**

**Scope.** This is a research MVP design for routing intelligence. It covers two pillars: the cascade (Understand, Select, Retrieve, Assemble, with typed decisions from rules, then System One, then an LLM only if unsure) and the memory and ontology that advise it. Both operate inside a given allowed set of sources and a required subset: policy, including access control, is an assumed input, not designed here. The design is read-only.

## Start here

An agent asks what a service does on a gateway timeout. Relevant information may live in code, a reviewed domain skill, documents, or earlier agent sessions. Those sources may use different names and disagree because they describe different versions or kinds of fact.

Given the sources the caller may use, Sanctum would resolve the question's names, choose useful sources, gather version-aware evidence, preserve conflicts, and fit the result into the caller's budget. Its memory records how to find and interpret source metadata. It cannot grant access or determine which source is true.

## Read according to your question

| Page | What it answers | Suggested reader |
|---|---|---|
| [Architectural proposal](hld.md) | What is proposed, how a request flows, what the boundaries and tradeoffs are | Working group, architects, technical stakeholders |
| [Memory and meta-taxonomy](memory-design.md) | How identities, locations, procedures, ownership and releases work | Memory, source integration and governance reviewers |
| [Contracts and worked scenarios](contracts-and-scenarios.md) | Exact response expectations and normal, ambiguous, conflicting and failed cases | Implementers, adapter owners and evaluators |
| [System One providers and the Jev handshake](system-one-providers.md) | How decisions reach a System One model: provider interface, `/v1/systemone` protocol, broker isolation, calibration and conformance | Decision-layer and provider reviewers |

For a first review, read this overview and the HLD, then follow only the relevant detail links. The [section map](section-map.md) lists every section and the page that owns it.

This set is design only: it states what Sanctum is and the rules it follows. Everything measured or run lives with the lab, outside this set, in the lab repository under `docs/experiments/` and `docs/reports/`. The lab links to these design pages; these pages do not link to the lab.

## How to interpret status

| Label | Meaning |
|---|---|
| Existing proposal | The team's starting proposal, to be linked and compared explicitly |
| Proposed extension | Architecture presented for discussion; not an adoption decision |
| Hypothesis | A claim whose value requires experiment evidence |
| Spike implementation | Experimental machinery; does not by itself prove the hypothesis |
| Finding | A reproducible result with a named comparison and stated limitations |
| Open decision | A question requiring a designated owner or working-group resolution |
| Deferred | Outside the proposed read-only pilot |

The team's proposal describes existing Sanctum as an MCP endpoint across Engram, Dobby, Deep Insights and KaaS. That description has not been independently audited here.

## Feedback requested

1. Does this expansion fit the team's initial proposal and contract?
2. Are the cascade, memory, and source-ownership boundaries appropriate?
3. Is the proposed one-service, read-only pilot a useful future validation slice?
4. Which hypotheses merit the spike, and what evidence would justify each mechanism?
5. Who owns source attestations, evaluation, and unresolved decisions?

The one open decision (cost versus completeness, the D2 margin) is in [HLD §10](hld.md#section-10).

## Publication and maintenance

Publish this as the parent Confluence page, with the linked design pages as children; the lab pages publish separately. Replace local links with their Confluence page/heading targets and render Mermaid diagrams using the supported mechanism in your space. Check cross-page anchors after import.

Each numbered section has one owning page. Hypotheses, execution status and measurements belong with the lab; schemas belong in their owning contract section; architectural decisions belong in the HLD.
