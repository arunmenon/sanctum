# E1 first look: Jev (typesafe-jev) as the D2 provider on dev and scenarios

> SYNTHETIC, NOT PRODUCTION EVIDENCE. Every number here is **measured once**. The calibration was fitted on dev and these runs are also on dev, so the dev rows are **in-sample**; the H1 claim needs the fresh acceptance set and the holdout, which were not touched. Latency is reported per profile and is never a gate (D-JEV).

## Setup

| Item | Value |
|---|---|
| Commit | `4b6c9a6` (calibration committed), runs at that commit |
| Provider | `typesafe-jev`, requested `jev-latest`, resolved `jev-1.13.0` on every call |
| Calibration | `configs/calibration/typesafe-jev@jev-1.13.0.yaml`: Platt on logit(p_raw), a 0.975, b -2.236; bands use 0.7, skip 0.07 (skip chosen on cross-validated held-out predictions, harm tolerance 0.05) |
| Calibration quality (held-out, CV over dev cases) | Brier 0.132 (raw 0.301); ECE 0.041 (raw 0.408). Raw Jev probabilities overstate usefulness; at the chosen band, 62 of 204 held-out judgments would skip, 0 of them harmful |
| Fit cost | 60 calls; 38,046 input / 5,100 output tokens |
| Profiles | strict: `configs/system_one_providers.yaml` strict deadline; relaxed: 60 s, 3 calls per round |
| Controls | C2 (for C3) and C4 (for C5) at the same commit |
| Metrics | safe grounded success; harmful omission (a necessary obligation missing); recall drop per case against the control; sources attempted per case (runner-observed); model calls from `trace.model_calls` |

## Results

| Set | Arm | Safe success | Mean recall | Harmful omissions | Sources per case | Recall drops vs control | D2 judgments | Confident skips | Model calls | p50 / p95 ms | Tokens in / out |
|---|---|---|---|---|---|---|---|---|---|---|---|
| dev (60) | C2 | 26 | 0.804 | 15 | 2.57 | | | | 0 | | |
| dev | C3 strict | 26 | 0.804 | 15 | 2.57 | 0 | 141 | 0 | 60, all unavailable (deadline) | 191 / 277 | 0 / 0 |
| dev | C3 relaxed | 26 | 0.784 | 16 | 2.27 | 1 (dev-012) | 141 | 20 | 60 ok | 366 / 424 | 33,697 / 3,085 |
| dev | C4 | 38 | 0.843 | 14 | 2.57 | | | | 0 | | |
| dev | C5 strict | 38 | 0.843 | 14 | 2.57 | 0 | 132 | 0 | 60, all unavailable | 194 / 282 | 0 / 0 |
| dev | C5 relaxed | 38 | 0.814 | 16 | 2.27 | 2 (dev-012, dev-055) | 132 | 18 | 60 ok | 382 / 436 | 33,301 / 2,896 |
| scenarios (24) | C2 | 16 | 0.800 | 6 | 2.88 | | | | 0 | | |
| scenarios | C3 strict | 16 | 0.800 | 6 | 2.88 | 0 | 57 | 0 | 24, all unavailable | 195 / 281 | 0 / 0 |
| scenarios | C3 relaxed | 16 | 0.757 | 7 | 2.62 | 2 (sc-ex-06-1, sc-fx-21-1) | 57 | 6 | 24 ok | 383 / 448 | 13,581 / 1,246 |
| scenarios | C4 | 19 | 0.829 | 5 | 2.88 | | | | 0 | | |
| scenarios | C5 strict | 19 | 0.829 | 5 | 2.88 | 0 | 53 | 0 | 24, all unavailable | 194 / 268 | 0 / 0 |
| scenarios | C5 relaxed | 19 | 0.795 | 6 | 2.58 | 2 (sc-ex-06-1, sc-fx-21-1) | 53 | 7 | 24 ok | 380 / 423 | 13,405 / 1,162 |

Model-call latency is the broker's elapsed time (laptop to hosted endpoint, including validation). Under the strict profile every call reached the deadline before an answer, so every D2 answer was `unavailable`, every candidate was kept, and C3/C5 matched C2/C4 exactly (the safe default working as designed). No usage was reported for those calls.

## Reading

- **Strict profile:** with the strict deadline, Jev never answers in time from this network position; the fallback keeps behaviour identical to the rules arm. This says nothing about a co-located deployment (D-JEV: latency is not a gate).
- **Relaxed profile:** Jev confidently skipped 14% of optional-source judgments on dev (20 of 141 on C3), cutting sources called per case by about 12% (2.57 to 2.27). Safe grounded success did not change (26 on C3, 38 on C5), but recall dropped on 1 to 2 dev cases and harmful omissions rose by 1 to 2. On scenarios the same pattern holds (two recall drops, one extra harmful omission).
- **In-sample caution:** the skip band was chosen on dev with zero held-out harmful skips, yet dev runs still show harmful skips. That gap is the reason the claim waits on the acceptance set: whether the savings stay within D-MARGIN is not established here.

## What was not done

- No holdout or acceptance-set run (per instructions).
- Calibration covers D2 with template `d2-noul-v1` and descriptor release `sha256:da6dfe982c5156d9` only; runs with IncidentHub released would use a different descriptor release and run shadow-only.
- Live model calls for these runs: 168 answered under the relaxed profile (60 + 60 on dev, 24 + 24 on scenarios) and 168 attempted under the strict profile, which all reached the deadline and reported no usage.
