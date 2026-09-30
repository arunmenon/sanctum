# System One prompt campaign: summary and spend ledger

> SYNTHETIC, NOT PRODUCTION EVIDENCE. Every row was **measured once**, shadow-only unless marked as the live arm, on dev cases, the scenarios set (live arm and budget stress) and the D6 challenge overlay. No acceptance or holdout case was used. Numbers only; no verdict on either model.

Row reports (full setup, denominators and failures): [D6 rows 1-3](system-one-prompt-ablation-d6.md), [D6 rows 4-5](system-one-prompt-ablation-d6-diagnostics.md), [D2 rows 6-7](system-one-prompt-ablation-d2.md), [D4 rows 8-9, budget stress and live arm](system-one-prompt-ablation-d4.md), [row 10 order and context](system-one-prompt-ablation-order-context.md), [D6 challenge](system-one-prompt-ablation-d6-challenge.md).

## D2 (rows 6-7, dev, 204 labelled judgments, 35 positive)

| Provider | Variant | Raw ROC-AUC (n 204, pos 35) | Raw PR-AUC | Raw Brier | Outer AUC mean (sd) | Outer Brier mean (sd) | Calibrators selected (5 folds) | Skip band per outer fold | Skipped / 204 | Harmful skips | Harmful among skipped, Wilson 95% | Calls, input / output tokens |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Jev | `d2-noul-v1` | 0.746 | 0.384 | 0.301 | 0.737 (0.060) | 0.132 (0.028) | source_intercepts x1, intercept_only x4 | 0.09, 0.07, 0.06, 0.06, 0.06 | 58 | 2 | 0.010 to 0.117 | 60, 38,046 / 5,100 |
| Jev | `d2-noul-v2-loss` | 0.760 | 0.395 | 0.181 | 0.746 (0.047) | 0.130 (0.030) | source_intercepts x1, intercept_only x4 | 0.11, 0.07, 0.07, 0.08, 0.07 | 66 | 2 | 0.008 to 0.104 | 60, 58,446 / 5,100 |
| Jev | `d2-descriptors-v2` | 0.746 | 0.374 | 0.226 | 0.758 (0.017) | 0.129 (0.032) | source_intercepts x1, intercept_only x4 | 0.07, 0.06, 0.05, 0.04, 0.05 | 47 | 1 | 0.004 to 0.111 | 60, 36,426 / 5,100 |
| Laya | `d2-noul-v1` | 0.575 | 0.258 | 0.174 | 0.726 (0.062) | 0.136 (0.033) | source_intercepts x5 | 0.04, 0.05, 0.04, 0.04, 0.04 | 21 | 1 | 0.008 to 0.227 | 240, 60,592 / 0 |
| Laya | `d2-noul-v2-loss` | 0.509 | 0.214 | 0.206 | 0.695 (0.071) | 0.137 (0.029) | source_intercepts x5 | 0.10, 0.06, 0.05, 0.08, 0.04 | 39 | 1 | 0.005 to 0.132 | 240, 80,992 / 0 |
| Laya | `d2-descriptors-v2` | 0.680 | 0.309 | 0.147 | 0.737 (0.086) | 0.137 (0.027) | source_intercepts x5 | 0.09, 0.07, 0.05, 0.08, 0.04 | 46 | 1 | 0.004 to 0.113 | 240, 53,872 / 0 |
| none | **control: source prior only** | n/a | n/a | n/a | 0.731 (0.064) | 0.133 (0.029) | source_intercepts x5 | 0.10, 0.08, 0.05, 0.10, 0.05 | 31 | 1 | 0.006 to 0.162 | 0 |

## D4 (rows 8-9, dev, 361 units, 127 positive)

