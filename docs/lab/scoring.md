# Scoring and interpreting results

This page owns quality criteria. Completing a native process is an operational outcome; task quality is assessed separately. The [runbook](runbook.md) owns scorer commands.

## Reference/world scoring

[sanctum_eval.metrics](../../src/sanctum_eval/metrics.py) evaluates retrieved evidence, conflicts, source obligations and safe grounded success using private gold plus observed traces. World gold is derived from authored world facts; M0 uses hand-authored fixture gold. These metrics evaluate the retrieval response, not a Claude-written design plan. See [measurement-plan.md](../measurement-plan.md) for the reference experiment's detailed measurement definitions.

## Agent mechanical and semantic scoring

The answer format has `schema_version`, prose `answer`, `claims` with IDs/text/citations, `uncertainties` and `unmet_requirements`. Phrasing need not match an answer key. [agent_score.py](../../src/sanctum_run/agent_score.py) uses distinct checks:

| Check | What earns credit |
|---|---|
| Protocol and citations | Parseable envelope; correct source/artifact/version/span/hash; passage actually delivered to this attempt |
| Required facts | Judge finds the meaning established, supported by declared claims and entailing delivered citations |
| Boundary facts | Precise missing-evidence diagnosis, relevant observed investigation and configured source obligations; generic refusal is insufficient |
| Whole-answer grounding | Inspect prose beyond the declared claim list for fabricated or uncited facts and contradictions |
| Plans | Score each dimension 0 absent/wrong, 1 partial with named gap, 2 all task-specific mandatory items coherently met |
| Completion | All required facts, supported citations, full required plan, uncertainties/caller obligations, no material unsupported claims or unresolved contradictions, observed retrieval and no exhausted-evidence condition |

HLD anchors concern responsibilities, boundaries, dependencies and reasoned tradeoffs. LLD anchors concern interfaces, data/state flow, failures, compatibility and observable tests. Multiple sound proposed designs can satisfy the rubric. Claims about existing systems require evidence; recommendations must distinguish proposed choices from implemented behavior.

Semantic packets include the public task, private criteria, neutral evidence inventory and investigation context, without arm/tool/cost identifiers. Each review is bound to a packet hash; schemas require per-item labels and reasons. Mechanically valid citations are not automatically semantically supporting citations.

## Failures and acceptance

Only a strict outer JSON fence may be removed. Invalid JSON is a zero-credit protocol failure, retained in the denominator. Do not rewrite an agent answer, manufacture a citation or rerun a poor answer to improve the result.

The quality driver permits one policy-declared schema retry for malformed judge output, preserving the first response and error. It does not relax scoring gates or assign missing semantic labels itself. After an exhausted schema retry, the driver records an unknown review failure and continues other judgments. The report remains incomplete where grades are missing; no agent-quality zero is invented. Calibration disagreement is a gate to investigate, not permission to pick the nicer grade.

`provisional_task_complete` is distinct from `task_complete`. Human acceptance requires a pinned human-reviewer registry and a receipt bound to the answer, gold, attempt and review. Independent acceptance of task gold is another prerequisite. The current PDLC judge is Sonnet 5.5 low judging Sonnet answers: same-model bias and post-run scoring-policy repairs must be disclosed. Human spot checks and all boundary-gold acceptance are still pending; this is exploratory development scoring.

## Comparison rules

[report_agent_run.py](../../tools/report_agent_run.py) validates saved bindings and, with a quality policy, recomputes scores from saved reviews before aggregation. Report supported-fact coverage, citation support, unsupported claims, plan scores, provisional completion, reliability, cost and latency together. Keep supported, partial and out-of-scope strata separate so successful refusals cannot hide weak supported answers.

Average repetitions within each task/arm, then compare paired task differences. The seeded bootstrap resamples tasks, not individual facts or repeated runs. Thirty tasks within one scenario support directional findings; they do not resolve a narrow noninferiority margin or establish production adoption. Missing or invalid comparisons are labeled rather than silently dropped.

Next: [runbook](runbook.md), [rubric fixtures](../../tests/fixtures/agent-score-cases.json), [quality review dispositions](../experiments/quality-scoring-review-dispositions.md).
