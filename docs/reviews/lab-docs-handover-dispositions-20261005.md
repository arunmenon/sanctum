# Documentation handover review: changes applied

Applied the supplied two-pass Claude/Fable review on 5 October 2026. The [original review](lab-docs-handover-review-20261005.md) is preserved unchanged. This is an implementation record, not another independent review.

## Handover findings

| Finding | Applied change |
|---|---|
| 1. Missing results index | Added `docs/experiments/README.md`, with five experiment entries and a direct-hub comparison link |
| 2. Superseded unconstrained scores led the page | Put v3 results first; retain original scoring in a collapsed, explicitly superseded section |
| 3. Cross-cohort confusion | Put cohort descriptions before tables and warn against comparing the 30-task and 12-question scores |
| 4. Stale System One budget | Show original/guarded and unconstrained/follow-up broker limits separately, with the method guide as the setup reference |
| 5. Modes not traceable to runs | Link each mode to its result record and explain raw selection at 0.5 |
| 6. Setup and findings mixed | Added `experiments/method/README.md`; moved campaign-specific scoring status out of the general scoring guide; split guarded findings from the historical plan |
| 7. Dense reference pages | Completion checklist, failure-handling table, term definitions, concrete link examples and clearer storage explanation |
| 8. Time-bound heading and local driver details | Renamed reading-order heading; placed driver limitations in a dedicated “Not portable yet” section |
| 9. Mixed experiment archive | Added categorized navigation for setup, findings, plans, reviews and corrections; existing historical file URLs remain stable |

## Scanability fixes

- Scoring: short definitions, two completion levels, an explicit checklist and failure table.
- Runbook: real-run prerequisites split into general and Sanctum-specific lists.
- System One: mode/result table, selection diagram, unconstrained rules as bullets.
- Results: routing counts in a table; limits and decisions as separate lists.
- Routing memory: define subject and selector before link types; examples before storage details.
- Architecture: define gateway, broker, arm and release before the inventory; four numbered retrieval steps.
- Harness: separate settings the operator chooses from checks the harness performs.
- Corpus: give tool responsibilities their own table.
- Quickstart: visible expected-output lists, explicit fixture completion explanation and an offline troubleshooting table.
- Start page: stable reading order and separate links to experiment method and findings.

## Accuracy checks

- Read raw-selection handling in `pipeline.py` and `providers/http_systemone.py`: the unconstrained path uses `p_raw >= 0.5` without calibration or selection overrides.
- Checked current comparison numbers against local validated v3 report files. The original shadow/direct complete-cohort difference is −2.69 points; unconstrained/guarded is +13.06; unconstrained/direct is +13.63.
- Kept guarded +3.04 as explicitly original scoring, rather than implying it is a new v3 comparison.
- Preserved material-unsupported-claim and unmet-requirement conditions in the completion checklist; did not copy looser shorthand from the proposed rewrites.
- Preserved original reports and historical plans. No agent answers, rubric criteria, judgments or runtime behavior changed.

## Verification

- Twenty Markdown entry/guide/record files: 164 relative links and anchors resolved; code fences balanced.
- `git diff --check` passed.
- Offline shipping fixture validated, scheduled and completed with `fixture: true`, `task_complete: false`; no Claude or Jev calls.
- Local fixture output: `build/docs-handover-20261005/shipping-run/` (ignored in Git).
- Browser checks follow publication; their outcome is recorded below.

## Remaining research limits

Raw experiment evidence is local, not published in Git. Independent task-gold acceptance, human answer acceptance and the follow-up grading-disagreement audit remain pending. These documentation changes do not resolve those research questions.
