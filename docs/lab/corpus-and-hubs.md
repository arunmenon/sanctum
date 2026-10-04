# Corpus and knowledge hubs

Hubs serve evidence. They are simulated, working MCP services over local JSONL artifacts and an SQLite FTS5 search index. They are not production repository connectors.

## Artifact contract and hierarchy

Each `hubs/<hub_id>/` directory contains `artifacts.jsonl` and `capabilities.json`. [HubRow](../../src/sanctum_hubs/corpus.py) requires `artifact_id`, `version`, `text`, `title`, `kind`, `path`, `location`, `environment`, `acl` and `metadata`. Identity is source + artifact + version. The enclosing manifest pins file bytes; content hashes identify exact evidence text.

| Pilot hub | Evidence | Typical home |
|---|---|---|
| CodeHub | Code, schemas, configuration and tests | Repo container → file path → version |
| DocHub | Designs, contracts, proposals and discussions | Document space → document/module path → version |
| SkillHub | Testing, rollout and recovery procedures | Guidance collection → procedure path |
| MemoryHub | Prior investigations, sessions and handoffs | Session collection → session ID |

The current PDLC candidate has 120 artifacts: 25 code, 49 documents, 16 procedures and 30 memories. Code artifacts occupy six synthetic repo containers; they are not 25 repositories. Five domains cross the four hubs. Domain, service and team links are many-to-many rather than a single nested ownership tree. The 18 added design documents provide one HLD and two module LLDs per repo, with draft status preserved. IncidentHub exists in the base lab but is outside this pilot.

[map_pdlc_hierarchy.py](../../tools/map_pdlc_hierarchy.py) assigns navigation containers and cross-links. [ingest_pdlc_corpus.py](../../tools/ingest_pdlc_corpus.py) preserves those mappings in metadata and converts audited drafts into HubRow records. A document-to-repo association does not make that document authoritative for current code behavior.

## Author, audit, load, accept

| Transition | Artifact and responsible role | Check |
|---|---|---|
| Author drafts | LLM author packets and raw outputs; corpus author | Local-context grounding, introduced claims and cost receipts |
| Audit and repair | Audited candidate and review receipts; corpus reviewer | Interfaces, versions, contradictions, realism and leakage |
| Package and load | `build/pdlc-pilot/`; ingestion operator | Design/source review hashes, hierarchy, unique IDs, hub schema |
| Verify retrieval | MCP verification receipt; lab operator | Every artifact can be fetched with the intended principal |
| Accept/freeze evaluation | Experiment readiness and task-gold records; independent evaluator | Separate gold acceptance and pinned snapshots; loading alone is insufficient |

Pilot authoring supports OpenAI and Gemini through [generate_pdlc_corpus.py](../../tools/generate_pdlc_corpus.py). It uses bounded jittered retries and a reservation ledger. Provider/model IDs and price records are explicit inputs to this historical preparation workflow, not a guarantee that they remain current.

The PDLC ingester intentionally writes only `build/pdlc-pilot` and requires local audited authoring inputs. It does not recreate the pilot from a fresh checkout automatically. Use the checked-in shipping fixture for onboarding, or supply a separately audited bundle for a new scenario.

[servers.py](../../src/sanctum_hubs/servers.py) owns source-specific search/fetch tools. [access.py](../../src/sanctum_hubs/access.py) enforces ACLs; [versions.py](../../src/sanctum_hubs/versions.py) controls version reads. Lab mutations and failure injection remain runner/admin functions, not agent tools.

Next: [routing memory](routing-memory.md), [extending](extending.md), [runbook](runbook.md).
