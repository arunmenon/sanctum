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
