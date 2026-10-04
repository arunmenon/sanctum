# Run the lab without inference

Use this page to verify a checkout and exercise a real MCP-backed agent fixture. Run every command from the repository root. You need Python 3.12 and POSIX process/socket support; the subscription helper also has a macOS Keychain fallback.

## Install and bootstrap

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
TIKTOKEN_CACHE_DIR="$PWD/build/token-cache" .venv/bin/python -c 'import tiktoken; tiktoken.get_encoding("cl100k_base")'
```

Installation and the initial tokenizer cache download need network access. Once dependencies and that cache exist, the commands below need no model credentials or inference service. Set the same `TIKTOKEN_CACHE_DIR` when running offline; the code uses the `cl100k_base` encoding for evidence budgets.

## Check the world and reference evaluator

```bash
PYTHONPATH=src TIKTOKEN_CACHE_DIR="$PWD/build/token-cache" .venv/bin/python tools/build_world.py --seed 20260930 --out build/docs-smoke/world
PYTHONPATH=src .venv/bin/python tools/lint_world.py --build build/docs-smoke/world
PYTHONPATH=src:. .venv/bin/python tools/score_m0.py
```

Rendering produces `hubs/`, a private provenance directory and a manifest. With the checked-in base world and this seed, the manifest reports 3,009 distinct artifacts. Lint should exit zero with `0 finding(s)`. M0 scoring prints three synthetic stub cases; it checks the hand-authored fixture evaluator, **not** the newly rendered world or the PDLC agent campaign.

## Exercise the agent harness

The [shipping bundle](../../examples/agent-bundles/shipping/README.md) is fully checked in and needs no PDLC preparation. Choose a fresh output directory; a dispatched attempt cannot be replayed in place.

```bash
PYTHONPATH=src .venv/bin/python tools/validate_agent_bundle.py examples/agent-bundles/shipping/experiment.yaml
PYTHONPATH=src:. .venv/bin/python tools/plan_agent_run.py examples/agent-bundles/shipping/experiment.yaml --out build/docs-smoke/shipping-run
PYTHONPATH=src:. TIKTOKEN_CACHE_DIR="$PWD/build/token-cache" .venv/bin/python tools/run_agent_attempt.py examples/agent-bundles/shipping/experiment.yaml --out build/docs-smoke/shipping-run --task-id shipping-eligibility --arm direct --fixture
```

Validation reports one task and `ready_for_paid_dispatch: false`. Planning creates one frozen schedule item. The fixture should produce a terminal `completed` record with `fixture: true` and `task_complete: false`; it exercises the controller, MCP tool path and delivered-evidence records without running Claude or judging answer quality.

```bash
PYTHONPATH=src:. .venv/bin/pytest -q
```

The suite verifies contracts, source isolation, failure handling, routing, memory and agent controls. Live-provider tests are skipped unless explicitly enabled; expected failures are documented in their tests. It does not independently accept private benchmark gold.

Next: [architecture](architecture.md), [runbook](runbook.md).
