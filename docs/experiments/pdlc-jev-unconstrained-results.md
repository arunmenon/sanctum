# Unconstrained Jev: development findings

Observed 5 October 2026. The current results below use the corrected v3 scorer. The original scoring is retained at the end and is superseded.

## Question

What happens when Jev chooses among all eligible hubs, without candidate-shortlisting, forced-source or nonempty-source overrides?

## What changed and what stayed constant

- **Changed together:** candidate selection, raw decision policy, selection overrides and broker capacity.
- **Held constant:** corpus, reviewed memory, agent model/effort and the original public tasks.
- **Decision rule:** Jev’s raw probability of usefulness at or above 0.5 selects the hub; below 0.5 skips it. No fitted calibration threshold applies.

## Cohort and scoring

**30 tasks × three repetitions = 90 unconstrained attempts**, compared with historical 90-attempt guarded and direct cohorts. Mix: 18 supported, six partial and six boundary tasks. All 90 unconstrained attempts finished and were scored without judge or agent-output protocol failures.

Scores are required-fact coverage. Repetitions are averaged within each task; intervals use 10,000 paired task resamples with seed 42. Do not compare these scores with the 12-question follow-up.

## Corrected results: unconstrained versus guarded

| Slice | Guarded coverage | Unconstrained coverage | Difference | Descriptive 95% interval |
|---|---:|---:|---:|---|
| Overall | — | — | +13.06 points | +5.07 to +21.41 |
| Supported | 76.08% | 90.86% | +14.78 points | +4.01 to +26.67 |
| Partial | 75.83% | 90.28% | +14.44 points | -2.78 to +32.22 |
| Boundary | 90.74% | 97.22% | +6.48 points | -5.56 to +20.37 |

The corrected scores show higher coverage in each slice. The earlier apparent boundary decline was a mechanical grading artifact, not an established quality regression.

### Comparison with direct hubs

The later recovery completed all 30 direct task pairs. Corrected overall coverage is **13.63 points higher** for unconstrained Sanctum; the descriptive interval is +7.33 to +20.39 points.

| Slice | Difference versus direct hubs |
|---|---:|
| Supported | +11.67 points |
| Partial | +13.70 points |
| Boundary | +19.44 points |

This is a historical-cohort comparison, not an isolated causal Jev effect. See [family-level gap diagnosis](pdlc-rubric-gap-diagnosis.md).

## Routing observations

| What was counted | Guarded | Unconstrained |
|---|---:|---:|
| Retrieval requests | 154 | 144 |
| Hub calls: searches and fetches | 881 | 1,768 |
| Jev source decisions | 134 active decisions | 576; 144 per hub |
| Applied skip recommendations | 0 of 3 proposed | 279 of 279 proposed |
| Retrieval requests with no hub calls | Not established here | 10 |

Considering every eligible hub roughly doubled backend work. These counts do not show savings. No source-selection overrides were observed in the unconstrained run.

## What this does not show

- An isolated effect from Jev: four parts of the setup changed together.
- Generalization beyond the reused development questions and synthetic corpus.
- Independent judging: the semantic judge uses the same model family.
- Accepted production readiness: independent gold and human acceptance are pending.
- A comparison free of historical timing/order differences.
- That every missing fact is a source-selection failure.
- Cost or call savings, or human-accepted task completion from coverage alone.

## Decision and evidence

Keep the quality signal and diagnose the remaining gaps. Do not turn these exploratory scores into a production-adoption claim.

| Local evidence | Purpose |
|---|---|
| `build/rubric-gap-audit/mechanical-v3-03/unconstrained-vs-guarded.json` | Current paired comparison |
| `build/rubric-gap-audit/mechanical-v3-03/unconstrained-vs-direct.json` | Complete direct-hub comparison |
| `build/agent-runs/sonnet55-jev-unconstrained-02/` | Original attempts, routing receipts and judgments |
| `build/agent-runs/sonnet55-jev-active-01/` | Guarded baseline |

These files remain local and ignored in Git. The [v3 audit](pdlc-scorer-v3-audit.md) records the scoring corrections; the [plan](pdlc-jev-active-plan.md#follow-on-jev-owns-candidate-selection) preserves setup history.

## Original scoring — superseded

The original table and its “boundary handling worsened” interpretation below are not the current findings. Agent runs and routing counts were preserved; corrected scoring is shown above.

<details>
<summary>Open the original scoring report</summary>

# Unconstrained Jev development results

**Scoring amendment:** The boundary and completion figures below describe the original mechanical scorer. The consistently rescored [v3 audit](pdlc-scorer-v3-audit.md) corrects those rules; its boundary coverage and comparisons supersede the original apparent decline. Agent runs and routing counts are unchanged.

Observed 5 October 2026. All 90 Sonnet 5.5 subscription attempts completed and all 90 answers were scored, with zero judge or agent-output protocol failures. This is an exploratory historical-cohort comparison against the preceding calibrated/guarded Sanctum run, not a frozen production acceptance result.

| Quality score difference, unconstrained minus guarded | Percentage points | Descriptive 95% interval | Tasks |
| --- | ---: | --- | ---: |
| Overall | +9.15 | +0.09 to +18.57 | 30 |
| Supported / in scope | +14.78 | +4.01 to +26.67 | 18 |
| Partial evidence | +12.50 | -12.50 to +31.94 | 6 |
| Out of scope | -11.11 | -22.22 to 0.00 | 6 |

Differences refer to graded rubric scores, not task-completion rates. Three repetitions are averaged within each task; intervals use 10,000 paired task-cluster bootstrap resamples with seed 42. Successful execution alone does not mean a task was correctly completed.

Jev made 576 raw source decisions across 144 retrieval requests: exactly 144 decisions for each of CodeHub, DocHub, SkillHub and MemoryHub. All 279 skip recommendations corresponded to no observed call to the skipped hub. Ten retrieval requests made zero hub calls. There was no source-selection override. Total backend hub tool calls rose from 881 to 1,768, including searches and fetches, despite fewer retrieval requests (154 versus 144). Considering previously excluded sources expanded the work; these counts do not establish savings.

The supported-task quality increase is encouraging, but boundary handling worsened and backend work approximately doubled. The experiment changed candidate policy, raw decision policy, source overrides and broker capacity together. Historical timing/order, reuse of development tasks, a same-model judge, and pending independent gold/human acceptance limit attribution. It does not isolate a causal Jev benefit or establish superiority over direct hub access.

Evidence: `build/agent-runs/sonnet55-jev-unconstrained-02/active-vs-shadow-report.json`, `quality-evaluation-01/complete.json`, and each original attempt's result, MCP receipt and saved semantic review. Baseline: `build/agent-runs/sonnet55-jev-active-01/`. Original shadow and direct cohorts remain unchanged. See the [experiment plan](pdlc-jev-active-plan.md#follow-on-jev-owns-candidate-selection) for mode semantics and the preserved retired first campaign.

</details>

[Back to results index](README.md)
