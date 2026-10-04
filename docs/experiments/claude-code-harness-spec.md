# Reusable coding-agent evaluation harness

Status: implementation in progress, 3 October 2026. Task bundle, offline validation, common evidence-delivery limits and session-bound MCP surfaces are implemented and checked. The controller, scorer and pinned Sanctum process/broker connection are implemented. PDLC memory acceptance/activation, complete configuration validation and final implementation review remain pending. This document does not authorize benchmark model spend.

## Task mix — before implementation details

The regenerated development bundle contains thirty tasks matching this matrix. Source verification and repairs are saved; independent task/gold acceptance and evaluation freeze remain pending.

| Primary family | Tasks | Variation to include |
|---|---:|---|
| Understand behavior | 5 | Different domains; current versus historical behavior; code and contracts |
| Trace dependency/change impact | 5 | Single-domain and cross-domain paths; interfaces and consumers; uncertain links |
| Plan implementation | 5 | Different components; requirements versus implementation; known gaps |
| Design testing | 5 | Failure paths, regressions and expected results; draft versus reviewed guidance |
| Plan rollout/recovery | 5 | Prerequisites, checks, stopping conditions and recovery; absent operational evidence |
| Resolve uncertainty | 5 | Ambiguous names, conflicting versions, incomplete evidence and justified partial answers |
| **Total** | **30** | **Distinct evidence obligations, not repeated wording** |

Across these rows, represent Payments, Identity, Platform, Ledger and Fraud/Risk. Track each task's domain(s), required facts, actual supporting sources, difficulty, answerability and version/conflict demands in private gold's `matrix` metadata. Some tasks should require one source and others several; some should be answerable and others require a supported partial answer. Exact allocations across these dimensions await corpus-backed task authoring, rather than claiming a full thirty-row matrix already exists. Independent review of fact overlap and evidence chains is mandatory before freezing.

Bundle configuration declares `diversity.family_counts`, `required_domains`, `required_sources`, `required_difficulties`, `required_answerability` and `reject_duplicate_fact_sets`. Offline validation checks these declared quotas and flags exact repeated fact sets. It cannot establish semantic diversity or evidence quality from metadata; human review remains required. Tiny development fixtures use their own quotas rather than Pilot-0's thirty-task requirement.

### Grounded authoring and scope boundaries

Author questions from the pinned, audited repository/code and document artifacts actually in the corpus, with applicable procedures and session evidence. These synthetic repo containers contain code artifacts, not complete executable checkouts. First assemble private evidence packets with exact versions/hashes/spans, current versus historical/proposed status and known missing links. The owner selected **GPT-6 Luna** for task drafting, using the existing provider-independent generator and preparation ledger. Model-generated assertions do not become gold without source verification. Check code/interface claims directly and execute isolated checks when feasible; distinguish unexecuted sketches and unresolved behavior. A separate task author/reviewer verifies required facts, alternative evidence, realistic task demand, scope and overlap before freezing. Task generation is preparation; agent benchmark execution remains separately budgeted.

Scope is a separate axis from the six task families. Proposed Pilot-0 allocation:

| Evidence scope | Tasks | Expected response |
|---|---:|---|
| In scope, sufficient evidence | 18 | Establish required facts and produce the requested grounded work |
| Partially supported | 6 | Answer the supported portion and identify the exact missing evidence |
| Outside corpus scope | 6 | Recognize absent support, avoid inventing an answer and request a relevant source or clarification |

These allocations total thirty, rather than adding six tasks to each family. Cross-tabulate them with the six family quotas during authoring; scope balance is not achieved by placing every negative in the uncertainty family. Maintain separate `matrix.scope` values (`in_scope`, `partial`, `out_of_scope`) and `matrix.answerability` labels. Report scoped results separately so successful abstentions cannot conceal poor supported-task performance. The current validator enforces exact scope counts and answerability consistency.

Out-of-scope examples include a service/domain not represented in the corpus, requests for live production state when only pinned synthetic snapshots exist, and implementation guarantees the artifacts do not establish. Avoid relying on claims about actual production systems. Check the full authorized corpus, aliases, versions and applicable source coverage when authoring negatives. Record the bounded absence check and scope declaration privately; a search miss alone does not prove something is absent from the world. Freeze evaluated negatives alongside positives and keep them inaccessible to runtime routing memory.

For a wholly unsupported request, gold obligations concern accurately stating the corpus boundary, avoiding unsupported conclusions, and identifying what evidence would be needed. An evidence-backed scope statement may cite published source descriptors; absence itself need not have a fictional artifact citation. Add `support_kind: evidence` or `support_kind: boundary` to gold obligations: evidence obligations require delivered supporting passages; boundary obligations are adjudicated against the pinned scope/absence record and observed investigation, with no fabricated citation required. Empty searches alone do not earn credit, and saying “I don't know” without diagnosing the boundary is incomplete. This exception is restricted to scope/absence obligations, not a route to accepting uncited positive factual claims. Public instructions explicitly permit insufficient-evidence answers in both arms without identifying which tasks are negative.

## Implementation checklist

Current closure: [readiness](pilot-0-readiness.md) and [one-pass review dispositions](pilot-0-implementation-review-collated.md). Historical evidence below is retained; the closure checklist is authoritative for the current ready development bundle.

- [x] Verify and save all thirty tasks against the 120-artifact corpus.
- [x] Implement MCP adapters, session/controller limits, normalized evidence, spend ledger, scoring and reports.
- [x] Verify direct and Sanctum reuse on PDLC and shipping, with citable reads and scorer probes.
- [x] Activate scoped reviewed routing memory in the ready development bundle; verify real System One plus name/procedure/ABOUT activations.
- [x] Verify exact Claude/Jev identifiers and pin CLI isolation/turn proofs.
- [x] Run one parallel review round; collate full Astra and partial Claude findings, repair confirmed blockers, and verify fixes.
- [x] Deliver readiness report and exact commands.
- [ ] Independently accept twelve boundary gold rows and freeze evaluation; assign pinned human adjudication roles.
- [x] Run the first explicitly authorized subscription development task on Sonnet 5.5 with isolated OAuth authentication (4 October; see readiness report).
- [ ] Reconcile nested usage, complete formal judging and independent gold acceptance, approve wider evaluation scope, then run paired evaluation.