| Provider | Template (state) | Units answered / 361 (cases) | Raw ROC-AUC (n, pos) | Raw PR-AUC | Raw Brier | Outer AUC mean (sd) | Outer Brier mean (sd) | Calibrators selected | Use band per outer fold | Units at or above band (false), Wilson 95% false rate | Calls, input / output tokens |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Jev | `d4-noul-v2-support-excerpts` (v2) | 294 (51) | 0.652 (294, 111) | 0.495 | 0.254 | 0.701 (0.084) | 0.210 (0.018) | source_intercepts x5 | 0.71, 0.74, 0.65, 0.75, 0.80 | 9 (2), 0.063 to 0.547 | 51 ok, 9 refused at row ceiling; 109,092 / 6,423 |
| Jev | control: source prior only (same units) | 294 | n/a | n/a | n/a | 0.631 (0.037) | 0.222 (0.016) | source_intercepts x5 | 1.0 in all folds | 0 | 0 |
| Jev | `d4-score-v1-excerpts` (diagnostic, score / 3) | 116 (22) | 0.412 (116, 51) | 0.412 | n/a | n/a | n/a | n/a | n/a | n/a | 22 ok, 38 refused at row ceiling; 45,081 / 2,192 |
| Jev | `d4-noul-v2-support-excerpts`, completed (8 + 8c) | 361 (60) | 0.680 (361, 127) | 0.494 | 0.244 | 0.697 (0.054) | 0.205 (0.026) | source_intercepts x5 | 0.72, 1.0, 0.83, 0.69, 0.75 | 5 (2), 0.118 to 0.769 | 60 ok; 132,465 / 7,878 |
| Jev | control: source prior only (all 361 units) | 361 | n/a | n/a | n/a | 0.639 (0.061) | 0.224 (0.029) | source_intercepts x5 | 1.0 in all folds | 0 | 0 |
| Jev | `d4-score-v1-excerpts`, completed (9r + 9c) | 361 (60) | 0.673 (361, 127) | 0.479 | n/a | n/a | n/a | n/a | n/a | n/a | 60 ok; 134,631 / 6,795 |
| Laya | `d4-noul-v1` (v1) | 361 (60) | 0.719 (361, 127) | 0.512 | 0.217 | 0.731 (0.059) | 0.198 (0.020) | source_intercepts x5 | 0.76, 0.71, 0.80, 0.80, 0.81 | 2 (0), 0.000 to 0.658 | 361, 70,389 / 0 |
| Laya | `d4-noul-v2-support-compact-150` | 361 (60) | 0.825 (361, 127) | 0.728 | 0.176 | 0.820 (0.048) | 0.159 (0.023) | platt_l2 x2, source_intercepts x3 | 0.59, 0.59, 0.61, 0.64, 0.57 | 88 (20), 0.152 to 0.325 | 361, 105,189 / 0 |
| Laya | control: source prior only | 361 | n/a | n/a | n/a | 0.639 (0.061) | 0.224 (0.029) | source_intercepts x5 | 1.0 in all folds | 0 | 0 |

## D6 on dev (rows 1-3: 84 pairs, 12 positive)

| Row | Provider | Template (state) | Pairs answered / 84 | ROC-AUC all (n, pos) | PR-AUC all | Brier all | ROC-AUC flagged (n, pos) | Candidates answered (pos) | Nested-CV candidate promotions (false) | Calls |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Jev | `d6-noul-v1` (v1) | 84 | 0.804 (84, 12) | 0.530 | 0.154 | 0.793 (62, 12) | 22 (0) | 0 (0), own CV | 28 ok |
| 2 | Jev | `d6-noul-v2-relations` (v1) | 80 | 0.812 (80, 11) | 0.532 | 0.433 | 0.766 (58, 11) | 22 (0) | 0 (0), own CV | 25 ok, 3 refused at row ceiling |
| 3 | Jev | `d6-noul-v3-excerpts` (v2) | 84 | 0.803 (84, 12) | 0.509 | 0.390 | 0.761 (62, 12) | 22 (0) | 0 (0) of 22 eligible | 28 ok |
| 1 | Laya | `d6-noul-v1` (v1) | 84 | 0.271 (84, 12) | 0.101 | 0.289 | 0.282 (62, 12) | 22 (0) | 0 (0), own CV | 28 ok |
| 2 | Laya | `d6-noul-v2-relations` (v1) | 38 | 0.688 (38, 6) | 0.356 | 0.265 | 0.649 (25, 6) | 13 (0) | 0 (0), own CV | 16 ok, 12 truncated |
| 3 | Laya | `d6-noul-v3-excerpts-compact` (compact 350) | 3 | undefined (3, 0) | undefined | 0.649 | undefined | 0 | not computed | 2 ok, 26 truncated |
| 3 | Laya | `d6-noul-v3-excerpts-compact-150` (compact 150) | 36 | 0.869 (36, 3) | 0.335 | 0.331 | 0.745 (20, 3) | 16 (0) | 0 (0) of 16 eligible | 12 ok, 16 truncated |

