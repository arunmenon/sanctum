# Pilot-0 preparation readiness — 3 October 2026

**Reusable harness and unpaid preparation are complete. Paid Claude trials and frozen evaluation remain gated.** The first subscription development task has now run (4 October); no paired benchmark or Sanctum quality advantage has been established. See the development flow record below.

The harness loads a scenario bundle, starts fresh Claude Code sessions, exposes either direct hub MCP tools or Sanctum, enforces interaction/evidence/deadline limits, records durable attempts and spend exposure, and scores supported facts, citations, boundary handling and task-specific plans. Schedules pin config, corpus, tasks, private gold and public instructions. Scoring requires current answer/judge-packet bindings; final task completion additionally requires an authorized independent human acceptance record.

## Completion evidence

| Preparation objective | Verified result |
|---|---|
| Corpus and task bundle | 120 synthetic records: CodeHub 25, DocHub 49, SkillHub 16, MemoryHub 30. Thirty saved tasks across six families; 18 supported, six partial, six out of scope; three HLD/two LLD. All source-verified; 88 supporting references and 18 bounded scope checks. |
| Routing memory | Scoped release `pilot-reviewed-317cbcc55f5e`: 350 independently recommended assertions accepted; 338 remain unreviewed. Separate reviewer grants, synthetic source-owner declarations, current-read visibility and version/hash bindings enforced. |
| System One and model identifiers | Live accepted-runtime smoke resolves names, activates procedures/ABOUT bindings and calls `jev-1.13.0`. Claude hosted review observed `claude-fable-5-1`, low. Current bundle pins model, effort and executable-bound isolation proofs. |
| Reusable MCP/session controller | Same direct and Sanctum runner succeeds on PDLC and unrelated shipping, including search/full-file citable retrieval. CLI localhost probes verify inherited-instruction/hook isolation, forbidden-tool denial and turn exhaustion. |
| Scoring | Eleven fixture oracles reviewed by Astra; actual direct and Sanctum delivered-citation probes credit supported paraphrase and reject wrong versions. Semantic labels remain hand-authored fixtures, not model-judge conformance. |
| Checks/review | 635 passed, two live checks skipped, six existing expected failures in broad regression; 73 targeted checks passed after later fixes. One parallel Astra/Claude review round collated; Claude inspection partial after budget exhaustion. Confirmed implementation blockers repaired and verified. |

Current bundle: `build/agent-bundles/pdlc-ready-development-02/experiment.yaml`. Corpus manifest SHA256: `464bb3869054ca3778f035bd2b422a3dac0312ff7605444f7228a14abecb3734`. Candidate canonical JSON SHA256: `2d3388bae6e9141edc879f982a0d019bdead70710862cc6e2e8e56241e758642`.

Evidence: `build/agent-probes/{bundle-connections-04,scorer-delivery-02,scorer-delivery-direct-01,accepted-runtime-03}`, `claude-isolation-03`, `claude-round-limit-01`, `full-regression-04.log`, `post-review-fixes-01.log`; task verification and independent dispositions reside in the bundle's private directory. [Collated findings and dispositions](pilot-0-implementation-review-collated.md) distinguish full Astra inspection from partial Claude inspection.

## Reproduce unpaid checks

Run from `sanctum-lab-m0`; use fresh output directories because dispatched attempts and probe records cannot be replayed.

```sh
PYTHONPATH=src .venv/bin/python tools/validate_agent_bundle.py build/agent-bundles/pdlc-ready-development-02/experiment.yaml
PYTHONPATH=src .venv/bin/python tools/plan_agent_run.py build/agent-bundles/pdlc-ready-development-02/experiment.yaml --out build/agent-runs/pdlc-ready-next-plan
PYTHONPATH=src:. .venv/bin/python tools/probe_bundle_connections.py --out build/agent-probes/bundle-connections-next
PYTHONPATH=src:. .venv/bin/python tools/probe_scorer_delivery.py --arm direct --connection-proof build/agent-probes/bundle-connections-04 --out build/agent-probes/scorer-delivery-direct-next
PYTHONPATH=src:. .venv/bin/python tools/probe_scorer_delivery.py --arm sanctum --connection-proof build/agent-probes/bundle-connections-04 --out build/agent-probes/scorer-delivery-sanctum-next
.venv/bin/pytest -q
```

