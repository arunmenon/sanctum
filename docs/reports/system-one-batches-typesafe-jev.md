# System One batch measurement: typesafe-jev

> SYNTHETIC, NOT PRODUCTION EVIDENCE. **Measured once**, relaxed profile (60 s deadline), from a laptop against the provider endpoint, so network time dominates; not evidence about the fast path.

Date 2026-09-30. Requested model `jev-latest`. HTTP calls 15 (cap 60). Usage total {"input_tokens": 9429, "output_tokens": 2628}.

| Questions | Run | Latency ms | Calls | Answered | Resolved model | Input tokens | Output tokens | Input tokens per question |
|---|---|---|---|---|---|---|---|---|
| 1 | cold | 568 | 1 | 1 | jev-1.13.0 | 392 | 26 | 392 |
| 1 | warm | 399 | 1 | 1 | jev-1.13.0 | 392 | 26 | 392 |
| 1 | warm | 351 | 1 | 1 | jev-1.13.0 | 392 | 26 | 392 |
| 2 | cold | 382 | 1 | 2 | jev-1.13.0 | 428 | 49 | 214 |
| 2 | warm | 322 | 1 | 2 | jev-1.13.0 | 428 | 49 | 214 |
| 2 | warm | 307 | 1 | 2 | jev-1.13.0 | 428 | 49 | 214 |
| 5 | cold | 419 | 1 | 5 | jev-1.13.0 | 534 | 115 | 107 |
| 5 | warm | 292 | 1 | 5 | jev-1.13.0 | 534 | 115 | 107 |
| 5 | warm | 313 | 1 | 5 | jev-1.13.0 | 534 | 115 | 107 |
| 10 | cold | 320 | 1 | 10 | jev-1.13.0 | 712 | 227 | 71 |
| 10 | warm | 295 | 1 | 10 | jev-1.13.0 | 712 | 227 | 71 |
| 10 | warm | 333 | 1 | 10 | jev-1.13.0 | 712 | 227 | 71 |
| 20 | cold | 352 | 1 | 20 | jev-1.13.0 | 1077 | 459 | 54 |
| 20 | warm | 283 | 1 | 20 | jev-1.13.0 | 1077 | 459 | 54 |
| 20 | warm | 272 | 1 | 20 | jev-1.13.0 | 1077 | 459 | 54 |

| Questions | Warm latency ms (median of repeats) |
|---|---|
| 1 | 375.0 |
| 2 | 314.5 |
| 5 | 302.5 |
| 10 | 314.0 |
| 20 | 277.5 |
