# System One: what Jev decides

System One is Sanctum’s decision layer. In the hosted experiments, Jev judges which hubs are likely to help answer a retrieval question. It selects evidence sources; Claude still writes the answer.

A **hub description** is the text Jev reads about a source’s contents. Changing that text changes the information available to Jev, even when the hub’s actual documents stay the same.

## The call path

```mermaid
flowchart TD
    S[Sanctum retrieval question] --> B[Runner-owned broker]
    D[Hub descriptions and prompt] --> B
    B --> J[Jev provider]
    J --> U[Source-usefulness decisions]
    U --> M[Configured routing mode]
    M --> H[Selected hubs searched by Sanctum]
```

The broker holds provider credentials and saves model-call records. Sanctum calls through the gateway; Claude has no Jev tool or provider key.

## Which Jev advice actually affects routing?

The lab retains three experimental behaviors. A real Jev call alone does not tell you which one ran.

| Mode | Selection behavior | Result record |
|---|---|---|
| Shadow | Record advice; keep candidates when skip decisions are uncalibrated | [Original comparison](../experiments/pilot-0-quality-results.md) |
| Guarded | Apply calibrated filtering; required-source and nonempty rules can override it | [Guarded findings](../experiments/pdlc-jev-guarded-results.md) |
| Unconstrained | Select on raw usefulness probability ≥ 0.5; no selection overrides | [Unconstrained findings](../experiments/pdlc-jev-unconstrained-results.md) |

Calibration means checking decisions on separate development examples before choosing a threshold. The unconstrained mode deliberately uses raw decisions without that fitted threshold.

```mermaid
flowchart TD
    J[Jev advice] --> S[Shadow: record advice]
    J --> G[Guarded: apply calibration]
    J --> U[Unconstrained: apply raw yes or no]
    S --> K[Keep routing candidates]
    G --> R[Required-source and nonempty overrides]
    U --> N[Search chosen hubs, possibly none]
    K --> H[Hubs searched]
    R --> H
    N --> H
```

**In unconstrained mode:**

- Jev considers all eligible pilot hubs, rather than a rule-selected shortlist.
- Sanctum searches the hubs Jev selects. That can be none.
- No rule adds a hub back, and no calibration adjusts the raw decision.
- Memory can translate names and search scopes; it cannot add or remove a hub.
- Access checks, process isolation and run limits still apply.
- Missing model answers are recorded as unavailable; they do not trigger rules-based selection.

Experiment setup and budgets are in the [method guide](../experiments/method/README.md). Outcomes are in the [results index](../experiments/README.md).

## Provider configuration and verification

Runtime bundles record the provider, descriptors, prompts, calibration files where applicable, resolved model and verification proof. A pinned model means a specific verified identifier, not a name that can silently resolve to a different model later.

Use native agent and broker records to establish what actually ran. Test providers exercise the connection without proving real model inference.

If a provider is unavailable, inspect the recorded error and the configured fallback. Earlier guarded behavior preserves candidates on uncertainty. Do not assume that behavior describes every experimental mode.

## Budgets and credentials

System One calls are accounted separately from Claude’s tool calls. Budgets belong to a campaign’s bundle, not to a routing mode globally.

| PDLC campaign | Broker calls per attempt | Input-token reservation per attempt |
|---|---:|---:|
| Original shadow and guarded | 2 | 10,000 |
| Unconstrained and four-variant follow-up | 32 | 500,000 |

Read the [method guide](../experiments/method/README.md#resource-limits) for the agent’s separate limits. New experiments must verify their own settings.

Unknown provider usage remains unknown and must be reconciled. An unissued request is different from a dispatched request whose usage receipt is missing.

Keys and authentication tokens stay in ignored local inputs. They are not corpus evidence or memory-release content. The hosted experiments use synthetic evidence.

## Find the code

| Responsibility | Entry point |
|---|---|
| Provider contract and budgets | [protocol.py](../../src/sanctum_systemone/protocol.py) |
| Broker, credentials and call records | [system_one_broker.py](../../src/sanctum_run/system_one_broker.py) |
| Decision implementations | [providers](../../src/sanctum_ref/providers/__init__.py) |
| Apply routing mode | [pipeline.py](../../src/sanctum_ref/pipeline.py) |

Verification: [provider tests](../../tests/test_system_one_providers.py), [broker tests](../../tests/test_system_one_broker.py), [runtime tests](../../tests/test_agent_runtime.py).

Next: [agent harness](agent-harness.md). [Back to start](README.md).
