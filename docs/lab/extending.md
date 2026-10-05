# Extending the lab

To test another repository or domain, supply a different scenario bundle. The same harness can then schedule questions, record searches and score answers against that bundle’s private criteria.

Some parts are reusable today; others still need implementation. Check the table before treating a new bundle as a complete integration.

| Capability | Current support |
|---|---|
| Alternate repository/domain content | Bundle-driven hub artifacts, public tasks and private criteria |
| Source inventory and ontology proposals | Reusable `HarvestConnector` inventory/fetch protocol and validators |
| Native coding agent | Claude Code in evidence-only, empty-workspace mode |
| Coding inside checked-out repositories | Future work; needs workspace and containment policy |
| Codex, Pi or another agent | Future adapter implementation; not accepted by the current runtime validator |
| External graph database / Spanner | Future storage choice; current release projection is local in memory |

## Bring a new scenario

Copy the [shipping example](../../examples/agent-bundles/shipping/README.md) into a fresh scenario. Replace evidence, source capabilities and principals, then author public tasks and separate private gold against exact versions. Update manifest/caller hashes, matrix quotas and task IDs; do not weaken validation to fit an inconsistent dataset.

Required positive facts need unique exact quotes or explicit character spans in the pinned corpus. Boundary tasks need recorded corpus limits and relevant investigation obligations. Review HLD/LLD tasks for design quality and grounded premises rather than an exact preferred architecture. A new domain does not require editing schedule, session or score logic.

For a Sanctum arm, add reviewed source manifests, canonical entities/names/places, grounded artifact subjects, scoped declarations and verification proofs. Pin the runtime file and all referenced policy files. A direct-only fixture does not establish Sanctum readiness.

The pilot's authoring, packaging and quality-driver scripts retain scenario/local assumptions. Reuse the contracts and validators; do not assume changing a repo name in those scripts creates a production ingestion pipeline.

## Bring a new hub

Implement source-specific search/fetch tools and capability declarations, ACL/version handling and the gateway mappings. The current simulated loader has an explicit hub-ID set, so adding a wholly new source type requires code and tests, not merely a config entry. The existing IncidentHub onboarding exercise adds a known type through manifests/releases.

Implement `HarvestConnector.inventory(cursor)` with stable snapshot IDs and `fetch(item)` returning a `HarvestArtifact`. Preserve source/version/content hash, visibility and principal scope. Incomplete inventories cannot prove deletion; cursor cycles and changed snapshots fail collection. LLM proposals need exact source spans and scoped review before becoming operational policy.

## Bring a new agent

An adapter must start a fresh session, expose only the arm's tools, enforce shared limits, capture native events/final answer, support cancellation and reconcile usage. Preserve schedule IDs, evidence normalization and private-gold isolation. The validator currently accepts only `claude_code`; another executable requires an explicit contract and implementation change plus installed-agent probes.

Useful checks: [test_agent_bundle.py](../../tests/test_agent_bundle.py), [test_agent_contract.py](../../tests/test_agent_contract.py), [test_agent_session.py](../../tests/test_agent_session.py), [test_memory_harvest.py](../../tests/test_memory_harvest.py), [test_agent_runtime.py](../../tests/test_agent_runtime.py).

Next: [codebase map](../codebase-map.md), [runbook](runbook.md).

[Back to start](README.md).
