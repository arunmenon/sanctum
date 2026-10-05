# PDLC rubric improvement plan

## Objective

Improve required-fact coverage, supported design/planning quality, and precise handling of missing or conflicting evidence. Extra backend calls are not a current optimization target. Keep Jev free to select all four hubs or none; do not reintroduce a rules shortlist, forced sources, calibration gate or nonempty fallback.

Use saved runs before dispatching more agents. Separate scoring problems from retrieval, memory and answer-generation failures. Preserve original results and evaluate any scorer repair on every comparison arm under a new version.

## Current rubric position

### Execution update: 5 October 2026

- [x] Recover the missing direct-hub judgment with one explicitly recorded format repair; preserve the failed response, original packet and original reports.
- [x] Recompute all 360 score records with mechanical v3 and validate their evidence bindings. The complete unconstrained-versus-direct comparison is +13.63 percentage points overall, with a descriptive task-cluster interval of +7.33 to +20.39. This remains an exploratory historical comparison.
- [x] Produce family/scope/design breakdowns and a trace-backed ledger: 37 gap observations across 16 tasks, not 37 independent failures.
- [x] Prepare four isolated development variants: unchanged unconstrained routing, richer grounded Jev descriptors, operational reviewed place mappings, and both changes.
- [x] Validate the four descriptor proposals against 30 exact source quotations. Review 142 grounded SELECTS_FOR assertions, projecting 52 operational places into a separate experimental release. This is Codex technical curation with inherited prior review decisions, not independent human acceptance.
- [x] Pass 28 focused gap-tool, harvest, runtime and unconstrained-routing checks, including false target-credit cases.
- [x] Complete paired retrieval probes on 36 separate development cases per variant (144 total). These measure target-source selection and exact bound target-quote delivery, not answer quality. Baseline and memory recall 24/36 targets; descriptions and combined recall 20/36. Rich descriptions improve MemoryHub targets from 5/10 to 7/10 but reduce SkillHub from 8/10 to 3/10. No candidate is promoted from this result.
- [x] Author and technically verify 12 fresh development tasks: two per family, six supported, three partial and three outside scope, including explicit HLD and LLD. Check historical/development evidence overlap and verify every boundary against all 120 artifacts. Repair family drift, remove a repeated index fact and disclose shared premises. New questions on the same corpus do not establish independent generalization; independent acceptance is pending.
- [x] Run and score all 48 answers across the four variants on identical fresh tasks and budgets. All agent runs completed; all scores and three paired comparisons are validated. See the [follow-up results](pdlc-rubric-followup-results.md).
- [ ] Diagnose the memory-only partial-evidence regression and the descriptor-induced supported-task failures before proposing another change or promoting a release.

The 48-attempt follow-up has started: twelve tasks, one fresh session per variant, randomized variant order within each task. The unchanged baseline is rerun alongside the three variations, avoiding a historical-only comparison. Sonnet 5.5 uses the approved subscription; Jev remains raw/unconstrained in every arm. The subscription SDK-estimate ceiling is $144, not an Anthropic API purchase; nested Jev rate-card exposure is bounded at $1.008. Scoring and paired reports are queued automatically after all scheduled outcomes are terminal. Existing calibration judgments are rechecked for exact packet equality and mechanically regraded before reuse; no fresh fixture calls are intended. All trial input validation passed before dispatch.

Predeclared decision rule for this small follow-up: report paired graded fact coverage by scope, checklist quality, citation support and material unsupported claims. A variation is promising only if coverage improves without new material unsupported claims or a decline in boundary diagnosis; otherwise revise or reject it. Report effect sizes and uncertainty, not a production win. The 36-case probes are diagnostic and cannot satisfy that answer-quality rule. Extra calls are not a rejection criterion.

Local evidence: `build/rubric-gap-audit/mechanical-v3-03/`, `trace-analysis-03/`, `descriptor-candidate-01/`, `place-memory-01/`, `variants-01/`, `retrieval-probes-01/`, `fresh-task-curation-01/`, `build/agent-bundles/pdlc-rubric-followup-01/`, and `build/agent-runs/sonnet55-rubric-followup-01/`. Historical bundles and active releases are unchanged.

Verified from the saved calibrated/guarded and unconstrained reports and score files on 5 October 2026. These are development results; independent gold and human acceptance remain pending.

