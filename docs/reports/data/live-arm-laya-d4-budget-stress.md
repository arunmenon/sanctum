# D4 budget stress

> SYNTHETIC, NOT PRODUCTION EVIDENCE. 60 dev + 40 holdout questions support directional results and debugging only, not population estimates.

Budgets and K fixed in configs/budget_stress.yaml before outcomes were inspected. Coverage@K is over answerable cases (n); rank is over cases with any supporting unit.

| arm | budget | coverage@1000 | coverage@2000 | coverage@4000 | first support rank (mean, median, n) | answerable without support |
|---|---|---|---|---|---|---|
| C4 | 1000 | 0.63 (n=72) | 0.63 (n=72) | 0.63 (n=72) | 1.13, 1, 63 | 9 |
| C4+D4 | 1000 | 0.63 (n=72) | 0.63 (n=72) | 0.63 (n=72) | 1.06, 1, 63 | 9 |
| C4 | 2000 | 0.66 (n=72) | 0.76 (n=72) | 0.76 (n=72) | 1.24, 1, 66 | 6 |
| C4+D4 | 2000 | 0.64 (n=72) | 0.76 (n=72) | 0.76 (n=72) | 1.15, 1, 66 | 6 |
| C4 | 4000 | 0.66 (n=72) | 0.74 (n=72) | 0.78 (n=72) | 1.44, 1, 68 | 4 |
| C4+D4 | 4000 | 0.60 (n=72) | 0.76 (n=72) | 0.78 (n=72) | 1.47, 1, 68 | 4 |

> SYNTHETIC, NOT PRODUCTION EVIDENCE. 60 dev + 40 holdout questions support directional results and debugging only, not population estimates.
