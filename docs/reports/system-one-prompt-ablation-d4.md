# Prompt campaign, rows 8 and 9: D4 support rubric on excerpts and D4 score diagnostic (shadow, dev)

> SYNTHETIC, NOT PRODUCTION EVIDENCE. **Measured once**, shadow-only, dev cases only; no D4 calibration is live, so every response stayed in rules order. Numbers only; no conclusion about either model is drawn here.

## Setup

| Item | Value |
|---|---|
| Commit | `eb2df1c` / `1efea21` (score criteria as a list); world `452b57d9`, checked before every call |
| Population | 60 dev cases; up to 20 units per request (`d4_max_units`), 361 units per complete run, 127 positive |
| Labels | evaluator side: a unit is positive when its span overlaps a necessary-evidence span (ruling: overlap) |
| Row 8 | `d4-noul-v2-support-excerpts` (Jev, `r3-state-v2`); `d4-noul-v2-support-compact-150` (Laya, `r3-state-v2-compact-150`); Laya baseline `d4-noul-v1` (v1 slices) at the same commit |
| Row 9 | `d4-score-v1-excerpts` (Jev), diagnostic; Laya does not offer the `score` primitive (refused, no call) |
| Band check | nested case-grouped CV (`sanctum_eval.calibration.nested_cv`, calibrators platt, platt_l2, intercept_only, source_intercepts); use band chosen on inner folds with at most 0.2 false promotions (unchanged tolerance). Counts below are over **all** answered units at or above the band; in a run, D4 may only add units the rules excluded, so this is an upper bound on what a live arm could add |
| Control | source prior only: the same nested CV with every raw p = 0.5 (per-source intercepts only); no provider call |
| Order metrics | the offline receipt-prefix report (m3-data, `docs/reports/system-one-d4-order.md`) uses these run directories |

## Results

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

## Denominators and failures

- Completion (owner, ceiling 1000 / 950k / 100k): the cases Jev did not reach in rows 8 and 9r were run on their own (rows 8c: 9 cases, 9c: 38 cases) on the same world, and the items merged (no overlap), so both Jev rows now cover all 361 units in 60 cases, paired with the Laya rows. The prompt text is identical across parts: between the parts' commits the only template change is the score-criteria list format, which 9r already used. Merged data: `docs/reports/data/row8-complete-*.json`, `row9-complete-*.json`.
- The first 8c attempt made no call (provider environment not exported to the runner; all 9 requests `not_configured`); its zero-spend ledger row is kept.

- The first Jev score pass returned HTTP 422 for all 51 calls (score criteria sent as a mapping; the hosted protocol takes a list). The ledger charges those exchanges at their input reservations (109,303 tokens), since no usage was reported. A one-call probe identified the format; the rerun (row 9r) sent criteria as an ordered list and was answered, within the remaining ceiling (116 of 361 units, 22 cases).
- Jev row 8 stopped at its row ceiling (110,000 input tokens) after 51 of 60 requests; the `r3-state-v2` excerpts cost about 2,140 input tokens per D4 call.
- Budget stress (`configs/budget_stress.yaml`) was run on Laya only; the Jev ceiling did not allow it (about 6k input tokens remained after row 10).

## Budget stress (Laya, `tools/run_budget_stress.py`)

