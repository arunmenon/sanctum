# Reusable agent harness

The implemented path runs Claude Code headlessly in an empty workspace. A scenario bundle supplies evidence, questions, private gold and limits; it does not supply a sequence of searches for Claude to follow.

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

All referenced paths are bundle-relative and constrained within its root. Manifest, caller and runtime hashes prevent accidental drift. Public tasks and private gold join by `task_id`; gold includes required facts, evidence or boundary obligations, task-specific plan checklists and a diversity matrix. See the complete [shipping example](../../examples/agent-bundles/shipping/experiment.yaml).

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

[agent_schedule.py](../../src/sanctum_run/agent_schedule.py) freezes task/arm/repetition IDs from pinned inputs and seed. [agent_runner.py](../../src/sanctum_run/agent_runner.py) opens the trusted gateway and chosen adapter. [agent_session.py](../../src/sanctum_run/agent_session.py) creates isolated HOME/config/workspace, starts the native CLI, enforces limits and records terminal outcomes. [agent_bridge.py](../../src/sanctum_run/agent_bridge.py) relays MCP over the session's local socket.

The direct arm exposes authorized hub tools. The Sanctum arm exposes only `sanctum_retrieve`; Sanctum then calls hubs through the gateway. [delivery.py](../../src/sanctum_run/delivery.py) normalizes both paths into citable passages and charges all displayed evidence metadata against shared limits. Full-file and search results must become observed, versioned evidence before citations can earn credit.

Each attempt has a fresh session. API and subscription authentication are explicit, incompatible modes. Subscription uses the first-party cached OAuth credential solely for Claude Code; it does not fall back to an API key. Isolation proofs are tied to the exact CLI binary/model/auth mode. POSIX cleanup and actual installed-CLI probes verify controls; they do not provide a hostile-code sandbox for future coding tasks.

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

Next: [runbook](runbook.md), [scoring](scoring.md), [extending](extending.md).
