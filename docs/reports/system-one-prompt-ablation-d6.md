# D6 prompt ablation, rows 1 to 3 (shadow, dev)

> SYNTHETIC, NOT PRODUCTION EVIDENCE. Every number is **measured once**, shadow-only, on the 60 dev cases (84 rule-produced D6 pairs). No calibration was applied and nothing was promoted. Acceptance and holdout sets were not touched. Plan: the prompt review, docs/reviews/system-one-prompt-review-full.md, rows 1 to 3; rows 4 to 10 wait for the lead.

## Setup

| Item | Value |
|---|---|
| Commit | `94402e2`; raw results in `docs/reports/data/{jev,laya}-d6-noul-v*.json` |
| Tool | `tools/ablate_system_one.py`: shadow collect through the runner and broker, labels from `sanctum_eval.calibration_labels`, campaign ceiling enforced before every HTTP attempt |
| Population | 84 pairs per full run: 62 rule-flagged, 22 promotable candidates (attribute clash, no identity overlap) |
| Labels | 12 positive pairs (a pair covers both witness bundles of a gold relation), **all 12 among the rule-flagged pairs; 0 of the 22 candidates is positive** |
| Band check | nested case-grouped CV (5 outer, 4 inner folds): Platt and the use band are chosen on inner folds of the outer-train cases, and candidate promotions are counted on outer-test cases at the 20% false-promotion tolerance. m3-data's shared nested-CV helper had not landed; this is the tool's own implementation |
| Jev ceilings | 30 calls and 40,000 input tokens per row |

## Results

Raw answers (no calibration). ROC-AUC and PR-AUC are undefined for the candidate stratum, which has no positive pair.

| Row | Provider | Template | Answered / 84 | ROC-AUC all | PR-AUC all | Brier all | ROC-AUC flagged | Brier candidates | Nested-CV candidate promotions (false) | Calls, input tokens |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Jev | `d6-noul-v1` (baseline repeat) | 84 | 0.804 | 0.530 | 0.154 | 0.793 | 0.117 | 0 (0) | 28, 33,107 |
| 2 | Jev | `d6-noul-v2-relations` | 80 | 0.812 | 0.532 | 0.433 | 0.766 | 0.461 | 0 (0) | 25 (3 more refused before dispatch), 39,435 |
| 1 | Laya | `d6-noul-v1` | 84 | 0.271 | 0.101 | 0.289 | 0.282 | 0.323 | 0 (0) | 83, 29,828 |
| 2 | Laya | `d6-noul-v2-relations` | 38 | 0.688 | 0.356 | 0.265 | 0.649 | 0.235 | 0 (0) | 64 (12 truncated), 30,776 |
| 3 | both | `d6-noul-v3-excerpts` | not run | | | | | | | |

Nested-CV bands per outer fold: Jev v1 0.50 to 0.65, Jev v2 0.50 to 0.75 (one fold 1.0), Laya v1 and v2 1.0 in every fold (no band met the tolerance).

## Reading

- **The candidate population holds no positive pair on dev.** All 12 relation-bearing pairs are already rule-flagged, and D6 may only promote candidates. However well a template discriminates, D6 cannot improve any dev metric: the measurement limit the review predicted is confirmed. A D6 benefit needs rule-missed relations in the candidate population, for example the independently authored challenge slice the review proposes.
- **Jev:** the relation-aligned rubric (row 2) leaves discrimination about the same (AUC 0.80 to 0.81 overall, 0.79 to 0.77 on flagged pairs) and moves raw probabilities up across the board (Brier 0.15 to 0.43); that is a calibration shift, not new discrimination. Row 2 hit its 40,000 input-token ceiling: 3 calls (4 pairs) were refused before dispatch, as designed.
- **Laya:** with the baseline rubric its raw answers run against the labels (AUC 0.27, the negative calibration slope seen earlier). The relation-aligned rubric turns that around on the pairs it answered (AUC 0.69), but the longer instructions push 12 of 28 calls past Laya's input window (truncated, voided), so only 38 of 84 pairs were answered. The baseline's inversion looks prompt-related rather than a fixed model property, but the evidence is partial.
- **Row 3** (`d6-noul-v3-excerpts`, labeled assertion-bearing excerpts) needs the broker's excerpt state (m3-data) and was not run.

## Cost

Jev rows 1 and 2: 53 HTTP calls, 72,542 input and 4,383 output tokens, within the review's ceiling for rows 1 to 3 (84 calls, about 95,000 input tokens). Row 3 on Jev would add at most 28 calls and about 22,000 input tokens.
