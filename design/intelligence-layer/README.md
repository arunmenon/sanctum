# Sanctum intelligence layer — overview and reading guide

## Purpose and relationship to the team's proposal

This document set expands the engineering team's initial Sanctum proposal. It develops a policy-constrained evidence router, a System One decision interface, and governed memory about knowledge sources. The accompanying lab is a spike to investigate the underlying hypotheses. Its findings will inform design choices and possible follow-on work.

The initial team proposal has not been included in this restructuring. Add its Confluence link here when publishing; compatibility with its contract remains Q1. The architectural expansion and lab do not imply approval or replacement of that proposal.

**Version: v5.2** (proposed). v5.2 adds an execution context, a governed assertion envelope, one evidence-preservation contract and an operational `ABOUT` layer, in response to the holistic review; see the [review history](review-history.md#v5-2).

## Start here

An agent asks what a service does on a gateway timeout. Relevant information may live in code, a reviewed domain skill, documents, or earlier agent sessions. Those sources may use different names and disagree because they describe different versions or kinds of fact.

Sanctum would first establish what the caller may access, then choose useful sources, gather version-aware evidence, preserve conflicts, and fit the result into the caller's budget. Its memory records how to find and interpret source metadata. It cannot grant access or determine which source is true.

## Read according to your question

| Page | What it answers | Suggested reader |
|---|---|---|
| [Architectural proposal](hld.md) | What is proposed, how a request flows, what the boundaries and tradeoffs are | Working group, architects, technical stakeholders |
| [Memory and meta-taxonomy](memory-design.md) | How identities, locations, procedures, ownership and releases work | Memory, source integration and governance reviewers |
| [Contracts and worked scenarios](contracts-and-scenarios.md) | Exact response expectations and normal, ambiguous, conflicting and failed cases | Implementers, adapter owners and evaluators |
| [System One providers and the Jev handshake](system-one-providers.md) | How decisions reach a System One model: provider interface, `/v1/systemone` protocol, broker isolation, calibration and conformance | Decision-layer, provider and security reviewers |
| [Review history](review-history.md) | Prior findings, editorial changes and their traceability | Reviewers needing the history |

For a first review, read this overview and the HLD, then follow only the relevant detail links. The [section map](section-map.md) locates every original section.

This set is design only: it states what Sanctum is and the rules it follows. Everything measured or run lives with the lab, outside this set: the hypothesis-validation spike (sections 2, 16, 17), the execution plan (section 18) and the System One lab page are in the lab repository under `docs/experiments/` (lab-spike.md, spike-plan.md, system-one-lab.md), with reports under `docs/reports/`. The lab links to these design pages; these pages do not link to the lab.

## How to interpret status

| Label | Meaning |
|---|---|
| Existing proposal | The team's starting proposal, to be linked and compared explicitly |
| Proposed extension | Architecture presented for discussion; not an adoption decision |
| Hypothesis | A claim whose value requires experiment evidence |
| Spike implementation | Experimental machinery; does not by itself prove the hypothesis |
| Finding | A reproducible result with a named comparison and stated limitations |
| Open decision | A question requiring a designated owner or working-group resolution |
| Deferred | Outside the proposed read-only pilot; retained to explain the future boundary |

The source HLD describes existing Sanctum as an MCP endpoint across Engram, Dobby, Deep Insights and KaaS. That description has not been independently audited here. The current lab README describes M0–M2 work and a planned M3 reference SUT; this restructuring does not certify implementation status or rerun experiments.

## Feedback requested

1. Does this expansion fit the team's initial proposal and contract?
2. Are the policy, judgment, memory, and source-ownership boundaries appropriate?
3. Is the proposed one-service, read-only pilot a useful future validation slice?
4. Which hypotheses merit the spike, and what evidence would justify retaining each mechanism?
5. Who owns source attestations, evaluation, approved data use, and unresolved decisions?

Detailed Q1–Q18 decisions remain in the HLD. Dates and the older monthly rollout sketch live on the execution page and are not delivery commitments.

## Publication and maintenance

Publish this as the parent Confluence page, with the five linked design pages as children; the lab pages publish separately. Replace local links with their Confluence page/heading targets and render Mermaid diagrams using the supported mechanism in your space. Check cross-page anchors after import. Keep the original v5.1 document as a historical attachment rather than a competing current page.

Each numbered section has one owning page. Changes to hypotheses belong in the lab's spike page, schemas in their owning contract section, execution status and measurements in the lab's records, and architectural decisions in the HLD. Summaries link to those owners. The detailed design, examples, diagrams and evaluation protocol have been preserved; the split introduces no page-length limit.