| Provider | Outer-fold AUC mean (sd, folds) | Outer-fold Brier mean (sd) | Calibrators selected | Use band per outer fold |
|---|---|---|---|---|
| Jev, excerpts | 0.734 (0.302, 5) | 0.110 (0.050) | platt_l2 ×3, platt ×2 | 1.0, 0.5, 0.5, 0.75, 1.0 |
| Laya, compact 150 | 0.583 (0.520, 3) | 0.174 (0.166) | intercept_only ×5 | 1.0 in all 5 |

## D6 diagnostics on dev (rows 4-5)

| Provider | Pairs answered / 84 | Signal | ROC-AUC all (n, pos) | PR-AUC all | Brier all | ROC-AUC flagged (n, pos) | Calls |
|---|---|---|---|---|---|---|---|
| Jev | 83 | same_subject | 0.786 (83, 12) | 0.504 | 0.272 | 0.745 (61, 12) | 27 ok, 1 refused at row ceiling |
| Jev | 83 | values_differ | 0.718 (83, 12) | 0.434 | 0.567 | 0.728 (61, 12) | |
| Jev | 83 | product (diagnostic) | 0.748 (83, 12) | 0.487 | 0.209 | 0.720 (61, 12) | |
| Laya | 84 | same_subject | 0.683 (84, 12) | 0.221 | 0.253 | 0.632 (62, 12) | 168 (28 rounds ok) |
| Laya | 84 | values_differ | 0.286 (84, 12) | 0.120 | 0.375 | 0.297 (62, 12) | |
| Laya | 84 | product (diagnostic) | 0.571 (84, 12) | 0.185 | 0.157 | 0.540 (62, 12) | |

| Provider | Pairs answered / 84 | ROC-AUC of 1 - p(no_conflict) (n, pos) | PR-AUC | Brier | ROC-AUC flagged (n, pos) | Relation type correct on positives (Wilson 95%) | Calls |
|---|---|---|---|---|---|---|---|
| Jev | 69 | 0.793 (69, 12) | 0.381 | 0.430 | 0.783 (58, 12) | 11 of 12 (0.646 to 0.985) | 25 ok, 3 refused at row ceiling |
| Laya | 79 | 0.462 (79, 11) | 0.134 | 0.577 | 0.511 (57, 11) | 7 of 11 (0.354 to 0.848) | 82 (27 rounds ok, 1 truncated) |


## D6 on the challenge world (c1-c5; slice-scope labels, 26 of 58 positive; case scope 22)