### Historical implementation evidence

Checked items have saved evidence; unchecked items are pending. Update this checklist as work is verified, not merely started.

**Owner-required execution order:** complete the current expanded-corpus/routing-memory review, disposition and repair document/source issues, then regenerate and verify task/gold candidates against the updated corpus (including explicit HLD/LLD demands), then resume remaining harness implementation. Task repair/source verification is complete and MCP adapters, session controls and scorer implementation have resumed. Review findings about activation remain tracked as readiness gates; do not mistake an inactive candidate review for operational memory acceptance. No extra model-review loop is implied by this sequence.

- [x] Write reusable scenario/agent/controller/scoring specification.
- [x] Obtain one-shot Astra low plan review and record findings/dispositions.
- [x] Add upfront six-family task matrix and supported/partial/out-of-scope targets (later additions, not independently re-reviewed).
- [x] Implement offline corpus hash, task/gold linkage and configurable family/diversity validation.
- [x] Verify unrelated bundle configurations and invalid-input cases (six bundle tests; thirteen including memory-harvest regression tests).
- [x] Enforce exact scope quotas and executable experiment/gold prerequisites, including caller/adapter identities, paid gates, plan dimensions, source/version/quote/span linkage and scoped boundary records (`agent_contract.py`; seven invalid-input checks).
- [x] Complete scorer integration and independent development-fixture label review. Full task/gold freeze remains gated above.
- [x] Prepare corpus-grounded authoring packets and draft thirty tasks with GPT-6 Luna under the preparation ledger (six completed calls; unverified drafts).
- [x] Prepare and dispatch one PDLC-focused Astra low task review using the saved [review prompt](pdlc-task-review-prompt-astra-low.md).
- [x] Receive the [one-shot task review](pdlc-task-review-astra-low.md): four retain, fifteen revise, eleven replace; all 83 quote references literal-match, but full-corpus grounding/scope/rubric/diversity defects remain.
- [x] Reauthor/revise task candidates against full evidence, normalize IDs/rubrics and verify actual family/scope mix. Saved development bundle is not independently accepted gold; no second Astra review loop requested.
- [x] Prepare v2 regeneration packets against corrected 120-record corpus: all 25 code and eighteen design documents supplied whole, unique repo/family task IDs, canonical checklist dimensions, five explicit HLD/LLD demands.
- [x] Complete GPT-6 Luna v2 generation: thirty unique tasks, six families of five, eighteen supported/six partial/six out-of-scope, three HLD/two LLD design tasks. Raw receipts preserved.
- [x] Repair three literal citation errors and source-grounding defects in a separate private v2 candidate; resolve known R42 handler facts, distinguish live deployment gaps, replace duplicate payment rollouts with ledger/fraud-client release decisions, and correct out-of-scope scoring obligations.
- [x] Complete implementer source/semantic/boundary and diversity verification; save `build/agent-bundles/pdlc-development/{experiment.yaml,public/tasks.jsonl,private/gold.jsonl,private/verification.json}`. 120 corpus records and file hashes checked, 88 supporting references verified, 18 bounded scope checks recorded. Three HLD/two LLD tasks. Shared tooling sources have no domain bindings; none invented. Independence remains separate.
- [x] Enforce exact configurable scope quotas, answerability consistency and corpus-file hashes; test tampering and bounded fact-set exceptions (eleven bundle checks).
- [ ] Independently review facts, alternative evidence, task diversity and private rubrics; freeze tasks/gold.
- [x] Repair memory proposal version selection: match source, artifact, version and hash; legacy receipts are bound to their original prompt bytes, and ambiguous or stale records are quarantined.
- [x] Enforce separately supplied reviewer delegations by source, edge type and optional entity scope; a review document cannot grant itself approval authority.
- [x] Preserve authority assertions and review/delegation hashes within the release, save release-local policy records, and retain PARENT navigation separately from semantic membership.
- [x] Connect accepted ABOUT bindings to fetched candidate assembly. Only successful current gateway reads may enable principal-scoped bindings; exact version/hash and visibility still apply. Unknown graph subjects do not become wildcard conflict matches. End-to-end activation proof remains pending.
- [x] Refresh the corrected 120-record corpus through actual hub MCP reads and reassemble existing authoring receipts without paid generation: `pilot-memory-2474e5a0ffcb`, 657 proposed assertions, nine quarantined proposals. Candidate remains inactive; no approval or source-owner declarations fabricated.
- [x] Run combined harness/reference/memory regression checks after these repairs: 86 tests passed. This does not substitute for actual Claude isolation probes or the final implementation review.
- [x] Complete the separate [HLD/LLD corpus expansion](pdlc-design-corpus-workstream.md), then recheck task grounding/scope and include explicit design tasks before freeze.
- [x] Implement session-bound direct-hub and Sanctum MCP adapters; verify actual MCP initialization and permissions.
- [x] Implement both MCP tool surfaces in `agent_mcp.py`; initialize/discover via MCP, exercise direct gateway retrieval and reject forged identity arguments. Sanctum actual runtime retrieval remains an integration gate.
- [x] Implement normalized delivered-evidence records and atomic concurrent budget enforcement.
- [x] Implement common passage/metadata normalization, exact or explicitly unknown excerpt spans, whole-unit omission, ordered atomic delivery and close/wakeup checks in `delivery.py` (five focused checks). Controller integration is exercised by the saved connection fixtures.
- [x] Implement headless Claude adapter, fresh sessions, native round accounting and durable scheduling/results.
- [x] Add configurable `agent_schedule.py`, `agent_runner.py`, `plan_agent_run.py` and `run_agent_attempt.py`: pin task/config/gold/corpus hashes, randomize paired order, refuse changed schedules, execute one scheduled attempt and preserve terminal records. PDLC has 180 planned attempts; no model attempts dispatched. Sanctum execution deliberately refuses until its real memory/broker integration is verified.
- [x] Implement `agent_session.py` with isolated per-attempt workspace/config, session UUID, single-connection local MCP relay, native assistant-ID accounting, durable dispatch/terminal records and no replay of dispatched attempts. Local fixture executes a real stdio MCP handshake and gateway call; actual Claude event mapping/isolation probes and schedule planning are now verified by the saved native probes and 180-attempt plan.
- [x] Verify CLI isolation, inherited-customization restrictions, deadline cancellation and descendant cleanup.
- [x] Verify local controller deadline, unknown usage recording, explicit-auth environment scrubbing, owned-child process-group termination and tool-inventory mismatch detection with fixtures (six session checks). Confirm installed CLI accepts `--max-turns 8 --version`; this proves option parsing, not inference-time enforcement.
- [x] Implement spend reservations, bounded nested calls/retries and unknown-cost stopping.
- [x] Implement `spend.py` durable reservations: approved budget/pricing record required, in-flight exposure counted, duplicate reservation refused, unknown usage blocks dispatch until reconciled, observed overrun stops new reservations. Seven spend checks pass. Combined agent/nested reservations are not reconciled from Claude-only cost; real provider exposure/pricing and nested-call enforcement remain pending.
- [x] Implement mechanical checks, semantic adjudication contract and scorer fixtures. Independent frozen-gold/human ownership remains gated above.
- [x] Implement `agent_score.py` and `score_agent_answer.py`: verify citation versions/spans/hash against actual delivered evidence, create a blinded full-prose judge packet, validate semantic labels, score facts/plans/boundaries, and require hash-bound human acceptance for final completion. Fourteen fixture checks cover paraphrases, alternative evidence, wrong version, unrelated citation, uncited extras, contradictions, invented thresholds, partial/refusal answers, injection, malformed output and missing retrieval. Fixture labels still await independent review; paid judge connector/ownership remain pending.
- [x] Implement task-cluster paired comparison with seeded descriptive bootstrap; outcome failures contribute zero, missing judgments/undispatched attempts cannot produce a primary estimate. Three schedule/report checks pass; scope-stratified reporting is implemented and covered by report tests.
- [x] Run the same direct controller/MCP fixture on saved PDLC and unrelated shipping bundles without runner edits. Save `build/agent-runs/repository-independence.json` with result hashes, native rounds and trace references. This proves transport/config independence; it does not prove Claude answer quality or Sanctum runtime integration.
- [x] Resolve routing-memory implementation findings and activate the 350-assertion scoped development release; 338 assertions stay unreviewed.
- [x] Replace the Sanctum runtime placeholder with `agent_runtime.py`: pin registry/matrix/release/provider/template/calibration files, require reviewed subject provenance and a matching live-model proof, start the existing ProcessSUT and runner-owned broker, and reject test providers for real agent runs. The local HTTP-double integration verifies actual MCP retrieval, memory-release receipt, ABOUT activation, model trace and cleanup. PDLC release acceptance remains pending.
- [x] Probe installed Claude Code 2.1.288 with a localhost canned API: fix the missing evidence-tool allowlist; confirm actual gateway retrieval, inherited instruction/hook canary isolation, and denials for Bash, Read, WebSearch and unrelated MCP. `build/agent-probes/claude-isolation-03/probe-report.json` passes. These are CLI/transport probes, not hosted inference or answer-quality measurements.
- [x] Verify installed CLI turn ceiling using a separate one-round localhost probe: `build/agent-probes/claude-round-limit-01/probe-report.json`; native max-turn termination is recorded as `agent_round_budget_exhausted`, not task completion.
- [x] Verify model identifiers from observed requests: Claude `fable` resolves to `claude-fable-5-1`; one bounded live synthetic Jev request under D-JEV resolves `jev-latest` to `jev-1.13.0`, with 320 input/24 output tokens. Saved at `build/agent-probes/system-one-live-01.json`. Live Jev evidence is a connectivity/model probe; no paid Claude trial was run.
- [x] Add scope-stratified comparison/report CLI, explicit unknown-cost accounting, controller elapsed time, saved result/ledger consistency checks and fixture exclusion from agent quality estimates. `tools/report_agent_run.py` reports the PDLC fixture with primary comparison unavailable.
- [x] Give each broker attempt its own existing `CampaignBudget`, bounding HTTP attempts and input-token reservations across rounds/retries without sharing exposure with other attempts; test independent client budgets and exhausted pre-dispatch refusal. Monetary exposure still needs approved provider pricing; token reservation estimates are not claimed as an invoice ceiling.
- [x] Keep runner/SUT imports separated and preserve old lab seed controls explicitly. Newly harvested releases require canonical subject bindings; agent runtime rejects legacy releases. The new integration tests also prove that a stale graph cannot supply ABOUT activation for an artifact subsequently unshared or deleted, with caller groups unchanged. This does not generalize the uniform pilot to independent metadata visibility for arbitrary users.
- [x] Reassemble the candidate with the strengthened projection contract: `pilot-memory-ff53fc1f05e4`, 120 artifacts, 657 proposed assertions, nine quarantined proposals; no ACTIVE pointer or invented approval.
- [x] Focused post-repair checks: 53 passed across runtime, report, controller, scheduling, harvesting, assembly and memory. Four separate per-client campaign/runtime checks passed. Full regression recheck is terminal: 609 passed, two live-provider checks skipped, six existing expected failures; saved at `build/agent-probes/full-regression-02.log`.
- [x] Complete accepted PDLC real-provider/memory activation proof (`accepted-runtime-03`). Paid pricing approval remains separate.
- [x] Complete implementation checks and prepare one pinned snapshot for both reviewers.
- [x] Author explicitly synthetic lab curator policy from the pinned hierarchy and inventories: six memberships, five scoped CodeHub authority declarations and twenty must-consult rules. 688-assertion candidate remains proposed; no enterprise approval inferred. Reject spoofed source owners and proposer self-approval.
- [x] Verify both direct and Sanctum connections on PDLC and unrelated shipping bundles through the same runner (`build/agent-probes/bundle-connections-03`). Both Sanctum attempts return fetched, citable ABOUT-bound evidence; local model and fixture acceptance only. Preserve earlier failures and repair the long-query search-contract violation.
- [x] Run one parallel implementation review round: Astra low complete; hosted Claude Fable 5.1 low partial report saved before budget exhaustion.
- [x] Collate findings/disagreements and record repairs, checks and remaining limits; no repeated review loop.
- [ ] Settle separate development/evaluation budget and verify all readiness gates.
- [ ] Run development trial, then frozen paired evaluation; record complete outcomes and task-level uncertainty.

