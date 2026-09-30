# Prompt campaign, rows 4 and 5: D6 diagnostics (shadow, dev)

> SYNTHETIC, NOT PRODUCTION EVIDENCE. **Measured once**, shadow-only, dev cases only. Diagnostic templates are never calibrated into bands and never change routing or assembly. Numbers only; no conclusion about either model is drawn here.

## Setup

| Item | Value |
|---|---|
| Commit | `fd19e4f`; world manifest `452b57d9` (frozen rebuild, as rows 1-3) |
| Population and labels | as rows 1-3: 84 pairs (62 rule-flagged, 22 candidates), 12 positive, all rule-flagged |
| Row 4 | `d6-decomp-v1`: two `noul` questions per pair, `same_subject` and `values_differ`; the product is reported as a diagnostic only (the questions are dependent, so it is not a probability of the conjunction) |
| Row 5 | `d6-choice-v1`: relation choice with `no_conflict`; the signal is 1 - p(no_conflict); relation-type accuracy is over positive pairs with an evaluator-side relation type (`relation_types_from_run`) |
| State | v1 text slices; Laya one item per call |
| Jev row ceilings | row 4: 56 calls, 60,000 input tokens; row 5: 28 calls, 40,000 input tokens |

## Row 4: decomposition

| Provider | Pairs answered / 84 | Signal | ROC-AUC all (n, pos) | PR-AUC all | Brier all | ROC-AUC flagged (n, pos) | Calls |
|---|---|---|---|---|---|---|---|
| Jev | 83 | same_subject | 0.786 (83, 12) | 0.504 | 0.272 | 0.745 (61, 12) | 27 ok, 1 refused at row ceiling |
| Jev | 83 | values_differ | 0.718 (83, 12) | 0.434 | 0.567 | 0.728 (61, 12) | |
| Jev | 83 | product (diagnostic) | 0.748 (83, 12) | 0.487 | 0.209 | 0.720 (61, 12) | |
| Laya | 84 | same_subject | 0.683 (84, 12) | 0.221 | 0.253 | 0.632 (62, 12) | 168 (28 rounds ok) |
| Laya | 84 | values_differ | 0.286 (84, 12) | 0.120 | 0.375 | 0.297 (62, 12) | |
| Laya | 84 | product (diagnostic) | 0.571 (84, 12) | 0.185 | 0.157 | 0.540 (62, 12) | |

## Row 5: relation choice

| Provider | Pairs answered / 84 | ROC-AUC of 1 - p(no_conflict) (n, pos) | PR-AUC | Brier | ROC-AUC flagged (n, pos) | Relation type correct on positives (Wilson 95%) | Calls |
|---|---|---|---|---|---|---|---|
| Jev | 69 | 0.793 (69, 12) | 0.381 | 0.430 | 0.783 (58, 12) | 11 of 12 (0.646 to 0.985) | 25 ok, 3 refused at row ceiling |
| Laya | 79 | 0.462 (79, 11) | 0.134 | 0.577 | 0.511 (57, 11) | 7 of 11 (0.354 to 0.848) | 82 (27 rounds ok, 1 truncated) |

Candidate pairs (0 positive) are answered in every row; their AUC is undefined. Relation-type accuracy uses the forced precedence of the template (version, then environment, then policy/implementation, then contradiction); real pairs may carry more than one relation.