| Row | Provider | Template (state) | Items answered / 58 | Raw ROC-AUC, slice (26 pos) | Raw PR-AUC, slice (base 0.448) | Raw Brier, slice | Raw ROC-AUC, case (22 pos) | Outer AUC mean (sd) | Outer Brier mean (sd) | Calibrators selected | Use band per outer fold | Promotions (false), Wilson 95% false rate | Calls, input / output tokens |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| c1 | Jev | `d6-noul-v1` (v1) | 58 | 0.581 | 0.505 | 0.250 | 0.568 | 0.621 (0.199) | 0.256 (0.033) | platt_l2 x2, intercept_only x3 | 1.0, 1.0, 1.0, 1.0, 0.57 | 6 (5), 0.437 to 0.970 | 11, 18,371 / 1,523 |
| c2 | Jev | `d6-noul-v2-relations` (v1) | 58 | 0.521 | 0.513 | 0.358 | 0.521 | 0.554 (0.158) | 0.263 (0.036) | platt_l2 x4, intercept_only | 1.0 in all folds | 0 | 11, 24,461 / 1,523 |
| c3 | Jev | `d6-noul-v3-excerpts` (v2) | 58 | 0.593 | 0.587 | 0.357 | 0.600 | 0.611 (0.070) | 0.249 (0.039) | intercept_only x5 | 1.0, 0.61, 0.57, 0.63, 0.66 | 4 (2), 0.150 to 0.850 | 11, 36,040 / 1,523 |
| c1 | Laya | `d6-noul-v1` (v1) | 58 | 0.335 | 0.406 | 0.307 | 0.327 | 0.622 (0.157) | 0.237 (0.024) | platt, platt_l2 x4 | 0.61, 0.67, 0.57, 0.65, 0.68 | 2 (0), 0.000 to 0.658 | 58, 17,899 / 0 |
| c2 | Laya | `d6-noul-v2-relations` (v1) | 58 | 0.730 | 0.717 | 0.227 | 0.774 | 0.742 (0.194) | 0.208 (0.045) | intercept_only x5 | 0.63, 0.70, 0.68, 0.60, 0.53 | 9 (2), 0.063 to 0.547 | 58, 24,627 / 0 |
| c3 | Laya | `d6-noul-v3-excerpts-compact-150` | 34 (18 pos slice, 14 case) | 0.566 | 0.585 (0.529) | 0.273 | 0.568 | 0.658 (0.317) | 0.279 (0.042) | platt_l2 x4, intercept_only | 0.68, 1.0, 0.72, 1.0, 1.0 | 0 | 47 (24 items truncated), 22,320 / 0 |

| Row | Provider | Template | Signal | Items | Raw ROC-AUC, slice | Raw PR-AUC, slice | Raw Brier, slice | Raw ROC-AUC, case | Calls, input tokens |
|---|---|---|---|---|---|---|---|---|---|
| c4 | Jev | `d6-decomp-v1` | same_subject | 58 | 0.564 | 0.578 | 0.272 | 0.518 | 11, 34,991 / 3,466 out |
| c4 | Jev | `d6-decomp-v1` | values_differ | 58 | 0.638 | 0.617 | 0.383 | 0.559 | (same calls) |
| c4 | Jev | `d6-decomp-v1` | product (diagnostic) | 58 | 0.588 | 0.589 | 0.244 | 0.532 | (same calls) |
| c5 | Jev | `d6-choice-v1` | 1 - p(no_conflict) | 58 | 0.514 | 0.445 | 0.470 | 0.491 | 11, 27,883 / 4,494 out |
| c5 | Jev | `d6-choice-v1` | relation type correct on case-scope positives | 15 of 22 (Wilson 0.473 to 0.836) | | | | | |
| c4 | Laya | `d6-decomp-v1` | same_subject | 58 | 0.776 | 0.755 | 0.206 | 0.801 | 116, 37,074 |
| c4 | Laya | `d6-decomp-v1` | values_differ | 58 | 0.576 | 0.583 | 0.275 | 0.607 | (same calls) |
| c4 | Laya | `d6-decomp-v1` | product (diagnostic) | 58 | 0.757 | 0.743 | 0.224 | 0.786 | (same calls) |
| c5 | Laya | `d6-choice-v1` | 1 - p(no_conflict) | 58 | 0.368 | 0.380 | 0.396 | 0.386 | 58, 23,525 |
| c5 | Laya | `d6-choice-v1` | relation type correct on case-scope positives | 0 of 22 (Wilson 0.000 to 0.149) | | | | | |

