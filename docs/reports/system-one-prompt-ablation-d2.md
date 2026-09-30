# Prompt campaign, rows 6 and 7: D2 evidence-loss rubric and descriptors v2 (shadow, dev)

> SYNTHETIC, NOT PRODUCTION EVIDENCE. **Measured once**, shadow-only, dev cases only. Numbers only; no conclusion about either model is drawn here.

## Setup

| Item | Value |
|---|---|
| Commit | tool at `c472d38` and later; ledger rows carry the commit and world manifest |
| World | `build/world`, manifest `452b57d9` (checked before every call) |
| Population | 60 dev cases x 4 released sources = 240 judgments; 204 labelled (51 cases with a defined recall), 35 positive |
| Labels | counterfactual, evaluator side: a source is positive for a case when removing its manifest lowers the case's recall (C1-fair runs, local) |
| Variants | `d2-noul-v1` (baseline, rerun at the same commit), row 6 `d2-noul-v2-loss` (evidence-loss rubric), row 7 `d2-descriptors-v2` (baseline rubric, descriptors v2) |
| Band check | nested case-grouped CV (`sanctum_eval.calibration.nested_cv`; calibrators platt, platt_l2, intercept_only, source_intercepts); skip band chosen on inner folds so that harmful skips stay within 0.05 of the positives (unchanged tolerance), evaluated on 5 outer folds |
| Control | source prior only: the same nested CV with every raw p = 0.5, so only per-source intercepts separate judgments; no provider call |
| Batching | Jev: one call per case (4 questions); Laya: one question per call |

## Results

| Provider | Variant | Raw ROC-AUC (n 204, pos 35) | Raw PR-AUC | Raw Brier | Outer AUC mean (sd) | Outer Brier mean (sd) | Calibrators selected (5 folds) | Skip band per outer fold | Skipped / 204 | Harmful skips | Harmful among skipped, Wilson 95% | Calls, input / output tokens |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Jev | `d2-noul-v1` | 0.746 | 0.384 | 0.301 | 0.737 (0.060) | 0.132 (0.028) | source_intercepts x1, intercept_only x4 | 0.09, 0.07, 0.06, 0.06, 0.06 | 58 | 2 | 0.010 to 0.117 | 60, 38,046 / 5,100 |
| Jev | `d2-noul-v2-loss` | 0.760 | 0.395 | 0.181 | 0.746 (0.047) | 0.130 (0.030) | source_intercepts x1, intercept_only x4 | 0.11, 0.07, 0.07, 0.08, 0.07 | 66 | 2 | 0.008 to 0.104 | 60, 58,446 / 5,100 |
| Jev | `d2-descriptors-v2` | 0.746 | 0.374 | 0.226 | 0.758 (0.017) | 0.129 (0.032) | source_intercepts x1, intercept_only x4 | 0.07, 0.06, 0.05, 0.04, 0.05 | 47 | 1 | 0.004 to 0.111 | 60, 36,426 / 5,100 |
| Laya | `d2-noul-v1` | 0.575 | 0.258 | 0.174 | 0.726 (0.062) | 0.136 (0.033) | source_intercepts x5 | 0.04, 0.05, 0.04, 0.04, 0.04 | 21 | 1 | 0.008 to 0.227 | 240, 60,592 / 0 |
| Laya | `d2-noul-v2-loss` | 0.509 | 0.214 | 0.206 | 0.695 (0.071) | 0.137 (0.029) | source_intercepts x5 | 0.10, 0.06, 0.05, 0.08, 0.04 | 39 | 1 | 0.005 to 0.132 | 240, 80,992 / 0 |
| Laya | `d2-descriptors-v2` | 0.680 | 0.309 | 0.147 | 0.737 (0.086) | 0.137 (0.027) | source_intercepts x5 | 0.09, 0.07, 0.05, 0.08, 0.04 | 46 | 1 | 0.004 to 0.113 | 240, 53,872 / 0 |
| none | **control: source prior only** | n/a | n/a | n/a | 0.731 (0.064) | 0.133 (0.029) | source_intercepts x5 | 0.10, 0.08, 0.05, 0.10, 0.05 | 31 | 1 | 0.006 to 0.162 | 0 |

The skip-band criterion is measured against the positives (harmful skips at most 0.05 x 35); the Wilson interval is the harmful-skip rate among the skipped judgments.

## Observations

- Live-arm decision (owner): no live Laya D2 arm. The source-prior-only control reaches an outer AUC and skip count comparable to the Laya variants (0.731 and 31 skips, against 0.695 to 0.737 and 21 to 46), so on this data the Laya band tracks the per-source prior.
- On Jev, the nested CV selected `intercept_only` in 4 of 5 outer folds for every variant; all three Jev variants skip more judgments than the control (47 to 66, against 31) with 1 to 2 harmful skips.