Cases: `gold/dev` plus `gold/scenarios` (84 cases, 72 answerable); no holdout or acceptance case was used (the tool's banner text mentions holdout generically). No D4 calibration was live, and the tool did not pass a System One profile, so the D4 arm ran on the strict profile (150 ms, 1 call): every D4 round was over budget with no call, and its receipts equal C4. This table therefore measures the rules-only order only; the live arm below is the D4 measurement.

| Arm | Budget | Coverage@1000 | Coverage@2000 | Coverage@4000 | First support rank (mean, median, n) | Answerable without support |
|---|---|---|---|---|---|---|
| C4 | 1000 | 0.63 (72) | 0.63 (72) | 0.63 (72) | 1.13, 1, 63 | 9 |
| C4+D4 | 1000 | 0.63 (72) | 0.63 (72) | 0.63 (72) | 1.13, 1, 63 | 9 |
| C4 | 2000 | 0.66 (72) | 0.76 (72) | 0.76 (72) | 1.24, 1, 66 | 6 |
| C4+D4 | 2000 | 0.66 (72) | 0.76 (72) | 0.76 (72) | 1.24, 1, 66 | 6 |
| C4 | 4000 | 0.66 (72) | 0.74 (72) | 0.78 (72) | 1.44, 1, 68 | 4 |
| C4+D4 | 4000 | 0.66 (72) | 0.74 (72) | 0.78 (72) | 1.44, 1, 68 | 4 |

## Live experiment arm: Laya D4 `d4-noul-v2-support-compact-150` (owner-approved)

| Item | Value |
|---|---|
| Calibration | `configs/calibration/laya-local@laya-rl-agent.d4.yaml`, fitted on dev (361 units, 361 calls, 105,189 input tokens): Platt a 1.397, b -0.672, use band 0.59, held-out Brier 0.158 (raw 0.176), ECE 0.066 (raw 0.158). Binding: laya-local, laya-rl-agent, revision 55cf4c4e, template `d4-noul-v2-support-compact-150`, layout `r3-state-v2-compact-150` (test `tests/test_d4_live_arm_binding.py`; one-case preflight: 3 of 3 D4 decisions calibrated, none shadow) |
| Arm | template override `laya-local: d4 -> d4-noul-v2-support-compact-150` set for the grid only and reverted after; relaxed profile; reorder-only gate active |
| Grid | `tools/run_budget_stress.py --provider laya-local --system-one-profile relaxed`; budgets 1,000 / 2,000 / 4,000; `gold/dev` plus `gold/scenarios` (84 cases, 72 answerable). Dev cases are the calibration set (in-sample); the 24 scenario cases are not |
| Control | no live source-prior arm exists; the offline source-prior control on the same 361 dev units selects band 1.0 in every fold and promotes nothing (row 8 table) |

Scored (all 84 cases, per budget; identical at every budget between arms):

| Budget | Arm | Safe grounded success | Mean recall | Mean tokens used | Cases with a failed gate | Reorder-only violations | Cases differing from C4 (success / recall) |
|---|---|---|---|---|---|---|---|
| 1000 | C4 | 27 | 0.552 | 743 | 5 | 0 | |
| 1000 | C4+D4 | 27 | 0.552 | 743 | 5 | 0 | 0 / 0 |
| 2000 | C4 | 53 | 0.695 | 1,322 | 5 | 0 | |
| 2000 | C4+D4 | 53 | 0.695 | 1,322 | 5 | 0 | 0 / 0 |
| 4000 | C4 | 57 | 0.719 | 1,773 | 5 | 0 | |
| 4000 | C4+D4 | 57 | 0.719 | 1,773 | 5 | 0 | 0 / 0 |

Order (offline receipt-prefix metrics on the live runs):

| Arm | Budget | Coverage@1000 | Coverage@2000 | Coverage@4000 | First support rank (mean, median, n) | Answerable without support |
|---|---|---|---|---|---|---|
| C4 | 1000 | 0.63 (72) | 0.63 (72) | 0.63 (72) | 1.13, 1, 63 | 9 |
| C4+D4 | 1000 | 0.63 (72) | 0.63 (72) | 0.63 (72) | 1.06, 1, 63 | 9 |
| C4 | 2000 | 0.66 (72) | 0.76 (72) | 0.76 (72) | 1.24, 1, 66 | 6 |
| C4+D4 | 2000 | 0.64 (72) | 0.76 (72) | 0.76 (72) | 1.15, 1, 66 | 6 |
| C4 | 4000 | 0.66 (72) | 0.74 (72) | 0.78 (72) | 1.44, 1, 68 | 4 |
| C4+D4 | 4000 | 0.60 (72) | 0.76 (72) | 0.78 (72) | 1.47, 1, 68 | 4 |

Per budget, 546 D4 judgments were calibrated (0 shadow), 146 of them at or above the use band, over 546 Laya calls. Mean tokens used are identical between arms at every budget, so no unit was added; D4 changed order only. Data: `docs/reports/data/live-arm-laya-d4-budget-stress.md`.