## Order, context size, batching (row 10)

| Provider | Comparison | Paired judgments | Mean abs change in p | Max abs change | AUC (first / second) |
|---|---|---|---|---|---|
| Jev | sorted vs identical repeat | 20 | 0.012 | 0.03 | 0.750 / 0.750 |
| Jev | sorted vs reversed order | 20 | 0.015 | 0.04 | 0.750 / 0.750 |
| Jev | short vs longer context | 20 | 0.132 | 0.35 | 0.750 / 0.694 |
| Jev | batched vs single-question calls | 12 | 0.008 | 0.02 | undefined (no positive) |
| Laya | sorted vs identical repeat | 20 | 0.000 | 0.00 | 0.528 / 0.528 |
| Laya | short vs longer context | 20 | 0.108 | 0.41 | 0.528 / 0.861 |

## Budget stress, rules-only order (Laya D4 arm on the strict profile made no calls)

| Arm | Budget | Coverage@1000 | Coverage@2000 | Coverage@4000 | First support rank (mean, median, n) | Answerable without support |
|---|---|---|---|---|---|---|
| C4 | 1000 | 0.63 (72) | 0.63 (72) | 0.63 (72) | 1.13, 1, 63 | 9 |
| C4+D4 | 1000 | 0.63 (72) | 0.63 (72) | 0.63 (72) | 1.13, 1, 63 | 9 |
| C4 | 2000 | 0.66 (72) | 0.76 (72) | 0.76 (72) | 1.24, 1, 66 | 6 |
| C4+D4 | 2000 | 0.66 (72) | 0.76 (72) | 0.76 (72) | 1.24, 1, 66 | 6 |
| C4 | 4000 | 0.66 (72) | 0.74 (72) | 0.78 (72) | 1.44, 1, 68 | 4 |
| C4+D4 | 4000 | 0.66 (72) | 0.74 (72) | 0.78 (72) | 1.44, 1, 68 | 4 |

## Live experiment arm: Laya D4 compact-150, relaxed, calibrated

| Budget | Arm | Safe grounded success | Mean recall | Mean tokens used | Cases with a failed gate | Reorder-only violations | Cases differing from C4 (success / recall) |
|---|---|---|---|---|---|---|---|
| 1000 | C4 | 27 | 0.552 | 743 | 5 | 0 | |
| 1000 | C4+D4 | 27 | 0.552 | 743 | 5 | 0 | 0 / 0 |
| 2000 | C4 | 53 | 0.695 | 1,322 | 5 | 0 | |
| 2000 | C4+D4 | 53 | 0.695 | 1,322 | 5 | 0 | 0 / 0 |
| 4000 | C4 | 57 | 0.719 | 1,773 | 5 | 0 | |
| 4000 | C4+D4 | 57 | 0.719 | 1,773 | 5 | 0 | 0 / 0 |

| Arm | Budget | Coverage@1000 | Coverage@2000 | Coverage@4000 | First support rank (mean, median, n) | Answerable without support |
|---|---|---|---|---|---|---|
| C4 | 1000 | 0.63 (72) | 0.63 (72) | 0.63 (72) | 1.13, 1, 63 | 9 |
| C4+D4 | 1000 | 0.63 (72) | 0.63 (72) | 0.63 (72) | 1.06, 1, 63 | 9 |
| C4 | 2000 | 0.66 (72) | 0.76 (72) | 0.76 (72) | 1.24, 1, 66 | 6 |
| C4+D4 | 2000 | 0.64 (72) | 0.76 (72) | 0.76 (72) | 1.15, 1, 66 | 6 |
| C4 | 4000 | 0.66 (72) | 0.74 (72) | 0.78 (72) | 1.44, 1, 68 | 4 |
| C4+D4 | 4000 | 0.60 (72) | 0.76 (72) | 0.78 (72) | 1.47, 1, 68 | 4 |

