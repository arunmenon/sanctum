# Prompt campaign, rows 1 to 3: D6 ablation (shadow, dev)

> SYNTHETIC, NOT PRODUCTION EVIDENCE. **Measured once**, shadow-only, dev cases only; no calibration was applied and nothing was promoted. Acceptance and holdout were not touched. Numbers only: these are new models and the measurement changes land alongside, so no conclusion about either model is drawn here. Plan: docs/reviews/system-one-prompt-review-full.md; spend in docs/reports/system-one-prompt-campaign.md.

## Setup

| Item | Value |
|---|---|
| Population | 60 dev cases; 84 rule-produced D6 pairs per complete run: 62 rule-flagged, 22 promotable candidates |
| Labels | evaluator side (`sanctum_eval.calibration_labels`): 12 positive pairs, all among the rule-flagged; 0 of 22 candidates positive |
| Rows 1-2 | commit `94402e2`, tool version 1 (own nested CV, no per-item record); raw results `docs/reports/data/{jev,laya}-d6-noul-v*.json` |
| Row 3 | commit `43ae50d`, tool version 2: `sanctum_eval.calibration.nested_cv` (calibrator and band chosen on inner case-grouped folds, reported on 5 outer folds), per-item records in `docs/reports/data/row3-*.json` |
| State | rows 1-2: v1 text slices (`refs`); row 3: labeled assertion-bearing excerpts (`excerpts`, broker-built r3-state-v2) |
| Tolerance | false-promotion rate 0.2 (unchanged) |

## Results

Raw `noul` answers. AUC and PR-AUC are undefined where a stratum has no positive.

| Row | Provider | Template | Pairs answered / asked | Cases | ROC-AUC all (n, pos) | PR-AUC all | Brier all | ROC-AUC flagged (n, pos) | Candidates answered (pos) | Nested-CV candidate promotions (false) | Outcome of provider calls |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Jev | `d6-noul-v1` | 84 / 84 | 60 | 0.804 (84, 12) | 0.530 | 0.154 | 0.793 (62, 12) | 22 (0) | 0 (0) | 28 ok |
| 2 | Jev | `d6-noul-v2-relations` | 80 / 84 | 60 | 0.812 (80, 11) | 0.532 | 0.433 | 0.766 (58, 11) | 22 (0) | 0 (0) | 25 ok, 3 refused at ceiling |
| 3 | Jev | `d6-noul-v3-excerpts` | 33 / 84 | 11 | 0.617 (33, 6) | 0.294 | 0.454 | 0.652 (28, 6) | 5 (0) | 0 (0); band 1.0 in all 5 outer folds | 11 ok, 17 refused at ceiling |
| 1 | Laya | `d6-noul-v1` | 84 / 84 | 60 | 0.271 (84, 12) | 0.101 | 0.289 | 0.282 (62, 12) | 22 (0) | 0 (0) | 28 ok |
| 2 | Laya | `d6-noul-v2-relations` | 38 / 84 | 60 | 0.688 (38, 6) | 0.356 | 0.265 | 0.649 (25, 6) | 13 (0) | 0 (0) | 16 ok, 12 truncated |
| 3 | Laya | `d6-noul-v3-excerpts` | 3 / 84 | 2 | undefined (3, 0) | undefined | 0.642 | undefined | 0 | not computed (no positive) | 2 ok, 26 truncated |

Row 3, Jev, nested CV over 33 pairs in 11 cases: outer-fold AUC mean 0.456 (sd 0.109, 4 folds with both classes), Brier mean 0.151 (sd 0.097), log loss 0.459 (sd 0.259); intercept-only selected in every outer fold. With no promotion, the false-promotion rate has no denominator.

## Notes on the denominators

- Rows 1 and 2 cover all 60 cases; row 3 on Jev covers the first 11 cases reached before its 25,000 input-token ceiling (the review's estimate for this row), so row 3 is not paired with rows 1 and 2. The excerpt state cost about 2,300 input tokens per call against about 1,200 for v1 slices.
- On Laya, row 2's longer rubric and row 3's excerpt records exceed the model's input window (about 500 tokens, measured) in most calls; truncated calls are voided by the guard, never used.
- With 0 positives among candidate pairs on dev, no variant can show a candidate promotion that is correct; a candidate promotion here could only be false.
