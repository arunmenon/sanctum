# Guarded Jev: development findings

Recorded from the calibrated campaign completed before the unconstrained experiment. This separates findings from the preserved [active-Jev plan](pdlc-jev-active-plan.md).

## Question

Does applying calibrated Jev advice improve Sanctum while the earlier routing rules still control candidates and overrides?

## What changed and what stayed constant

- **Changed:** a matching development calibration and its runtime binding.
- **Held constant:** corpus, reviewed memory, agent configuration and the original 30 questions.
- **Still enforced:** required-source obligations and the nonempty-source fallback.

## Cohort and results

**30 tasks × three repetitions = 90 new attempts**, compared with 90 historical shadow attempts. The table below preserves the original scoring version; it is not a new v3 estimate.

| Measure | Finding |
|---|---|
| Original overall coverage difference vs shadow | +3.04 percentage points |
| Original descriptive 95% interval | −1.13 to +7.41 points; includes zero |
| Active source decisions | 134 |
| Proposed skips | 3 |
| Applied skips | 0; all three overridden by the nonempty-source rule |
| Hub calls | 881 guarded, versus 852 shadow |

## What this shows

Calibration was active, but the run did not demonstrate Jev-driven hub skipping. More calls and a small uncertain coverage difference do not establish source-selection benefit.

## Limits and decision

- The comparison uses historical shadow runs, so timing and order differ.
- Judging uses the same model family; independent and human acceptance remain pending.
- The original quality figures were later subject to mechanical rescoring.

The next experiment gave Jev control over eligible candidates. Read the [corrected unconstrained results](pdlc-jev-unconstrained-results.md) and [v3 audit](pdlc-scorer-v3-audit.md), rather than treating this original table as the final scoring policy.

Evidence: the preserved [plan’s follow-on section](pdlc-jev-active-plan.md#follow-on-jev-owns-candidate-selection) and local `build/agent-runs/sonnet55-jev-active-01/` records. Raw records remain local.

[Back to results index](README.md)