## What each result can and cannot say

- **All tables:** measured once. Jev answers vary slightly between runs at the same version (row 10: mean change 0.012 on an identical repeat), and no row was repeated, so differences between rows of similar size are within run-to-run variation not measured here.
- **D2:** can say how each variant's nested-CV skip band compares with the source-prior control on the same 204 judgments. Cannot say anything about holdout or acceptance behavior. For Laya, the control reaches a comparable outer AUC and skip count, so the Laya bands cannot be separated from the per-source prior on this data (owner: no live Laya D2 arm).
- **D4 rows 8-9:** can say how the support rubric ranks 361 dev units against the per-source prior (control: nested AUC 0.639, no band). Jev rows were completed in two parts (same prompt text, different commits; see report). The score row is diagnostic only. Promotion counts are over all answered units and bound what a live arm could add; they are not additions.
- **D6 dev (rows 1-5):** every positive pair on dev is already rule-flagged, so no D6 row there can show a promotion effect; AUC over flagged pairs is reported, promotions are 0 by construction. Laya compact rows cover 3 or 36 of 84 pairs (truncation), so they are not comparable to full rows. The first rows 4-5 ran on a changing world and are recorded as invalid; the reported rows 4-5 are reruns on world 452b57d9.
- **D6 challenge:** 58 items on 12 questions, one overlay world; per-fold bands rest on 6 to 14 items. 4 of the 20 positive pairs are never exposed (candidate cap 6), so no variant can reach them. Slice and case scope differ on 4 repeated pairs; both are shown. Laya c3 covers 34 of 58 items. No source-prior control applies (D6 items carry no source split).
- **Row 10:** 5 cases, 20 judgments with 2 positives; AUC moves in steps of 1/36, so the AUC columns show direction only; the paired probability changes are the measurement.
- **Budget stress (strict):** measures rules-only order at three budgets; the D4 arm made no calls, so it says nothing about D4.
- **Live arm:** dev cases are the calibration set (in-sample); only the 24 scenario cases are out of sample. It can say that the calibrated D4 arm changed order but not the packed set or any scored metric on these 84 cases at these budgets, and that the reorder-only gate never fired. It cannot say how the arm behaves on holdout or acceptance. There is no live source-prior arm; the comparison is to the offline control, which promotes nothing.

## Worlds