Implementation can progress without paid inference. Draft tasks are not independent gold, and implementation reviews do not substitute for task/rubric review. Codex/Pi adapters, executable coding mode and real-data importers remain deferred.

Latest focused verification: `PYTHONPATH=src .venv/bin/pytest -q tests/test_agent_mcp.py tests/test_agent_delivery.py tests/test_agent_bundle.py` — eighteen passed. `PYTHONPATH=src .venv/bin/python tools/validate_agent_bundle.py build/agent-bundles/pdlc-development/experiment.yaml` verifies all thirty tasks, five domains and exact family/scope quotas. Actual CLI reinspection reports Claude Code 2.1.288, with `--bare`, `--restricted`, `--disable-slash-commands`, strict MCP config and stream JSON options available. Help confirms a `fable` alias but does not yet prove the owner's exact Fable 5.1 model identifier or runtime isolation.

Controller/spend verification: `.venv/bin/pytest -q tests/test_agent_session.py tests/test_agent_spend.py tests/test_agent_mcp.py tests/test_agent_delivery.py tests/test_agent_bundle.py` — thirty-one passed. These checks run local fixture processes/MCP, never paid Claude inference. They establish controller behavior; they do not substitute for the installed-CLI canary probes or real Sanctum/memory/System One trace proof.

