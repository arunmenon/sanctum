# Direct hubs versus shadow Sanctum: findings

## Question

Does Claude answer better through Sanctum when Jev’s uncalibrated skip advice is recorded but not applied? This is the original two-arm comparison, not the later unconstrained experiment.

## What changed and what stayed constant

- **Changed:** Claude’s tool surface: direct hub tools versus Sanctum retrieval.
- **Held constant:** the synthetic corpus, public questions, private criteria, agent configuration and shared agent limits.
- **Jev behavior:** real calls in the Sanctum arm, without the intended source-pruning effect.

## Cohort and scoring

**30 tasks × two setups × three repetitions = 180 attempts.** Task mix: 18 supported, six partial and six out of scope. All attempts finished. Four agent-output protocol failures remain zero-credit; a missing direct judgment was recovered without an agent rerun.

The table uses the corrected v3 scoring policy and all 30 task pairs. Do not compare these absolute scores with the later 12-question follow-up.

## Corrected results

Differences are shadow Sanctum minus direct hubs, in percentage points. These are required-fact coverage differences, not completion rates.

| Slice | Tasks | Difference | Descriptive 95% interval |
|---|---:|---:|---|
| Overall | 30 | -2.69 | -14.13 to +8.83 |
| Supported | 18 | -6.73 | -19.94 to +6.91 |
| Boundary | 6 | +9.26 | -25.00 to +38.89 |
| Partial | 6 | -2.50 | -26.39 to +22.78 |

All intervals include zero. This comparison does not establish a quality winner. The supported-task estimate favors direct access; it is not proof of a general advantage.

## Limits

- One synthetic scenario and a small task set.
- Same-model semantic judging and post-run scoring-policy repairs.
- Independent task-gold acceptance and human answer acceptance pending.
- This tests shadow Sanctum, not Jev-driven candidate selection.

## Decision and evidence

Keep this comparison as the historical baseline. Use the [unconstrained record](pdlc-jev-unconstrained-results.md) for the later Jev-selection comparison.

Local source: `build/rubric-gap-audit/mechanical-v3-03/original/report.json`. The source is ignored in Git; public summaries do not publish raw answers or credentials. See the [scorer audit](pdlc-scorer-v3-audit.md) for the recorded judgment recovery.

## Original scoring — superseded

The original 2026-10-04 report below is retained for audit history. Its missing-grade status and completion figures are superseded by the v3 correction and recorded recovery above.

<details>
<summary>Open the original report</summary>

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

</details>

[Back to results index](README.md)
