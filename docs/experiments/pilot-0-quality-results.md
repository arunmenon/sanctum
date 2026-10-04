# Pilot-0 exploratory quality results

Recorded 2026-10-04 from the saved Sonnet 5.5 subscription campaign. All 180 native agent runs completed: 30 tasks × two arms × three repetitions. The quality driver finished processing the schedule in `build/agent-runs/sonnet55-full-development-01/quality-evaluation-07`.

## Scoring completeness

175 semantic judgments plus four zero-credit agent protocol failures give 179 scored attempts. One direct-arm attempt for `fraud-batch-client-uncertainty-v2` remains unscored: the judge returned `claim_reviews` instead of required `claims` both initially and on the single schema retry. Its quality is unknown, not zero; the original records remain saved and no agent task was rerun. There are no score-binding issues in the report.

The full primary comparison is therefore not ready. Twenty-nine tasks have all paired repetition scores; the supported and out-of-scope strata are complete, while the partial stratum has five complete task pairs out of six.

## Supported-fact coverage comparison

Differences are Sanctum minus direct access, in percentage points. Repetitions are averaged within each task/arm; the descriptive interval comes from 10,000 seeded paired task-cluster bootstrap resamples.

| Slice | Complete task pairs | Paired difference | Descriptive 95% interval |
|---|---:|---:|---:|
| Overall complete-task analysis | 29 | -2.45 | -13.56 to +8.93 |
| Supported tasks | 18 | -6.73 | -19.94 to +6.91 |
| Partial tasks, complete pairs only | 5 | +8.89 | -16.11 to +40.00 |
| Out-of-scope tasks | 6 | +0.93 | -23.15 to +25.00 |

All intervals span zero. This pilot does not establish a clear quality advantage for either arm. The supported-task point estimate favors direct access; partial-task results cannot justify an overall win. Boundary handling must remain separate from supported-answer quality.

## Other quality dimensions

On the 54 supported attempts per arm, provisional completion is 19 direct versus 13 Sanctum. These are rubric-derived provisional results, not human-accepted task success. Material unsupported-claim incidence is 1 direct versus 5 Sanctum on supported tasks, and 0 direct versus 5 Sanctum on partial tasks. Four protocol failures split three direct and one Sanctum. Evidence-budget exhaustion is frequent in both arms and contributes to incomplete work: 57 direct versus 40 Sanctum attempts across all task scopes.

The earlier execution-only summary showed median elapsed times of 23.35 seconds direct and 20.67 seconds Sanctum. That observation does not establish better answers. Subscription SDK cost estimates are not invoices; judge inference and preparation are separate from the original agent-run cost comparison.

## Limits and next action

The study has one synthetic connected scenario, 30 tasks, same-model Sonnet judging, no completed human spot-check acceptance, and post-run scoring-policy repairs. Independent acceptance of twelve boundary/partial task gold records remains pending. Native run and score artifacts stay local; this Markdown summarizes them without publishing credentials or traces.

Next: examine task-level failure patterns and conduct the pending independent gold/human checks before changing routing or making adoption claims. Do not silently repair the failed judge record or rerun selected agent answers. Any later adjudication requires a separately recorded decision and preserved original evidence.

Sources: local `comparison-report.json`, `execution-summary.json`, `quality-evaluation-07/{scores,judge-failures,complete}.json`; [scoring contract](../lab/scoring.md), [review dispositions](quality-scoring-review-dispositions.md).
