# System One prompt campaign: summary and spend ledger

> SYNTHETIC, NOT PRODUCTION EVIDENCE. Every row was **measured once**, shadow-only, on dev cases (and the D6 challenge overlay). Numbers only; no verdict on either model.

## Row reports

| Rows | Decision | Report |
|---|---|---|
| 1-3 | D6 rubric, relations, excerpts | `docs/reports/system-one-prompt-ablation-d6.md` |
| 4-5 | D6 decomposition and relation choice | `docs/reports/system-one-prompt-ablation-d6-diagnostics.md` |
| 6-7 | D2 evidence-loss rubric, descriptors v2, with source-prior control | `docs/reports/system-one-prompt-ablation-d2.md` |
| 8-9 | D4 support rubric on excerpts, D4 score, with source-prior control; budget stress (Laya) | `docs/reports/system-one-prompt-ablation-d4.md` |
| 10 | order, context size, single vs batched, repeats | `docs/reports/system-one-prompt-ablation-order-context.md` |
| c1-c5 | D6 rows 1-5 on the challenge world (Laya) | `docs/reports/system-one-prompt-ablation-d6-challenge.md` |

## Worlds

- Dev rows ran on the frozen `build/world`, manifest `452b57d9`, checked before any call (`--expect-world`) and recorded per ledger row.
- The world build changed while the first rows 4-5 were running (another agent's rebuild). Those runs were recorded as invalid and rerun on the frozen world; the invalid runs' spend stays in the ledger.
- Challenge rows ran on `build/world-challenge`, manifest `15304c65481ba2bf`.

## Failures charged to the ledger

- Jev row 3 first ran at a 25k input-token row ceiling and stopped at 33 of 84 pairs; rerun as 3r.
- The first Jev D4 score pass (row 9) returned HTTP 422 on all 51 calls (score criteria sent as a mapping). Charged at input reservations since no usage came back; rerun as 9r with criteria as a list.
- Laya does not offer the `score` primitive; row 9 on Laya was refused with no call.

## Ceiling history (Jev; enforced before dispatch, never exceeded)

- 470/420000/45000
- 600/560000/60000
- 800/760000/80000 (owner, before rows 6-10 and the D6 challenge rows)

Jev spend against the current ceiling: 529 of 800 calls, 754,041 of 760,000 input tokens, 51,795 of 80,000 output tokens. The D6 challenge rows and the budget-stress grid were not run on Jev: the remaining input budget (5,959 tokens) is below one row.

## Spend ledger

| Row | Provider | Template | World manifest | Calls | Input tokens | Output tokens |
|---|---|---|---|---|---|---|
| 1 | typesafe-jev | `d6-noul-v1` | 452b57d9 | 28 | 33,107 | 2,248 |
| 2 | typesafe-jev | `d6-noul-v2-relations` | 452b57d9 | 25 | 39,435 | 2,135 |
| 1 | laya-local | `d6-noul-v1` | 452b57d9 | 83 | 29,828 | 0 |
| 2 | laya-local | `d6-noul-v2-relations` | 452b57d9 | 64 | 30,776 | 0 |
| 3 | typesafe-jev | `d6-noul-v3-excerpts` | 452b57d9 | 11 | 25,035 | 876 |
| 3 | laya-local | `d6-noul-v3-excerpts` | 452b57d9 | 32 | 16,216 | 0 |
| 4 | typesafe-jev | `d6-decomp-v1` | 9f813169 (invalid) | 26 | 49,522 | 3,874 |
| 5 | typesafe-jev | `d6-choice-v1` | 9f813169 (invalid) | 22 | 31,733 | 4,159 |
| 4 | laya-local | `d6-decomp-v1` | 9f813169 (invalid) | 194 | 75,016 | 0 |
| 5 | laya-local | `d6-choice-v1` | 9f813169 (invalid) | 91 | 42,055 | 0 |
| 3r | typesafe-jev | `d6-noul-v3-excerpts` | 452b57d9 | 28 | 60,825 | 2,248 |
| 3r | laya-local | `d6-noul-v3-excerpts-compact` | 452b57d9 | 32 | 16,214 | 0 |
| 3r | laya-local | `d6-noul-v3-excerpts-compact-150` | 452b57d9 | 57 | 27,541 | 0 |
| 4 | typesafe-jev | `d6-decomp-v1` | 9f813169 (invalid) | 27 | 59,446 | 4,992 |
| 5 | typesafe-jev | `d6-choice-v1` | 9f813169 (invalid) | 25 | 39,791 | 5,357 |
| 4 | laya-local | `d6-decomp-v1` | 9f813169 (invalid) | 168 | 60,780 | 0 |
| 5 | laya-local | `d6-choice-v1` | 9f813169 (invalid) | 82 | 36,663 | 0 |
| 6-7 | laya-local | `d2-noul-v1` | 452b57d9 | 0 | 0 | 0 |
| 6-7 | laya-local | `d2-noul-v2-loss` | 452b57d9 | 0 | 0 | 0 |
| 6-7 | laya-local | `d2-descriptors-v2` | 452b57d9 | 0 | 0 | 0 |
| 6-7 | laya-local | `d2-noul-v1` | 452b57d9 | 240 | 60,592 | 0 |
| 6-7 | laya-local | `d2-noul-v2-loss` | 452b57d9 | 240 | 80,992 | 0 |
| 6-7 | laya-local | `d2-descriptors-v2` | 452b57d9 | 240 | 53,872 | 0 |
| 6-7 | typesafe-jev | `d2-noul-v1` | 452b57d9686b9582 | 60 | 38,046 | 5,100 |
| 6-7 | typesafe-jev | `d2-noul-v2-loss` | 452b57d9686b9582 | 60 | 58,446 | 5,100 |
| 6-7 | typesafe-jev | `d2-descriptors-v2` | 452b57d9686b9582 | 60 | 36,426 | 5,100 |
| 6-7 | laya-local | `d2-noul-v1` | 452b57d9686b9582 | 240 | 60,592 | 0 |
| 6-7 | laya-local | `d2-noul-v2-loss` | 452b57d9686b9582 | 240 | 80,992 | 0 |
| 6-7 | laya-local | `d2-descriptors-v2` | 452b57d9686b9582 | 240 | 53,872 | 0 |
| 8-9 | typesafe-jev | `d4-noul-v2-support-excerpts` | 452b57d9686b9582 | 51 | 109,092 | 6,423 |
| 8-9 | typesafe-jev | `d4-score-v1-excerpts` | 452b57d9686b9582 | 51 | 109,303 | 0 |
| 8-9 | laya-local | `d4-noul-v1` | 452b57d9686b9582 | 361 | 70,389 | 0 |
| 8-9 | laya-local | `d4-noul-v2-support-compact-150` | 452b57d9686b9582 | 361 | 105,189 | 0 |
| 8-9 | laya-local | `d4-score-v1-compact-150` | 452b57d9686b9582 | 0 | 0 | 0 |
| 8-9 probe | typesafe-jev | `d4-score-v1-excerpts` | n/a | 1 | 150 | 0 |
| 9r | typesafe-jev | `d4-score-v1-excerpts` | 452b57d9686b9582 | 22 | 45,081 | 2,192 |
| 10 | typesafe-jev | `d2-noul-v1 (order/context/repeat)` | n/a (direct D2 state) | 32 | 18,603 | 1,991 |
| 10 | laya-local | `d2-noul-v1 (order/context/repeat)` | n/a (direct D2 state) | 60 | 14,647 | 0 |
| c1 | laya-local | `d6-noul-v1` | 15304c65481ba2bf | 58 | 17,899 | 0 |
| c2 | laya-local | `d6-noul-v2-relations` | 15304c65481ba2bf | 58 | 24,627 | 0 |
| c3 | laya-local | `d6-noul-v3-excerpts-compact-150` | 15304c65481ba2bf | 47 | 22,320 | 0 |
| c4 | laya-local | `d6-decomp-v1` | 15304c65481ba2bf | 116 | 37,074 | 0 |
| c5 | laya-local | `d6-choice-v1` | 15304c65481ba2bf | 58 | 23,525 | 0 |
| total | typesafe-jev | | | 529 | 754,041 | 51,795 |
| total | laya-local | | | 3362 | 1,041,671 | 0 |
