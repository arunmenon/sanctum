# E3: D4 relevance via System One (dev and scenarios)

> SYNTHETIC, NOT PRODUCTION EVIDENCE. Every number is **measured once**. Calibrations were fitted on dev, so dev rows are **in-sample**. Acceptance and holdout sets were not touched. Latency is reported per profile and is never a gate.

## Setup

| Item | Value |
|---|---|
| Commit | `790f8e9`; all arms run at that commit |
| Decision | D4, template `d4-noul-v1`, at most `d4_max_units` (20) units per request, half from the rules' top rank and half from units the rules excluded; the broker reads each unit's text itself |
| What D4 may change | the order of packed units; rules-excluded units at or above the use band may fill budget the rules left unused; it never removes a rules-packed unit (superset tested) |
| Labels (evaluator side) | a unit is positive when its span overlaps any necessary-evidence span (ruling: overlap) |
| Jev calibration | `typesafe-jev@jev-1.13.0.d4.yaml`: 361 units, 60 calls (72,627 / 7,878 tokens); Platt a 0.826, b -1.516; no band meets the false-addition tolerance, so use 1.0 (never add); held-out Brier 0.203 (raw 0.315), ECE 0.104 (raw 0.330) |
| Laya calibration | `laya-local@laya-rl-agent.d4.yaml`: 361 units, 197 calls; Platt a 0.982, b -0.926; use 1.0; held-out Brier 0.192 (raw 0.220), ECE 0.076 (raw 0.182) |

## Results

| Set | Arm | Safe success | Mean recall | Harmful omissions | Precision proxy | Tokens per response | Reorder-only gate | Model calls (HTTP) | p50 / p95 ms |
|---|---|---|---|---|---|---|---|---|---|
| dev (60) | C4 | 38 | 0.843 | 14 | 0.485 | 1,666 | | | |
| dev | C4+D4 Jev strict | 38 | 0.843 | 14 | 0.485 | 1,666 | never failed | 60 unavailable (60) | 193 / 281 |
| dev | C4+D4 Jev relaxed | 38 | 0.843 | 14 | 0.485 | 1,666 | never failed | 60 ok (60) | 377 / 439 |
| dev | C4+D4 Laya strict | 38 | 0.843 | 14 | 0.485 | 1,666 | never failed | 60 unavailable (13) | 0 / 153 |
| dev | C4+D4 Laya relaxed | 38 | 0.843 | 14 | 0.485 | 1,666 | never failed | 60 ok (197) | 1,557 / 4,722 |
| scenarios (24) | C4 | 19 | 0.829 | 5 | 0.483 | 2,041 | | | |
| scenarios | C4+D4 Jev relaxed | 19 | 0.829 | 5 | 0.483 | 2,041 | never failed | 24 ok (24) | 370 / 401 |
| scenarios | C4+D4 Laya relaxed | 19 | 0.829 | 5 | 0.483 | 2,041 | never failed | 24 ok (102) | 2,294 / 4,698 |

Strict scenario rows equal C4 as on dev. Every D4 arm is identical to C4 case by case on every scored metric.

## Reading

- **No measurable effect.** Neither provider's calibration found a use band within the false-addition tolerance, so D4 only reorders packed units. None of the scored metrics depends on order, and the rules-packed set is always kept (the evaluator's reorder-only gate never fired), so every result equals C4. H3 is not supported for D4 on this data.
- **Where D4 could matter:** only when the rules leave budget unused and some rules-excluded unit is truly necessary. On this corpus the rules already include every unit with query overlap, and excluded units rarely overlap necessary spans.
- **Cost:** Jev D4 adds about 1,200 input tokens per request; Laya D4 on CPU costs about 3 HTTP calls per request and p95 up to about 4.7 s. Latency is not a gate here, but it bounds any deployment of D4 on CPU.
