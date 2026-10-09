# ADR-025: Apply Jev conflict assessment alongside passage relevance

- **Bucket:** [System One](README.md)
- **Status:** Experimental — lab scope only
- **Recorded:** 2026-10-09

## Context

The reference implementation can ask a model about potentially conflicting passage pairs, but the Claude runner did not enable this step. The CLI also allowed relevance or conflict assessment, not both in one retrieval request.

## Decision

- Allow D6 conflict assessment and D4 relevance together, or independently, through the existing runner and broker.
- In the new experimental arm, promote a rule-produced candidate pair to a reported possible conflict when Jev's raw positive probability is at least 0.5.
- Preserve rule-flagged conflicts regardless of model response. Preserve the existing packing rules for their supporting passages.
- Keep unavailable answers distinct from negative answers; they do not promote a pair. Record the policy and model responses.

## Why this approach?

This exercises the existing conflict decision in the agent-level experiment, rather than inferring benefit from an unused capability. The broker reads source-bound evidence; the answering agent does not supply the model's passage text.

## Tradeoffs and limits

- Jev assesses bounded candidate pairs produced by rules. It cannot invent arbitrary pairs or erase existing rule flags.
- Raw probabilities are not calibrated. Missing judgments must remain visible in the analysis.
- A request with no conflict candidates needs no D6 call; lack of a call is not by itself an integration failure.
- Combined decisions share the attempt's existing deadline and broker budget. Their overhead can affect delivery and must be reported.

## Related decisions

- [ADR-010](010-broker-and-pins.md): broker and evidence-reference validation.
- [ADR-023](../evidence-and-hubs/023-evidence-assembly.md): preserve reported conflicts and omissions.
- [ADR-024](024-active-passage-relevance.md): relevance and experimental raw policy.

## Evidence

- [Combined decision path](../../../src/sanctum_ref/pipeline.py)
- [CLI](../../../src/sanctum_ref/__main__.py)
- [Runtime wiring](../../../src/sanctum_run/agent_runtime.py)
- [Conflict behavior checks](../../../tests/test_round3_decisions.py)
- [MCP integration checks](../../../tests/test_agent_runtime.py)
- [Experiment setup](../../experiments/pdlc-jev-entire-flow-plan.md)

[Back to catalog](../README.md)
