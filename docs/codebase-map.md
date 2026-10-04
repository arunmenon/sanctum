# Lab codebase map

Inspected 2026-10-04 against the working tree based on commit `0bab10b`. This is a navigation index; [lab documentation](lab/README.md) explains behavior. Paths are relative to repository root. The checked-in examples are synthetic.

| Area | Entry points / responsibilities | Verification |
|---|---|---|
| Wire contracts | `src/sanctum_contracts/`; request, evidence, receipts and schemas | `tests/test_contracts.py`, `tests/test_schema_freeze.py` |
| World preparation | `src/sanctum_world/`, `world/`, `tools/build_world.py`, `tools/lint_world.py`, `tools/derive_gold.py` | `tests/test_world_render.py`, `tests/test_world_lint.py`, `tests/test_gold_derivation.py` |
| Hub services | `src/sanctum_hubs/__main__.py`, `servers.py`, `corpus.py`, `index.py`, `access.py`, `versions.py` | `tests/test_hub_mcp_stdio.py`, hub/ACL/version tests |
| Reference retrieval | `src/sanctum_ref/__main__.py`, `pipeline.py`, `resolution.py`, `routing.py`, `assembly.py` | `tests/test_sanctum_ref.py`, `tests/scenarios/` |
| Routing memory | `src/sanctum_ref/harvest.py`, `memory.py`, `registry.py`; `owners/manifests/`, `owners/memory_seed/` | `tests/test_memory_harvest.py`, `tests/test_sanctum_ref_memory.py` |
| System One | `src/sanctum_ref/providers/`, `src/sanctum_systemone/protocol.py`, `src/sanctum_run/system_one_broker.py` | `tests/test_system_one_providers.py`, `tests/test_system_one_broker.py` |
| Trusted gateway / reference runner | `src/sanctum_run/gateway.py`, `proxy.py`, `process_sut.py`, `runner.py`; `tools/run_lab.py` | `tests/test_gateway_proxy.py`, `tests/test_isolation_static.py` |
| Independent reference evaluator | `src/sanctum_eval/`; gold under `gold/`; `tools/score_m0.py` | `tests/test_stub_scoring.py`, evaluator mutation tests |
| Agent bundle / schedule | `src/sanctum_run/bundle.py`, `agent_contract.py`, `agent_schedule.py`; `tools/validate_agent_bundle.py`, `tools/plan_agent_run.py` | `tests/test_agent_bundle.py`, `tests/test_agent_contract.py`, `tests/test_agent_schedule.py` |
| Agent execution / MCP | `agent_runner.py`, `agent_session.py`, `agent_bridge.py`, `agent_mcp.py`, `agent_runtime.py`, `delivery.py`, `spend.py` in `src/sanctum_run/`; `tools/run_agent_attempt.py`, `tools/run_agent_campaign.py` | `tests/test_agent_session.py`, `tests/test_agent_mcp.py`, `tests/test_agent_delivery.py`, `tests/test_agent_runtime.py`, `tests/test_agent_spend.py` |
| Agent scoring / reporting | `src/sanctum_run/agent_score.py`, `quality_policy.py`; `tools/score_agent_answer.py`, `tools/report_agent_run.py` | `tests/test_agent_score.py`, `tests/test_agent_report.py`, `tests/test_quality_scoring.py` |
| Pilot preparation | `tools/pdlc-authoring/`, `tools/generate_pdlc_corpus.py`, `tools/map_pdlc_hierarchy.py`, `tools/ingest_pdlc_corpus.py`, `tools/harvest_pdlc_memory.py`, task/design preparation tools | `tests/test_design_ingestion_gate.py`; local MCP verification receipts |
| Local semantic evaluation driver | `tools/run_quality_evaluation.py`; pinned local CLI, fixture calibration, saved-answer judgments | Current driver limitations in [runbook](lab/runbook.md) |

## Verified starting commands

After Python 3.12 dependency setup, from repository root:

```bash
PYTHONPATH=src:. .venv/bin/pytest -q
PYTHONPATH=src .venv/bin/python tools/validate_agent_bundle.py examples/agent-bundles/shipping/experiment.yaml
```

The full [offline tutorial](lab/quickstart.md) covers tokenizer bootstrap, world rendering, lint and an inference-free MCP fixture. Native inference requires separate readiness/auth/model/CLI verification.

## Non-obvious constraints

- Runtime Sanctum/hubs cannot import evaluator gold or authored world. The trusted runner observes calls; private facts stay evaluator-side.
- Bundle paths are confined to the bundle root and relevant input bytes are pinned. Paid native dispatch needs installed-CLI proofs; fixture validation does not open that gate.
- Current executable support is Claude evidence-only in an empty workspace. Generic bundles are not yet generic agent executables.
- Generated corpus, memory releases and run records live in ignored `build/` / `runs/`; the PDLC pilot cannot be recreated merely by cloning source.
- `tools/ingest_pdlc_corpus.py` deliberately targets only `build/pdlc-pilot`; the quality driver is currently developer-local. Neither is a general production connector.
- Keep immutable agent results separate from post-run scoring-policy revisions. Never edit an active evaluator's code/pins in place.
