# Jev at three retrieval decisions

## Question

Does using Jev after hub selection improve Claude's answers? This experiment keeps Jev hub selection active and adds passage relevance, conflict assessment, or both.

Claude still writes the answer. Jev helps Sanctum decide where to search, which retrieved passages to prioritize, and which passage pairs may disagree.

## What we ran

| Setup | Hub selection | Passage relevance | Conflict assessment |
|---|---|---|---|
| Baseline | Jev | Rules | Rules |
| Relevance | Same Jev selection | Jev | Rules |
| Conflicts | Same Jev selection | Rules | Jev |
| Both | Same Jev selection | Jev | Jev |

The same 12 development questions run once under each setup: **48 fresh Claude sessions**. Six questions have complete evidence, three have partial evidence, and three ask beyond the corpus boundary. This is a comparison between Sanctum configurations; there is no new direct-hub arm.

- **Agent:** Claude Sonnet 5.5, low effort, subscription authentication.
- **System One:** hosted `typesafe-jev`, resolved model `jev-1.13.0`.
- **Unchanged:** corpus, routing memory, hub descriptions, questions, rubric and limits.
- **Limits:** eight agent rounds, 8,000 cumulative evidence tokens, 4,000 per response and 120 seconds per task; 32 broker calls and 500,000 reserved input tokens per attempt.
- **Order:** setup order randomized within each task.

See the [implementation plan](pdlc-jev-entire-flow-plan.md) for configuration and verification details.

## What active advice means

All three steps apply raw positive probabilities at a threshold of 0.5. The new passage and conflict decisions are not silently recorded in shadow mode. Raw probabilities are experimental signals; they are not fitted confidence estimates.

- **Hub selection:** Jev chooses among all eligible hubs and can choose none. No routing override adds a hub back.
- **Relevance:** Jev changes passage order and can add qualifying passages when budget remains. It does not remove evidence already packed by the rules.
- **Conflicts:** Jev can promote a candidate pair to a possible conflict. It does not erase existing rule flags or generate arbitrary pairs.
- **No candidate pairs:** Sanctum does not call conflict assessment when there is nothing to assess.

These limits matter when interpreting the comparison. It tests the implemented decision points, rather than a replacement for every retrieval rule.

## Results

**All 48 agent attempts succeeded and all 48 answers were scored.** Reporting recomputed the scores from saved answers and judgments, with no binding issues. A successful execution does not mean a completed task.

Coverage is the average fraction of required facts established per task. It is not the percentage of questions answered correctly.

| Setup | Overall | Supported: 6 tasks | Partial: 3 tasks | Boundary: 3 tasks | Answers with material unsupported claims |
|---|---:|---:|---:|---:|---:|
| Hub selection only | 70.14% | 79.17% | 55.56% | 66.67% | 1 |
| Add relevance | 72.92% | 72.22% | 63.89% | 83.33% | 0 |
| Add conflicts | 84.72% | 95.83% | 63.89% | 83.33% | 1 |
| Add both | 70.83% | 79.17% | 41.67% | 83.33% | 1 |

The supported-task plan checklist averaged the maximum score of 2 in every dimension for the three added-decision setups. The baseline averaged 1.8 for validation and 1.5 for scope/dependencies, with 2 for the other dimensions. Supported-task citation support averaged 1.0 in every setup.

**Coverage and checklist scores are not full completion.** Provisional completion was 0/12 for the baseline and 1/12 for each other setup. Human acceptance remains pending.

### What actually happened in Jev?

| Setup | D2 HTTP calls | D4 HTTP calls | D6 HTTP calls | Positive relevance judgments | Additional conflict promotions |
|---|---:|---:|---:|---:|---:|
| Hub selection only | 17 | 0 | 0 | — | — |
| Add relevance | 19 | 18 | 0 | 128 of 158 | — |
| Add conflicts | 16 | 0 | 9 | — | 0 of 39 |
| Add both | 18 | 17 | 10 | 120 of 151 | 0 of 40 |

No provider decisions were unavailable and no question IDs were invalid. All 309 passage judgments and 79 conflict judgments were answered with shadow mode off. A positive relevance judgment does not necessarily add a new passage: the passage may already be packed by the rules.