Scorer/schedule/controller verification: `.venv/bin/pytest -q tests/test_agent_score.py tests/test_agent_schedule.py tests/test_agent_session.py tests/test_agent_spend.py tests/test_agent_mcp.py tests/test_agent_delivery.py tests/test_agent_bundle.py` — forty-eight passed. Saved fixture command: `PYTHONPATH=src .venv/bin/python tools/run_agent_attempt.py build/agent-bundles/pdlc-development/experiment.yaml --out build/agent-runs/pdlc-fixture --task-id payment-authorization-behavior-v2 --arm direct --fixture`. Existing dispatched output must not be replayed; choose a new output directory for a new fixture demonstration. Shipping uses the same command with `build/agent-bundles/shipping-fixture/experiment.yaml`, `shipping-eligibility`, and its own output directory. `tools/create_unrelated_agent_bundle.py --out build/agent-bundles/shipping-fixture` constructs the unrelated corpus; it copies only the CodeHub type contract, never PDLC records/gold.

## Purpose and boundary

Run Claude Code against a configurable knowledge ecosystem and measure evidence-supported task outcomes. Repository names, domains, hub endpoints, permissions, task prompts and expected answers belong in scenario bundles, never in runner logic. The first bundle is the [PDLC Pilot-0](pdlc-claude-code-pilot-plan.md); later bundles may use other synthetic or authorized real repositories.

Reuse the existing `sanctum_run` gateway, observed-call tracing, proxy and reference process. Add a thin client-facing MCP adapter and a headless session controller. The existing retrieval evaluator scores retrieval contracts, not arbitrary Claude prose: final-answer evaluation is a separate required component. No new hosted service, graph database or general workflow framework is required.

The runner is reusable across repositories through configuration. A new hub API may require a connector; a new outcome type may require a scorer. Those extensions do not justify hard-coding repository-specific behavior in the runner.

## Agent adapter boundary

Claude Code is the first agent adapter, not the identity of the harness. Later adapters may launch Codex, Pi or another coding agent or connect to its existing execution harness. Those integrations are explicitly deferred. Keep experiment scheduling, task/gold handling, scoring and result storage outside the Claude-specific launcher.

The minimal adapter contract is:

| Operation | Responsibility |
|---|---|
| Inspect capabilities | Report agent/runtime version, available authentication method without secrets, MCP support, isolation controls, event/usage support and cancellation behavior |
| Prepare session | Apply the public task, workspace, selected model/effort, explicit tool surface and session limits; return effective settings and tool inventory |
| Start and observe | Launch or attach to one fresh attempt; emit attributable model/tool/final-answer events and native receipts |
| Cancel and close | Terminate the attempt and owned descendants/connections, reporting any unverified termination |
| Collect result | Return final answer, terminal status, usage with unknown fields explicit, and references to raw events |

Normalize events into run/session ID, timestamp, event kind and payload, preserving native event records. Do not pretend different agents define turns or usage identically: document mappings to harness rounds and report unsupported accounting. Evidence limits remain enforced at the common MCP boundary; adapters enforce agent-side controls and cancellation. If an agent cannot meet an experiment's isolation or accounting requirements, fail readiness rather than silently relaxing them.

Keep the first implementation small: one Claude adapter and an explicit Python interface. Add other adapters when requested, using the same scenario bundle. Cross-agent comparisons are a separate experiment: paired Sanctum/direct runs must still match agent/model settings within each comparison, and model/effort names are adapter-specific. This specification does not claim Codex or Pi integration has been verified.

## Scenario bundle

Separate agent-visible inputs from evaluator-private inputs, with the controller retaining the latter outside the agent workspace and MCP surface.

| Input | Contents | Visible to Claude |
|---|---|---|
| Experiment configuration | Bundle version, repetitions, seed, arm definitions, budgets and output destination | Only necessary task instructions and tool definitions |
| Corpus reference | Immutable manifest/hash and connector configuration; optional checkout commits | Through authorized tools, or matched checkouts in coding mode |
| Public tasks | Stable task ID, question, output format and explicit caller requirements | Yes |
| Private gold | Required facts, accepted evidence/spans/versions, conflicts, unknowns and rubric | No |
| Workspace recipe | Empty evidence-only workspace or pinned repository checkouts | Workspace contents only |
| Credential references | Environment variable names or local secret-provider references | No secrets in prompts, logs or bundle files |

Illustrative configuration below is a proposed contract, not an executable launcher today. Paths resolve against the bundle directory. The resolver must verify referenced manifests and releases rather than trusting their labels.

