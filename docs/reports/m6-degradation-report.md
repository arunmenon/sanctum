# Sanctum Lab failure runs

> SYNTHETIC, NOT PRODUCTION EVIDENCE. 60 dev + 40 holdout questions support directional results and debugging only, not population estimates.

## Degradation under injected failures

Status honesty: never `sufficient` when a mandatory source's calls all timed out or errored (runner-observed trace), and every source with a non-ok call reported as a gap. Latency is the runner's wall clock around each request (simulated hub latency, scaled).

| config | profile | n | success | d success | honesty | overclaims | unreported gaps | unknown | partial | failed calls | p50 ms | p95 ms | d p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C2 | none | 84 | 0.50 | 0.00 | 1.00 | 0 | 0 | 0.00 | 0.01 | 0 | 61.6 | 79.6 | 0.0 |
| C2 | degraded | 84 | 0.20 | -0.30 | 1.00 | 0 | 0 | 0.00 | 0.13 | 275 | 1191.9 | 3044.2 | 2964.6 |
| C2 | flaky | 84 | 0.37 | -0.13 | 1.00 | 0 | 0 | 0.00 | 0.05 | 130 | 427.5 | 955.4 | 875.9 |
| C2 | skillhub_timeout | 84 | 0.12 | -0.38 | 1.00 | 0 | 0 | 0.00 | 0.18 | 29 | 2951.3 | 3046.4 | 2966.9 |
| C4 | none | 84 | 0.68 | 0.00 | 1.00 | 0 | 0 | 0.00 | 0.07 | 0 | 99.1 | 122.7 | 0.0 |
| C4 | degraded | 84 | 0.20 | -0.48 | 0.98 | 2 | 0 | 0.00 | 0.32 | 154 | 988.8 | 2494.1 | 2371.4 |
| C4 | flaky | 84 | 0.44 | -0.24 | 0.99 | 1 | 0 | 0.00 | 0.19 | 67 | 399.9 | 920.7 | 798.1 |
| C4 | skillhub_timeout | 84 | 0.20 | -0.48 | 1.00 | 0 | 0 | 0.00 | 0.35 | 33 | 3015.2 | 3125.2 | 3002.5 |
| C5 | none | 84 | 0.68 | 0.00 | 1.00 | 0 | 0 | 0.00 | 0.07 | 0 | 99.9 | 123.5 | 0.0 |
| C5 | degraded | 84 | 0.20 | -0.48 | 0.98 | 2 | 0 | 0.00 | 0.32 | 154 | 985.2 | 2469.2 | 2345.7 |
| C5 | flaky | 84 | 0.44 | -0.24 | 0.99 | 1 | 0 | 0.00 | 0.19 | 67 | 397.0 | 916.9 | 793.4 |
| C5 | skillhub_timeout | 84 | 0.20 | -0.48 | 1.00 | 0 | 0 | 0.00 | 0.35 | 33 | 3019.3 | 3123.3 | 2999.8 |
- C4 / degraded dishonest status: dev-018, dev-052
- C4 / flaky dishonest status: dev-018
- C5 / degraded dishonest status: dev-018, dev-052
- C5 / flaky dishonest status: dev-018

> SYNTHETIC, NOT PRODUCTION EVIDENCE. 60 dev + 40 holdout questions support directional results and debugging only, not population estimates.

## Known residuals (lead)

After the honesty fix (ce1d56f), overclaims fell from 38 to 6 across the matrix; C2 is fully honest. Residual overclaims on memory arms: dev-018 (C4/C5 degraded and flaky) and dev-052 (C4/C5 degraded). Not fixed in this pass; tracked for follow-up.