**Conflict-only scored highest, but Jev promoted no conflict pairs.** That improvement cannot be attributed to additional conflict findings. The question set, one-shot agent variation, iterative retrieval and judging need inspection before calling it a conflict-detection benefit.

### How uncertain are these differences?

These paired differences compare each setup with this campaign's fresh hub-selection-only sessions. The descriptive intervals resample whole tasks, with 10,000 resamples and seed 42.

| Addition | Overall difference in percentage points | Descriptive 95% interval |
|---|---:|---|
| Relevance | +2.78 | −20.83 to +21.53 |
| Conflicts | +14.58 | +2.78 to +28.47 |
| Both | +0.69 | −25.69 to +23.61 |

These intervals describe this small sample; they do not include all agent-run or judge uncertainty. The conflict-only interval does not establish the proposed mechanism, since no extra conflicts were reported. This baseline is a new set of answers, so its score need not equal earlier runs on the same questions.

## Decision and next checks

**Keep the three decision points available, but do not promote a new default based on these results.** Wiring is verified; a consistent quality improvement is not established.

- Trace the supported-task losses in relevance-only and the partial-evidence losses when both decisions run.
- Compare delivered passages, ordering, missing facts and uncertainty statements before deciding whether to change Jev or memory.
- Add independently checked development cases that exercise actual conflict promotions, including true disagreements and harmless version differences. Keep later evaluation cases separate.
- Inspect the conflict-only gains for agent and grading variation; do not treat them as demonstrated conflict-assessment benefit.

## Execution and scoring recovery

The campaign paused after 34 successful attempts because accounting classified a two-batch conflict decision as unknown usage. Both saved HTTP responses were successful and supplied complete token counts. Their sum matched the broker trace.

The accounting fix accepts successful batches only with complete, matching receipts and disjoint question sets. Failed calls, retries and missing usage remain unknown. The original result and ledgers were preserved, and only accounting fields were reconciled; completed agent attempts were not replayed.

The scoring driver also now resumes an already-recorded format retry. It validates the saved retry against the same answer and rubric, rather than issuing another judgment. Original malformed reviews remain available.

Nine saved, valid retries were recovered after the streaming process used the earlier resume logic. The original failure record and a hash-bound reconciliation receipt are retained. No agent was rerun, no new recovery judgment was requested, and no rubric changed.

Verification: 93 integration/provider checks passed before dispatch, with two live-provider checks skipped; 57 accounting, session and scoring checks passed after the recovery fixes. Provider inference was verified separately in the hosted traces.

## Limits

- These are reused development questions, with one answer per question per setup.
- Independent acceptance of the task criteria and human acceptance of the answers remain pending.
- The semantic judge uses the same model family as the answering agent.
- Earlier grading disputes remain separate; this experiment does not settle them.
- Successful calls and positive judgments alone do not prove better answers.
- Findings do not establish production usefulness or generalization to real repositories.

## Local evidence

The detailed records are local, ignored artifacts; they are not included in the Git documentation pack.

| Path | Contents |
|---|---|
| `build/agent-bundles/pdlc-jev-entire-flow-01/` | Pinned inputs, four configurations and private criteria |
| `build/agent-runs/sonnet55-jev-entire-flow-01/` | Frozen schedule, original answers, traces and provider exchanges |
| Run's `accounting-reconciliation-01/` | Original accounting records and reconciliation receipt |
| Run's `quality-evaluation-01/` | Judge packets, original reviews, format retries and scores |
| Run's `scoring-resume-reconciliation-01/` | Original failure records and recovery receipt |
| Run's `jev-flow-summary.json` | Four-setup coverage and decision counts |
| Run's `baseline-vs-{relevance,conflicts,all-decisions}.json` | Three complete paired comparisons |

To rebuild the summary from the saved records:

```sh
PYTHONPATH=src:. .venv/bin/python tools/report_jev_flow.py \
  build/agent-bundles/pdlc-jev-entire-flow-01/experiment.yaml \
  --run build/agent-runs/sonnet55-jev-entire-flow-01 \
  --scores build/agent-runs/sonnet55-jev-entire-flow-01/quality-evaluation-01/scores.json \
  --policy build/agent-bundles/pdlc-jev-entire-flow-01/private/evaluation-policy.json
```

The multi-arm operational report's generic comparison-ready flag is not the authority for this analysis. The three explicit paired reports are complete, with no missing tasks.

[Back to results index](README.md)