```yaml
schema_version: 1
experiment_id: example-investigation
mode: evidence_only
corpus:
  manifest: corpus/manifest.json
  expected_sha256: <frozen-manifest-hash>
caller:
  identity_ref: pilot-reader
tasks: public/tasks.jsonl
gold: private/gold.jsonl
agent:
  adapter: claude_code
  model: <explicitly-selected-model>
  effort: <explicitly-selected-effort>
  cli_version: <verified-installed-version>
workspace:
  kind: empty
arms:
  direct:
    tool_surface: direct_hubs
    connection: connections/direct.yaml
  sanctum:
    tool_surface: sanctum_only
    connection: connections/sanctum.yaml
    memory_release: <reviewed-pinned-release>
    registry_hash: <pinned-registry-hash>
    system_one_config: connections/system-one.yaml
limits:
  agent_rounds: 8
  cumulative_evidence_tokens: 8000
  tool_response_evidence_tokens: 4000
  tokenizer: <pinned-tokenizer-and-version>
  task_deadline_seconds: 120
  total_inference_spend_usd: <separately-approved-ceiling>
execution:
  repetitions: 3
  random_seed: 42
  fresh_session_per_attempt: true
scoring:
  primary: supported_required_fact_coverage
  rubric: private/rubric.yaml
outputs: runs/
```

An additional repository changes corpus references and, in coding mode, the checkout list. Domain/team/repository relationships remain corpus and routing-memory data. They are not embedded in task dispatch or tool-selection logic.

## Task and gold contracts

A public task contains `task_id`, `family`, `prompt`, `caller_requirements` and `answer_format`. The same question and requirements go to both arms. A requirement such as consulting a particular source is caller policy, exposed identically; hidden gold locations are never converted into routing instructions.

A private gold record uses the same task ID and contains:

- Required fact IDs, accepted values/renderings and equal fact weights for Pilot-0; any later weighting is frozen before runs.
- Supporting source/artifact/version/hash and passage spans, including acceptable alternative evidence.
- Conflicts and expected distinctions between proposed, historical and implemented behavior.
- Known unknowns, prohibited unsupported conclusions and appropriate partial-answer conditions.
- A frozen plan-quality rubric, plus optional executable checks for a later coding experiment.

Require a common structured final-answer envelope with `schema_version`, `answer` (full prose/plan), `claims` (claim ID, text and citation references), `uncertainties` and `unmet_requirements`. Citation references contain source/artifact/version, start/end character coordinates and an optional delivered evidence ID; the controller resolves the hash. Public instructions specify the schema and task's applicable planning work identically in both arms. Preserve the original output. Mechanical scoring can validate exact references and predefined fact values; it cannot prove arbitrary paraphrase entailment. Ambiguous support or materially unsupported additional claims require blinded adjudication. Malformed answers are protocol-incomplete; deterministic extraction or human reading of recoverable prose may yield graded scores, with the extraction method recorded, but cannot repair completion status. No model-based silent repair.

Independent task authorship or revision is required before an independently validated benchmark claim. Development tasks use different facts. The runtime implementer must not tune against private evaluation answers.

## Scorer and frozen rubric

### Pilot-0 task diversity gate

The evaluation bundle targets 30 tasks: five each for behavior understanding, dependency/impact analysis, implementation planning, testing, rollout/recovery and ambiguity/conflict/missing evidence. These are authoring quotas, not thirty questions already written. Track each task's primary family, domain associations, required fact IDs, evidence sources, version/conflict needs, difficulty and answerability in a private task matrix. Use all five corpus domains across the set; include single-domain and cross-domain tasks, single-source and multi-source reasoning, and fully answerable and legitimately partial outcomes. Distinguish difficulty by actual reasoning/evidence requirements rather than prompt length.

Before freezing, an independent task reviewer checks the matrix for family balance and paraphrases that reuse the same required facts. Exact duplicate required-fact sets require revision or a recorded justification for a distinct reasoning demand; report overlapping facts across otherwise different tasks. Do not inflate diversity by changing wording or merely assigning different family labels. Review the actual evidence chains and task-specific rubrics. If the corpus cannot support a quota, record the gap and revise the corpus or quota before runs, rather than fabricate gold. The balanced quota is specific to Pilot-0; the reusable validator reads diversity requirements from bundle configuration.

Task mix is an evaluation readiness gate, not a blocker to implementing the runner on small development fixtures. All thirty tasks still share a connected scenario; diverse tasks do not establish cross-ecosystem generalization.

Ground truth is a set of evidence-supported obligations, not an ideal paragraph. Different wording, alternative valid evidence and different sound plans can receive the same score. Freeze gold, scorer version, judge prompt/model, severity definitions and task-specific anchors before evaluation. The existing retrieval evaluator is useful for reference validation but is not the final-answer scorer.

### Scoring stages

1. Validate the final-answer envelope and reconcile its citations with evidence actually delivered in this attempt. Require source ID, artifact ID, version and passage coordinates; resolve them against the pinned corpus/hash and caller access. A reference to valid but never delivered evidence fails the evidence-access check. Record schema failures without silently reparsing with a model.
2. Check exact canonical values and reference spans mechanically where possible. Exact matching is a shortcut, not a requirement for equivalent language, and a matching value plus an unrelated citation is not support.
3. A blinded semantic judge evaluates required-fact coverage, entailment, contradictory/unsupported claims, uncertainty and plan quality using the saved full answer, private rubric and resolved passages. Inspect prose as well as declared claims, so omitting a claim from the structured list does not evade scoring. Treat answer and retrieved content as data, not judge instructions. Remove arm labels/tool branding from judge inputs where feasible; preserve immutable originals and record remaining clues to arm identity.
4. A human adjudicates ambiguous support, reliability failures and disagreements between mechanical checks, the single semantic judge and human checks, and checks a stratified 20 percent sample across arms/task families and score ranges. No second judge service is required. Segment compound assertions into independently verifiable factual claims; distinguish recommended actions from assertions that those actions are implemented or required. Record agreement for fact-support labels and task completion plus plan-score differences; do not report agreement from only easy examples. An LLM judgment alone is provisional; missing human adjudication is reported as pending, never silently converted into a pass.

