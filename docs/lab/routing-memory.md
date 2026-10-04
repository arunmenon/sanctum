# Sanctum routing memory

Routing memory tells Sanctum how to identify subjects and where to search. MemoryHub stores session evidence; it does not itself activate routing policy.

## What the graph represents

| Relation or record | Meaning | Runtime treatment |
|---|---|---|
| DENOTES | A scoped native name identifies a canonical entity | Accepted names support resolution |
| SELECTS_FOR | A source place is a useful search scope for an entity | Accepted selectors guide retrieval |
| MEMBER_OF | An explicit entity/domain membership | Trusted declarations guide context |
| ABOUT | An artifact or passage discusses a subject | Accepted, version/hash-bound subjects affect evidence identity |
| Procedures and authority assertions | Reviewed routing obligations and fact-kind authority | Scoped owner declarations and review required |
| PARENT / related associations in harvest | Navigation/context structure | Do not assume every harvested edge is traversed at runtime |
| RELATES_TO | Relationship retained for review | Stored, deliberately unused operationally |

[harvest.py](../../src/sanctum_ref/harvest.py) has a connector contract for paginated inventory and versioned fetch. It collects stable snapshots, validates source IDs and hashes, proposes links, validates exact supporting spans and quarantines unsupported proposals. LLM output is a proposal, never an ownership declaration.

[RelationStore](../../src/sanctum_ref/memory.py) keeps entities in dictionaries and adjacency-style edge lists keyed by subject/relation. `TableStore` implements equivalent queries using flat tables. ABOUT bindings use an artifact lookup keyed by source, artifact, version and content hash. There is no external graph database. A harvested candidate graph and its runtime projection have different shapes; projection exposes only supported, accepted records.

## Acceptance and selection are distinct

| Step | Responsible role | Artifact / check |
|---|---|---|
| Declare source policy | Source owner, or explicitly scoped synthetic lab curator | Owner registry, membership, authority and routing declarations |
| Collect and propose | Harvest connector / LLM author | Stable inventory snapshot and grounded candidate assertions |
| Decide assertion status | Delegated reviewer | Candidate snapshot hash, reviewer identity and source/edge/entity grants |
| Assemble release | Release operator | `review_bundle` / `project_release`; unspecified proposals stay unreviewed |
| Select runtime release | Experiment operator | Explicit memory release argument or `ACTIVE` pointer; runtime pins and scoped review bindings checked |
| Accept an evaluation | Independent evaluator | Corpus/task acceptance separate from runtime memory selection |

The harvest pipeline does **not** switch `ACTIVE`. [agent_runtime.py](../../src/sanctum_run/agent_runtime.py) verifies a bundle's release, review, delegation and owner-policy pins before opening Sanctum. Explicit release selection is preferred for experiments; changing global `ACTIVE` would affect later unpinned reference runs.

The pilot's reviewed release is synthetic lab policy. Some assertions remain unreviewed; unknown subjects stay unknown. Owner declarations cannot be inferred from prose or invented to fill a graph gap. Visibility/principal scope and source versions remain attached to records.

Next: [System One](system-one.md), [runbook](runbook.md), [HLD artifacts](../../design/intelligence-layer/README.md).
