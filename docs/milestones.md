# Lab milestones (source of truth)

Supersedes the milestone numbering in `docs/experiments/lab-spike.md` §10. Each milestone ends in a demo.

| Milestone | Deliverables | Done when |
|---|---|---|
| **M0** Contracts and evaluator | Frozen wire contracts + JSON Schemas; `sanctum_eval`; stub SUT; `configs/matrix.yaml`; 44 tests incl. 17 evaluator mutations and static isolation | Done |
| **M1** Synthetic world | `world/world.yaml` (4-6 core services, ~26 filler, R40-R42 + experiment branch, all planted situations); world linter; renderer to per-hub corpora (~3,000 artifacts, hub-specific vocabulary, deterministic by seed); gold-derivation machinery (world + question spec → gold) | Linter green; every planted situation rendered; same seed gives identical output; gold derivable for a sample question per family |
| **M2** Hubs and runner | CodeHub, SkillHub, DocHub, MemoryHub as MCP servers (FTS5/BM25); token service; ACL; version reads; capability files; failure knobs; admin API; conformance suite; runner producing observed traces | Conformance green per hub; honest miss on unknown alias |
| **M3** Questions and sanctum-ref C1/C2 | 60 dev questions with derived gold; holdout author assigned and 40 holdout drafted (by that author, not the SUT team); `sanctum_ref` C1-naive, C1-fair, C2; receipts; SUT runs out of process and reaches hubs only through an MCP gateway proxy holding the token secret (discrepancy register 16) | Scenario tests EX-01..04, 06..10, FX-24 pass on C2. Result: 8/10 pass; EX-04 (unscoped historical) and EX-06 (ambiguous explore) are strict xfail on C2 and move to C4 at M4 |
| **M4** Memory v0 (C4, C4a) | Memory store, seed release `r1` (deliberately incomplete), name resolution with ambiguity, per-source query plans, procedures + ladder, C4a-equivalent and C4a-label-only controls | FX-16..23, EX-05, EX-15 pass; C4 and C4a runs complete. Result: on C4 (out of process, entity alignment) EX-05, EX-09b, EX-15, FX-16 (both cases), FX-17, FX-19 case 2, FX-20 pass; FX-18 and FX-23 unit-tested; FX-19 case 1, FX-21, EX-04, EX-06 strict xfail; FX-22 not built. Scenarios (22 cases): C2 15, C4 18, C4a-equivalent 18, C4a-label-only 15. Dev (60): C2 26, C4 38, C4a-equivalent 38, C4a-label-only 33. Q3b plan equivalence holds (test) |
| **M5** First paired report | Leak scanner, paired clustered stats, per-family report, B* profile (pinned cross-encoder) | C1-fair vs C2 vs C4 vs C4a report on dev + one holdout run; leakage gate evaluated. Report states results, whichever direction they go. Result (lexical ranker, B* deferred, register 18): dev safe success C1-fair 0.50, C2 0.43, C4 0.63, C4a-equivalent 0.63, C4a-label-only 0.55; holdout C1-fair 0.68, C2 0.50 (C2 minus C1-fair -0.17, 95% CI [-0.32, -0.05]), C4 0.65, C4a-equivalent 0.65. Memory beats rules (dev +0.20 [0.04, 0.35]; holdout +0.15 [-0.03, 0.31]) but neither rules nor memory beats fan-out on holdout. Leakage gate passes for all arms; C4a-label-only fails wrong-entity. See docs/reports/ |
| **M6** Decision provider (C3, C5) and failures | `DecisionProvider` with rules and local stand-in (Jev only if approved); failure-injection runs | C3, C5 reports; EX-09 variants pass under injected failure. Result: D2 stand-in (TF-IDF over pinned descriptors, logistic calibration fitted on dev counterfactual runs, configs/d2_standin.yaml) never reaches a confident "not useful" at the skip band 0.1, so C3 = C2 (scenarios 15/22, dev 26/60) and C5 = C4 (18/22, 38/60), same sources called (2.57/case on dev). At skip band 0.2 it skipped 109 sources and lost recall (C3 dev 20/60, C5 26/60). EX-09a, EX-09b, EX-09c, EX-09d pass; FX-21 script driven; FX-22 not built |
| **M7** Fifth hub onboarding | IncidentHub via adapter + manifest, no core edits | EX-12 passes; previously `insufficient` questions now answered. Result: onboarding is data only (owners/manifests/incidenthub.yaml, memory release r2; `git diff 92b4d62 -- src/sanctum_ref` empty, tested). EX-12 passes on C2 and C4 (released: answered from IncidentHub; held back: insufficient). Dev (60, gold derived with IncidentHub held back): C2 26 held / 24 released, C4 38 held / 37 released, sources per case 2.57 to 3.35; no dev question gains, because dev gold cannot credit incident evidence |
| **M8** Stretch | Agent-level H0 (direct hub access vs Sanctum C2/C4); release swap and rollback during requests | H0 report; FX-23 under concurrent load |

Holdout is run once per milestone from M5 on, by the holdout owner, and never used for tuning.

## E1 (H1 with Jev): result

Measured once, relaxed profile, `typesafe-jev` resolved to `jev-1.13.0`, calibration `typesafe-jev@jev-1.13.0` fitted on dev (60 calls). Latency reported, not gated (model_call p50 about 360 ms, p95 about 430 to 470 ms, laptop to hosted endpoint).

