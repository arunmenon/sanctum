# PDLC rubric follow-up: isolated descriptions and place memory

## Question

Can Sanctum answer better by changing the information it uses to find evidence? This compares four Sanctum configurations, not a new direct-hub baseline.

## What changed and what stayed constant

- **Variants:** unchanged Sanctum, richer hub descriptions for Jev, reviewed place-memory mappings, and both changes together.
- **Held constant:** corpus, public prompts, rubric, agent configuration and resource limits.
- **Selection:** raw unconstrained Jev in every variant.
- **Order:** randomized variant order.

## Cohort and scoring

**12 new questions × four configurations × one attempt = 48 runs.** Mix: six supported, three partial and three boundary questions. All 48 finished and were scored.

These are different questions from the earlier 30-task campaigns. **Do not compare their absolute scores across pages.** The questions were technically reviewed but independent human/gold acceptance remains pending.

## Coverage and unsupported claims

| Variation | Overall | Supported (6 tasks) | Partial (3 tasks) | Boundary (3 tasks) | Answers with material unsupported claims |
| --- | ---: | ---: | ---: | ---: | ---: |
| Unchanged Sanctum | 73.61% | 77.78% | 55.56% | 83.33% | 0 |
| Richer Jev descriptions | 65.28% | 52.78% | 55.56% | 100.00% | 1 |
| Reviewed place memory | 84.03% | 95.83% | 44.44% | 100.00% | 0 |
| Both changes | 65.28% | 52.78% | 55.56% | 100.00% | 2 |

## What we learned

| Change | Signal | Remaining concern |
|---|---|---|
| Memory only | Supported coverage rises from 77.78% to 95.83% | Partial-evidence coverage falls from 55.56% to 44.44% |
| Richer descriptions | No supported-task improvement | Supported coverage falls to 52.78%; one answer has material unsupported claims |
| Both changes | Memory does not recover the description decline | Two answers have material unsupported claims |

### How uncertain is the overall difference?

Differences below are percentage points versus unchanged Sanctum. These descriptive intervals resample whole tasks and all include zero.

| Variation | Difference | Descriptive 95% interval |
|---|---:|---|
| Memory only | +10.42 | −2.78 to +23.61 |
| Richer descriptions | −8.33 | −26.39 to +9.72 |
| Both | −8.33 | −26.39 to +9.72 |

Six supported and three questions per other slice are too few to establish reliable family effects or a narrow quality margin.

### Coverage is not completion

The full checklist also checks uncertainty and declared unmet requirements.

| Configuration | Provisionally complete answers |
|---|---:|
| Unchanged | 1/12 |
| Richer descriptions | 1/12 |
| Memory only | 0/12 |
| Both | 0/12 |

These are automated completion results, not human-accepted task success.

## Decision

**Do not promote any variation yet.** Keep the existing active configuration.

- Diagnose the partial-evidence regression in memory-only.
- Diagnose the supported-evidence failures in description variants.
- Check grading disagreements before treating every missing credit as a product failure.
- Retain the negative results; make changes only where traces identify a specific mechanism.

## Scoring recovery and verification

Saved records were preserved during recovery:

1. The first workflow scored 47 answers, then reporting failed because `sys` was imported only in the CLI entry point. Moving that import to module scope fixed embedded invocation.
2. The replacement evaluation reused saved judgments and fifteen exact-match calibration packets. It did not rerun agents or invoke new fixture inference.
3. One remaining judge reply added three plan dimensions to a behavior task whose frozen checklist was empty, even after its format retry.
4. A recorded format repair removed only those inapplicable annotations. Fact, claim, citation, severity and contradiction labels remained unchanged.
5. Final reporting recomputed scores and validated evidence bindings. No new judge call or rubric change was made for that repair.

### Local evidence

All paths below sit under `build/agent-runs/sonnet55-rubric-followup-01/` and are ignored in Git.

| Record | Purpose |
|---|---|
| `quality-evaluation-03/` | Final saved judgments and scores |
| `quality-format-recovery-01/format-repair-receipt.json` | Exact format repair and preserved originals |
| `followup-summary.json` | Four-configuration summary |
| `baseline-vs-{system-one,memory,combined}.json` | Three complete paired comparisons |

The explicit paired reports establish comparisons. The general multi-arm report is operational; its generic comparison-ready field is not the authority for this four-arm analysis.

## Limits and next work

- One attempt per configuration on twelve same-corpus tasks.
- Technical task acceptance by Codex, with shared premises disclosed.
- Same-model semantic judge; independent gold and human acceptance pending.
- Fresh questions do not establish independent generalization.
- Follow-up fact-versus-recommendation grading disagreements remain under investigation.

For each miss, inspect selected hubs, search filters, delivered evidence, Claude’s answer and the judge’s credit. Keep Jev unconstrained and answer quality as the objective.

[Back to results index](README.md) · [Experiment method](method/README.md)
