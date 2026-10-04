# Active Jev routing comparison

User authorized a new native Sonnet 5.5 subscription run on 2026-10-04. Preserve the previous shadow-mode Sanctum cohort as the historical comparison, not a no-Jev-cost baseline. Existing corpus, routing memory, agent model/effort, public questions, private gold and shared resource limits stay fixed. Changes are confined to a separately calibrated D2 policy and its pinned runtime binding.

## Sequence and gates

1. Author development calibration questions with GPT-6 Luna from artifacts not cited by evaluation gold; do not supply the thirty evaluation prompts or fit on their results. Validate exact source/version/unique evidence spans and audit questions before calls.
2. Label source usefulness by counterfactual reference retrieval on these development cases: full-source C1-fair versus each source removed. Labels concern marginal evidence recall, not assumed hub type.
3. Collect real Jev scores with the exact pilot descriptors/template/model, bounded at 80 calls and 200,000 input tokens. Group cross-validation by development artifact; fit Platt scaling and choose a conservative harmful-skip band. Record raw scores, failures and calibration provenance. If evidence does not support a safe nonzero skip band, report that limitation rather than force pruning.
4. Copy the original bundle into a new active-Jev experiment, add the calibration file to runtime pins, keep original inputs immutable, and create a fresh spend/attempt ledger. Verify matching calibration, non-shadow decision receipts, and an actual optional-source skip while required-source obligations remain enforced.
5. Run ninety fresh Sanctum attempts (30 tasks × 3 repetitions) with the same subscription model/limits. Save every recommendation, applied skip, fallback, observed hub call, evidence delivery and native outcome. No selective agent reruns.
6. Score with the current quality policy/calibration and compare active Jev against original shadow Sanctum, with direct access retained as context. Report source/call savings alongside fact coverage, unsupported claims, plan quality and latency. Historical cohorts have timing/order confounding; a fresh randomized paired comparison is needed before causal or production claims. Preserve unknown judge grades and independent acceptance limits.

The existing evaluation questions have already been observed, so this rerun is a development ablation, not a fresh held-out adoption test. A later unseen task set is required for generalization. We must not silently enrich descriptors, memory or prompts in the same ablation.

## Preflight findings and gate clarification

36 exact-quote-validated development cases and 144 counterfactual source labels were collected; two drafts were quarantined. Five-fold case-grouped calibration selected skip band 0.03, with ten held-out skips and one harmful skip out of 36 useful-source labels. This is a limited development retrieval-target calibration, not a confidence-certified safety guarantee.

The matching calibration was loaded: 36 development probes observed calibrated, non-shadow decisions where optional decisions were present, but no applied hub skip. Original campaign diagnostics show 130 optional D2 decisions, all for CodeHub; applying the new calibration to those raw responses recommends only three skips, all on requests whose sole called source was CodeHub. The existing no-empty-source guard preserves it. Required-source obligations also remain protected.

Accordingly, distinguish activation readiness from pruning proof: a calibrated non-shadow native ablation is ready, but source/call reduction is not established. Proceed with the user's requested fresh 90-attempt run to observe actual active recommendations, guarded application and quality; do not claim that calibration alone will improve retrieval. The earlier strict requirement for a demonstrated skip is superseded by this documented finding, without changing runtime guards.

## Execution checklist

- [x] Preserve original 180-run campaign and its exploratory score records.
- [x] Draft separate development cases with GPT-6 Luna; validate 36, quarantine two nonmatching quotes.
- [x] Run full-source and four source-removal reference retrieval passes; collect 144 source labels.
- [x] Collect real Jev scores, fit grouped cross-validation and bind the calibration to exact pilot descriptors/model/template.
- [x] Verify non-shadow decisions; document no applied skips in development probes and the sole-source guard in diagnostic replay.
- [x] Prepare a fresh, pinned 90-attempt active-Jev bundle and subscription spend ledger; native dispatch started.
- [x] Start a completion worker that waits for terminal native execution, judges saved answers and validates both cohorts before producing `active-vs-shadow-report.json`. It never reruns an agent and preserves unknown judgments.
- [ ] Complete the 90 native attempts and saved-answer judgments.
- [ ] Report applied/guarded recommendations, hub calls and quality differences with historical-cohort and development-calibration limitations.

Local outputs: `build/pdlc-jev-active/`, `build/agent-bundles/pdlc-sonnet-55-jev-active-01/`, `build/agent-runs/sonnet55-jev-active-01/`. These remain ignored; commands and source are versioned.

Verification: 54 calibration/runtime/provider/schedule/quality checks passed, two live-provider tests skipped; one additional ablation test passed to distinguish applied from guarded skip recommendations. Source code compiles and staged whitespace checks pass.
