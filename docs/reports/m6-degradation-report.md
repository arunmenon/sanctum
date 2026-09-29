# Sanctum Lab failure runs

> SYNTHETIC, NOT PRODUCTION EVIDENCE. 60 dev + 40 holdout questions support directional results and debugging only, not population estimates.

## Degradation under injected failures

Status honesty: never `sufficient` when a retrieval operation (search or fetch, per tool) on a mandatory source timed out or errored without a successful retry (runner-observed trace), and every failed source reported as a gap with a failure status or explicit failure reason. Latency is the runner's wall clock around each request (simulated hub latency, scaled).

| config | profile | n | success | d success | honesty | overclaims | unreported gaps | unknown | partial | failed calls | p50 ms | p95 ms | d p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C2 | none | 84 | 0.50 | 0.00 | 1.00 | 0 | 0 | 0.00 | 0.01 | 0 | 75.6 | 94.9 | 0.0 |
| C2 | degraded | 84 | 0.02 | -0.48 | 1.00 | 0 | 0 | 0.00 | 0.37 | 275 | 1174.6 | 3051.8 | 2956.9 |
| C2 | flaky | 84 | 0.15 | -0.35 | 1.00 | 0 | 0 | 0.00 | 0.32 | 130 | 424.2 | 953.5 | 858.6 |
| C2 | skillhub_timeout | 84 | 0.12 | -0.38 | 1.00 | 0 | 0 | 0.00 | 0.18 | 29 | 2958.9 | 3051.4 | 2956.5 |
| C4 | none | 84 | 0.68 | 0.00 | 1.00 | 0 | 0 | 0.00 | 0.07 | 0 | 103.6 | 141.0 | 0.0 |
| C4 | degraded | 84 | 0.08 | -0.60 | 0.98 | 2 | 0 | 0.00 | 0.50 | 154 | 984.7 | 2525.1 | 2384.1 |
| C4 | flaky | 84 | 0.36 | -0.32 | 0.99 | 1 | 0 | 0.00 | 0.30 | 67 | 398.2 | 915.9 | 774.9 |
| C4 | skillhub_timeout | 84 | 0.20 | -0.48 | 1.00 | 0 | 0 | 0.00 | 0.35 | 33 | 3043.3 | 3121.9 | 2980.8 |
| C5 | none | 84 | 0.68 | 0.00 | 1.00 | 0 | 0 | 0.00 | 0.07 | 0 | 104.6 | 139.7 | 0.0 |
| C5 | degraded | 84 | 0.08 | -0.60 | 0.98 | 2 | 0 | 0.00 | 0.50 | 154 | 989.2 | 2501.9 | 2362.2 |
| C5 | flaky | 84 | 0.36 | -0.32 | 0.99 | 1 | 0 | 0.00 | 0.30 | 67 | 404.5 | 917.8 | 778.1 |
| C5 | skillhub_timeout | 84 | 0.20 | -0.48 | 1.00 | 0 | 0 | 0.00 | 0.36 | 33 | 3024.8 | 3119.6 | 2979.9 |
- C4 / degraded dishonest status: dev-018, dev-052
- C4 / flaky dishonest status: dev-018
- C5 / degraded dishonest status: dev-018, dev-052
- C5 / flaky dishonest status: dev-018

> SYNTHETIC, NOT PRODUCTION EVIDENCE. 60 dev + 40 holdout questions support directional results and debugging only, not population estimates.

## Known residuals (lead)

Rerun after the final Codex fixes (fetch failures now count as failures; metrics-0.2.0). Remaining overclaims on memory arms: dev-018 (C4/C5 degraded and flaky) and dev-052 (C4/C5 degraded). C2 is fully honest. Not fixed in this pass.
