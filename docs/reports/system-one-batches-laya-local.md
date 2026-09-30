# System One batch measurement: laya-local

> SYNTHETIC, NOT PRODUCTION EVIDENCE. **Measured once**, relaxed profile (60 s deadline), from a laptop against the provider endpoint, so network time dominates; not evidence about the fast path.

Date 2026-09-30. Requested model `convaiinnovations/laya`. HTTP calls 15 (cap 60). Usage total {"input_tokens": 15984, "output_tokens": 0, "state_tokens": 1305, "state_tokens_dropped": 0, "truncated": 0}.

| Questions | Run | Latency ms | Calls | Answered | Resolved model | Input tokens | Output tokens | Input tokens per question |
|---|---|---|---|---|---|---|---|---|
| 1 | cold | 297 | 1 | 1 | laya-rl-agent | 140 | 0 | 140 |
| 1 | warm | 338 | 1 | 1 | laya-rl-agent | 140 | 0 | 140 |
| 1 | warm | 204 | 1 | 1 | laya-rl-agent | 140 | 0 | 140 |
| 2 | cold | 445 | 1 | 2 | laya-rl-agent | 280 | 0 | 140 |
| 2 | warm | 307 | 1 | 2 | laya-rl-agent | 280 | 0 | 140 |
| 2 | warm | 322 | 1 | 2 | laya-rl-agent | 280 | 0 | 140 |
| 5 | cold | 619 | 1 | 5 | laya-rl-agent | 701 | 0 | 140 |
| 5 | warm | 584 | 1 | 5 | laya-rl-agent | 701 | 0 | 140 |
| 5 | warm | 586 | 1 | 5 | laya-rl-agent | 701 | 0 | 140 |
| 10 | cold | 980 | 1 | 10 | laya-rl-agent | 1402 | 0 | 140 |
| 10 | warm | 992 | 1 | 10 | laya-rl-agent | 1402 | 0 | 140 |
| 10 | warm | 975 | 1 | 10 | laya-rl-agent | 1402 | 0 | 140 |
| 20 | cold | 1816 | 1 | 20 | laya-rl-agent | 2805 | 0 | 140 |
| 20 | warm | 1824 | 1 | 20 | laya-rl-agent | 2805 | 0 | 140 |
| 20 | warm | 1817 | 1 | 20 | laya-rl-agent | 2805 | 0 | 140 |

| Questions | Warm latency ms (median of repeats) |
|---|---|
| 1 | 271.0 |
| 2 | 314.5 |
| 5 | 585.0 |
| 10 | 983.5 |
| 20 | 1820.5 |
