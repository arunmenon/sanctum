# E1: Laya on CPU vs Jev as the D2 provider (dev and scenarios)

> SYNTHETIC, NOT PRODUCTION EVIDENCE. Every number is **measured once**. Both calibrations were fitted on dev, so dev rows are **in-sample**. Acceptance and holdout sets were not touched. Latency is reported per profile and is never a gate (D-JEV).

## Setup

| Item | Laya (`laya-local`) | Jev (`typesafe-jev`) |
|---|---|---|
| Runtime | Laya 0.3.22 on CPU, localhost; English checkpoint revision `55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851`; responses report model `laya-rl-agent` | Hosted; `jev-latest` resolved to `jev-1.13.0` |
| Host | Apple M1 Pro, 10 cores, 16 GB; server resident memory about 1.9 GB | laptop to hosted endpoint |
| Calibration (dev, CV-separated bands) | Platt a 0.428, b -1.265; skip 0.09, use 0.7 | Platt a 0.975, b -2.236; skip 0.07, use 0.7 |
| Held-out Brier (raw) / ECE (raw) | 0.144 (0.174) / 0.029 (0.166) | 0.132 (0.301) / 0.041 (0.408) |
| Held-out skips at band / harmful | 8 of 204 / 0 | 62 of 204 / 0 |
| Fit cost | 60 local calls, 60,592 input tokens | 60 calls, 38,046 / 5,100 tokens |

All arms were run at commit `d4c615d` with the same controls. The checkpoint revision is recorded in Laya's calibration binding; Laya's responses do not carry it, so it is pinned by the running server rather than checked per call.

## Batch behaviour (measured once, relaxed)

| Questions per call | Laya warm ms | Laya input tokens | Jev warm ms | Jev input tokens |
|---|---|---|---|---|
| 1 | 204 to 338 | 140 | 351 to 399 | 392 |
| 5 | 584 to 586 | 701 | 292 to 313 | 534 |
| 10 | 975 to 992 | 1,402 | 295 to 333 | 712 |
| 20 | 1,817 to 1,824 | 2,805 | 272 to 283 | 1,077 |

On CPU, Laya scores questions one after another: latency grows by about 90 ms per question and input tokens by about 140 per question, so batching saves nothing per question. Jev's latency stays flat and its input cost per question falls with batch size. Laya reported no truncation at any size (`state_tokens` 87, `state_tokens_dropped` 0).

## Results

| Set | Arm | Safe success | Mean recall | Harmful omissions | Sources per case | Recall drops vs control | Confident skips / D2 judgments | Model calls | p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|
| dev (60) | C2 | 26 | 0.804 | 15 | 2.57 | | | | |
| dev | C3 Laya strict | 26 | 0.804 | 15 | 2.57 | 0 | 0 / 141 | 60 unavailable | 152 / 152 |
| dev | C3 Laya relaxed | 26 | 0.804 | 15 | 2.57 | 0 | 0 / 141 | 60 ok | 611 / 1,081 |
| dev | C3 Jev strict | 26 | 0.804 | 15 | 2.57 | 0 | 0 / 141 | 60 unavailable | 191 / 270 |
| dev | C3 Jev relaxed | 25 | 0.765 | 17 | 2.22 | 2 (dev-012, dev-058) | 21 / 141 | 60 ok | 367 / 508 |
| dev | C4 | 38 | 0.843 | 14 | 2.57 | | | | |
| dev | C5 Laya strict | 38 | 0.843 | 14 | 2.57 | 0 | 0 / 132 | 60 unavailable | 152 / 153 |
| dev | C5 Laya relaxed | 38 | 0.843 | 14 | 2.57 | 0 | 0 / 132 | 60 ok | 532 / 683 |
| dev | C5 Jev strict | 38 | 0.843 | 14 | 2.57 | 0 | 0 / 132 | 60 unavailable | 192 / 277 |
| dev | C5 Jev relaxed | 38 | 0.814 | 16 | 2.27 | 2 (dev-012, dev-055) | 18 / 132 | 60 ok | 379 / 517 |
| scenarios (24) | C2 | 16 | 0.800 | 6 | 2.88 | | | | |
| scenarios | C3 Laya relaxed | 16 | 0.800 | 6 | 2.88 | 0 | 0 / 57 | 24 ok | 619 / 899 |
| scenarios | C3 Jev relaxed | 16 | 0.757 | 7 | 2.58 | 2 (sc-ex-06-1, sc-fx-21-1) | 7 / 57 | 24 ok | 372 / 411 |
| scenarios | C4 | 19 | 0.829 | 5 | 2.88 | | | | |
| scenarios | C5 Laya relaxed | 19 | 0.829 | 5 | 2.88 | 0 | 0 / 53 | 24 ok | 760 / 1,666 |
| scenarios | C5 Jev relaxed | 19 | 0.795 | 6 | 2.62 | 2 (sc-ex-06-1, sc-fx-21-1) | 6 / 53 | 24 ok | 356 / 450 |

Strict profiles on scenarios behave like dev: every call reaches the deadline, answers are unavailable, and each arm equals its control (Laya p50 about 152 ms, Jev about 192 ms, the deadline plus overhead).

## Reading

- **Laya never skips.** With its calibration (held-out, only 8 of 204 judgments fall below the skip band), no dev or scenario judgment falls below 0.09, so Laya arms keep every candidate and equal C2 and C4 exactly. It is a safe, no-savings provider on this data. It is also slower on CPU (p50 about 530 to 760 ms per D2 round) and grows linearly with the number of questions.
- **Jev saves and costs.** Jev skips 13 to 15% of judgments on dev and cuts sources per case by about 13%, with recall drops on 2 dev cases per arm and 1 to 2 more harmful omissions. Compared with the previous Jev run (commit `4b6c9a6`), dev C3 moved from 26 to 25 safe successes and one skip changed (dev-058): Jev's answers vary slightly between runs even at the same resolved version.
- **Neither result supports H1 yet.** Laya gives no savings; Jev's savings come with harmful omissions that exceed the zero-harm held-out estimate. Acceptance-set and holdout evaluation remain the deciding evidence.

## Notes

- Laya's startup warns that choice temperature is clamped for 11 or more options. D2 uses `noul` only, so this does not apply, but a future `choice` question with 11+ options on Laya must account for it.
- Truncation guard: Laya reports `usage.truncated`, `state_tokens_dropped` and `truncated_questions`; any truncated state voids the call and any truncated question voids its decision (protocol core). Our largest state here was 87 tokens.
