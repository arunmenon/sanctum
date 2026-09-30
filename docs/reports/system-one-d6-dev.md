# E3: D6 possible conflict via System One (dev and scenarios)

> SYNTHETIC, NOT PRODUCTION EVIDENCE. Every number is **measured once**. Calibrations were fitted on dev, so dev rows are **in-sample**. Acceptance and holdout sets were not touched. Latency is reported per profile and is never a gate.

## Setup

| Item | Value |
|---|---|
| Commit | `790f8e9` (calibrations committed); all arms run at that commit |
| Decision | D6, template `d6-noul-v1`, on typed-rule pairs only: rule-flagged pairs (always kept) plus up to 6 candidate pairs per request that the same-subject rule dropped; the broker reads the evidence text itself from provenance refs |
| What D6 may change | promote a candidate pair to `possible_conflict` when its calibrated p reaches the use band; it never hides, dismisses or confirms a flag (design page §14) |
| Labels (evaluator side) | a pair is positive when each unit covers one witness bundle of a gold relation (`sanctum_eval.calibration_labels`) |
| Jev calibration | `typesafe-jev@jev-1.13.0.d6.yaml`: 84 pairs, 12 positive, 28 calls (33,107 / 2,248 tokens); Platt a 1.600, b -1.533; use band 0.61; held-out Brier 0.098 (raw 0.152), ECE 0.063 (raw 0.231) |
| Laya calibration | `laya-local@laya-rl-agent.d6.yaml`: 84 pairs, 83 calls; Platt a **-1.761** (Laya's D6 answers run against the labels); no band meets the false-promotion tolerance, so use 1.0 (never promote); held-out Brier 0.132 (raw 0.289) |

## Results

| Set | Arm | Safe success | Conflict witnesses kept | Conflicts flagged | False conflicts | Model calls (HTTP) | p50 / p95 ms |
|---|---|---|---|---|---|---|---|
| dev (60) | C4 | 38 | 0.632 | 62 | 24 | | |
| dev | C4+D6 Jev strict | 38 | 0.632 | 62 | 24 | 28 rounds unavailable (28) | 193 / 272 |
| dev | C4+D6 Jev relaxed | 38 | 0.632 | 62 | 24 | 28 ok (28) | 357 / 458 |
| dev | C4+D6 Laya strict | 38 | 0.632 | 62 | 24 | 28 unavailable (10) | 0 / 153 |
| dev | C4+D6 Laya relaxed | 38 | 0.632 | 62 | 24 | 28 ok (83) | 986 / 3,106 |
| scenarios (24) | C4 | 19 | 0.846 | 44 | 10 | | |
| scenarios | C4+D6 Jev relaxed | 19 | 0.846 | 44 | 10 | 19 ok (19) | 356 / 407 |
| scenarios | C4+D6 Laya relaxed | 19 | 0.846 | 44 | 10 | 19 ok (64) | 1,884 / 2,519 |

Strict scenario rows equal C4 as on dev. Every D6 arm is identical to C4 case by case.

## Reading

- **No effect.** Jev's calibrated p reached the 0.61 band on 2 of 84 dev judgments and 1 of 67 on scenarios, and none of them was a candidate pair, so nothing was promoted. Laya never promotes (negative calibration slope). With both providers, D6 adds cost and latency and changes no output. H3 is not supported for D6 on this data.
- **Why little room exists:** the typed rules already flag the pairs that carry the gold relations the metric checks (conflict witnesses kept 0.632 on dev), and the rules' dropped candidates rarely hold a real relation (12 of 84 pairs positive, mostly flagged ones).
- **Laya's context:** Laya truncates total input near 500 tokens (measured). With two 1,200-character excerpts per pair, pairs went unanswered until `laya-local` was declared at 2 questions and 1,500 state characters per call; D6 on Laya then needs about 3 HTTP calls per round (83 for 28 rounds) and its p95 reaches about 3 s on CPU.
- Strict profile: every round reached the deadline; the fallback is rules-only by design.