These fixture probes use local model doubles, not hosted Claude. The following separate smoke makes bounded real Jev calls on synthetic data under existing D-JEV authorization; it is not a Claude benchmark:

```sh
PYTHONPATH=src .venv/bin/python tools/probe_accepted_runtime.py build/agent-bundles/pdlc-ready-development-02/experiment.yaml --out build/agent-probes/accepted-runtime-next
```

## Gates before paid trials or frozen evaluation

1. Approve the separate M8/D-EXT development/evaluation budget and pin verified provider pricing/conservative exposure in the spend ledger. SDK monetary limits are soft: the authorized review reported a $3.76373275 SDK estimate despite a $3 limit. Unknown nested cost stops further paid dispatch. Review estimate is not a billed invoice.
2. Supply explicit Claude provider authentication for the fresh isolated launcher. Cached interactive Max login is not inherited by `--bare`. Credentials stay outside scenario bundles and reports.
3. Before frozen evaluation, independently accept the twelve boundary gold rows, appoint human adjudication ownership and pin its registry, freeze the corpus/tasks/rubric, and calibrate semantic judging. Eighteen tasks are independently recommended for development only. No full gold or enterprise-policy acceptance is claimed.
4. Measure actual task latency and quality under eight rounds, 32 tool calls, 8,000 cumulative/4,000 per-response evidence tokens and 120 seconds. All shown metadata counts. D2 is shadow/preserve and uncalibrated. Shared facts and empty current caller requirements limit generalization; use a fresh independent holdout for stronger conclusions.

The following is the future command shape, **not authorization to execute**. It currently fails paid readiness gates:

```sh
PYTHONPATH=src .venv/bin/python tools/run_agent_attempt.py build/agent-bundles/pdlc-ready-development-02/experiment.yaml --out build/agent-runs/approved-development --task-id payment-authorization-behavior-v2 --arm sanctum
PYTHONPATH=src .venv/bin/python tools/score_agent_answer.py build/agent-bundles/pdlc-ready-development-02/experiment.yaml --task-id payment-authorization-behavior-v2 --attempt PATH_TO_RESULT --answer PATH_TO_STRUCTURED_ANSWER --judge-packet --out PATH_TO_PACKET
PYTHONPATH=src .venv/bin/python tools/score_agent_answer.py build/agent-bundles/pdlc-ready-development-02/experiment.yaml --task-id payment-authorization-behavior-v2 --attempt PATH_TO_RESULT --answer PATH_TO_STRUCTURED_ANSWER --review PATH_TO_PACKET_BOUND_REVIEW --out PATH_TO_SCORE
PYTHONPATH=src .venv/bin/python tools/report_agent_run.py build/agent-bundles/pdlc-ready-development-02/experiment.yaml --run build/agent-runs/approved-development --scores PATH_TO_SCORES
```

Private gold is never exposed to Claude. Real-repository importers, real session ingestion, local coding/editing and Codex/Pi adapters remain follow-on scope. All corpus and graph files persist locally; synthetic model authoring and the explicitly recorded provider/review calls were external.

## Newly authorized development trial

The user authorized Claude execution with Sonnet 5.5. A separate `build/agent-bundles/pdlc-sonnet-55-development-01` preserves the prior bundle and pins `claude-sonnet-5-5`, low effort. Model-specific localhost isolation and turn-limit probes pass. Total spending cap is requested and pending; paid dispatch remains disabled. Existing cached Max authentication is present but the isolated bare launcher still needs explicit supported authentication. No trial has been dispatched.

