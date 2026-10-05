# Mechanical scorer v3 audit and correction

This is a scoring-policy correction, not a new product experiment. The current comparison summaries are in the [results index](README.md).

## Complete-cohort update — current

The missing direct-hub judgment was recovered on 5 October with one recorded schema-repair judge call, preserving its original packet and failed response. This exception involved no agent rerun and supersedes the earlier incomplete-comparison status below. The merged recovery lives in `quality-recovery-01/` under the original run, and all 360 records were rescored separately in `build/rubric-gap-audit/mechanical-v3-03/`.

**30 tasks × three repetitions per setup**, with the original semantic judgments and recorded recovery under the v3 mechanical policy.

| Unconstrained minus direct access | Difference |
|---|---:|
| Overall | +13.63 percentage points |
| Supported | +11.67 points |
| Partial | +13.70 points |
| Boundary | +19.44 points |

The overall descriptive interval is +7.33 to +20.39 points. Limits still apply:

- Historical campaign timing and order differ.
- The semantic judge uses the same model family.
- Independent and human acceptance remain pending.

The [gap diagnosis](pdlc-rubric-gap-diagnosis.md) separates task-family results and remaining failure causes.

## What changed

The 0/1/2 checklist scale is unchanged. Two mechanical criteria were corrected:

1. An evidence-delivery budget flag no longer automatically prevents provisional completion. Required facts, supported citations, mandatory plan items, uncertainty, caller requirements, observed investigation, execution success and answer-declared unmet requirements still determine completion. The flag remains separately reported as `evidence_delivery_limited`.
2. A boundary diagnosis may use supported factual premises as well as boundary-typed claims. Factual premises still require valid, semantically entailing delivered citations. A correct diagnosis must still be marked met, relevant, supported, uncontradicted and based on successful investigation of the required source. Recommendations, unsupported premises, failed or irrelevant investigation, and generic refusal receive no automatic boundary credit.

Version: `mechanical-v3-boundary-support-completion`. Judge packets, semantic judgments, task gold, agent answers and runs were not changed. This is a scoring-policy repair, not a new product experiment. Blind-judge visibility of operational metadata is still a separate unresolved audit; no new judge calls were made.

## Initial verification and rescoring — before the recovery

46 focused checks passed, including successful and unsuccessful content under a delivery limit, mixed boundary/factual premises, nonentailing and uncited premises, irrelevant/failed investigation, stale bindings and report preservation.

359 available original score records were recomputed across the original direct/shadow campaign and the two subsequent Sanctum cohorts. The four original agent-output protocol failures remain zero; the original unscored direct-arm judgment remains unknown. Every recomputed score retained the original answer, attempt, gold, judge-packet and semantic-review hashes. Reports independently recomputed score derivations and found no binding issues. Original files and reports were preserved. No agent reruns or inference calls occurred. The failed first offline command encountered a protocol-failure score without a `fact_credit` field; the runner was corrected to handle that existing schema, and version `mechanical-v3-02` completed.

## Revised rubric results

**Cohort: the original 30 tasks, with three attempts per task/setup.** This table compares the historical guarded and unconstrained cohorts using the same v3 mechanical policy. It does not describe the later 12-question follow-up.

| Required-fact coverage | Calibrated / guarded | Unconstrained |
| --- | ---: | ---: |
| Supported tasks | 76.08% | 90.86% |
| Partial evidence | 75.83% | 90.28% |
| Out of scope / precise boundary diagnosis | 90.74% | 97.22% |

The earlier apparent out-of-scope decline (26.85% to 15.74%) was driven by the mechanical claim-type rule; it is superseded by this consistently rescored comparison. This does not imply that every boundary answer is perfect. Supported-task coverage is unchanged. Checklist scores and original material-unsupported-claim incidence are unchanged because semantic judgments were reused.

Overall unconstrained versus guarded: +13.06 percentage points, descriptive paired task-cluster bootstrap interval +5.07 to +21.41 points. Versus original shadow mode: +16.31 points, interval +6.85 to +26.26. These remain exploratory historical-cohort comparisons with pending human/independent-gold acceptance. At this earlier audit stage, the direct comparison was incomplete. That status is superseded by the complete-cohort recovery at the top of this page; the original missing judgment was recovered without an agent rerun.

Provisional supported-task completion is 31/54 for unconstrained, 21/54 for guarded, 23/54 for original shadow and 23/54 for direct access. These are answer attempts across repetitions, not independent task counts, and none constitutes human acceptance. Across all unconstrained scopes, 33 answers are provisionally complete. Some accurately diagnosed boundary/partial responses still declare original caller requirements unmet, so coverage and full completion must remain separate measures.

## Reproduction and evidence

`tools/rescore_saved_quality.py` takes a JSON specification containing policy, cohort bundle/run/original-score paths, and comparisons. It never invokes an agent or judge, refuses changed evidence bindings and writes a new output directory. `tools/report_agent_run.py` supports an explicit `output_path` so versioned validation does not overwrite historical reports.

Local outputs: `build/rubric-gap-audit/mechanical-v3-02/complete.json`, `changes.json`, per-cohort `scores.json` and validated `report.json`, and three comparison files. Input specification: `build/rubric-gap-audit/rescore-spec.json`. Original evidence remains under the original run directories. Artifacts remain local and ignored in Git; source, tests and this report are versioned.

## Remaining work

Trace missing supported facts and plan/uncertainty gaps using the corrected scores. Resolve true versus invented operational metadata claims through original receipts before changing judge visibility. Then choose System One and routing-memory changes from that evidence, retaining unconstrained Jev selection and verifying their effects on fresh development and held-out tasks. No call-count optimization is a current objective.

[Back to results index](README.md)
