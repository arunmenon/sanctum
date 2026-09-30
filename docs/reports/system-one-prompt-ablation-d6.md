# Prompt campaign, rows 1 to 3: D6 ablation (shadow, dev)

> SYNTHETIC, NOT PRODUCTION EVIDENCE. **Measured once**, shadow-only, dev cases only; no calibration was applied and nothing was promoted. Acceptance and holdout were not touched. Numbers only: these are new models and the measurement changes land alongside, so no conclusion about either model is drawn here. Plan: docs/reviews/system-one-prompt-review-full.md; spend in docs/reports/system-one-prompt-campaign.md.

## Setup

| Item | Value |
|---|---|
| World | build rebuilt from HEAD in a separate worktree, manifest `452b57d9` for every row here (the in-progress challenge world was not used; see the campaign summary) |
| Population | 60 dev cases; 84 rule-produced D6 pairs per complete run: 62 rule-flagged, 22 promotable candidates |
| Labels | evaluator side (`sanctum_eval.calibration_labels`): 12 positive pairs, all among the rule-flagged; 0 of 22 candidates positive |
| Rows 1-2 | commit `94402e2`, tool version 1: the tool's own nested CV, and no per-item records, so they cannot be re-reported with the shared helper offline; raw results `docs/reports/data/{jev,laya}-d6-noul-v*.json` |
| Row 3 | commit `fd19e4f`, tool version 2 with `sanctum_eval.calibration.nested_cv` (calibrator and use band chosen on inner case-grouped folds, reported on 5 outer folds); per-item records `docs/reports/data/row3r-*.json` |
| State | rows 1-2: v1 text slices; row 3 Jev: `r3-state-v2` labeled excerpts (up to 1,200 chars per record); row 3 Laya: `r3-state-v2-compact` (350) and `r3-state-v2-compact-150` (150), one pair per call |
| Tolerance | false-promotion rate 0.2 (unchanged) |

## Results

Raw `noul` answers. AUC and PR-AUC are undefined where a stratum has no positive.

| Row | Provider | Template (state) | Pairs answered / 84 | ROC-AUC all (n, pos) | PR-AUC all | Brier all | ROC-AUC flagged (n, pos) | Candidates answered (pos) | Nested-CV candidate promotions (false) | Calls |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Jev | `d6-noul-v1` (v1) | 84 | 0.804 (84, 12) | 0.530 | 0.154 | 0.793 (62, 12) | 22 (0) | 0 (0), own CV | 28 ok |
| 2 | Jev | `d6-noul-v2-relations` (v1) | 80 | 0.812 (80, 11) | 0.532 | 0.433 | 0.766 (58, 11) | 22 (0) | 0 (0), own CV | 25 ok, 3 refused at row ceiling |
| 3 | Jev | `d6-noul-v3-excerpts` (v2) | 84 | 0.803 (84, 12) | 0.509 | 0.390 | 0.761 (62, 12) | 22 (0) | 0 (0) of 22 eligible | 28 ok |
| 1 | Laya | `d6-noul-v1` (v1) | 84 | 0.271 (84, 12) | 0.101 | 0.289 | 0.282 (62, 12) | 22 (0) | 0 (0), own CV | 28 ok |
| 2 | Laya | `d6-noul-v2-relations` (v1) | 38 | 0.688 (38, 6) | 0.356 | 0.265 | 0.649 (25, 6) | 13 (0) | 0 (0), own CV | 16 ok, 12 truncated |
| 3 | Laya | `d6-noul-v3-excerpts-compact` (compact 350) | 3 | undefined (3, 0) | undefined | 0.649 | undefined | 0 | not computed | 2 ok, 26 truncated |
| 3 | Laya | `d6-noul-v3-excerpts-compact-150` (compact 150) | 36 | 0.869 (36, 3) | 0.335 | 0.331 | 0.745 (20, 3) | 16 (0) | 0 (0) of 16 eligible | 12 ok, 16 truncated |

Nested CV (shared helper), row 3:

| Provider | Outer-fold AUC mean (sd, folds) | Outer-fold Brier mean (sd) | Calibrators selected | Use band per outer fold |
|---|---|---|---|---|
| Jev, excerpts | 0.734 (0.302, 5) | 0.110 (0.050) | platt_l2 ×3, platt ×2 | 1.0, 0.5, 0.5, 0.75, 1.0 |
| Laya, compact 150 | 0.583 (0.520, 3) | 0.174 (0.166) | intercept_only ×5 | 1.0 in all 5 |

With no candidate promotion, the false-promotion rate has no denominator; with 0 positives among the 22 candidates, any candidate promotion on dev could only be false.

## Denominators and costs

- Jev row 3 was first run with a 25,000 input-token row ceiling (the review's estimate) and stopped at 33 of 84 pairs (11 calls, 17 refused before dispatch; recorded in the ledger as row 3). The rerun (row 3r) sized the ceiling for all 84 pairs: 28 calls, 60,825 input tokens (about 2,170 per call, against about 1,180 for v1 slices).
- Laya's state window is about 450 tokens (reported `state_tokens` cap) within about 512 total input tokens. A compact-350 pair state serialized to about 1,350 to 1,450 characters (about 560 to 580 state tokens) and was truncated; compact-150 fit in 12 of 28 rounds. Truncated calls are voided, never used.
