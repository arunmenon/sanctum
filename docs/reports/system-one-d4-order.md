# System One D4: order-sensitive measurement (offline)

> SYNTHETIC, NOT PRODUCTION EVIDENCE. 60 dev + 40 holdout questions support directional results and debugging only, not population estimates.

Computed from saved receipts only, no live calls. Rules order is the packed evidence as returned; D4 order sorts the same packed units by the D4 probability (the only change D4 may make). Coverage@K is over answerable cases (n); first-support rank is over cases with any supporting unit.

| run | order | scored requests (units) | coverage@1000 | coverage@2000 | coverage@4000 | first support rank (mean, n) | answerable without support |
|---|---|---|---|---|---|---|---|
| row8-9-typesafe-jev-d4-noul-v2-support-excerpts+completion | rules | 60 (361) | 0.662 (n=51) | 0.748 (n=51) | 0.784 (n=51) | 1.55 (n=49) | 2 |
| row8-9-typesafe-jev-d4-noul-v2-support-excerpts+completion | d4 | 60 (361) | 0.623 (n=51) | 0.699 (n=51) | 0.784 (n=51) | 1.94 (n=49) | 2 |
| row9r-typesafe-jev-d4-score-v1-excerpts+completion | rules | 60 (361) | 0.662 (n=51) | 0.748 (n=51) | 0.784 (n=51) | 1.55 (n=49) | 2 |
| row9r-typesafe-jev-d4-score-v1-excerpts+completion | d4 | 60 (361) | 0.650 (n=51) | 0.730 (n=51) | 0.784 (n=51) | 1.80 (n=49) | 2 |
| row8-9-laya-local-d4-noul-v1 | rules | 60 (361) | 0.662 (n=51) | 0.748 (n=51) | 0.784 (n=51) | 1.55 (n=49) | 2 |
| row8-9-laya-local-d4-noul-v1 | d4 | 60 (361) | 0.577 (n=51) | 0.765 (n=51) | 0.784 (n=51) | 2.00 (n=49) | 2 |
| row8-9-laya-local-d4-noul-v2-support-compact-150 | rules | 60 (361) | 0.662 (n=51) | 0.748 (n=51) | 0.784 (n=51) | 1.55 (n=49) | 2 |
| row8-9-laya-local-d4-noul-v2-support-compact-150 | d4 | 60 (361) | 0.619 (n=51) | 0.753 (n=51) | 0.784 (n=51) | 1.55 (n=49) | 2 |

## Reading

- All four rows are shadow D4 on build/world (manifest 452b57d9), dev cases, prompt-campaign rows 8-9 (m3-ref). The D4 scores are raw and uncalibrated, and the responses are in rules order. The "d4" rows are therefore the counterfactual order D4's raw scores would impose on the same packed units. Every row now scores all 361 units in all 60 cases.
- The two Jev rows each merge the original run with its completion (commit 80e251f), which covers disjoint cases with the same prompt text. Where the dirs overlap, the rules order agrees in all of them (0 mismatches).
- Coverage@4000 is identical in every row, because at this budget the whole packed set fits and reordering cannot change it. Whole-response metrics cannot see D4.
- At K=1000, every D4 order has lower coverage than the rules order (0.577-0.650 against 0.662).
- At K=2000, the two Jev orders are below the rules order (0.699 and 0.730 against 0.748) and the two Laya orders slightly above (0.753-0.765).
- The mean first-support rank is the same or worse under D4 (1.55-2.00 against 1.55).
- On these 51 answerable cases (49 with any supporting unit) the rules order already puts support near the top (rank 1.55), which leaves little headroom. The direction is flat to worse, and no improvement is supported.
- These numbers do not include the predeclared budget stress (1000/2000/4000 token budgets, `configs/budget_stress.yaml`). Those runs need their own live runs.

Regenerate with `python tools/d4_order_report.py --run <dir>[,<completion dir>] ... --cases gold/dev`.

> SYNTHETIC, NOT PRODUCTION EVIDENCE. 60 dev + 40 holdout questions support directional results and debugging only, not population estimates.
