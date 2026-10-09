# Lab architecture decision catalog

An architecture decision record (ADR) explains **why the lab is built or tested a particular way**. Use this catalog for decisions; use the [lab guide](../lab/README.md) for a walkthrough and the [results index](../experiments/README.md) for findings.

The catalog contains 25 decisions grouped into seven buckets. The initial retrospective records use source baseline `848da1f` and its linked design, implementation and experiment records. ADR-024 and ADR-025 record the subsequent 9 October Jev integration experiments. The [catalog plan](catalog-plan.md) explains the grouping and scope.

## What is this lab?

Sanctum retrieves evidence for an answering agent. In this lab, Claude answers engineering questions using either hub tools directly or Sanctum’s retrieval tool. Jev helps Sanctum choose hubs; a separate scorer checks saved answers against private criteria.

- **Knowledge hubs** serve code, documents, procedures and prior-session evidence.
- **Routing memory** maps names and subjects to useful search locations. It is different from **MemoryHub**, which holds session records as evidence.
- **System One** is the decision-model layer; **Jev** is the provider used in these experiments.
- **The harness** starts agent sessions, records their evidence and saves answers for scoring.

For the full question-to-answer flow, start with the [architecture guide](../lab/architecture.md).

## Terms used in the records

| Term | Plain meaning |
|---|---|
| PDLC | Product development life cycle: understanding, designing, changing, testing and releasing software |
| MCP | Model Context Protocol: the tool interface agents use to call Sanctum and the hubs |
| Private gold | Expected facts and grading criteria hidden from the answering agent |
| Arm | One experiment setup, such as direct hub access or Sanctum retrieval |
| Pin | Select an exact version or configuration so a run can be reproduced |
| Ontology | The defined kinds of things and relationships in routing memory |
| HLD / LLD | High-level design / low-level design |

## Buckets

| Bucket | What it covers | Records |
|---|---|---|
| [Scope and contracts](scope-and-contracts/README.md) | Define the research scope, keep private answers outside runtime, and maintain explicit interfaces. | ADR-001–003 |
| [Evidence and hubs](evidence-and-hubs/README.md) | Represent searchable evidence while preserving its origin, version and business relationships. | ADR-004–006, 023 |
| [Routing memory](routing-memory/README.md) | Turn evidence into a reviewed map of subjects and useful search locations. | ADR-007–009 |
| [System One: model decisions](system-one/README.md) | Separate model invocation from the policy that applies source-selection advice. | ADR-010–012, 024–025 |
| [Agent harness](agent-harness/README.md) | Run fresh, recorded agent attempts using reusable scenario inputs. | ADR-013–016 |
| [Evaluation](evaluation/README.md) | Create diverse grounded questions and separate valid evidence, answer meaning and acceptance. | ADR-017–020 |
| [Operations and documentation](operations-and-documentation/README.md) | Make local inputs, reproduction limits and documentation navigation explicit. | ADR-021–022 |

## How to read these records

Each ADR has a short context, concrete decision, reason, tradeoffs and source links. The recording date is not an invented original meeting or approval date. Tradeoffs explain the consequences; they do not claim that every alternative was formally evaluated.

| Status | Meaning |
|---|---|
| Implemented | The choice is represented in lab code or the recorded workflow; not production approval |
| Experimental | Implemented for an explicitly scoped experiment; not a promoted default |
| Historical | Describes an earlier campaign policy still available as a control; not the later campaign’s behavior |

Where a reason is reconstructed from implementation, it explains the observed choice; it is not a claimed quotation from an original decision meeting.

This catalog does not grant new approvals, change runtime configuration or replace the owning HLD. Some decisions are working assumptions rather than formally ratified owner decisions. Follow the linked evidence for that distinction.

## Decision history and open questions

- **Owner decisions:** [existing register](../decisions.md). Its D-* IDs remain intact; these ADR IDs document different, implementation-level choices.
- **Design intent:** [intelligence-layer HLD and memory design](../../design/intelligence-layer/README.md). Experimental unconstrained selection is explicitly separate from an HLD-conformance claim.
- **Jev evolution:** [ADR-011](system-one/011-shadow-and-guarded-controls.md) records earlier controls; [ADR-012](system-one/012-unconstrained-selection.md) records the experimental override of that selection policy. Both modes remain implemented.
- **Scoring evolution:** [ADR-019](evaluation/019-versioned-scoring-repair.md) records v3 repairs. The 0/1/2 checklist meaning is unchanged.
- **Pending acceptance:** independent task-gold and human answer acceptance remain unresolved; numerical findings are exploratory.
- **Deferred capabilities:** production connectors, local coding workspaces, other native agent adapters and external graph storage have no accepted implementation decision here.
- **Unpromoted variations:** richer Jev descriptions and place-memory changes remain experiments, not new runtime defaults.

## Add or change an ADR

1. Choose the bucket by the decision’s primary responsibility, not by the service’s business domain.
2. Use the next unused global ADR ID and the same short sections. Give it evidence links and an accurate status.
3. State which earlier choice it changes. Preserve the earlier record and link both directions if a decision is superseded.
4. Update the bucket index and this catalog. Keep measured results in their experiment record.
5. Correct wording, facts or links in place with a dated correction note. A changed architectural choice needs a new ADR; preserve the old choice and link both records.
6. Record any missing approval or evidence rather than turning an assumption into an accepted decision.
