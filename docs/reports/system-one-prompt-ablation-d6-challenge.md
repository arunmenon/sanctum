# Prompt campaign, D6 rows on the challenge world (shadow)

> SYNTHETIC, NOT PRODUCTION EVIDENCE. **Measured once**, shadow-only, on the challenge overlay only. Numbers only; no conclusion about either model is drawn here.

## Setup

| Item | Value |
|---|---|
| World | `build/world-challenge` (overlay `world/challenge-d6.yaml`), manifest `15304c65481ba2bf`, checked before every call and recorded in every ledger row |
| Cases | `gold/challenge-d6` (12 questions); 11 requests produced D6 questions |
| Items | 58 judged (case, pair) items per complete row, all candidate pairs (the strict same-subject rule dropped them; up to 6 per request); 0 rule-flagged |
| Labels (owner ruling) | primary: slice scope, a pair is positive when it witnesses any relation in the slice (26 of 58 positive). Secondary: case scope, positive only for a relation of that case's gold (22 of 58). 16 of the slice's 20 distinct positive pairs are exposed as candidates (m3-data, `8ff0127`) |
| Band check | nested case-grouped CV (`sanctum_eval.calibration.nested_cv`), use band chosen on inner folds at a 0.2 false-promotion tolerance (unchanged), 5 outer folds, slice-scope labels |
| Laya | all 5 rows; relabelled offline to slice scope from the kept run dirs (no new calls) |
| Jev | all 5 rows; c4 and c5 ran after the owner raised the ceiling to 1,100 / 1,030k / 110k |
| Data | `docs/reports/data/challenge-c*-{laya-local,typesafe-jev}-*.json`; each item carries `label` (slice) and `label_case` |

## Results (`noul` rows)

| Row | Provider | Template (state) | Items answered / 58 | Raw ROC-AUC, slice (26 pos) | Raw PR-AUC, slice (base 0.448) | Raw Brier, slice | Raw ROC-AUC, case (22 pos) | Outer AUC mean (sd) | Outer Brier mean (sd) | Calibrators selected | Use band per outer fold | Promotions (false), Wilson 95% false rate | Calls, input / output tokens |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| c1 | Jev | `d6-noul-v1` (v1) | 58 | 0.581 | 0.505 | 0.250 | 0.568 | 0.621 (0.199) | 0.256 (0.033) | platt_l2 x2, intercept_only x3 | 1.0, 1.0, 1.0, 1.0, 0.57 | 6 (5), 0.437 to 0.970 | 11, 18,371 / 1,523 |
| c2 | Jev | `d6-noul-v2-relations` (v1) | 58 | 0.521 | 0.513 | 0.358 | 0.521 | 0.554 (0.158) | 0.263 (0.036) | platt_l2 x4, intercept_only | 1.0 in all folds | 0 | 11, 24,461 / 1,523 |
| c3 | Jev | `d6-noul-v3-excerpts` (v2) | 58 | 0.593 | 0.587 | 0.357 | 0.600 | 0.611 (0.070) | 0.249 (0.039) | intercept_only x5 | 1.0, 0.61, 0.57, 0.63, 0.66 | 4 (2), 0.150 to 0.850 | 11, 36,040 / 1,523 |
| c1 | Laya | `d6-noul-v1` (v1) | 58 | 0.335 | 0.406 | 0.307 | 0.327 | 0.622 (0.157) | 0.237 (0.024) | platt, platt_l2 x4 | 0.61, 0.67, 0.57, 0.65, 0.68 | 2 (0), 0.000 to 0.658 | 58, 17,899 / 0 |
| c2 | Laya | `d6-noul-v2-relations` (v1) | 58 | 0.730 | 0.717 | 0.227 | 0.774 | 0.742 (0.194) | 0.208 (0.045) | intercept_only x5 | 0.63, 0.70, 0.68, 0.60, 0.53 | 9 (2), 0.063 to 0.547 | 58, 24,627 / 0 |
| c3 | Laya | `d6-noul-v3-excerpts-compact-150` | 34 (18 pos slice, 14 case) | 0.566 | 0.585 (0.529) | 0.273 | 0.568 | 0.658 (0.317) | 0.279 (0.042) | platt_l2 x4, intercept_only | 0.68, 1.0, 0.72, 1.0, 1.0 | 0 | 47 (24 items truncated), 22,320 / 0 |

## Diagnostic rows (not band-eligible)

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

## Denominators and notes

- The 58 items include pairs judged in two cases; 4 repeated pairs change label between cases under case scope and not under slice scope (m3-data, `8ff0127`).
- Limit (owner decision): `MAX_CANDIDATE_PAIRS` stays at 6 and the SUT is not tuned to this slice, so 4 of the 20 distinct positive pairs are never exposed as candidates and cannot be promoted by any variant.
- Laya c3 lost 24 of 58 items to input truncation; those items keep the rules-only result and are excluded from its denominators.
- Promotion counts are summed over outer folds of 6 to 14 items each, so the per-fold bands rest on few positives.
- The Laya nested-CV columns were recomputed under slice scope; the case-scope nested CV is kept in each file as `nested_cv_case_scope`.
