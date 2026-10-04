# Lab documentation plan

Prepared 2026-10-04 from the current working tree. Scope: the lab implementation, including corpus authoring, hub serving, routing memory, System One and the agent-level harness. Architecture decisions remain owned by `design/intelligence-layer/`; experiment histories remain in `docs/experiments/`.

## Reader journey

An engineer should find three things within one screen: what the lab does, an offline command that works from a fresh checkout, and the path to the subsystem they want to modify. Separate concepts, tutorials, operations and reference. Link to historical reviews rather than asking readers to read them first.

## Proposed hierarchy

| Page | Purpose | Grounding |
|---|---|---|
| `docs/lab/README.md` | Start here; choose offline tutorial, architecture, subsystem or runbook | Existing root README, packages, tools |
| `docs/lab/quickstart.md` | Python 3.12 setup; deterministic world, lint and tests; no paid inference | pyproject.toml, build_world.py, lint_world.py, score_m0.py |
| `docs/lab/architecture.md` | Two flows: reference evaluation and Claude/direct-vs-Sanctum; trust and private-gold boundaries | runner.py, process_sut.py, agent_runner.py, agent_mcp.py, agent_runtime.py |
| `docs/lab/corpus-and-hubs.md` | Artifact schema, four pilot hubs, repo/domain/team cross-links, author/audit/package/verify flow | corpus.py, servers.py, PDLC authoring and ingestion tools |
| `docs/lab/routing-memory.md` | Candidate vs accepted release; node/edge semantics, source declarations, provenance, runtime projection | harvest.py, memory.py, resolution.py, registry.py |
| `docs/lab/system-one.md` | Broker/provider contract, model verification, budgets, calibration and fail-open behavior | system_one_broker.py, sanctum_systemone/protocol.py, decision.py |
| `docs/lab/agent-harness.md` | Bundle public/private contract; adapter/controller, tool surfaces, isolation, delivery and ledger | bundle.py, agent_contract.py, agent_session.py, agent_schedule.py, delivery.py |
| `docs/lab/scoring.md` | Mechanical checks vs semantic judging; PDLC/HLD/LLD anchors, protocol zeros, paired reporting, acceptance gates | agent_score.py, quality_policy.py, report_agent_run.py, tests fixtures |
| `docs/lab/runbook.md` | Plan/dispatch/inspect/resume/score/report commands, fresh output paths, failures and prerequisites | CLI argparse, run_agent_campaign.py, run_quality_evaluation.py |
| `docs/lab/extending.md` | New corpus, source connector and agent adapter; implemented vs future capabilities | HarvestConnector, registry contracts, supported claude_code adapter, evidence_only mode |
| `docs/codebase-map.md` | Compact source/test index with relative paths | Verified package entry points and test names |

Use at most two heading levels below each title, short paragraphs and flat tables. Each page begins with its purpose and prerequisites and ends with a small related-links list. Keep the main index around one screen. Put field contracts in their owning page; avoid repeating the same schema across pages.

## Essential accuracy constraints

- Distinguish the world-derived reference evaluator from private PDLC task gold; the latter is authored and only partly independently accepted.
- Hubs are working simulated MCP services over synthetic local files/FTS5, not imported production repositories. Code artifacts are files inside repo containers, not one repo per artifact.
- Six synthetic repos and five domains describe the current pilot, not hard-coded harness requirements.
- Evidence-only empty workspace is implemented. Local coding loops and Codex/Pi adapters remain future work.
- Reviewed pilot routing memory is scoped synthetic policy. Generated proposals cannot create enterprise ownership or authority.
- A completed native run is not task success. Same-model semantic judging and post-run repairs make the current comparison exploratory; human and boundary-gold acceptance remain separate.
- `build/`, runs, credentials and API keys stay local. A GitHub checkout does not include the prepared 120-artifact corpus, release or 180 native results.
- Generic bundle/config primitives are reusable; PDLC preparation scripts and the quality-evaluation driver currently have local paths/provider assumptions. Document these rather than claiming universal portability.

## Verification and delivery

1. One Astra low review of this plan and code grounding, specifically engineer findability, cognitive load, overlap, runnable commands, honest boundaries and missing extension/troubleshooting guidance.
2. Incorporate that single review without a review loop; write the pages and add a short root README pointer.
3. Run the required lab checks and validate Markdown relative links and command entry points. Execute an offline fresh-directory tutorial, keeping live scoring outputs untouched.
4. Inspect the exact Git diff and candidate staged files for credentials/local paths or generated runtime data. Commit source, tests, tooling and Markdown on a new branch; push to origin without rewriting main.
5. Deliver branch URL, documentation entry point and check results. Preserve local-only evidence references as explicit prerequisites.

## One-pass review disposition

[Astra low review](reviews/lab-documentation-plan-astra-low.md) completed once. All six findings incorporated: bootstrap/offline distinction and expected outcomes; separate acceptance/activation states; two-pipeline navigation; single page ownership; recovery table and local-driver limitations; supported/future extension matrix. Add the fully materialized synthetic shipping fixture under `examples/agent-bundles/shipping` so the agent tutorial needs no ignored PDLC inputs. No second review loop.

## Delivery checklist and verification

- [x] Ground structure in package entry points and actual CLI arguments.
- [x] Complete one Astra low plan review and incorporate all six findings.
- [x] Write ten lab pages, a shared codebase map and a prominent root README entry point.
- [x] Include a fully materialized synthetic shipping fixture; keep PDLC outputs/credentials local.
- [x] Verify 89 relative links and staged diff whitespace.
- [x] Full regression: 652 passed, 2 live-provider skips, 6 expected failures.
- [x] Subsequent quality-driver continuation change: 40 focused checks passed, including exhausted-retry failure isolation.
- [x] Run six tutorial/fixture steps from a clean staged-file copy with no original build/runs/env inputs: render, lint, M0 score, bundle validation, schedule and MCP fixture all exit zero. Existing Python 3.12 dependencies/tokenizer cache were reused; package installation was not tested offline.
- [x] Inspect staged files for credential patterns and excluded generated directories; none found.

Publication target: new branch `lab/pdlc-harness-docs-20261004` on origin. Verification proves the offline source/fixture path, not production behavior or independent benchmark acceptance. Live quality scoring continues separately and retains unknown judge failures without fabricated grades.