| Dimension | Calibrated / guarded | Unconstrained | Meaning |
| --- | ---: | ---: | --- |
| Supported required-fact coverage | 76.08% | 90.86% | 54 answers, 18 tasks per arm |
| Partial-evidence fact coverage | 62.78% | 75.28% | 18 answers, 6 tasks per arm |
| Out-of-scope rubric coverage | 26.85% | 15.74% | Boundary diagnosis credit, not percentage of factual answers |
| Supported-answer citation support | 98.02% | 99.54% | Scorer-validated support for cited claims |
| Supported answers with material unsupported claims | 7 / 54 | 2 / 54 | Incidence, not number of claims |
| Proposed-change checklist score | 1.50 / 2 | 2.00 / 2 | Applicable supported planning tasks |
| Scope/dependencies checklist score | 1.67 / 2 | 2.00 / 2 | Applicable supported planning tasks |
| Validation checklist score | 1.78 / 2 | 2.00 / 2 | Applicable supported planning tasks |
| Rollout/recovery checklist score | 1.89 / 2 | 1.89 / 2 | Applicable supported planning tasks |
| Uncertainty checklist score | 1.33 / 2 | 1.67 / 2 | Applicable supported planning tasks |

Checklist means apply only to tasks containing that dimension; they do not imply every task is a design task. Partial-evidence uncertainty stays at 1.00 / 2. Aggregate gains are not sufficient to establish task completion.

## 1. Audit scorer validity before interpreting the gaps

- [x] Inspect dimension reports, score derivations and representative saved semantic reviews.
- [x] Audit the claim-type mechanism and consistently rescore all available original judgments; detailed case disposition remains part of the failure ledger. Trace all semantic/mechanical fact-credit disagreements, retaining the exact rule that withheld credit. In the unconstrained run, the judge marked facts met but the mechanical score withheld credit on 35 out-of-scope, 12 partial and 5 supported fact assessments. These counts are assessments across repetitions, not unique tasks; some withholding may be correct.
- [x] Correct and verify mixed factual/boundary premise handling. Example: `fraud-batch-client-behavior-v2` is out of scope because deployed state is unknown. The judge marked both boundary facts met, but referenced claims were labeled factual; the scorer requires every associated claim to be boundary-typed and therefore grants zero. Determine whether the label or the scoring rule is wrong; do not simply grant all disputed credit.
- [x] Audit and correct the completion gate in `src/sanctum_run/agent_score.py`. All 90 unconstrained answers have provisional completion false. Forty-three meet the simpler check of full fact coverage, full checklist items/scores and no material unsupported claim; all 43 have an evidence-budget flag. The real completion gate additionally checks contradictions, citations, uncertainties, caller requirements and unmet requirements. Establish which conditions actually block each answer. Hitting a delivery limit must not automatically be treated as substantive task failure without an agreed rubric justification.
- [ ] Audit judge visibility of retrieval metadata. Reviews flag budget/conflict/receipt statements as unsupported because the blinded packet omits those fields. Verify whether the statements are true in saved traces. If relevant, supply neutral metadata consistently without revealing the arm; retain penalties for invented metadata.
- [x] Version mechanical criteria, preserve unchanged judge packets and judgments, and regrade all available cohorts. If policy changes are justified, version the scorer/packet, validate positive and negative cases, and regrade every cohort consistently. Keep old scores and publish the effect of the correction separately from product improvements. Do not modify task gold to fit answers.

## 2. Build a failure ledger grounded in traces

The [first gap diagnosis](pdlc-rubric-gap-diagnosis.md) records the completed family breakdown and representative cases. Its evidence and candidate tests are tracked in the execution checklist above.

For every missing required fact, incomplete plan item and material unsupported claim, record the task/repetition, rubric item, gold evidence, source decision, query/alias/selector, fetched passages, delivered passages and judge rationale. Classify: source not selected; wrong query/subject; evidence fetched but omitted; relevant evidence delivered but answer missed it; missing corpus evidence correctly diagnosed; or scoring dispute. Gold evidence identifies an investigation target; absence of its exact artifact alone is not proof that alternate supporting evidence was unavailable.

Start with distinct examples covering HLD, LLD, implementation/testing, rollout and partial/out-of-scope questions. For `payment-authorization-testing-v2`, one saved review credits timeout regression and retry arguments but withholds the client exception-conversion fact: the answer says the client source was not retrieved and does not establish conversion of a requests timeout to `FraudServiceTimeout`. Trace why the handler/client dependency did not yield delivered support before choosing a fix.

Deliver a task-by-rubric matrix and a small case pack explaining success and failure in plain language. Do not prioritize calls or latency over rubric quality.

