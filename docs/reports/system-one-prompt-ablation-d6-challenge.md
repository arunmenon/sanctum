# Prompt campaign, D6 rows 1 to 5 on the challenge world (Laya, shadow)

> SYNTHETIC, NOT PRODUCTION EVIDENCE. **Measured once**, shadow-only, on the challenge overlay only. Numbers only; no conclusion about the model is drawn here.

## Setup

| Item | Value |
|---|---|
| World | `build/world-challenge` (overlay `world/challenge-d6.yaml`), manifest `15304c65481ba2bf`, checked before every call and recorded in every ledger row |
| Cases | `gold/challenge-d6` (12 questions); 11 requests produced D6 questions |
| Pairs judged | 58 per complete row, all candidate pairs (the strict same-subject rule dropped them; up to 6 per request); 0 rule-flagged pairs; 22 positive under the evaluator-side labels |
| Provider | Laya only (`laya-local`, one pair per call). Jev was not run: about 6k input tokens remained under the 800 / 760k / 80k ceiling after row 10, below one row (about 1,200 to 2,200 input tokens per pair) |
| Band check | nested case-grouped CV (`sanctum_eval.calibration.nested_cv`), use band chosen on inner folds at a 0.2 false-promotion tolerance (unchanged), 5 outer folds |
| Data | `docs/reports/data/challenge-c{1..5}-laya-local-*.json` |

## Results (`noul` rows)

| Row | Template (state) | Pairs answered / 58 (pos) | Raw ROC-AUC | Raw PR-AUC (base rate) | Raw Brier | Outer AUC mean (sd) | Outer Brier mean (sd) | Calibrators selected | Use band per outer fold | Promotions (false), Wilson 95% false rate | Calls, input tokens |
|---|---|---|---|---|---|---|---|---|---|---|---|
| c1 | `d6-noul-v1` (v1) | 58 (22) | 0.327 | 0.355 (0.379) | 0.301 | 0.673 (0.143) | 0.230 (0.025) | platt_l2 x5 | 0.50, 0.57, 0.52, 0.53, 0.66 | 3 (2), 0.208 to 0.939 | 58, 17,899 |
| c2 | `d6-noul-v2-relations` (v1) | 58 (22) | 0.774 | 0.722 (0.379) | 0.231 | 0.788 (0.149) | 0.191 (0.039) | platt_l2, intercept_only x2, platt x2 | 0.63, 0.50, 0.79, 0.50, 0.59 | 10 (2), 0.057 to 0.510 | 58, 24,627 |
| c3 | `d6-noul-v3-excerpts-compact-150` | 34 (14) | 0.568 | 0.468 (0.412) | 0.313 | 0.633 (0.300) | 0.257 (0.036) | platt_l2 x4, intercept_only | 1.0, 1.0, 1.0, 0.58, 1.0 | 1 (1), 0.207 to 1.000 | 47 (24 pairs truncated), 22,320 |

## Diagnostic rows (not band-eligible)

| Row | Template | Signal | Pairs (pos) | Raw ROC-AUC | Raw PR-AUC | Raw Brier | Calls, input tokens |
|---|---|---|---|---|---|---|---|
| c4 | `d6-decomp-v1` | same_subject | 58 (22) | 0.801 | 0.750 | 0.206 | 116, 37,074 |
| c4 | `d6-decomp-v1` | values_differ | 58 (22) | 0.607 | 0.543 | 0.289 | (same calls) |
| c4 | `d6-decomp-v1` | product (diagnostic) | 58 (22) | 0.785 | 0.712 | 0.198 | (same calls) |
| c5 | `d6-choice-v1` | 1 - p(no_conflict) | 58 (22) | 0.386 | 0.322 | 0.440 | 58, 23,525 |
| c5 | `d6-choice-v1` | relation type correct on positives | 0 of 22 (Wilson 0.000 to 0.149) | | | | |

## Denominators and notes

- The gold description gives 20 positive pairs, 16 of them exposed as candidates; the tool's labels mark 22 of the 58 judged pairs positive and none rule-flagged. The labelling on the overlay has not been reconciled against the gold count; the numbers above use the tool's labels as they are.
- c3 lost 24 of 58 pairs to Laya input truncation (4 of 11 requests had a truncated answer); those pairs keep the rules-only result and are excluded from its denominators.
- Promotion counts are summed over outer folds; each fold has 6 to 14 pairs, so the per-fold bands rest on few positives.