Accept newly identified equivalent evidence only through arm-blind adjudication with a recorded reason. Apply the same disposition to both arms and every affected answer, preserving original and revised scores under explicit scorer revisions. This resolves incomplete gold fairly without tuning routing or rewriting the task after seeing results.

### Measures and completion rule

| Measure | Definition |
|---|---|
| Supported required-fact coverage (primary) | Number of required obligations correctly established divided by number of required obligations; equal weights, binary 0/1 per fact. Positive facts require supporting delivered evidence; explicitly marked scope/absence obligations use the frozen boundary record and observed investigation. Missing, wrong, contradictory or unsupported obligations score 0. An answer must resolve its own conflicting assertions before receiving credit. Report in-scope, partial and out-of-scope strata separately. |
| Citation validity | Fraction of cited references resolving to the authorized pinned artifact/version/span and delivered evidence. A resolvable citation is not automatically entailing. |
| Citation support | Fraction of cited factual claims actually supported by their cited passages. Record uncited factual claims separately; no citations means N/A precision, not perfect precision. |
| Unsupported claims | Count and severity of factual claims lacking support or contradicting evidence, including claims outside required facts. Severity is material when it could change the task decision, scope, tests or rollout. |
| Conflict/gap handling | Each task's checklist of version/status distinctions, unresolved conflicts and unknowns, scored 0/1 per obligation. |
| Required-source compliance | Actual gateway observations satisfy explicit caller obligations; a mention of a source in prose does not count. |
| Plan quality | Anchored 0–2 scores per applicable dimension below, with N/A fixed by task before execution. |

Each task has at least one required evidence-supported obligation. For an unanswerable question, obligations describe the supported gap/conflict and justified inability to conclude, rather than requiring a fabricated answer. A generic refusal earns no fact coverage. Resource ceilings can cause incomplete answers; report that as an outcome, not evidence that the private gold was unreasonable.

Planning dimensions use **0 = absent, incorrect or unsafe given the evidence; 1 = useful but incomplete; 2 = complete enough for this task and grounded**:

- Scope/dependencies: identifies affected components and interfaces without inventing broader impact.
- Proposed change: connects the requested behavior to the evidence and separates recommendations from implemented facts.
- Validation: covers task-specific failure paths and regressions with observable expected outcomes.
- Rollout/recovery: includes evidence-supported prerequisites, rollout checks, stopping conditions and recovery; no invented numerical thresholds.
- Uncertainty/dependencies on missing evidence: states what must be verified before acting and why it matters.

The task-specific rubric names mandatory items under each applicable dimension. A task is complete only if coverage is 100 percent, no material unsupported or contradicted claim remains, citation validity/support have no failures for relied-upon facts, all caller/conflict/gap obligations are met, and every applicable planning dimension scores 2. Report incomplete tasks with graded scores rather than only pass/fail. Minor unsupported extras remain visible and prevent describing the whole answer as fully supported. Completion is an evaluator judgment, separate from a process exiting normally.

### Worked scoring example

Illustrative task: assess a service timeout change and propose validation. Gold requires five facts: the pinned implementation behavior, interface shape, an affected consumer, applicable test guidance and a documented unknown. Claude establishes four with supporting evidence and misses the unknown: 4/5 = 80 percent coverage. It may still receive useful plan scores, but is incomplete. If it invents an automatic retry that would alter the proposed tests, record a material unsupported claim as well. An alternative wording or valid alternative passage establishing all five facts receives full credit.

### Scorer verification and ownership

Before paid runs, test the scorer against hand-labeled saved fixtures: faithful paraphrase, valid alternative evidence, wrong version, valid-but-unrelated citation, uncited extra claim, self-contradiction, unsupported plan threshold, justified partial answer, prompt injection in evidence, malformed output and missing retrieval. The golden fixture labels must be independently checked; scorer tests must not merely mirror its implementation.

Assign task/gold ownership and human adjudication before evaluation; those roles are currently unassigned. A separate judge may assist, but independence is organizational, not achieved just by a second model call. Scorer development can use synthetic fixtures without paid calls. Judge/development/evaluation spending is separately recorded under the approved benchmark budget. Unresolved scorer ambiguity or absent independent review limits results to developer validation.

## One-session handshake

1. Validate the bundle, cross-reference task/gold IDs, verify hashes, and check the declared budget. Allocate a run ID and fresh request/session IDs.
2. Create an isolated workspace and explicit Claude configuration. Start the gateway and the selected MCP surface; bind caller identity inside the trusted controller.
3. Perform MCP initialization and list-tool discovery. Compare the effective inventory against the arm allowlist. Do not ask Claude to supply gateway tokens or trusted request metadata; the adapter supplies them from the session binding.
4. Start headless Claude with the public task, common answer instructions and allowed tools. Private gold and corpus source files remain inaccessible in evidence-only mode.
5. Claude chooses searches, follow-up queries and stopping behavior. The harness controls limits and records calls; it does not prescribe a sequence of hub searches or inject gold-derived hints. Sanctum may be called repeatedly.
6. The adapter enforces evidence budgets before delivering results and emits an explicit exhaustion marker. The controller enforces the overall deadline, stops Claude and owned child processes, and finalizes traces even on failure.
7. Store the final response and usage, then release the caller binding and workspace. Score separately with private gold. A new attempt starts from clean state.

Direct arm: Claude → client MCP adapter → existing gateway → hub MCP tools. Sanctum arm: Claude → client MCP adapter → reference router → existing gateway → hub MCP tools, with pinned memory and System One. Expose no direct hub or System One tool to Claude in the Sanctum arm. Count internal router/model calls as treatment cost.

## Modes and fair access

**Evidence-only, implemented first:** empty workspace, MCP evidence access only. Disable built-in shell/file/web tools, unrelated MCP servers, inherited instructions, skills/hooks and automatic memory. No checkout is supplied. This measures investigation and planning, not executable code changes.

**Coding, deferred:** configure one or more authorized repositories pinned to commits; create fresh writable worktrees or copies per attempt. Both arms receive identical local files and editing/test permissions. Sanctum supplies surrounding knowledge. Grade patches with explicit tests and task outcomes in addition to evidence quality. Repository commands are bundle inputs, not hard-coded runner branches; their execution policy must be declared before running.