## 3. Improve System One where evidence supports it

Hypotheses to test on development examples, without changing the frozen historical run:

- Improve hub descriptors and decision questions so usefulness covers the entire request: current behavior, dependencies, design constraints, tests and uncertainty, rather than keyword overlap alone.
- Expose resolved subjects and grounded dependency/context descriptions to Jev when the failure ledger shows the query lacks that context. No gold facts or expected source labels go into runtime state.
- Investigate decomposing multi-part PDLC requests into evidence needs and composing their source decisions. Jev still owns source selection; no must-consult override.
- For boundary tasks, distinguish useful contextual evidence from evidence that establishes current deployment or an approved contract. Source usefulness is not proof of fact availability.

Make the smallest change justified by actual misselection or query failures. Do not assume every missed fact is a classifier failure.

## 4. Improve routing memory where evidence supports it

- Audit canonical subjects, aliases, repo/module/service ownership and artifact-to-subject bindings for failed cases against the HLD ontology and source spans.
- Check version/status distinctions: deployed versus draft, current versus historical, proposed versus implemented, and known versus unavailable. Unknown deployment facts remain unknown.
- Verify cross-repo dependencies and document-to-code links are represented by the existing ontology where supported. If a missing relationship requires an ontology extension, document the evidence and HLD change before adding it.
- Improve grounded retrieval vocabulary and dependency traversal when a resolved handler question needs its client, configuration, contract or test evidence. Memory supplies context to Jev and search; it does not force hubs in this experiment.
- Reuse the existing harvest/propose/validate/review/release pipeline. Do not manually seed evaluation answers, convert speculative notes into authority, or invent artifacts to make out-of-scope questions answerable.

## 5. Validate attribution and rubric outcomes

After the scorer audit and failure ledger, declare the selected hypotheses and numeric targets before further paid runs. Keep the current unconstrained cohort as the historical baseline. Compare a System One-only change, a memory-only change, and their combination where both are justified. Each arm uses the same model, corpus, prompts, rubric and resource limits; record all routing decisions and saved answers.

Use separate development facts for tuning, then fresh held-out tasks with explicit HLD/LLD, partial evidence and boundary cases. The reused thirty tasks can diagnose regressions but cannot establish generalization. Report coverage, citation support, checklist items and unsupported-claim incidence separately by scope and task family. Treat the joint arm as the package effect; attribute improvements only where the isolated comparisons support it.

Completion: deliver an audited rubric report, evidence-backed failure ledger, selected changes and verification, and a versioned comparison showing which gaps improved, remained or regressed. Human acceptance remains an explicit status, not a reason to halt authorized analysis.

## Evidence locations

- `build/agent-runs/sonnet55-jev-unconstrained-02/comparison-report.json`
- `build/agent-runs/sonnet55-jev-unconstrained-02/quality-evaluation-01/scores.json` and per-attempt semantic reviews
- `build/agent-runs/sonnet55-jev-active-01/comparison-report.json`
- [Unconstrained results](pdlc-jev-unconstrained-results.md)
- [Implementation and experiment plan](pdlc-jev-active-plan.md)

## First scorer audit: completion gate

The exact gate replay found 33 of 90 answers satisfy every implemented completion condition except `budget_exhausted`. That flag is set by the delivery layer whenever any evidence unit is omitted, even if all required facts and checklist items were satisfied. This is a confirmed scoring-policy problem to resolve: omission of an extra passage is not by itself proof that the requested work is incomplete. It is not a bug in the 0/1/2 checklist scale. No scores have been changed yet.

Nonexclusive failed gate counts: missing fact credit 45, material unsupported claim 2, citation support 2, plan score 10, uncertainty 2, answer-declared unmet requirements 53, evidence budget 89. No execution, observed-backend, caller-requirement or contradiction failures occurred. Gates overlap, so do not add these counts. Exact per-attempt replay is saved at `build/rubric-gap-audit/completion-gates.json`.

The 33-answer count checks all completion conditions and supersedes the earlier 43-answer simplified diagnostic for identifying answers blocked only by the budget flag. The primary fact-coverage scores are unaffected by this particular gate. Boundary typing and judge metadata visibility remain separate audits.

The [mechanical v3 audit](pdlc-scorer-v3-audit.md) supersedes the original boundary coverage figures and completion interpretation above. Supported coverage remains 76.08% versus 90.86%; corrected partial coverage is 75.83% versus 90.28%, and corrected boundary coverage is 90.74% versus 97.22%. Original results remain preserved.
