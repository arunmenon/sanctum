# Jev across the Claude retrieval flow

## Objective

Keep the latest unconstrained Jev hub selection (D2). Also apply Jev at the implemented passage-relevance (D4) and conflict-assessment (D6) points, as requested on 9 October 2026. Verify effects on delivered evidence and answer quality, not merely successful model calls.

## Four setups

| Setup | Hub selection | Passage relevance | Conflict assessment |
|---|---|---|---|
| Baseline | Existing raw D2 | Rules | Rules |
| Relevance | Same D2 | Raw D4 | Rules |
| Conflicts | Same D2 | Rules | Raw D6 |
| All decisions | Same D2 | Raw D4 | Raw D6 |

All use the unchanged baseline corpus, memory release and hub descriptions from the previous follow-up. The 12 development tasks are reused: six supported, three partial and three boundary questions. One fresh session per setup gives 48 attempts, with randomized setup order within each task. This is a development comparison, not fresh generalization evidence; tasks are not independently accepted gold.

## Application policy and limits

D4/D6 use positive, non-diagnostic `noul` templates and raw probability at least 0.5. No calibration file is fabricated. D4 changes ordering and permits additional evidence in spare budget, preserving rule-packed units. D6 promotes existing candidate pairs and preserves rule-flagged conflicts. A request with no pair candidates does not need a D6 call.

Each setup retains eight agent rounds, 8,000 cumulative evidence tokens, 4,000 per response and 120 seconds per task. All retain the same broker limit of 32 calls and 500,000 reserved input tokens per attempt. Claude uses Sonnet 5.5 through the authorized subscription; provider credentials remain local. Existing spend accounting applies. Extra calls are reported but not the primary optimization objective.

## Implementation and verification

- [x] Keep existing bundles/defaults unchanged; add independent D4/D6 and combined settings.
- [x] Add explicit raw application policy; preserve legacy calibrated/shadow behavior.
- [x] Verify relevance changes delivered order and conflict judgments add reported conflicts on controlled fixtures.
- [x] Verify D2/D4/D6 through the actual process/MCP/broker path with a local provider double.
- [x] Pass affected checks: 93 passed, two live-provider checks skipped.
- [x] Refresh installed Claude isolation and round-limit checks against a local API double; both passed. This does not prove hosted inference.
- [x] Prepare and freeze the 48-attempt development schedule.
- [x] Verify hosted D4/D6 calls in real Claude traces: first combined attempt `5bd33631e8f5a3cdad032827f889c435` recorded D2, D4 and D6; D4/D6 records show raw policy, threshold 0.5 and shadow false. Controlled fixtures separately prove ordering and conflict-promotion effects.
- [ ] Complete all scheduled attempts, retaining failures and unavailable decisions.
- [ ] Score saved answers with the existing rubric and versioned policy; report three paired comparisons against the D2-only baseline.
- [ ] Publish observed decision effects, rubric results, failures and limitations. No configuration promotion is implied.

## Evidence and reproduction

- [Bundle preparation tool](../../tools/prepare_jev_flow_bundle.py)
- Local bundle: `build/agent-bundles/pdlc-jev-entire-flow-01/experiment.yaml`.
- Local run: `build/agent-runs/sonnet55-jev-entire-flow-01/`.
- Local CLI checks: `build/agent-probes/jev-entire-flow-{isolation,round-limit}-01/`.
- [Relevance ADR](../adr/system-one/024-active-passage-relevance.md) and [conflict ADR](../adr/system-one/025-active-conflict-assessment.md).

Interpret scores only after checking source decisions, actual delivered evidence and judge disputes. Preserve the earlier grading-audit work as a separate concern; this campaign does not settle those disputes.
