# Experiments: setup, findings and open questions

Start here to find what the lab has tested. **Coverage means required facts established, not tasks completed.** All findings below are exploratory: synthetic evidence, small task sets, and human acceptance pending.

## Choose what to read

| Need | Read |
|---|---|
| Understand how experiments are run | [Experiment method](method/README.md) |
| Understand the software and components | [Lab guide](../lab/README.md) |
| Find an experiment’s findings | The records below |
| Trace remaining answer gaps | [Rubric gap diagnosis](pdlc-rubric-gap-diagnosis.md) |
| Understand a scoring correction | [Scorer v3 audit](pdlc-scorer-v3-audit.md) |

## Results index

**Do not compare absolute scores across cohorts.** The first campaigns reuse 30 tasks with three attempts per task/setup. The follow-up uses 12 different questions with one attempt per question/setup.

| Experiment | Question and cohort | Main finding | Record |
|---|---|---|---|
| Direct hubs vs shadow Sanctum | Does Sanctum help without applying Jev skips? 30 tasks, 180 attempts | Corrected overall difference −2.69 points; interval includes zero | [Original comparison](pilot-0-quality-results.md) |
| Guarded Jev | Does calibrated advice help under the earlier routing rules? Same 30 tasks, 90 new attempts | Three proposed skips were overridden; original scoring showed +3.04 points vs shadow, with interval including zero | [Guarded findings](pdlc-jev-guarded-results.md) |
| Unconstrained Jev | What happens when Jev chooses among all eligible hubs? Same 30 tasks, 90 new attempts | Corrected coverage +13.06 points vs guarded; +13.63 vs direct. These are historical comparisons | [Unconstrained findings](pdlc-jev-unconstrained-results.md) |
| Scorer correction | Which grades change when two mechanical rules are repaired? 360 existing records | Apparent boundary regression was a grading artifact; no agent reruns | [Scorer v3 audit](pdlc-scorer-v3-audit.md) |
| Memory and descriptions | Which change helps Sanctum? 12 new tasks, four configurations, 48 attempts | Memory helped supported questions but hurt partial evidence; richer descriptions hurt supported coverage; nothing promoted | [Four-variant follow-up](pdlc-rubric-followup-results.md) |
| Jev at three decisions | Does adding passage relevance and conflict assessment help? Same 12 development questions, 48 fresh attempts | Mixed coverage; combined setup hurt partials. Conflict-only scored highest but promoted no conflicts; nothing promoted | [Entire-flow findings](pdlc-jev-entire-flow-results.md) |

“Points” means percentage points. Each record identifies its scoring version and comparison. Original scores remain available as superseded history.

## What is still unsettled?

- Independent acceptance of task criteria and human acceptance of answers remain pending.
- Some follow-up grades disagree with the supported meaning of the answer; investigate before calling every lost mark a routing failure.
- Changes to descriptions and memory have not been promoted.
- These experiments do not establish production usefulness or generalization to real repositories.

## Where new work belongs

- **Setup:** add methodology under `method/`, without result numbers.
- **Findings:** add a dated record and a row in this index. Use question, changes, cohort, results, limits and decision headings.
- **Plans and reviews:** preserve existing files as historical records. Their progress checkboxes are not the current results index.
- **Corrections:** identify what is superseded; retain the original result and link to the corrected record.

Historical entry points: [pilot readiness](pilot-0-readiness.md), [active-Jev plan](pdlc-jev-active-plan.md), [rubric improvement plan](pdlc-rubric-improvement-plan.md), [quality review dispositions](quality-scoring-review-dispositions.md). The documentation structure review lives separately in [reviews](../reviews/lab-docs-handover-review-20261005.md).
