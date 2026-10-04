# One-shot Astra low review prompt: thirty PDLC task drafts

Review the thirty GPT-6 Luna task drafts as a prospective PDLC benchmark, not as completed gold or a production-system evaluation. Perform one independent review pass. Do not rewrite tasks, call paid providers, inspect credentials, activate memory or run agent benchmarks. Review all thirty tasks, including their private criteria, against actual corpus artifacts. Preserve deliberate evidence uncertainty; do not repair fictional source content merely to make questions answerable.

## Inputs

- `build/pdlc-authoring/pdlc-tasks.jobs.json`: six authoring prompts and source excerpts.
- For each job, `build/pdlc-authoring/<job-name>-openai-gpt-6-luna.result.json`: five draft tasks and private proposed facts/checklists.
- `build/pdlc-authoring/pdlc-task-authoring-manifest.json`: source manifest pin and generation status.
- `build/pdlc-pilot/manifest.json` and `build/pdlc-pilot/hubs/*/artifacts.jsonl`: the complete authorized synthetic evidence corpus, including full text and metadata. Do not restrict review to the author's excerpts.
- `docs/experiments/claude-code-harness-spec.md`: required task mix, scoring contracts and boundary handling.
- `docs/experiments/pdlc-claude-code-pilot-plan.md`: decision question, baselines and statistical limits.

## Review pillars

1. **PDLC relevance and breadth.** Does each question reflect a credible developer decision or investigation in understanding, impact, implementation, testing, rollout/recovery or uncertainty? Does its assigned family reflect the actual work requested? Distinguish task usefulness from repeated generic planning or excessive coaching. Inspect representation of Payments, Fraud/Risk, Identity, Ledger and Platform and cross-domain dependency reasoning.
2. **Source grounding and gold correctness.** Verify every positive required fact against its cited full artifact, source, version and literal quote; check quote entailment rather than existence alone. Respect code versus proposed design versus draft skill versus recollection authority. Identify unsupported claims, missing context, important omissions and alternative valid evidence. Do not assume fragments establish executable integration or end-to-end guarantees.
3. **Scope and answerability.** Verify the 18 supported / six partial / six out-of-scope allocation against the entire corpus, aliases and snapshots. Are negatives genuinely outside available support, or only absent from an authoring packet? Do stale proposals get confused with live production evidence? Are negatives plausible tasks rather than contrived impossible requests? Is a bounded, useful partial answer or abstention correctly rewarded without demanding fictional absence citations?
4. **Diversity and discriminative value.** Audit actual required-fact overlap and repeated reasoning, not only labels or distinct fact IDs. Do thirty tasks mostly ask for the same timeout plan? Check single/multiple-source needs, complexity, ambiguity, version conflicts and domain breadth. Can these tasks distinguish the benefit of Sanctum from direct hub access, or are they already answered/coached in the prompt? The study remains directional with one connected scenario.
5. **Rubric validity and fairness.** Can each criterion be judged from evidence? Are factual obligations essential to the user's task, and do mandatory planning items allow multiple sound approaches? Check consistency with the shared five plan dimensions and 0/1/2 anchors. Identify overly prescriptive requirements, hidden caller-policy advantages, accidental answer-key leakage and unjustified automatic failures. Equivalent paraphrases/alternative support must receive fair credit in both arms. Flag whether citation and scope obligations can actually be evaluated by the planned scorer.
6. **Integrity and reproducibility.** Check task-ID uniqueness across all jobs, stable fact identities across equivalent claims, valid domain/source labels, schemas, missing fields and repeatable corpus pinning. Keep private gold and authoring packets out of public prompts/hubs/routing memory. Distinguish private generation scaffolding from realistic user language. Require independent gold acceptance before freeze; another model's draft is not automatically true.

## Output

Write `docs/experiments/pdlc-task-review-astra-low.md` with: readiness recommendation (ready for independent acceptance / needs targeted repair / needs substantive reauthoring); severity-ranked findings referencing job/family plus task ID when IDs collide; a compact disposition for all thirty tasks (retain, revise or replace); observed family/domain/scope/evidence diversity; and the smallest next steps before freeze. Summarize source-verification results and any incomplete checks honestly. Keep quoted artifact excerpts short. Do not claim execution, deployment or statistical proof. No second review loop is requested.
