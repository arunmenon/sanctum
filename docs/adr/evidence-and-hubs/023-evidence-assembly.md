# ADR-023: Pack whole evidence passages and preserve reported conflicts

- **Bucket:** [Evidence and hubs](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`; added after catalog review

## Context

Choosing a hub does not guarantee that every retrieved passage reaches the agent. Sanctum has a limited evidence budget and must choose what to include. Silently dropping one side of a disagreement could make uncertain evidence look settled.

## Decision

- Pack complete evidence units, including their source metadata, rather than cutting them mid-passage.
- Reserve both passages supporting each rule-flagged conflict before filling remaining space by rank.
- Keep the conflict record when both passages cannot fit, and report missing passages as omissions.
- Use remaining budget for model-promoted conflict pairs and additional evidence; these do not displace the initial rule-based reservations.

## Why this approach?

*Retrospective explanation of the linked assembly code, not a new approval.*

The agent should see the evidence behind a disagreement, rather than receive a silently resolved answer. Whole passages retain context and provenance, while omission records show what the budget prevented Sanctum from delivering.

## Tradeoffs and limits

- Preserving conflicting passages consumes budget that could otherwise hold more evidence.
- Conflict detection uses bounded rules and optional model judgments; it does not discover every disagreement.
- A recorded conflict may lack one or both supporting passages in the delivered response. It must not be read as complete coverage.
- This is Sanctum’s evidence assembly policy. The harness separately records and limits what Claude actually receives.

## Related decisions

- [ADR-015](../agent-harness/015-evidence-delivery-and-limits.md): delivery accounting and attempt limits.
- [ADR-018](../evaluation/018-mechanical-and-semantic-scoring.md): source support and answer quality.

## Evidence

- [Assembly implementation and policy](../../../src/sanctum_ref/assembly.py)
- [Retrieval pipeline](../../../src/sanctum_ref/pipeline.py)
- [Architecture guide](../../lab/architecture.md)

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
