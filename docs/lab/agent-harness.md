# Reusable agent harness

The harness runs the experiment: start Claude, give it a question, record its searches and answer, then hand those records to the scorer. **Headless** means the command-line agent runs without an interactive chat window.

The current path uses an empty workspace and evidence tools. Claude does not edit a checked-out repository in these experiments.

## One task, from start to finish

```mermaid
flowchart TD
    B[Load scenario bundle] --> V[Validate inputs and prerequisites]
    V --> P[Freeze task and setup schedule]
    P --> C[Start fresh Claude session]
    C --> T[Claude searches via allowed MCP tools]
    T --> A[Save final answer and delivered evidence]
    A --> S[Separate scorer evaluates answer]
    S --> R[Comparison report]
```

A scenario bundle is the experiment kit: evidence, public questions, private expected facts and plan criteria, connection settings and limits. Claude receives the question, not the private answer criteria. It chooses its own searches and may retrieve repeatedly within the limits.

## Bundle contract

```text
scenario/
  experiment.yaml
  corpus/manifest.json
  corpus/hubs/<hub>/artifacts.jsonl
  corpus/hubs/<hub>/capabilities.json
  connections/principals.json
  public/tasks.jsonl
  public/instructions.txt
  private/gold.jsonl
  runtime/                     # when a Sanctum arm is configured
```

All referenced paths stay within the bundle’s root. File hashes record exact inputs so changes cannot pass unnoticed. Each public question and its private criteria share a `task_id`.

The criteria contain required facts, evidence or missing-evidence obligations, and any task-specific plan checklist. A diversity matrix records the task mix. See the complete [shipping example](../../examples/agent-bundles/shipping/experiment.yaml).

| Configuration | Purpose |
|---|---|
| `mode`, `workspace` | Currently `evidence_only`, empty workspace |
| `agent` | Adapter `claude_code`, exact model, effort, authentication and installed-CLI proofs |
| `arms` | `direct_hubs` or `sanctum_only`; Sanctum requires a verified runtime file |
| `limits` | Rounds, calls, cumulative/per-response evidence tokens, deadline and inference ceiling |
| `execution` | Repetitions, random seed and fresh-session requirement |
| `readiness` | Explicit dispatch, isolation and independent-freeze gates |

[bundle.py](../../src/sanctum_run/bundle.py) checks offline linkage, corpus hashes and task mix; its success alone does not enable inference. [agent_contract.py](../../src/sanctum_run/agent_contract.py) and [agent_runtime.py](../../src/sanctum_run/agent_runtime.py) enforce executable and Sanctum prerequisites.

## Controller and evidence path

The controller is the code that manages a run. It does four jobs:

| Job | Implementation |
|---|---|
| Record the task, setup and repetition to execute, using a fixed random seed | [agent_schedule.py](../../src/sanctum_run/agent_schedule.py) |
| Start the gateway and selected agent adapter | [agent_runner.py](../../src/sanctum_run/agent_runner.py) |
| Create isolated home, configuration and workspace directories; start the agent CLI; enforce limits | [agent_session.py](../../src/sanctum_run/agent_session.py) |
| Relay MCP messages through the session’s local socket | [agent_bridge.py](../../src/sanctum_run/agent_bridge.py) |

An adapter translates the harness’s commands into the chosen agent’s command-line behavior. Claude Code is the implemented native adapter.

The direct arm exposes authorized hub tools. The Sanctum arm exposes only `sanctum_retrieve`; Sanctum then calls hubs through the gateway. [delivery.py](../../src/sanctum_run/delivery.py) normalizes both paths into citable passages and charges all displayed evidence metadata against shared limits. Full-file and search results must become observed, versioned evidence before citations can earn credit.

### Sessions and authentication

Every attempt starts fresh so earlier conversations cannot leak into later answers. The bundle chooses either API authentication or subscription authentication; they are separate modes.

Subscription mode uses Claude Code’s cached first-party OAuth credential and does not fall back to an API key. Checks are tied to the exact installed CLI, model and authentication mode.

The current process and isolation checks verify the evidence-only experiment. They do not provide a hostile-code sandbox for future tasks that edit and execute repositories.

## Durable outputs

| Record | Meaning |
|---|---|
| `schedule.json` | Immutable task/arm/repetition plan and input hashes |
| `attempts.json` | Locked dispatch/terminal ledger; unresolved attempts cannot be replayed |
| `attempts/<id>/events.jsonl` | Native agent events |
| `attempts/<id>/result.json` | Terminal status, effective tools, observed MCP calls, delivered evidence and accounting |
| `attempts/<id>/answer.json` | Original final answer text |
| `structured-answer.json` | Optional strictly parsed sidecar; original text remains authoritative |

The fixture agent tests orchestration, not Claude capability. Future Codex/Pi adapters and local editing/testing workflows need separate implementation and containment.

[Back to start](README.md). Next: [runbook](runbook.md), [scoring](scoring.md), [extending](extending.md).
