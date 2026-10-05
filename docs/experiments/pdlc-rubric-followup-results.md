# PDLC rubric follow-up: isolated descriptions and place memory

All 48 Sonnet 5.5 subscription runs completed, and all 48 answers are scored. Twelve newly authored, technically reviewed development tasks ran once each through four variants, with randomized variant order, identical corpus, prompts, rubric and resource limits. Jev remained raw and unconstrained in every variant. This compares Sanctum variations, not a new direct-hub baseline.

## Coverage and unsupported claims

| Variation | Overall | Supported (6 tasks) | Partial (3 tasks) | Boundary (3 tasks) | Answers with material unsupported claims |
| --- | ---: | ---: | ---: | ---: | ---: |
| Unchanged Sanctum | 73.61% | 77.78% | 55.56% | 83.33% | 0 |
| Richer Jev descriptions | 65.28% | 52.78% | 55.56% | 100.00% | 1 |
| Reviewed place memory | 84.03% | 95.83% | 44.44% | 100.00% | 0 |
| Both changes | 65.28% | 52.78% | 55.56% | 100.00% | 2 |

Memory-only overall coverage improves by 10.42 percentage points; its descriptive paired task-cluster interval spans −2.78 to +23.61 points. Descriptions alone and combined each decline by 8.33 points, with intervals −26.39 to +9.72. These intervals include zero. Six supported, three partial and three boundary questions are too few to establish narrow margins or robust family effects.

The memory variation is a promising supported-task signal, with no material unsupported claims, but partial-evidence coverage regresses by 11.11 points. Do not promote it without diagnosing that regression. The description variation is not supported by these results: supported coverage falls by 25 points and unsupported claims appear. Combining it with memory does not recover that loss. The existing active configuration remains unchanged.

Coverage does not mean completion. Provisional completion is 1/12 unchanged, 1/12 descriptions, 0/12 memory and 0/12 combined under the separate full checklist, uncertainty and unmet-requirement gates. Inspect those obligations before equating high fact coverage with completed PDLC work.

## Scoring recovery and verification

The initial workflow scored 47 answers and stopped at reporting because the evaluator imported `sys` only in its CLI entry point. Moving that import to module scope fixes embedded invocation. A new evaluation directory reused the saved judgments and fifteen exact-match calibration packets; no agent reruns or new fixture inference occurred.

The remaining judge response invented three planning dimensions for a behavior task whose frozen mandatory checklist is empty, even after its allowed format retry. A deterministic, recorded format repair removed only those nonapplicable annotations. Every fact, claim, citation, severity and contradiction label remained unchanged; the original response and failed retry remain preserved. No new judge call or rubric change was made. Final reporting recomputed all score derivations and validated evidence bindings.

Local evidence: `build/agent-runs/sonnet55-rubric-followup-01/quality-evaluation-03/`, `quality-format-recovery-01/format-repair-receipt.json`, `followup-summary.json`, and `baseline-vs-{system-one,memory,combined}.json`. The general multi-arm report is operational; the three explicit paired reports establish complete comparisons. Its generic comparison-ready field is not the authority for this four-arm analysis.

## Limits and next work

This is one attempt per variant on twelve same-corpus tasks, with Codex technical acceptance, disclosed shared premises and a same-model semantic judge. Independent human/gold acceptance remains pending. These fresh questions do not establish independent generalization, and their absolute scores must not be compared directly with the previous thirty-task cohort.

Next, trace the partial-evidence failures in memory-only and the supported failures in the description variants to selected sources, native filters, delivered evidence and answer/judge decisions. Preserve the negative results. Make further changes only where those traces establish a specific failure mechanism; keep Jev unconstrained and rubric quality as the objective.
