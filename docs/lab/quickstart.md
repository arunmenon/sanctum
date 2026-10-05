# Run the lab without inference

This tutorial checks that the lab works on your machine. It uses a small scripted stand-in for an agent, so it makes no Claude or Jev calls.

You will build a synthetic world, check it, then run one task through the MCP tools. The expected outputs below tell you whether each step worked. Run every command from the repository root. You need Python 3.12 and POSIX process/socket support; the subscription helper also has a macOS Keychain fallback.

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

**You should see:**

- A `hubs/` directory, private provenance and a manifest containing 3,009 distinct artifacts.
- Lint exit successfully with `0 finding(s)`.
- M0 scoring print three synthetic stub cases.

M0 checks the hand-authored fixture evaluator. It does not score the newly rendered world or the PDLC agent campaign.

## Exercise the agent harness

The [shipping bundle](../../examples/agent-bundles/shipping/README.md) is fully checked in and needs no PDLC preparation. Choose a fresh output directory; a dispatched attempt cannot be replayed in place.

```bash
PYTHONPATH=src .venv/bin/python tools/validate_agent_bundle.py examples/agent-bundles/shipping/experiment.yaml
PYTHONPATH=src:. .venv/bin/python tools/plan_agent_run.py examples/agent-bundles/shipping/experiment.yaml --out build/docs-smoke/shipping-run
PYTHONPATH=src:. TIKTOKEN_CACHE_DIR="$PWD/build/token-cache" .venv/bin/python tools/run_agent_attempt.py examples/agent-bundles/shipping/experiment.yaml --out build/docs-smoke/shipping-run --task-id shipping-eligibility --arm direct --fixture
```

**You should see:**

- Validation: one task and `ready_for_paid_dispatch: false`.
- Planning: one frozen schedule item.
- Fixture result: `completed`, `fixture: true`, and `task_complete: false`.

**`task_complete: false` is expected, not a failure.** This fixture checks orchestration, MCP calls and evidence delivery. It does not run Claude or assess answer quality.

```bash
PYTHONPATH=src:. .venv/bin/pytest -q
```

The suite verifies contracts, source isolation, failure handling, routing, memory and agent controls. Live-provider tests are skipped unless explicitly enabled; expected failures are documented in their tests. It does not independently accept private benchmark gold.

## If the offline tutorial stops

| Symptom | What to check |
|---|---|
| Python 3.12 is unavailable | Install Python 3.12, then create the virtual environment |
| Import or dependency error | Confirm the install step completed and use `.venv/bin/python` from the repo root |
| Tokenizer tries to download while offline | Bootstrap the cache with network access, then reuse the same `TIKTOKEN_CACHE_DIR` |
| Attempt already dispatched | Choose a new output directory; do not delete or replay its existing receipt |
| Fixture completes but task is not accepted | Expected: the fixture does not judge quality or provide human acceptance |

Next: [architecture](architecture.md), [runbook](runbook.md).

[Back to start](README.md).
