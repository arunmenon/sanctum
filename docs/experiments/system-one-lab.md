# System One in the lab: decisions, measurements and campaign

Lab companion to the design page [System One providers](../../design/intelligence-layer/system-one-providers.md).
The design page states the rules; this page records what the lab decided, measured and ran against
them. Each item names the design section it tests.

> SYNTHETIC, NOT PRODUCTION EVIDENCE. Every number on this page was **measured once** unless it says otherwise.

## Why the lab looked at System One

Tests: [design §1 (cascade)](../../design/intelligence-layer/system-one-providers.md#1-the-cascade-and-where-providers-sit), [§3 (wire protocol)](../../design/intelligence-layer/system-one-providers.md#3-wire-protocol-post-v1systemone), [§5 points 2 and 4](../../design/intelligence-layer/system-one-providers.md#5-the-handshake-thirteen-points).

The M6 stand-in (TF-IDF over pinned descriptors) never reached a confident "not useful" answer, so C3 equalled C2 and hypothesis H1 (does a System One model route better?) was untested. One live Jev call showed what an integration must handle:

| Observation | Consequence |
|---|---|
| `model: "jev-latest"` came back as `jev-1.13.0` | Calibration is per resolved version |
| One call with 2 questions took 531 ms end to end | Above the 150 ms Round 2 target; latency is measured per profile |
| A `choice` answer had `confidence` 0.24 while its top probability was 0.50 | Bands use calibrated `noul` only, never `confidence` |
| `usage`: 363 input tokens, 60 output tokens | Hosted usage is reported; open backends may report none |

## Owner decisions for the spike

Tests: [design §5 points 7 and 9 (latency profiles, data classes)](../../design/intelligence-layer/system-one-providers.md#5-the-handshake-thirteen-points) and [§14 (when a variant may go live)](../../design/intelligence-layer/system-one-providers.md#14-template-and-state-layout-registry).

| ID | Decision |
|---|---|
| D-JEV | Hosted Jev is approved for synthetic lab data only. Real data waits on data-class and egress approval. |
| Latency | Measured per profile (strict, relaxed); never a gate in this spike. |
| First scope | D2 source usefulness live (Jev and the stand-in); D6 and D4 as experiment E3. |
| D-MARGIN | Source-call savings count only within the agreed evidence-quality tolerance. |
| Laya D2 | No live Laya D2 arm: its bands match the no-model source-prior control (campaign rows 6-7). |
| Laya D4 | Live experiment arm approved on dev and scenarios only for `d4-noul-v2-support-compact-150`; run once (results below). |
| Challenge labels | D6 challenge rows use slice-scope labels as primary, case scope as secondary. |
| Candidate cap | `MAX_CANDIDATE_PAIRS` stays 6; the SUT is not tuned to the challenge slice. |
| Campaign ceiling (Jev) | 470/420k/45k, raised to 600/560k/60k, 800/760k/80k, 1,000/950k/100k and 1,100/1,030k/110k (attempts / input / output tokens), enforced before dispatch. |

## Acceptance blockers carried into E1

Tests: [design §7 (what the model can and cannot lose)](../../design/intelligence-layer/system-one-providers.md#7-what-the-model-can-and-cannot-lose) and [§5 point 1 (auth)](../../design/intelligence-layer/system-one-providers.md#5-the-handshake-thirteen-points).

| Blocker | Status |
|---|---|
| Residual status overclaims under failure on C4/C5 (dev-018, dev-052) | Must be fixed before any favorable Jev result is accepted. |
| Holdout exposure | The M5 holdout was run and rerun once and seen by the lead; the Jev claim also needs a fresh acceptance set of about 20 cases, unseen before the run. |
| Key hygiene | The key was shared in chat; the owner chose to proceed on synthetic data and rotate afterwards. Verification scrubs the SUT environment and scans outputs for the configured key value. |

## Measurements

### Calibrations

Tests: [design §8 (binding and shadow-only rule)](../../design/intelligence-layer/system-one-providers.md#8-calibration-binding-and-the-shadow-only-rule). Files in `configs/calibration/`; a fit whose use band is 1.0 is kept under `rejected/`, so the SUT runs shadow by absence.

| Binding | Template, layout | Fitted on | Band | Held-out Brier (raw) | Status |
|---|---|---|---|---|---|
| `typesafe-jev@jev-1.13.0` D2 | `d2-noul-v1`, descriptor release pinned | dev, 204 judgments, 35 positive | use 0.7, skip 0.07 | 0.13 (0.30) | live |
| `laya-local@laya-rl-agent` D2 (revision 55cf4c4e) | `d2-noul-v1` | dev, 204 judgments | skip 0.09 | 0.144 (0.174) | live; no confident skips in runs |
| `typesafe-jev@jev-1.13.0.d6` | `d6-noul-v1`, `none` (v1 slices) | dev, 84 pairs, 12 positive | use 0.61 | 0.098 (0.152) | live |
| `laya-local` D6 | `d6-noul-v1` | dev, 84 pairs | 1.0 | 0.132 (0.289), negative slope | rejected |
| `typesafe-jev` D4 | `d4-noul-v1` | dev, 361 units, 127 positive | 1.0 | 0.203 (0.315) | rejected |
| `laya-local` D4 | `d4-noul-v1` | dev, 361 units | 1.0 | 0.192 (0.220) | rejected |
| `laya-local@laya-rl-agent.d4` (revision 55cf4c4e) | `d4-noul-v2-support-compact-150`, `r3-state-v2-compact-150` | dev, 361 units, 127 positive | use 0.59 | 0.158 (0.176) | experiment arm only: applies when the laya-local D4 template override is set; the override is not set in the committed config |

Finding: Round 3 fits used to record the layout as `none`, which the SUT accepts for any layout. The fit tool now records the layout the broker reports (`round3_release`); the Laya D4 binding was rewritten to its exact layout (provenance records why) and is pinned by `tests/test_d4_live_arm_binding.py`.

### Batch measurement

Tests: [design §11 (batching)](../../design/intelligence-layer/system-one-providers.md#11-batching). `typesafe-jev`, relaxed profile, laptop to hosted endpoint ([report](../reports/system-one-batches-typesafe-jev.md)):

| Questions per call | Warm latency ms (median of 2) | Input tokens | Output tokens | Input tokens per question |
|---|---|---|---|---|
| 1 | 375 | 392 | 26 | 392 |
| 2 | 315 | 428 | 49 | 214 |
| 5 | 303 | 534 | 115 | 107 |
| 10 | 314 | 712 | 227 | 71 |
| 20 | 278 | 1,077 | 459 | 54 |

Every call resolved `jev-latest` to `jev-1.13.0`; cold calls took 320 to 568 ms. Campaign row 10 (5 cases): an identical repeat changed Jev probabilities by 0.012 on average, reversed order by 0.015, single-question calls by 0.008, and a longer context by 0.132 ([report](../reports/system-one-prompt-ablation-order-context.md)).

### Local Laya on CPU

Tests: [design §13 (self-hosted provider example)](../../design/intelligence-layer/system-one-providers.md#13-example-a-self-hosted-provider-laya-on-cpu-laya-local). Laya 0.3.22, English checkpoint `55cf4c4e`, Apple M1 Pro (10 cores, 16 GB) ([report](../reports/system-one-laya-dev.md), [batches](../reports/system-one-batches-laya-local.md)):

| Measure | Value |
|---|---|
| Server resident memory | about 1.9 GB |
| Latency per call, warm | 0.2 to 0.34 s for 1 question, 0.58 s for 5, 0.98 s for 10, 1.82 s for 20 (about 90 ms per added question) |
| Input tokens | about 140 per question; batching does not lower cost per question on CPU |
| Input limit | total input near 500 tokens is truncated (`usage.truncated`); configured as 1 question per call, 1,500 state characters |
| D2 round latency in runs (relaxed) | p50 about 530 to 760 ms, p95 up to 1.7 s |
| Round 3 latency (relaxed) | D6 p50 1.0 to 1.9 s (p95 3.1 s); D4 p50 1.6 to 2.3 s (p95 4.7 s) |
| Primitives | `noul`, `choice`; `score` not offered |
| Conformance | passes against Laya 0.3.22; `experimental` pending a second run |

## Round 3 (D6, D4) variants and status

Tests: [design §12 (Round 3)](../../design/intelligence-layer/system-one-providers.md#12-round-3-decisions-d6-conflict-d4-relevance) and [§14 (template and state-layout registry)](../../design/intelligence-layer/system-one-providers.md#14-template-and-state-layout-registry). **Live** means a calibration with a usable band exists and a run may apply it; **shadow** means answers are recorded and never applied; **diagnostic** means shadow-only by definition.

| Variant | Decision | Kind | Status | Campaign result pointer |
|---|---|---|---|---|
| `d2-noul-v1` | D2 | template | live: Jev and Laya | rows 6-7 |
| `d2-noul-v2-loss` | D2 | evidence-loss rubric | shadow | rows 6-7 |
| `d2-descriptors-v2` | D2 | descriptor set | shadow | rows 6-7 |
| `d6-noul-v1` | D6 | baseline | live for Jev (use 0.61); rejected for Laya | rows 1, c1 |
| `d6-noul-v2-relations` | D6 | aligned target | shadow | rows 2, c2 |
| `d6-noul-v3-excerpts` | D6 | on `r3-state-v2` | shadow | rows 3, c3 (Jev) |
| `d6-noul-v3-excerpts-compact`, `-compact-150` | D6 | on compact layouts | shadow (Laya truncates 24 of 58 challenge items at 150) | rows 3, c3 (Laya) |
| `d6-laya-positive-v1` | D6 | short template | shadow, not run in the campaign | |
| `d6-laya-negative-v1` | D6 | reversed polarity | diagnostic, not run in the campaign | |
| `d6-decomp-v1` | D6 | two questions per pair | diagnostic | rows 4, c4 |
| `d6-choice-v1` | D6 | relation choice | diagnostic | rows 5, c5 |
| `d4-noul-v1` | D4 | baseline | shadow (fits rejected) | row 8 baseline (Laya) |
| `d4-noul-v2-support-excerpts` | D4 | support rubric on `r3-state-v2` | shadow (Jev) | row 8 |
| `d4-noul-v2-support-compact-150` | D4 | support rubric on `r3-state-v2-compact-150` | calibrated for Laya; ran once as the approved live experiment arm; not set in the committed config | row 8, live arm |
| `d4-score-v1` | D4 | score | diagnostic (Jev only) | row 9 |
| `r3-state-v1` | D6, D4 | text slices up to 1,200 chars | in use (default) | |
| `r3-state-v2` | D6, D4 | labeled, assertion-bearing excerpts | shadow | |
| `r3-state-v2-compact`, `-compact-150` | D6, D4 | v2 fields, excerpt capped at 350 / 150 chars | shadow (small-context providers); 150 used by the Laya D4 arm | |

E3 before the campaign: every Round 3 arm (C4+D6, C4+D4, both providers) equalled C4 case by case on dev (38/60) and scenarios (19/24) with the baseline templates.

## Prompt campaign

Full tables, ledger and caveats: [campaign summary](../reports/system-one-prompt-campaign.md). Headline numbers, dev unless marked:

| Decision | Measurement | Result |
|---|---|---|
| D2 (Jev) | nested-CV outer AUC, variants vs source-prior control | 0.737 to 0.758 vs 0.731; 47 to 66 skips (1 to 2 harmful) vs 31 (1) of 204 |
| D2 (Laya) | same | 0.695 to 0.737 vs 0.731 |
| D4 (Jev, 361 units) | support rubric on excerpts, nested AUC vs control | 0.697 vs 0.639; 5 units at or above band (2 false) |
| D4 (Laya, 361 units) | compact-150, nested AUC vs control | 0.820 vs 0.639; 88 units at or above band (20 false) |
| D4 live arm (Laya, 84 cases, 3 budgets) | scored metrics vs C4 | identical safe success, recall and tokens at every budget; order changed (first support rank 1.13 to 1.06 at 1,000; coverage@1000 0.66 to 0.60 at 4,000); reorder-only gate never fired |
| D6 dev | promotions | 0 by construction: every positive pair is rule-flagged |
| D6 challenge (58 items, 26 positive slice scope) | raw AUC, noul rows | Jev 0.521 to 0.593; Laya 0.335 to 0.730 |
| D6 challenge diagnostics | Jev decomposition / choice | values_differ 0.638, choice 0.514; relation type 15 of 22 |

## Reports

- [Campaign summary](../reports/system-one-prompt-campaign.md) with the spend ledger and "What each result can and cannot say"
- Row reports: [D6 1-3](../reports/system-one-prompt-ablation-d6.md), [D6 4-5](../reports/system-one-prompt-ablation-d6-diagnostics.md), [D2 6-7](../reports/system-one-prompt-ablation-d2.md), [D4 8-9, budget stress, live arm](../reports/system-one-prompt-ablation-d4.md), [row 10](../reports/system-one-prompt-ablation-order-context.md), [D6 challenge](../reports/system-one-prompt-ablation-d6-challenge.md)
- Earlier: [Laya vs Jev](../reports/system-one-laya-dev.md), [Jev batches](../reports/system-one-batches-typesafe-jev.md), [Laya batches](../reports/system-one-batches-laya-local.md), [D6 dev](../reports/system-one-d6-dev.md), [D4 dev](../reports/system-one-d4-dev.md)