Subscription clarification: user explicitly requested the existing Claude Max subscription. `sonnet55-subscription-auth-02` successfully invoked hosted `claude-sonnet-5-5` with no API key. Preserve USER/LOGNAME/native security session for keychain authentication; the first overly stripped environment failed and is retained. SDK estimate $0.200564 is not an incremental invoice. This was a one-turn no-tool authentication smoke, not a task trial. Subscription-compatible isolation must be verified before substituting this launcher for the bare API-only benchmark path. Nested Jev usage remains separately metered.

## Executed Claude subscription development flow — 4 October 2026

The user explicitly requested running the Claude flow on the existing Max subscription. Added a subscription auth mode to the existing session launcher: cached first-party OAuth is passed only to Claude Code in a fresh HOME/config/workspace, with no API-key fallback, hooks disabled, strict MCP configuration and evidence-tool allowlist. No credential is saved in bundle/result records. Mixed OAuth/API authentication is rejected. Non-bare subscription isolation and turn-limit probes passed (`sonnet55-subscription-isolation-01`, `sonnet55-subscription-round-limit-01`); 28 affected session/contract/runtime/spend checks passed.

Actual run: `build/agent-runs/sonnet55-subscription-development-01`, task `payment-authorization-behavior-v2`, Sanctum arm, observed hosted `claude-sonnet-5-5`, low effort. Completed in 15,949 ms, two assistant rounds, one Sanctum MCP request, four citable units, one real Jev call; process cleanup verified. Only `mcp__evidence__sanctum_retrieve` was available. Raw answer, normalized structured answer, native stream, result and blinded judge packet are saved. `development-flow-report.json` summarizes evidence.

The answer distinguishes the R42 flag-disabled FAILED response from the flag-enabled NotImplementedError stub and states deployment uncertainty. This is an observed answer, not independently judged correctness. Formal quality scoring and final human task acceptance remain pending; no paired adoption comparison follows from a single task. SDK agent estimate $0.0513038 is recorded as subscription usage estimate, not an incremental invoice. The local ledger uses a $2 SDK-estimate guardrail and $3 estimate reservation for this one requested development attempt; this does not authorize Anthropic API billing or unlimited trials. Nested Jev dollar usage is unknown and blocks subsequent dispatch until reconciliation.

Reproduce after reconciliation with a fresh output directory:

```sh
PYTHONPATH=src .venv/bin/python tools/run_agent_attempt.py build/agent-bundles/pdlc-sonnet-55-development-01/experiment.yaml --out build/agent-runs/sonnet55-subscription-development-next --task-id payment-authorization-behavior-v2 --arm sanctum
```

## Full exploratory campaign — authorized 4 October 2026

User requested all runs. `build/agent-bundles/pdlc-sonnet-55-full-development-01` and `build/agent-runs/sonnet55-full-development-01` pin the full 30 tasks × 2 arms × 3 repetitions schedule, fresh subscription sessions, existing evidence/deadline limits, and scoped active memory/System One. The earlier single-task development result remains separate. This is exploratory development, not independently frozen evaluation. All failures remain recorded; no selective reruns.

Jev pricing was reverified against https://docs.typesafe.ai/models: $0.042/million input tokens, output free. Ninety Sanctum attempts reserve at most 900,000 input tokens in aggregate ($0.0378 at list price). Successful single-request usage receipts are reconciled as rate-card estimates; retries, failed or missing usage remain unknown and stop subsequent dispatch. Claude SDK totals are subscription usage estimates, not a new API invoice. The campaign ledger uses an estimated exposure guardrail and explicit user authorization for 180 subscription runs, not permission to use an Anthropic API key.

Run command: `PYTHONPATH=src .venv/bin/python tools/run_agent_campaign.py build/agent-bundles/pdlc-sonnet-55-full-development-01/experiment.yaml --out build/agent-runs/sonnet55-full-development-01`. Progress and final disposition are persisted as `campaign-progress.json` and `campaign-result.json`; dispatch logs and all native/result/answer records are retained. Thirty affected session/spend/contract/report checks passed before dispatch. Formal semantic scoring remains separate.

