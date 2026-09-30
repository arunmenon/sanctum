# Plan: System One in Round 3 (D6 conflict, D4 relevance)

## Task Description

Extend the System One provider layer (design/intelligence-layer/system-one-providers.md) to the post-retrieval decisions of HLD §6.4 Round 3: D6 possible conflict first, then D4 relevance. Reuse the provider strategy interface, HTTP adapter (Jev, Laya), broker, calibration binding and shadow-only rule unchanged; add one decision template per decision, its pipeline placement, its safe default, and its own calibration and measurement. D5 stays exact-hash only. This is lab plan experiment E3, one decision at a time.

## Objective

- Design page section 14 "Round 3 decisions" specifying templates, placement, safe defaults, cost bounds, and metrics for D6 and D4.
- D6 live behind the broker: bounded candidate pairs from the existing rules get one `noul` each; uncertain, failed, invalid or truncated → `possible_conflict`, both sides kept. Calibrated per provider on dev; shadow-only otherwise.
- D4 live behind the broker: one `noul` per candidate evidence unit; may only reorder within the budget, never remove a unit the rules would have packed; uncertain → keep, lower rank.
- E3 runs: C4 vs C4 + D6, C4 vs C4 + D4, for typesafe-jev and laya-local, on dev and scenarios, then once on acceptance and holdout. Latency reported, not gated.

## Solution Approach

| Decision | Template | Input state | Pairs or units per call | Safe default | Primary metrics |
|---|---|---|---|---|---|
| D6 | `d6-noul-v1`: "Do these two evidence units assert incompatible values for the same fact, scope and version?" | the two units' text spans, their source ids, versions, environments | bounded pairs from `conflict_extraction: typed_rules` only | flag `possible_conflict`, keep both | conflict witnesses kept, expected conflicts flagged, false conflicts flagged, relation type accuracy |
| D4 | `d4-noul-v1`: "Does this evidence unit support an answer to the query?" | query + one unit's text, source id, version | up to `candidates` (60), batched by provider limit | keep, lower rank | necessary-evidence recall within budget, precision proxy, harmful omissions, tokens returned |

Rules that must hold:
- Model calls in Round 3 are `model_call` observations, separate from source calls (already the case).
- D4 never removes a unit that the rules-only packer would include; it may promote or demote within the budget. A test proves packed-set superset property under any D4 output.
- D6 judges only rule-produced pairs; it cannot create pairs or dismiss a rule-flagged conflict below the flag (it can raise `possible_conflict` to a calibrated probability, never hide the pair).
- Cost bound: per-round total-call limit and shared deadline as in handshake point 14; on laya-local D4 latency grows ~90 ms per unit, so report it and cap units per request by config.
- Calibration per decision, provider, resolved model, template, descriptor release; fitted on dev only; labels from gold relations (D6) and necessary-evidence spans (D4) through the evaluator side, never read by the SUT.

## Team

- m3-ref: design section, templates, pipeline placement, SUT tests, runs.
- m3-data: evaluator labels for calibration (D6 from gold relations, D4 from necessary spans) exposed through the fit tool only; metrics additions (false conflicts flagged, relation accuracy, D4 reorder-only check in scoring); report sections.

## Steps

1. design-round3 (m3-ref): section 14 + cross-links; commit.
2. d6-live (m3-ref) in parallel with d6-labels-metrics (m3-data); calibrate D6 for jev and laya on dev; runs; commit.
3. d4-live (m3-ref) in parallel with d4-labels-metrics (m3-data); calibrate; runs; commit.
4. Acceptance and holdout once per decision (lead), reports, milestones E3 record, push.

## Acceptance Criteria

- Adapter, broker and provider registry unchanged except configuration.
- D6 and D4 each have a template, safe default, calibration file per provider, and tests for the invariants above.
- E3 reports for dev, acceptance and holdout with paired deltas and intervals; results reported whichever direction they go.