| Set | Comparison | Safe success | Necessary-evidence recall | Sources called per case | Wrong entity |
|---|---|---|---|---|---|
| Acceptance (20, fresh, run once) | C2 vs C3 | 0.50 vs 0.50 | 0.88 vs 0.88 | 2.60 vs 2.30 (-0.30, 95% CI [-0.67, -0.05]) | 0 vs 0 |
| Acceptance (20) | C4 vs C5 | 0.65 vs 0.65 | 0.97 vs 0.97 | 2.60 vs 2.25 (-0.35, [-0.72, -0.10]) | 0 vs 0 |
| Holdout (40, tag M6-jev) | C2 vs C3 | 0.50 vs 0.53 | 0.88 vs 0.85 (-0.03, [-0.09, 0.00]) | 2.75 vs 2.38 (-0.38, [-0.57, -0.19]) | 0 vs 0 |
| Holdout (40) | C4 vs C5 | 0.65 vs 0.68 | 0.91 vs 0.88 (-0.03, [-0.09, 0.00]) | 2.75 vs 2.33 (-0.42, [-0.64, -0.21]) | 0 vs 0 |

Reading: Jev as the D2 usefulness model cuts sources called by 12 to 15 percent with no change in safe success and no wrong-entity activations. On the holdout it costs one case of necessary-evidence recall per comparison (one harmful skip in 40); on the acceptance set none. Whether one harmful skip in 40 is inside D-MARGIN is an owner decision. Strict profile: every call hit the 150 ms deadline from this laptop, so C3/C5 equal C2/C4 there. Dev results are in-sample (calibration set). Reports: docs/reports/system-one-jev-{dev,acceptance,holdout}.md; run logs in acceptance/runs.log and holdout/runs.log.

### E1 with local Laya on CPU (measured once, commit d4c615d)

Laya 0.3.22, English checkpoint 55cf4c4e, CPU (M1 Pro, about 1.9 GB RSS). Calibration `laya-local@laya-rl-agent` on dev: held-out Brier 0.144 (raw 0.174), ECE 0.029 (raw 0.166); raw Laya is far better calibrated than raw Jev, but at the harm-tolerant skip band only 8 of 204 held-out judgments skip. In runs it makes 0 confident skips on dev and scenarios, so C3/C5 with Laya equal C2/C4 exactly (26/60, 38/60; 16/24, 19/24) and no acceptance or holdout run was spent on it. Latency on CPU grows about 90 ms per question (0.2 to 0.34 s for 1, 1.8 s for 20), so batching saves nothing there, unlike Jev. Laya exposes truncation metadata; the protocol core now voids truncated calls. Reports: docs/reports/system-one-laya-dev.md, system-one-batches-laya-local.md.

## E3 (Round 3: D6 conflict, D4 relevance) with Jev and Laya: result

Measured once at 790f8e9..b26f7b3, relaxed profile, calibrations on dev (CV-separated bands). Every Round 3 arm (C4+D6, C4+D4, for typesafe-jev and laya-local) equals C4 case by case: dev 38/60, scenarios 19/24, identical recall, conflicts and tokens. No acceptance or holdout run was spent on them.

| Fit | Items | Positives | Use band | Held-out Brier (raw) |
|---|---|---|---|---|
| Jev D6 | 84 pairs | 12 | 0.61 | 0.098 (0.152) |
| Laya D6 | 84 pairs | 12 | 1.0 (never promotes) | 0.132 (0.289); negative slope, answers run against the labels |
| Jev D4 | 361 units | | 1.0 (never adds) | 0.203 (0.315) |
| Laya D4 | 361 units | | 1.0 (never adds) | 0.192 (0.220) |

Why nothing moves: for D6 the typed rules already flag every pair that carries a gold relation, and the dropped candidates rarely hold one; Jev cleared its band on 2 of 84 judgments, neither a candidate pair. For D4 no add band met the false-promotion tolerance for either provider, so D4 only reorders, and the scored metrics ignore order; the reorder-only gate never fired. Under the strict profile every round hit the deadline and the rules-only fallback applied. The design invariants (D6 add-only on rule-produced pairs, D4 reorder-and-fill only) cap what either decision can change; the null is partly a consequence of those guardrails and partly of the rules already covering the gold conflicts on this world.

Cost and latency (reported, not gated): Jev p50 about 360 to 380 ms, about 1.2k input tokens per request for D4. Laya on CPU: D6 p50 1.0 to 1.9 s (p95 3.1 s), D4 p50 1.6 to 2.3 s (p95 4.7 s), about 3 HTTP calls per round. H3 is not supported for D6 or D4 on this data with either provider. Reports: docs/reports/system-one-d6-dev.md, system-one-d4-dev.md.

## E3-prompt campaign (System One prompt and state variants): result

Measured once, shadow-only except one owner-approved live experiment arm; dev, scenarios (live arm and budget stress) and the D6 challenge overlay (manifest 15304c65); no acceptance or holdout case used. Jev spend 631 calls, 1,008,710 input and 70,382 output tokens under a pre-dispatch ceiling of 1,100 / 1,030k / 110k. Numbers only:

- D2: Jev variants reach nested-CV outer AUC 0.737 to 0.758 against 0.731 for the no-model source-prior control; Laya variants 0.695 to 0.737 (no live Laya D2 arm).
- D4 (361 dev units): Jev support rubric on excerpts 0.697, Laya compact-150 0.820, control 0.639. Laya D4 live arm (84 cases, budgets 1,000 / 2,000 / 4,000): safe success, recall and tokens identical to C4 at every budget; order changed; reorder-only gate never fired.
- D6: 0 promotions on dev by construction (every positive pair rule-flagged); on the challenge slice (58 items, 26 positive, 4 of 20 positive pairs never exposed) noul raw AUC Jev 0.521 to 0.593, Laya 0.335 to 0.730.

Summary, tables, ledger and caveats: docs/reports/system-one-prompt-campaign.md; lab page: docs/experiments/system-one-lab.md.