Freeze the Claude model/effort, corpus, caller permissions, task text and limits across paired arms. Randomize arm order with a recorded seed. Sessions and local agent memory reset between tasks; router memory is a pinned release and does not learn from evaluation runs.

The installed CLI was inspected as version 2.1.288. Isolation flags, authentication behavior and turn counting must be verified against that installed version before dispatch. In particular, `--bare` changes authentication behavior; do not assume existing interactive login works in that mode. Use an explicit compatible configuration and inspect actual startup/tool behavior. CLI turn limits alone do not establish the plan's definition of an agent decision round.

Evidence accounting uses one pinned tokenizer over the delivered evidence content, including citation metadata. Repeated passages count again; schemas and other prompt overhead are recorded separately in total inference usage. Budgeted responses preserve complete citation units or explicitly mark omitted units; never truncate a passage while pretending its original span supports the displayed content.

### Concrete limit contract

A round is one completed agent model response that issues one or more tool calls or produces the final answer. Tool-result delivery does not start a separate round. Parallel calls from one response use one round but count as separate calls; any additional model response after the eighth is prohibited. The Claude adapter must prove its native event mapping before use; hidden/unobservable model steps make readiness fail for this limit rather than being counted as free.

Normalize evidence-bearing hub results and Sanctum responses into delivered records: source/artifact/version/hash, actual displayed text and character coordinates, public metadata and citation data. Search snippets count, as do evidence-bearing metadata or errors. Operational error/exhaustion markers without domain evidence remain trace/inference overhead. Duplicate structured/text renderings are removed before delivery when semantically identical and recorded as such; if both are delivered, both count. A shortened passage receives its actual displayed coordinates, not its original full span.

Use an atomic per-session counter for concurrent results. Assign call sequence IDs at invocation and deliver parallel results in that order, so asynchronous completion cannot determine which arm receives the last allowance. Enforce 4,000 evidence tokens per response and 8,000 cumulative before delivering complete citation units; omit oversized units explicitly. Save direct/Sanctum normalization equivalence and parallel-exhaustion fixtures. Each Sanctum request packs to the remaining allowance. Router internal retrieval does not consume the agent's delivered-evidence allowance, but every backend call and model invocation consumes the declared time/call/spend bounds and is recorded. Explicit nested-call maxima must be part of the frozen connection configuration; an unbounded router configuration fails readiness.

### Spend reservation contract

Before dispatch, approve and freeze a pricing basis and ceilings for agent execution, nested System One, bounded retries and judging. Reserve a conservative per-attempt maximum before launch, including every allowed nested model call/retry; configure enforceable provider output/request caps. Judging has its own reservation or separate cap. Reconcile receipts against reservations; a failed or timed-out call without known usage retains its reservation and stops further paid dispatch until reconciled.

If provider controls cannot bound input/output charges or expose hidden inference, do not claim a hard dollar cap. Establish a conservative worst-case in-flight exposure, including concurrent calls, inside the approved ceiling before running; if that exposure cannot be bounded, paid dispatch is not ready. A deadline and evidence limit alone are insufficient. Missing pricing or insufficient remaining balance for a reservation stops dispatch. This uses a local durable ledger, not a new billing service.

## Results and failure handling

Persist an immutable run manifest, effective tool inventory, public prompt hash, corpus/release/config hashes, CLI/model/effort, paired order and timestamps. Store Claude events, client MCP calls, independently observed gateway calls, System One receipts, delivered evidence counters, final answer, scores and reviewer dispositions. Keep credentials and caller tokens out of saved records.

Every planned attempt has a terminal ledger row: completed, deadline exceeded, budget exhausted, protocol violation, infrastructure failure or launch failure. Missing retrieval is a protocol failure. Missing usage is unknown cost, not zero. Preserve provider failures and partial outputs. Do not selectively retry poor answers; any transport retry policy is bounded, declared and recorded. Resume schedules only attempts never dispatched; uncertain attempts require reconciliation and are not silently replayed.

Report coverage, citation support, unsupported claims, required-source compliance, uncertainty handling and plan quality alongside total cost, tokens, calls and latency. Aggregate paired differences by task; three repetitions do not create three independent tasks. Pilot-0 remains directional and may be inconclusive.

Freeze the attempt schedule before execution. Score partial answers for supported facts actually present; missing answers receive zero coverage, and deadline, evidence exhaustion, missing retrieval and schema violations cannot be task-complete. Report every dispatched attempt in operational reliability denominators, including launch/provider failures. Report undispatched attempts separately with reasons; never score them as success or as observed zero-quality answers.

The planned primary comparison is all three repetitions in both arms per task, including outcome/protocol failures. A shared infrastructure defect that invalidates a comparison is labeled explicitly; preserve all records and report counts by arm. If infrastructure failures leave an incomplete planned comparison, do not present a complete primary estimate: provide an explicitly labeled exploratory complete-task analysis plus observed failure rates and missingness, without selective replacement runs. For a complete run, average repetitions within each arm/task, compute paired task differences, and use a seeded paired task-cluster bootstrap with 10,000 resamples for a descriptive 95 percent interval. Facts and repetitions are not resampled as independent observations. Thirty tasks and one connected scenario remain a limited directional study.

### Isolation and cancellation acceptance matrix

Trusted `ProcessSUT` transport currently passes `HOME` and runs the router from the repository root. Reuse its gateway binding/pipe transport without treating it as Claude isolation. The Claude launcher creates a separate configuration/workspace boundary and controls its own process group.

| Boundary | Required probe before paid tasks |
|---|---|
| User/project instructions, hooks, skills, automatic memory | Harmless canaries in otherwise inherited locations must not appear or execute; inspect effective configuration |
| MCP discovery and built-in tools | Only arm tools available; unrelated MCP and shell/file/web attempts denied |
| Local corpus and gold | Agent-visible workspace contains neither; allowed tool paths cannot read them |
| Authentication | Explicit supported auth source works without loading unrelated customization; no secrets in receipts |
| Descendants and in-flight calls | Owned child fixture is terminated on deadline/cancel; pending MCP calls canceled, caller bindings released and cleanup recorded |