Campaign status repair: 50 attempts completed, then a third System One request was refused before HTTP dispatch (calls=0, elapsed=0, over_budget). Preserve original result under `result-before-usage-reconciliation.json`; price two successful receipts, zero additional refusal usage, and reconcile the ledger. Sixteen session/spend tests pass, including refusal-versus-actual-unknown distinctions. Global Claude auto-updated to 2.1.289; campaign-local `pinned-cli/claude` selects retained, hash-verified 2.1.288 without changing global CLI. Auto-update disabled inside subsequent isolated sessions. Resume skips all completed attempts; original frozen schedule remains unchanged.

Full campaign terminal: all 180 native attempts completed, 90 direct and 90 Sanctum. No attempts selectively rerun. See `campaign-result.json`, `execution-summary.json` and `comparison-unscored.json` under `build/agent-runs/sonnet55-full-development-01`. Operational completion is distinct from scored task success; formal semantic judgment and comparison remain pending.

## Quality scoring scheduled — one-pass review and repairs

User requested a new focused Astra low scorer/rubric review before judging. Completed once: `build/quality-scoring-review/astra-low-review.md` and findings JSON. Five blocking findings repaired; dispositions in `docs/experiments/quality-scoring-review-dispositions.md`. Thirty-nine focused checks pass. Current job: `build/agent-runs/sonnet55-full-development-01/quality-evaluation-04`; policy: `build/quality-scoring/evaluation-policy.json`. Fifteen live Sonnet calibration cases pass (eleven original oracle cases, complete/incomplete HLD and LLD). Original thin design examples and transport/label-format mismatches are preserved in earlier evaluation directories. Unchanged replies were revalidated from cache rather than regenerated; mandatory label typography (curly/ASCII quotes and whitespace) is normalized, never wording or actual answer content.

The pinned randomized judging schedule covers all180 saved attempts: 176 semantic candidates plus four mechanically bound protocol-zero failures. Fresh no-tool subscription Sonnet5.5 low sessions; judge model/prompt/policy/scorer/CLI and original run schedule pinned. Packet has task/rubric/evidence/topic context but no arm, tool strategy or cost. Actual runs are never repeated. Score aggregation recomputes from saved reviews; reports facts, plan dimensions, citations, unsupported claims, protocol/budget failures and provisional completion by arm/scope. Human acceptance and independent boundary gold remain pending; post-run repairs and same-model risk are disclosed, not described as frozen independent evaluation.

Current command: `PYTHONPATH=src:. .venv/bin/python tools/run_quality_evaluation.py build/agent-bundles/pdlc-sonnet-55-full-development-01/experiment.yaml --run build/agent-runs/sonnet55-full-development-01 --policy build/quality-scoring/evaluation-policy.json --out build/agent-runs/sonnet55-full-development-01/quality-evaluation-04`. Resume uses the same pinned schedule and saved replies; changed configuration/scorer is rejected. `progress.json`, `stopped.json` if present, and `complete.json` record actual state.

Quality evaluation resumed in `quality-evaluation-05`, preserving the 17 completed scores and all native agent runs. A missing severity field in an additional-claim finding stopped evaluation-04. The controller now allows the policy-declared single schema retry, records the error and retains the initial judgment; it does not assign a severity automatically or rerun the agent. All 39 focused scorer/report checks passed after the correction. Final scoring and human/independent-gold acceptance remain pending.

Evaluation-05 stopped at 35 scores on a missing top-level model label; native usage verified Sonnet 5.5. Evaluation-06 resumes all 35 scores with the same one-retry schema limit, now covering this error. Original outputs retained; 39 focused checks pass.

Evaluation-06 reached 131 scores, then a judge used `claim_reviews` instead of required `claims` on both initial and single retry replies. Evaluation-07 preserves the unscored review failure and continues remaining judgments; missing quality is unknown, not zero. A report with missing grades must remain incomplete/exploratory. Documentation delivery is tracked in [the lab documentation plan](../lab-documentation-plan.md).