- Dev rows: frozen `build/world`, manifest `452b57d9`, checked before any call and recorded per ledger row. The world changed while the first rows 4-5 ran (another agent's rebuild); those runs are invalid and their spend stays in the ledger.
- Challenge rows: `build/world-challenge`, manifest `15304c65481ba2bf`.

## Failures charged to the ledger

- Jev row 3 first ran at a 25k row ceiling and stopped at 33 of 84 pairs; rerun as 3r.
- The first Jev D4 score pass (row 9) returned HTTP 422 on all 51 calls (score criteria sent as a mapping), charged at input reservations; rerun as 9r and completed as 9c.
- The first row 8c attempt made no call (provider environment not exported); zero-spend row kept.
- Laya does not offer the `score` primitive; row 9 on Laya was refused with no call.

## Ceiling history (Jev; enforced before dispatch, never exceeded)

- 470/420000/45000
- 600/560000/60000
- 800/760000/80000 (owner, before rows 6-10 and the D6 challenge rows)
- 1000/950000/100000 (owner: completing paired Jev D4 rows and running the Jev D6 challenge rows)
- 1100/1030000/110000 (owner: Jev diagnostics c4-c5 on the challenge slice so its near-chance result is interpretable)

Jev spend against the current ceiling: 631 of 1,100 calls, 1,008,710 of 1,030,000 input tokens, 70,382 of 110,000 output tokens. Laya is local and uncapped; its calibration fit (361 calls, 105,189 input tokens) and the live-arm grid (1,638 D4 calls) ran outside the ledger's ablation rows.

## Spend ledger

| Row | Provider | Template | World manifest | Calls | Input tokens | Output tokens | Note |
|---|---|---|---|---|---|---|---|
| 1 | typesafe-jev | `d6-noul-v1` | 452b57d9 | 28 | 33,107 | 2,248 |  |
| 2 | typesafe-jev | `d6-noul-v2-relations` | 452b57d9 | 25 | 39,435 | 2,135 |  |
| 1 | laya-local | `d6-noul-v1` | 452b57d9 | 83 | 29,828 | 0 |  |
| 2 | laya-local | `d6-noul-v2-relations` | 452b57d9 | 64 | 30,776 | 0 |  |
| 3 | typesafe-jev | `d6-noul-v3-excerpts` | 452b57d9 | 11 | 25,035 | 876 |  |
| 3 | laya-local | `d6-noul-v3-excerpts` | 452b57d9 | 32 | 16,216 | 0 |  |
| 4 | typesafe-jev | `d6-decomp-v1` | 9f813169 (invalid) | 26 | 49,522 | 3,874 | world build changed mid-campaign; results not comparable with rows 1-3 |
| 5 | typesafe-jev | `d6-choice-v1` | 9f813169 (invalid) | 22 | 31,733 | 4,159 | world build changed mid-campaign; results not comparable with rows 1-3 |
| 4 | laya-local | `d6-decomp-v1` | 9f813169 (invalid) | 194 | 75,016 | 0 | world build changed mid-campaign; results not comparable with rows 1-3 |
| 5 | laya-local | `d6-choice-v1` | 9f813169 (invalid) | 91 | 42,055 | 0 | world build changed mid-campaign; results not comparable with rows 1-3 |
| 3r | typesafe-jev | `d6-noul-v3-excerpts` | 452b57d9 | 28 | 60,825 | 2,248 |  |
| 3r | laya-local | `d6-noul-v3-excerpts-compact` | 452b57d9 | 32 | 16,214 | 0 |  |
| 3r | laya-local | `d6-noul-v3-excerpts-compact-150` | 452b57d9 | 57 | 27,541 | 0 |  |
| 4 | typesafe-jev | `d6-decomp-v1` | 9f813169 (invalid) | 27 | 59,446 | 4,992 |  |
| 5 | typesafe-jev | `d6-choice-v1` | 9f813169 (invalid) | 25 | 39,791 | 5,357 |  |
| 4 | laya-local | `d6-decomp-v1` | 9f813169 (invalid) | 168 | 60,780 | 0 |  |
| 5 | laya-local | `d6-choice-v1` | 9f813169 (invalid) | 82 | 36,663 | 0 |  |
| 6-7 | laya-local | `d2-noul-v1` | 452b57d9 | 0 | 0 | 0 |  |
| 6-7 | laya-local | `d2-noul-v2-loss` | 452b57d9 | 0 | 0 | 0 |  |
| 6-7 | laya-local | `d2-descriptors-v2` | 452b57d9 | 0 | 0 | 0 |  |
| 6-7 | laya-local | `d2-noul-v1` | 452b57d9 | 240 | 60,592 | 0 |  |
| 6-7 | laya-local | `d2-noul-v2-loss` | 452b57d9 | 240 | 80,992 | 0 |  |
| 6-7 | laya-local | `d2-descriptors-v2` | 452b57d9 | 240 | 53,872 | 0 |  |
| 6-7 | typesafe-jev | `d2-noul-v1` | 452b57d9686b9582 | 60 | 38,046 | 5,100 |  |
| 6-7 | typesafe-jev | `d2-noul-v2-loss` | 452b57d9686b9582 | 60 | 58,446 | 5,100 |  |
| 6-7 | typesafe-jev | `d2-descriptors-v2` | 452b57d9686b9582 | 60 | 36,426 | 5,100 |  |
| 6-7 | laya-local | `d2-noul-v1` | 452b57d9686b9582 | 240 | 60,592 | 0 |  |
| 6-7 | laya-local | `d2-noul-v2-loss` | 452b57d9686b9582 | 240 | 80,992 | 0 |  |
| 6-7 | laya-local | `d2-descriptors-v2` | 452b57d9686b9582 | 240 | 53,872 | 0 |  |
| 8-9 | typesafe-jev | `d4-noul-v2-support-excerpts` | 452b57d9686b9582 | 51 | 109,092 | 6,423 |  |
| 8-9 | typesafe-jev | `d4-score-v1-excerpts` | 452b57d9686b9582 | 51 | 109,303 | 0 |  |
| 8-9 | laya-local | `d4-noul-v1` | 452b57d9686b9582 | 361 | 70,389 | 0 |  |
| 8-9 | laya-local | `d4-noul-v2-support-compact-150` | 452b57d9686b9582 | 361 | 105,189 | 0 |  |
| 8-9 | laya-local | `d4-score-v1-compact-150` | 452b57d9686b9582 | 0 | 0 | 0 |  |
| 8-9 probe | typesafe-jev | `d4-score-v1-excerpts` | n/a | 1 | 150 | 0 | one probe call: provider returned 422 (score criteria must be a list) |
| 9r | typesafe-jev | `d4-score-v1-excerpts` | 452b57d9686b9582 | 22 | 45,081 | 2,192 |  |
| 10 | typesafe-jev | `d2-noul-v1 (order/context/repeat)` | n/a (direct D2 state) | 32 | 18,603 | 1,991 |  |
| 10 | laya-local | `d2-noul-v1 (order/context/repeat)` | n/a (direct D2 state) | 60 | 14,647 | 0 |  |
| c1 | laya-local | `d6-noul-v1` | 15304c65481ba2bf | 58 | 17,899 | 0 |  |
| c2 | laya-local | `d6-noul-v2-relations` | 15304c65481ba2bf | 58 | 24,627 | 0 |  |
| c3 | laya-local | `d6-noul-v3-excerpts-compact-150` | 15304c65481ba2bf | 47 | 22,320 | 0 |  |
| c4 | laya-local | `d6-decomp-v1` | 15304c65481ba2bf | 116 | 37,074 | 0 |  |
| c5 | laya-local | `d6-choice-v1` | 15304c65481ba2bf | 58 | 23,525 | 0 |  |
| 8c | typesafe-jev | `d4-noul-v2-support-excerpts` | 452b57d9686b9582 | 0 | 0 | 0 |  |
| 8c | typesafe-jev | `d4-noul-v2-support-excerpts` | 452b57d9686b9582 | 9 | 23,373 | 1,455 |  |
| 9c | typesafe-jev | `d4-score-v1-excerpts` | 452b57d9686b9582 | 38 | 89,550 | 4,603 |  |
| c1 | typesafe-jev | `d6-noul-v1` | 15304c65481ba2bf | 11 | 18,371 | 1,523 |  |
| c2 | typesafe-jev | `d6-noul-v2-relations` | 15304c65481ba2bf | 11 | 24,461 | 1,523 |  |
| c3 | typesafe-jev | `d6-noul-v3-excerpts` | 15304c65481ba2bf | 11 | 36,040 | 1,523 |  |
| c4 | typesafe-jev | `d6-decomp-v1` | 15304c65481ba2bf | 11 | 34,991 | 3,466 |  |
| c5 | typesafe-jev | `d6-choice-v1` | 15304c65481ba2bf | 11 | 27,883 | 4,494 |  |
| total | typesafe-jev | | | 631 | 1,008,710 | 70,382 | |
| total | laya-local | | | 3362 | 1,041,671 | 0 | |
