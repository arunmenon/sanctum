# Two evaluation paths

This page explains process boundaries. Subsystem pages own field contracts; the [runbook](runbook.md) owns operational commands.

## Reference retrieval

```text
request + private gold -> lab runner / independent evaluator
                             |
                             v
                       reference Sanctum process
                             |
                        gateway proxy
                             |
                       hub MCP services
                             |
                    synthetic public artifacts
```

[runner.py](../../src/sanctum_run/runner.py) creates a gateway and observes hub calls. [process_sut.py](../../src/sanctum_run/process_sut.py) starts Sanctum as a separate process. Its inherited proxy pipes expose permitted hub operations; hub tokens stay runner-side. [sanctum_ref](../../src/sanctum_ref/__main__.py) resolves intent and subjects, selects sources, retrieves, assembles and packs evidence with receipts.

The world renderer produces public hub rows and separate private provenance. [sanctum_eval](../../src/sanctum_eval/metrics.py) scores reference responses using private gold and observed traces. It does not trust Sanctum's self-reported hub activity.

## Agent comparison

```text
public task -> fresh headless Claude session
                 |                     |
          direct-hub arm          Sanctum arm
                 |                     |
          hub MCP tools          sanctum_retrieve
                 |                     |
                 |              reference Sanctum
                 |                     |
                 +----- trusted gateway -----+
                             |
                        hub MCP services

saved answer + delivered evidence + private gold -> separate quality scorer
```

[agent_runner.py](../../src/sanctum_run/agent_runner.py) uses the same hub gateway for both arms. [agent_mcp.py](../../src/sanctum_run/agent_mcp.py) exposes one arm's tool surface. Claude decides its own searches and may call Sanctum repeatedly within the shared limits. The controller does not provide a scripted answer path.

| Boundary | Enforcement |
|---|---|
| Agent sees task, not gold or local corpus | Empty workspace, isolated configuration and restricted MCP tools |
| Direct tools cannot impersonate a caller | Gateway-owned tokens and audience-checked calls |
| Sanctum cannot read evaluator gold | Process environment/transport boundaries and isolation tests |
| Judge cannot infer arm from controller identifiers | Neutral evidence aliases and stripped tool/arm metadata |
| Agent completion cannot certify task quality | Separate semantic review, score binding and human acceptance |

System One is called through a runner-owned broker, not directly by Claude. Routing memory is a pinned reviewed release; MemoryHub is a separate evidence source containing prior sessions.

Next: [corpus and hubs](corpus-and-hubs.md), [agent harness](agent-harness.md), [scoring](scoring.md).
