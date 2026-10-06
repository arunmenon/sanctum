# ADR-010: Call decision providers through a runner-owned broker

- **Bucket:** [System One](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

System One supplies model decisions inside Sanctum retrieval; Jev is the provider used in these experiments. Sanctum needs these decisions without receiving provider credentials or making internal model calls invisible to the experiment’s usage records.

## Decision

- Keep credentials and request/response accounting in the runner-owned broker.
- Validate the provider’s request/response format and select exact versions of the model, prompt, hub descriptions and any applicable calibration inputs.
- Verify the resolved provider/model rather than treating a configuration alias as execution proof.

## Why this approach?

*Retrospective explanation based on the linked implementation and records; not a new approval.*

The broker makes external decisions and their cost distinguishable from agent tool calls.

## Tradeoffs and limits

- Provider invocation and policy application are different readiness checks.
- Unknown usage is not zero; test providers do not establish real inference.

## Evidence

- [system_one_broker.py](../../../src/sanctum_run/system_one_broker.py)
- [protocol.py](../../../src/sanctum_systemone/protocol.py)
- [test_system_one_broker.py](../../../tests/test_system_one_broker.py)
- [system-one.md](../../lab/system-one.md)

*Documentation reviewed and clarified on 2026-10-06; runtime choices unchanged.*

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
