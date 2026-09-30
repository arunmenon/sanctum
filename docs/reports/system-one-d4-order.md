# System One D4: order-sensitive measurement (offline)

> SYNTHETIC, NOT PRODUCTION EVIDENCE. 60 dev + 40 holdout questions support directional results and debugging only, not population estimates.

Computed from saved receipts only, no live calls. Rules order is the packed evidence as returned; D4 order sorts the same packed units by the D4 probability (the only change D4 may make). Coverage@K is over answerable cases (n); first-support rank is over cases with any supporting unit.

| run | order | scored requests | coverage@1000 | coverage@2000 | coverage@4000 | first support rank (mean, n) | answerable without support |
|---|---|---|---|---|---|---|---|
| row8-9-typesafe-jev-d4-noul-v2-support-excerpts | rules | 51 | 0.662 (n=51) | 0.748 (n=51) | 0.784 (n=51) | 1.55 (n=49) | 2 |
| row8-9-typesafe-jev-d4-noul-v2-support-excerpts | d4 | 51 | 0.639 (n=51) | 0.709 (n=51) | 0.784 (n=51) | 1.84 (n=49) | 2 |
| row9r-typesafe-jev-d4-score-v1-excerpts | rules | 22 | 0.662 (n=51) | 0.748 (n=51) | 0.784 (n=51) | 1.55 (n=49) | 2 |
| row9r-typesafe-jev-d4-score-v1-excerpts | d4 | 22 | 0.644 (n=51) | 0.743 (n=51) | 0.784 (n=51) | 1.82 (n=49) | 2 |
| row8-9-laya-local-d4-noul-v1 | rules | 60 | 0.662 (n=51) | 0.748 (n=51) | 0.784 (n=51) | 1.55 (n=49) | 2 |
| row8-9-laya-local-d4-noul-v1 | d4 | 60 | 0.577 (n=51) | 0.765 (n=51) | 0.784 (n=51) | 2.00 (n=49) | 2 |
| row8-9-laya-local-d4-noul-v2-support-compact-150 | rules | 60 | 0.662 (n=51) | 0.748 (n=51) | 0.784 (n=51) | 1.55 (n=49) | 2 |
| row8-9-laya-local-d4-noul-v2-support-compact-150 | d4 | 60 | 0.619 (n=51) | 0.753 (n=51) | 0.784 (n=51) | 1.55 (n=49) | 2 |

## Reading

- All four runs are shadow D4 on build/world (manifest 452b57d9), dev cases, prompt-campaign rows 8-9 (m3-ref). The D4 scores are raw and uncalibrated, and the responses are in rules order. The "d4" rows are therefore the counterfactual order D4's raw scores would impose on the same packed units.
- Jev answered 294 of 361 units with `d4-noul-v2-support` and 116 of 361 with `d4-score-v1` (row ceilings). Unscored units keep their rules order after the scored ones, so those rows only partly reflect D4. Laya answered all 361 units in both of its runs. Two further dirs had no usable answers and are left out: Jev score-v1 first pass (every call 422) and Laya score-v1 (Laya has no score primitive).
- Coverage@4000 is identical in every row, because at this budget the whole packed set fits and reordering cannot change it. That is the review's point that whole-response metrics cannot see D4.
- At K=1000, every D4 order has lower coverage than the rules order (0.577-0.644 against 0.662). The mean first-support rank is the same or worse (1.55-2.00 against 1.55). At K=2000 the Laya orders are slightly above rules (0.753-0.765 against 0.748) and the Jev orders slightly below. On these 51 answerable cases (49 with any supporting unit) the rules order is already good (first support at rank 1.55), which leaves little room. None of these differences is supported as an improvement; the direction is flat to worse.
- These numbers do not include the predeclared budget stress (1000/2000/4000 token budgets, `configs/budget_stress.yaml`). Those runs need live calls and have not been made.

Regenerate with `python tools/d4_order_report.py --run <dir> ... --cases gold/dev`.

> SYNTHETIC, NOT PRODUCTION EVIDENCE. 60 dev + 40 holdout questions support directional results and debugging only, not population estimates.