Verify actual installed-CLI behavior and save probe results; startup inventory alone is not sufficient. Unverified descendant termination or unreleased calls fail readiness. Hostile native code sandboxing is outside evidence-only mode; coding-mode execution requires its own declared containment policy.

## Implementation slices and acceptance

| Slice | Deliverable | Required demonstration |
|---|---|---|
| 1 bundle validation | Config loader and public/private task contracts | Two unrelated small bundles validate without runner edits; missing gold IDs and hash mismatches fail before dispatch |
| 2 MCP connection | Session-bound direct/Sanctum adapters using existing gateway | Initialization, correct tool inventories, observed retrieval and denied unauthorized access, without paid Claude calls |
| 3 session control | Headless launcher, isolation, counters and durable attempt ledger | Actual CLI restrictions, deadline child-process termination, explicit evidence exhaustion and no duplicate dispatch |
| 4 development trial | A small separately budgeted development run | Real Claude retrieval and final citations; Sanctum traces prove reviewed memory and real System One use |
| 5 evaluation/scoring | Frozen independent tasks/gold and separate scorer | Paired scheduling, blinded review, complete failures/usage and task-level uncertainty |

The first implementation is a local Python launcher plus JSON/YAML bundles and the thin MCP adapter. Reuse existing token service, gateway and process transport; do not alter their trusted caller binding to accommodate the client. A dry-run mode validates configuration and inventories without paid agent inference. A run mode dispatches only after budget and readiness checks pass. A score mode consumes saved outputs without rerunning agents.

Current prerequisites for the Sanctum development trial remain: resolve the four [Astra routing-memory findings](pdlc-domain-coverage-memory-review-astra-low.md), review explicit routing declarations, pin a coherent release, wire accepted subject bindings into runtime evidence assembly, and select/verify System One. Candidate memory is not active. The separate evaluation budget remains the M8 / D-EXT decision documented in the pilot plan. These are readiness gates for this scenario, not repository-specific harness code.

## One-shot review and disposition

### Implementation review requested by the owner

After implementation and required checks, run two independent reviews in parallel: Astra at low effort and Claude with the owner-confirmed model **Fable 5.1**, also at **low effort**. Verify its accepted CLI/provider model identifier before invoking that reviewer; do not silently replace it. Review the same pinned implementation state, task/scoring contracts, validation evidence and known limitations. Collate findings by severity and affected behavior, preserve disagreements and identify required corrections versus deferred work. This is one review round, not a repeated plan-review loop. Reviewer execution and any external inference must fit an explicit budget; implementation authorization does not erase the separate benchmark-budget gate.

Proceed autonomously with implementation, offline verification and review preparation. The agent/controller must remain unable to dispatch paid evaluation until declared readiness and budget checks pass. Task drafting and gold ownership remain distinct from implementation review; two code reviews do not independently validate the benchmark tasks.

Implementation started with `sanctum_run.bundle` and `tools/validate_agent_bundle.py` after the user required the task-diversity gate. The offline validator checks corpus pinning, separate task/gold files, IDs, required fact IDs and configurable matrix quotas. It reports `ready_for_paid_dispatch: false`; full configuration/security/readiness validation remains subsequent work. This does not create independent gold or activate routing memory. Runtime MCP, session control and scoring remain subsequent slices. Invoke from the repository with `PYTHONPATH=src .venv/bin/python tools/validate_agent_bundle.py <bundle>/experiment.yaml`.

[Astra low reviewed this plan once](claude-code-harness-review-astra-low.md). Recommendation: proceed with unpaid implementation slices; no paid runs yet. The single revision above addresses H1 through spend reservation/unknown-cost stopping rules; H2 through round, normalized evidence and concurrent-counter contracts; M1 through frozen failure denominators and incomplete-pair analysis; M2 through the explicit isolation/cleanup acceptance matrix. Envelope parsing, claim segmentation, judge disagreements and public planning instructions were clarified. These are design dispositions requiring implementation proof, not independently rechecked fixes. No second review loop was commissioned.

Current one-pass implementation review: immutable `build/implementation-review/snapshot-01`, manifest SHA256 `b81d39ebe0be359e97671c41c627c43fa4a33e9aaca5595eea8d744d32d23b25`; Astra low and actual hosted Claude `claude-fable-5-1` low are dispatched. Reviews have not yet returned. The snapshot retains earlier checklist wording; this current checklist reconciles completed integration/probe items against their saved evidence. No paid benchmark attempt has been dispatched.

### Quality-scoring execution checklist

- [x] Complete all180 native development attempts, preserving prior single-task trial separately.
- [x] Perform requested new one-pass Astra low scorer/rubric review.
- [x] Repair five blocking findings and pass39 focused checks.
- [x] Validate15 live judge calibration cases; retain disagreements and processing corrections.
- [x] Pin and dispatch saved-answer evaluation; four protocol failures remain in the denominator.
- [ ] Finish176 semantic labels and mechanically bound scores for all180 attempts.
- [ ] Deliver scope-separated quality comparison with plan/grounding/completion measures and explicit study limits.
- [ ] Complete independent boundary-gold and human acceptance before frozen or final task-success claims.

Quality evaluation resumed in `quality-evaluation-05`, preserving the 17 completed scores and all native agent runs. A missing severity field in an additional-claim finding stopped evaluation-04. The controller now allows the policy-declared single schema retry, records the error and retains the initial judgment; it does not assign a severity automatically or rerun the agent. All 39 focused scorer/report checks passed after the correction. Final scoring and human/independent-gold acceptance remain pending.

Evaluation-05 stopped at 35 scores on a missing top-level model label; native usage verified Sonnet 5.5. Evaluation-06 resumes all 35 scores with the same one-retry schema limit, now covering this error. Original outputs retained; 39 focused checks pass.

Evaluation-06 reached 131 scores, then a judge used `claim_reviews` instead of required `claims` on both initial and single retry replies. Evaluation-07 preserves the unscored review failure and continues remaining judgments; missing quality is unknown, not zero. A report with missing grades must remain incomplete/exploratory. Documentation delivery is tracked in [the lab documentation plan](../lab-documentation-plan.md).
