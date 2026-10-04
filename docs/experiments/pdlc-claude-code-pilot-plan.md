# Sanctum PDLC pilot with Claude Code

Status: unpaid harness preparation complete; paid trial and frozen evaluation gated, 3 October 2026. This plan proposes an agent-level experiment; it does not report benchmark results or approve production adoption.

The decision is whether Claude Code should use Sanctum rather than directly accessing the same knowledge hubs for product development lifecycle (PDLC) tasks. Sanctum must improve evidence-supported task outcomes under a fixed resource budget, or reduce total resources within an agreed quality margin. Fewer backend calls alone are insufficient.

The audience is the Sanctum product lead and implementers. This plan connects the domain corpus, hub hydration, Claude Code integration, evaluation and adoption decision. It extends the [existing spike plan](spike-plan.md) with a concrete agent-level slice and follows the goals in [HLD section 3](../../design/intelligence-layer/hld.md#section-3).

The first pilot includes both routing memory and System One. The primary comparison is the complete Sanctum configuration against direct hub access. Separate rules-only and component-removal comparisons are deferred; they are not prerequisites for this pilot. Deterministic constraints and safe fallback behavior remain part of the HLD cascade.

## Current state

Current implementation closure is recorded in [readiness](pilot-0-readiness.md) and [collated review dispositions](pilot-0-implementation-review-collated.md). The reusable harness is implemented; thirty source-verified tasks and 120 synthetic artifacts are saved. The ready development bundle activates a scoped 350-assertion routing-memory release with real Jev operation verified. One parallel review round is collated (full Astra, partial Claude); implementation blockers are repaired. Paid trials, full independent boundary-gold acceptance and frozen evaluation remain gated. The dated history below describes earlier stages and is not the current readiness declaration.

### Required evaluation task mix

The owner also requested a separate [HLD/LLD corpus workstream](pdlc-design-corpus-workstream.md): repo-level HLD plus two source-grounded module LLDs for each of the six synthetic repos, with explicit navigation and draft status. Audit and ingestion precede task-gold repair/freeze. Design tasks must evaluate requirements, constraints and tradeoffs rather than require one exact architecture; explicitly include HLD and LLD demands when rebuilding the thirty-task mix.

| Family | Target tasks |
|---|---:|
| Understand behavior | 5 |
| Trace dependencies/change impact | 5 |
| Plan implementation | 5 |
| Design tests | 5 |
| Plan rollout/recovery | 5 |
| Resolve ambiguity/conflicts/missing evidence | 5 |
| **Total** | **30** |

The target is implemented in the thirty-task development bundle; it is not frozen evaluation gold. The private per-task matrix tracks domains, required fact IDs, supporting sources, difficulty, answerability and version/conflict demands. Cover all five domains, single/cross-domain tasks, single/multiple sources and complete/partial answers. Inspect overlapping facts and paraphrased questions before freezing; task labels alone cannot establish diversity. The [upfront harness matrix](claude-code-harness-spec.md#task-mix--before-implementation-details) details this gate. Task authoring and source verification are complete; independent review records overlap and partial acceptance limits in the closure report.

Cross-cutting scope targets within those thirty tasks: 18 sufficiently supported, six partially supported and six outside corpus scope. Author from the actual pinned code/doc/procedure/session evidence, optionally using LLM proposals followed by direct source checks and independent review. Negative tasks require a private corpus-scope/absence check, not merely a failed search. Score justified boundary recognition without demanding fabricated absence citations; retain evidence requirements for positive facts. Report results by scope so abstentions do not hide weak supported answers. The [authoring and scope specification](claude-code-harness-spec.md#grounded-authoring-and-scope-boundaries) records the process. Actual tasks and quota validation are implemented; twelve boundary gold rows still await independent semantic absence acceptance.

The lab contains simulated hubs, a reference router and an evaluator for synthetic cases. Four public repositories have been downloaded into the workspace at `pilot/sources`: Engram, gisting-coding-agent, kg-memory-mcp and openclaw-skills. They are candidate integration fixtures, not an ingested corpus or evidence of PDLC performance. Additional repositories may be selected if needed.

Real-data importers and benchmarks are deferred. The standalone Claude Code MCP/controller integration is implemented and verified through native isolation probes and local connection fixtures. The existing reference process depends on the runner gateway; exposing it to a normal MCP client requires integration work. IncidentHub is held back in the lab's default configuration.

## Historical implementation progress — earlier on 3 October 2026

| Workstream | Verified status | Remaining exit evidence |
|---|---|---|
| Scenario and preparation | Corpus built; old task set reviewed and superseded; regenerated thirty-task development bundle saved with implementer source review, 88 reference checks and 18 bounded scope checks | Independent task/gold acceptance, freeze and separate evaluation budget remain open |
| Hierarchy and mappings | 96 core/context artifacts mapped and reference-validated; six supplement mappings loaded and reviewed | Carry semantics and uncertainty through hydration |
| Semantic audit and resolutions | Astra low reviewed 96 sources; nine dispositions; six corrected artifacts independently rechecked in private audited candidate | Human realism review and base-world reconciliation |
| Packaging and hub hydration | 120 records loaded, including six procedure supplements and eighteen HLD/LLD drafts; all records verified through four MCP hubs | Human realism/acceptance checks, repaired independent gold and frozen manifest |
| Routing-memory hydration | Corrected 120-record snapshot refreshed through MCP; 657 proposed assertions, nine quarantined proposals, release `pilot-memory-ff53fc1f05e4` inactive. Version/hash binding, scoped review delegations, release-local authority and accepted-subject assembly implemented; full regression passes (609 passed, two skipped, six expected failures) | Owner declarations/review, pilot registry and PDLC activation proof |
| MCP integration and development trial | Both tool surfaces, session controller, evidence budgets, scorer, spend ledger and paired schedule implemented. Direct MCP fixtures completed on PDLC and unrelated shipping bundle; actual installed-Claude localhost isolation and turn-limit probes pass; one real synthetic Jev model probe succeeds; full regression passes | Reviewed PDLC memory integration with the real provider; final parallel implementation review; separately approved paid trial |
| Paired evaluation and decision | Not run | M8 / D-EXT budget, independent gold/judging and complete evidence ledger |

We are in Stage 2 (corpus and routing memory), with hub loading verified but corpus freezing and routing-memory activation pending. The [audit report](pdlc-semantic-audit-astra-low.md) and [corpus specification](pdlc-corpus-spec.md) record fixes and evidence limits. The focused resolution recheck and initial packaging/hydration are complete. All 120 current records were retrieved through the four MCP hubs. The corpus is a development candidate, with human realism review and independent gold still pending before freezing. It is a separate generated corpus using the hub loader rather than a merged world/fact overlay; base-world reconciliation is required if later combined. Missing schema bindings and event transformations are explicit gold constraints, not invented implementations.

## Pilot-0

This is the agent-level H0 experiment within [milestone M8](../milestones.md). [Discrepancy register row 20](../discrepancy-register.md) records its pending LLM-budget decision under [D-EXT](../decisions.md). Planning and prior synthetic Jev permission do not approve the new run budget.

Use two arms: direct access to the four existing simulated hubs versus Sanctum with routing memory and System One. Separate rules-only and component ablations remain deferred. Repository importers, general hydration infrastructure, real-session ingestion and production-service engineering are outside this pilot's critical path; their discussion below is follow-on planning.

The base world contains payment-auth, identity-auth, fx-quote, ledger-post and gateway-edge, but no fraud service. Author the connected fraud-timeout scenario as an overlay using the mechanism demonstrated by [the D6 challenge slice](../../world/challenge-d6.yaml). The [world builder](../../tools/build_world.py) supports separate overlay builds. Preserve the base world, use synthetic sessions, and reuse rendering, linting, provenance and gold derivation. Keep private gold inaccessible to the runtime.

Expose the reference router behind the existing gateway through a thin MCP bridge. Direct tools receive equivalent gateway observation. Proposed System One configuration is existing Jev D2 on synthetic state, with pinned model, calibration, bands and deadline profile. Verify real provider calls and memory use on development tasks, report fallback rates, and count all provider cost and latency. No evaluation-case fitting.

### Shared interaction limits

Proposed limits, validated on development cases and frozen before evaluation:

- Both arms may retrieve repeatedly, including multiple Sanctum calls, within 8 agent decision rounds. A round is one model response issuing tools or producing the final answer. Count parallel calls separately in usage.
- Each arm receives at most 8,000 cumulative evidence tokens per task and 4,000 per tool response, measured with one pinned tokenizer. Count repeated passages again. Enforce limits before delivery with an exhaustion marker. Sanctum packing is capped by the remaining allowance. Record internal retrieval separately and include schemas and metadata in total inference usage.
- Each task has a shared 120-second deadline and matching hub timeout policy. Record the System One deadline separately. Scored runs wait until the bridge demonstrably enforces the limits.
- State required-source obligations identically as caller requirements in both prompts; give Sanctum the equivalent structured input. Do not provide gold locations or optional-source hints. The direct agent is not automatically forced to comply; score compliance as workflow behavior, not discovery of hidden policy.

### Tasks and scoring

Task mix is critical and must be reviewed before evaluation freezes: target five tasks in each of the six families below, totaling thirty. Maintain a private matrix of domains, required facts, evidence sources, difficulty, answerability and version/conflict demands. Cover all five domains, single- and cross-domain reasoning, varied source needs and justified partial answers. An independent reviewer checks for repeated fact sets and paraphrased tasks; family labels alone do not prove diversity. The [harness task-diversity gate](claude-code-harness-spec.md#pilot-0-task-diversity-gate) records this requirement. Authoring and independent review remain pending; implementation may start with development fixtures.

Use 30 evaluation tasks and three repetitions per arm: 180 sessions, plus separately budgeted development and failure checks. Pilot-0 is directional, with graded supported required-fact coverage averaged per task as the primary endpoint. Binary success is secondary: all required facts supported, no materially unsupported claim, required-source obligations met, and appropriate conflict/insufficiency handling. It cannot establish a 5-point quality margin or approve deployment.

Assign evaluation-task authorship or independent revision to someone other than the runtime implementer. Development tasks use different facts rather than evaluation paraphrases. Freeze tasks, gold, accepted alternative evidence and rubric before tuning. Until independent ownership exists, label findings developer validation.

Reuse world-derived gold for mechanical canonical fact/value and citation checks. A final-answer scorer still needs implementation: the existing retrieval evaluator cannot automatically grade arbitrary prose. Freeze accepted renderings and refer ambiguous claims to blinded human adjudication. A valid artifact ID alone does not prove support. Report unsupported claims and citation precision separately from coverage.

The evaluator owns mechanical scoring independently of runtime implementation. A separate LLM judge may score plan quality against a frozen rubric. Assign a human reviewer to check a stratified 20 percent sample, all reliability failures and ambiguous claims. Blind judgments to arm identity, report judge/human agreement and disagreements, and account for judging spend separately.

### Isolation and decision rule

Run fresh headless sessions outside `~/projects`, in a temporary workspace without corpus files, with a clean configuration directory, explicit settings and strict MCP-only tools. Disable shell, local reads, web, unrelated servers, inherited project instructions, automatic memory and prior sessions. Verify installed-version behavior using startup inventories and deliberate restriction probes, not flags alone.

Randomize paired arm order and treat tasks, not repetitions or facts, as independent evaluation clusters. Report paired uncertainty and family failures. Freeze total Claude and System One spend ceilings under D-EXT before dispatch. Do not selectively rerun unfavorable answers. Report required-hub timeout and provider-unavailability checks separately.

Pilot-0 may recommend a confirmatory study, diagnose regressions or remain inconclusive. Advancement needs a consistent coverage/resource tradeoff, useful plan quality and no unresolved reliability failure; a point estimate alone is not a pass. Keep the later adoption targets below separate. Size a fresh confirmatory study using observed paired variation and a power calculation; neither 30 nor 80–100 tasks guarantees adequacy. Do not tune on frozen evaluation cases.

## Domain scenario and corpus

### LLM authored hydration

The user authorized provider-independent synthetic authoring through Gemini or OpenAI under the same $20 preparation ceiling. After Gemini 3.8 Flash returned persistent high-demand 503s, the user selected OpenAI and asked for a current cost-effective model. Use GPT-6 Luna through the Responses API, verified against official documentation on 3 October 2026 ($0.10 input / $0.50 output per million tokens). The 96 target drafts have now been generated: eight 3.8 Flash artifacts were preserved and the remaining 88 generated with OpenAI; the earlier 24 Gemini 3.5 drafts remain development evidence. Both adapters share prompts, validation, audit outputs, provenance, jittered exponential backoff and a single reservation ledger. Model selection, billing status and corpus acceptance are separate checks; no benchmark budget is implied. Jev remains the proposed runtime System One provider, and Claude Code remains the agent under evaluation.

Use LLMs wherever they improve the realism of synthetic artifacts, rather than relying solely on uniform templates. The existing world and overlay pipeline provide the private scenario structure, packaging and validation; generated prose and code supply varied source content. This requires an authoring step and integration with the renderer, not an assumption that the current renderer already generates nuanced artifacts.

First define a private scenario ledger of intended requirements, implemented behavior by version, known incidents or investigations, ambiguities and deliberately unresolved facts. It is the evaluator's record, not text to publish into hubs. Give artifact-generation calls only the local context their fictional authors would know. Generate different source perspectives in separate calls: developer code and tests, a designer's proposal, reviewed procedures, hurried investigation notes and session conversations. Keep benchmark prompts and answer keys out of generation inputs.

Ask for plausible imperfect evidence: uneven detail, domain jargon, aliases, partial explanations, abandoned hypotheses, stale documents, disagreement between intent and implementation, incidental repetition and incomplete cross-references. Vary author voice, chronology and document structure. Avoid making every artifact neatly agree or state a complete answer. Distinguish deliberate inconsistency from accidental generation errors in the private ledger; retain useful ambiguity rather than normalizing it away.

Validate generated artifacts against the scenario ledger and source provenance. For implementation claims, inspect or execute the generated code and relevant tests where feasible; model assertions alone are not gold. Record newly introduced claims and resolve them into the ledger or mark them unsupported before freezing. Adapt lint checks to permit declared messiness while still detecting identifier leaks, broken provenance and unintended world inconsistencies. Human spot checks assess whether the artifacts look like ordinary engineering material and whether scenario assumptions are credible.

Freeze generated outputs, prompts, model versions and hashes so benchmark repetitions use identical data; regenerating with a seed is not a reproducibility guarantee. Derive expected evidence only after the corpus audit. Use independent task authorship or review to limit generator/evaluator bias. A separate LLM can assist review, but it cannot alone establish independent gold. Apply the same frozen corpus to both arms.

Corpus-generation inference is part of the preparation budget and must be explicitly bounded before execution. The selected authoring models and $20 preparation ceiling are recorded above; benchmark inference still needs its separate budget decision. Report generation and review cost separately from benchmark inference cost.

Proposed first scenario: change payment authorization behavior when a fraud decision times out, including the identity context needed to interpret the request. Follow one connected journey from requirements through design, implementation, testing and rollout. This is a fictional payments enterprise scenario.

Use a clearly labeled synthetic domain corpus initially. Authorized internal artifacts could later replace it in a separately scoped real-data slice. Public repository imports establish that ingestion works on real files, but cannot establish usefulness for a payments PDLC by themselves.

Domains cut across hubs; hubs distinguish evidence types. The same service should have related code, requirements, procedures and investigation history.

| Hub | Proposed contents | Interpretation |
|---|---|---|
| CodeHub | Authorization, fraud and identity implementations, configuration, interfaces, dependencies and tests | What the pinned implementation does |
| SkillHub | Explicit testing procedures, reviewed development practices and rollout rules | What the reviewed procedure requires; preserve review status |
| DocHub | Requirements, architecture decisions, API contracts, migration plans and version changes | Reference evidence; no default blanket authority |
| MemoryHub | Prior investigations and engineering sessions linked to the same projects | What occurred or was concluded in a session, not proof the conclusion is correct |
| IncidentHub | Relevant timeout incidents and observed recovery behavior | Optional fifth-hub extension after the four-hub comparison |

Include aliases shared across domains, old and current versions, conflicting design and implementation evidence, documents discussing several services, irrelevant neighboring material and deliberate coverage gaps. Build enough distractors to make source selection meaningful. Keep the corpus independent of evaluation prompts and answer keys.

## Follow-on hydration and routing memory

Import selected repositories into the hub artifact format at a recorded commit SHA. Preserve repository URL, path, source line range, version, domain, artifact type and provenance. Split large files into bounded searchable passages without losing their original location. Exclude dependencies, binaries and generated files; document all selection rules.

Route source code to CodeHub, design and reference documents to DocHub, and explicit skills or runbooks to SkillHub. Do not infer that an instruction file is a reviewed authoritative procedure. Duplicate evidence across hubs must retain a shared origin so assembly can recognize copies.

Pilot-0 uses synthetic sessions only. Real sessions are follow-on work requiring a defined scope, a scrub for credentials, proprietary and third-party content, and explicit user sign-off on the retained sample and destinations. Existing hosted-provider permission covers synthetic data only. Exclude benchmark executions and answer keys from runtime memory.

Seed Sanctum routing memory with reviewed project names, canonical subjects, repository and document locations, query translations and applicable procedures. A document about a service must not become an identity alias for that service. Record the routing-memory release alongside the corpus manifest.

Deliverable: reproducible corpus build, source manifest, routing-memory release and a sample retrieval report. Required verification covers known facts, exact citation locations, version selection, missing evidence and source failures.

## Pilot routing-memory hydration — required before the first demo

MemoryHub session evidence is loaded, but Sanctum routing memory is not hydrated for this pilot. The existing r1/r2 releases describe the original lab corpus and cannot be reused blindly against the new repositories and spaces. This work follows [memory design sections 11–12](../../design/intelligence-layer/memory-design.md), including the stable contract / entity types / instances distinction. System One and this memory remain prerequisites for the first Claude demonstration, not later ablations.

Build a separate, provenance-backed candidate release from the public hub records, capabilities, native repo/space/path/session structure and explicit pilot source-owner declarations. Use LLMs to propose scoped vocabulary and descriptors where useful; every proposal retains supporting public record/version references and review status. No private introduced claims, audit gold, evaluation tasks or answers enter routing memory. A hierarchy navigation assignment alone cannot establish service identity, domain membership or authority.

1. **Source map:** four pinned source descriptors and capabilities, fact-kind authority from explicit registry declarations, and coverage declared separately from coverage measured by development probes. Unknown coverage stays unknown; finding one artifact does not prove comprehensive coverage.
2. **Vocabulary:** canonical entities plus source/namespace-specific Terms. Use reviewed `DENOTES` for names, `SELECTS_FOR` for searchable places, `PARENT` for native navigation and `MEMBER_OF` for reviewed semantic membership. Keep Auth ambiguity and unresolved flag/service aliases. Generic dashboard labels and document titles do not silently become identities.
3. **Routing procedures:** reviewed must-consult rules and supported source-specific selectors for applicable fact kinds; these describe which hub to ask, not the payment rollout steps stored in SkillHub. Verify every selector against the hydrated paths and hub capabilities.
4. **Artifact bindings:** public artifact/version/hash records and provenance-backed `ABOUT` bindings, including unknown subjects. Only exact content equality supports duplicate bindings; version lineage requires explicit evidence. Navigation containers are not evidence that every record discusses their service.
5. **Observations:** record development routing receipts, misses and unresolved terms from day one. Do not fabricate historical success or activate learned routing behavior from evaluation runs; the HLD gates that later use.

The reference memory now additionally stores Artifact/ABOUT records and exposes accepted-only, hash/version/access-bound subject lookup in both backends. This API is tested but not yet wired into runtime evidence assembly; close that integration gap before claiming the full ontology is active. Reuse the existing versioned manifest and relation-store interfaces; no new database/service is required by this pilot.

Validate scoped identity conflicts, unknown terms, ambiguous Auth interpretations, multi-domain artifacts, actual filters, procedure applicability, visibility and unsupported version reads. Independently review candidate assertions; proposed/shadow assertions stay operationally inactive. Publish and pin one coherent pilot release with the corpus hash, registry, descriptors and decision settings; rollback must preserve the original lab release. Keep authorization live. The end-to-end demo must expose observed release use, query translations and real System One calls in traces.

Deliverable: candidate/reviewed pilot memory manifest, projection/runtime support for attributed subjects, provenance and review record, selector/ambiguity checks and an activation configuration. Candidate hydration has run; owner review, declarations and runtime activation remain pending. Do not label the pilot memory active from the existence of the corpus hierarchy or generated proposals.

## Claude Code integration

The [reusable harness specification](claude-code-harness-spec.md) defines scenario bundles, public tasks/private gold, session-bound MCP handshakes, isolation, limits, result records and implementation slices. Pilot-0 is its first configuration; repository/domain names are data rather than runner branches. Evidence-only mode comes first, with matched local checkouts and test-based scoring deferred to coding mode. The specification is written; the launcher and MCP adapter remain unimplemented.

For Pilot-0, build only a thin MCP bridge around the existing reference router and gateway. A reusable standalone service is follow-on work. Keep authentication and hub-token handling inside the service boundary. Reuse existing hub search and retrieval rather than implementing a second retrieval engine.

Enable a pinned routing-memory release and a real System One provider from the first end-to-end demonstration. Choose and record the provider, resolved model version, decision types, calibration, uncertainty bands and deadline behavior before evaluation. The existing Jev and local Laya integrations are candidates; provider selection remains open. Verify observed System One calls and memory use on development cases. Report fallback and abstention rates so an enabled but consistently bypassed provider cannot be presented as a demonstrated System One contribution. Evaluate the complete stack regardless of whether individual decisions change outcomes.

Provide two explicit client configurations: direct access to the four hub interfaces, and access to Sanctum alone. Verify the installed Claude Code version and effective tools at startup. For the initial retrieval experiment, disable alternate evidence paths such as local repository reads, shell, web, unrelated MCP servers, inherited project instructions and prior sessions. Run from an isolated workspace without the corpus files. Verify these restrictions empirically rather than assuming one configuration flag provides complete isolation.

Require retrieval before an evidence-supported answer and verify actual calls in the transcript. Missing retrieval is a recorded protocol failure, not a silently discarded run. Record Claude events and independently observed Sanctum and hub calls with request identifiers. Do not depend on the agent's own description of which tools it used.

Deliverable: a reproducible launcher, explicit configurations and an end-to-end demonstration with citations. Interactive use follows this verification. Coding tasks that need local files and execution form a subsequent experiment with matched workspace access.

## Tasks and expected evidence

Proposed initial scope is about 30 evaluation tasks, plus a separate development set used for integration and tuning. Before implementation tuning, freeze evaluation prompts, expected facts, supporting artifacts, accepted alternative evidence, scoring rubric and corpus versions. The evaluator must not be the runtime system; independent human review is needed before calling the benchmark independently validated.

| Task family | Example | What to check |
|---|---|---|
| Understand behavior | What does authorization do when the fraud call times out? | Correct service, release and implemented behavior |
| Assess impact | Which interfaces and consumers are affected by a timeout change? | Cross-domain dependency coverage and grounded scope |
| Plan implementation | What changes are needed to implement the new requirement? | Requirement-to-code connection and explicit uncertainties |
| Plan testing | Which failure paths and regression tests are required? | Procedure requirements and implementation coverage |
| Plan rollout | What must be checked before enabling the change? | Applicable rollout procedure and operational evidence |
| Handle uncertainty | An old design disagrees with current code; what can we conclude? | Versions, evidence roles, conflict preservation and appropriate abstention |

Begin with read-only understanding and planning tasks. Executable patch tasks require their own test-based outcomes and are deferred from this first evaluation.

## Comparisons and run controls

| Configuration | Agent evidence access | Purpose |
|---|---|---|
| Direct hubs | All four hub tools; Claude chooses which to use | Strong primary baseline, not forced fan-out |
| Sanctum with memory and System One | Sanctum retrieval with a pinned routing-memory release and a real System One provider | Test the complete proposed intelligence layer against direct hubs |

Rules-only, memory-only and provider ablations are deferred diagnostic experiments. The primary comparison can establish the value of the combined stack, but cannot attribute a gain to memory or System One individually.

All configurations use identical hub corpora, caller permissions, required-source obligations, model version, task prompts, answer rubric and resource ceilings. Document interface differences as part of the treatment. Match timeout policy and available backend capabilities. Freeze configuration mappings instead of assuming existing synthetic lab arms already implement this comparison exactly.

Use fresh sessions for every task and configuration. Proposed pilot repetition is three runs per task per configuration, with randomized configuration order and failure conditions paired where practical. Judge final answers without revealing the configuration. Aggregate paired results by task; repetitions are not independent new tasks. Fix the model and effort before testing, retaining the user's settings unless a different choice is agreed.

Start with the declared no-failure environment, then run a separately reported controlled failure slice, including System One unavailability. Set an explicit run count, total token or monetary ceiling and stop conditions before paid execution. Stop on infrastructure failures; record failed cases and do not selectively rerun unfavorable answers. Include System One inference usage and latency in all resource totals from the first pilot.

## Success criteria and adoption decision

Pilot-0 uses graded supported required-fact coverage as its primary endpoint, with binary task success secondary. Record required-fact coverage, correctness, citation validity, conflict handling and appropriate partial or insufficient responses. Resource metrics include total Claude and router inference cost, input and output tokens, evidence tokens, model calls, hub calls and end-to-end latency. Keep evidence tokens distinct from inference usage. Include Sanctum overhead; report ingestion and indexing costs separately and explain any amortization assumptions.

| HLD goal | Evaluation measure |
|---|---|
| G1 valid evidence within budget | Task success, required-fact coverage and appropriate abstention |
| G2 fewer useful backend calls without required omissions | Hub calls plus required-source compliance |
| G3 conflicts and provenance | Citation validity, version accuracy and conflict handling |
| G4 inexpensive fast path | Total cost and latency, including router overhead |
| G5 explain each response | Source decisions and reasons reconcile with observed traces |
| G6 onboarding without core edits | Later configuration-only source onboarding check |

Proposed targets for a later adequately powered confirmatory study, not Pilot-0 pass thresholds:

- Quality route: at least a 10 percentage-point increase in task success over direct hubs under the same declared resource ceilings.
- Efficiency route: at least 20 percent lower total inference cost, with task success no more than 5 percentage points below direct hubs. Token and latency results remain separately reported; fewer source calls are not a substitute for lower total cost.
- Reliability gate: no observed fabricated citations, silent required-source omissions or claims of completeness when known required evidence is absent in the controlled checks. Any occurrence triggers diagnosis before adoption. Zero observed failures does not prove a zero failure rate.

Report paired differences and uncertainty, including per-family failures. For an adoption claim, the quality gain must be supported beyond an isolated point estimate; the efficiency route must support both savings and the quality margin. Roughly 30 tasks may not establish a narrow margin. An inconclusive result leads to a larger fresh evaluation, not retuning on the frozen set or weakening thresholds after seeing results.

Possible decisions: expand the read-only pilot, fix a specific diagnosed limitation and evaluate on fresh cases, collect more evidence, or retain direct hub access. Existing synthetic router results do not establish this agent-level benefit.

## Pilot-0 stages and follow-on decisions

| Stage | Deliverable | Exit evidence |
|---|---|---|
| 1 scenario and benchmark specification | Connected domain story, artifact inventory, task rubric and proposed thresholds | Product review of PDLC relevance; thresholds and run budget settled |
| 2 overlay corpus | Separate synthetic build, authored sessions, routing memory and gold | Linter/provenance checks; base world unchanged; labels hidden |
| 3 client integration | Thin MCP bridge around the existing gateway and reference router, with memory and System One | Observed calls, shared limits, memory use and isolation verified |
| 4 development trial | Small trial on development tasks only | Operational failures resolved; configurations frozen |
| 5 evaluation | Paired repeated runs and blinded scoring | Complete run ledger, failures, resource accounting and uncertainty |
| 6 decision | Directional report and next-study recommendation | No unsupported adoption claim |

The user subsequently authorized synthetic preparation and implementation. Corpus generation, hierarchy and audit resolution have progressed as recorded above. Benchmark execution still needs a separate approved run budget; no delivery dates or internal data access are assumed. During active work, provide brief progress updates identifying what is complete, the current step and any blocking issue.

## Decisions to settle before implementation and evaluation

Confirm the overlay inventory, independent task author, evaluator and judge/human-review ownership. Agree the Claude model and effort, pinned Jev settings, shared interaction limits and total spend ceiling under D-EXT. Real-session selection, repository importers, live synchronization, reusable service engineering, interactive use and fifth-hub onboarding are follow-on decisions.

The scenario and inventory now exist. The current next steps are remaining corpus-acceptance checks and thin Claude/Sanctum MCP integration; scored runs wait for independent gold, freezing and the budget decision. Independent task and scoring specification remains required before benchmark tuning. The final evaluation package includes manifests, runnable configurations, prompts, expected evidence, observed traces, scores, failures, resource totals and the adoption recommendation.

## Ontology pipeline implementation evidence

The reusable pipeline has harvested all 96 records through MCP, using a complete permission-filtered pilot inventory. The first candidate contains 222 ABOUT, 150 DENOTES, 97 SELECTS_FOR and 13 PARENT assertions (482 total); four invalid quote proposals were quarantined. Explicit membership/authority/procedure declarations are supported inputs, but none were supplied for this run, so no semantic membership or policy was invented. GPT-6 Luna semantic generation cost an estimated $0.012718 across 16 calls in the existing preparation ledger. Candidate/review artifacts and content-addressed memory releases are under `build/pdlc-memory`; no active pointer changed. Source-neutral collection handles pagination, snapshot changes and incomplete inventories without deletion inference. Focused tests cover review gating, scoped identity conflict, stale/inaccessible subjects, principal checks, false evidence, pagination failures and explicit owner-policy inputs. Existing lab memory and scenario regressions were also checked. Actual remote hubs require their own native inventory adapter; this pilot does not claim those connectors are built.

Domain coverage was expanded with six grounded draft procedures: Ledger and Platform now have SkillHub representation and Identity coverage is stronger. All five domains are represented across all four hubs; this does not imply comprehensive coverage. The corpus totals 102 artifacts (25 code, 31 docs, 16 skills, 30 sessions), verified through MCP. Original generation/audit records remain unchanged. Routing-memory harvesting refreshed the candidate against all 102 artifacts, producing 504 proposed assertions and quarantining five invalid proposals. Activation remains pending.

## Astra low review of expanded corpus and memory pipeline

The [independent review](pdlc-domain-coverage-memory-review-astra-low.md) accepts the six new procedures as unapproved, unexecuted drafts for read-only development. It confirms all five domains have metadata associations in all four hubs, not measured comprehensive coverage. Twenty-five narrow harvest/memory tests passed. Before using affected capabilities operationally, resolve four findings: delegated reviewer scope, version/hash identity for semantic proposals, immutable release-local authority/registry pinning, and live authorization/revocation around subject/metadata exposure. The current all-proposed, inactive 504-assertion candidate remains appropriate. These are tracked activation/integration requirements, not approval to activate.
