# ADR-024: Apply Jev passage-relevance judgments in the Claude runner

- **Bucket:** [System One](README.md)
- **Status:** Experimental — lab scope only
- **Recorded:** 2026-10-09

## Context

The Claude experiments used Jev to choose hubs, while the reference code's optional passage-relevance decision was not enabled by the agent runner. Calling a model without applying its response would not test whether it improves delivered evidence.

## Decision

- Expose D4 passage relevance through pinned runtime settings in the existing Claude runner and broker.
- In the new experimental arm, apply raw positive `noul` probabilities directly, using 0.5 as the inclusion threshold for additional evidence. No fitted calibration is claimed.
- Use scores to reorder delivered passages and allow qualifying rule-excluded passages into spare budget. Retain the existing rule-packed evidence and whole-passage budget behavior.
- Record raw probability, application policy, threshold and shadow status. Keep earlier calibrated/shadow behavior as the default for existing runs.

## Why this approach?

The owner requested Jev across the implemented retrieval decision points. This reuses the existing model interface and evidence assembly instead of introducing a separate ranking service. D2 hub selection remains unchanged, allowing its contribution to be distinguished from D4.

## Tradeoffs and limits

- This is active relevance advice, but not unrestricted deletion: D4 does not remove evidence already packed by the rules.
- Raw probability is an experimental signal, not calibrated confidence. Unavailable judgments supply no scores.
- The relevance input is a bounded set of retrieved passages; Jev does not search for passages that retrieval never found.
- The comparison reuses development questions. It is not a fresh holdout or production validation.

## Related decisions

- [ADR-010](010-broker-and-pins.md): provider credentials, pins and accounting.
- [ADR-012](012-unconstrained-selection.md): unchanged unconstrained hub selection.
- [ADR-023](../evidence-and-hubs/023-evidence-assembly.md): whole-passage packing and omissions.
- [ADR-025](025-active-conflict-assessment.md): conflict assessment, selectable alongside relevance.

## Evidence

- [Runtime wiring](../../../src/sanctum_run/agent_runtime.py)
- [Decision application](../../../src/sanctum_ref/pipeline.py)
- [Raw and calibrated judgments](../../../src/sanctum_ref/providers/http_systemone.py)
- [Behavior checks](../../../tests/test_round3_decisions.py)
- [Experiment setup](../../experiments/pdlc-jev-entire-flow-plan.md)

[Back to catalog](../README.md)
