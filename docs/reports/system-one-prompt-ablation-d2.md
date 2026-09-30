# Prompt campaign, rows 6 and 7: D2 evidence-loss rubric and descriptors v2 (shadow, dev)

> SYNTHETIC, NOT PRODUCTION EVIDENCE. **Measured once**, shadow-only, dev cases only. Numbers only; no conclusion about either model is drawn here. Laya part complete; the Jev part waits for the owner's decision on the remaining campaign ceiling.

## Setup

| Item | Value |
|---|---|
| Commit | `0609375` (tool with one call per source for one-question providers); world manifest `452b57d9` (frozen rebuild) |
| Population | 60 dev cases x 4 released sources = 240 judgments; 204 labelled (51 cases with a defined recall), 35 positive |
| Labels | counterfactual, evaluator side: a source is positive for a case when removing its manifest lowers the case's recall (C1-fair runs, local) |
| Variants | `d2-noul-v1` (baseline), `d2-noul-v2-loss` (evidence-loss rubric), `d2-descriptors-v2` (baseline rubric, descriptors v2 from `configs/d2_descriptors_v2.yaml`) |
| Band check | nested case-grouped CV (`sanctum_eval.calibration.nested_cv`, calibrators platt, platt_l2, intercept_only, source_intercepts); skip band chosen on inner folds so that harmful skips stay within 0.05 of the positives (unchanged tolerance), evaluated on 5 outer folds |
| Control | "source prior only": the same nested CV with every raw p set to 0.5, so only the per-source intercepts can separate judgments (no provider call) |

## Results (Laya, one question per call)

| Variant | Answered / labelled | Raw ROC-AUC (n, pos) | Raw PR-AUC | Raw Brier | Outer AUC mean (sd) | Outer Brier mean (sd) | Calibrator selected | Skip band per outer fold | Skipped / 204 | Harmful skips (of 35 positives) | Harmful-skip rate among skipped, Wilson 95% | Calls, input tokens |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `d2-noul-v1` | 240 / 204 | 0.575 (204, 35) | 0.258 | 0.174 | 0.726 (0.062) | 0.136 (0.033) | source_intercepts x5 | 0.04, 0.05, 0.04, 0.04, 0.04 | 21 | 1 | 0.008 to 0.227 | 240, 60,592 |
| `d2-noul-v2-loss` | 240 / 204 | 0.509 (204, 35) | 0.214 | 0.206 | 0.695 (0.071) | 0.137 (0.029) | source_intercepts x5 | 0.10, 0.06, 0.05, 0.08, 0.04 | 39 | 1 | 0.005 to 0.132 | 240, 80,992 |
| `d2-descriptors-v2` | 240 / 204 | 0.680 (204, 35) | 0.309 | 0.147 | 0.737 (0.086) | 0.137 (0.027) | source_intercepts x5 | 0.09, 0.07, 0.05, 0.08, 0.04 | 46 | 1 | 0.004 to 0.113 | 240, 53,872 |
| Control: source prior only | n/a / 204 | n/a | n/a | n/a | 0.731 (0.064) | 0.133 (0.029) | source_intercepts x5 | 0.10, 0.08, 0.05, 0.10, 0.05 | 31 | 1 | 0.006 to 0.162 | 0 |

The skip-band criterion is measured against the positives (harmful skips at most 0.05 x positives); the Wilson interval above is the harmful-skip rate among the skipped judgments, reported for the denominator's uncertainty.

## Jev

Not run yet: the remaining Jev ceiling (about 81k input tokens) does not cover rows 6 to 10 at the review's estimates (about 197k). Waiting for the owner's allocation.
