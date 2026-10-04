# PDLC corpus scenario and authoring specification

Status: initial implementation specification, 3 October 2026. Synthetic only. The 96-artifact target has been generated (8 Gemini 3.8 Flash and 88 GPT-6 Luna drafts), in addition to 24 earlier Gemini 3.5 development drafts; semantic audit and hub ingestion remain incomplete. This develops the [Pilot-0 plan](pdlc-claude-code-pilot-plan.md); the scenario numbers below are proposed choices, not observed production behavior.

Authoring provider update: the user authorized Gemini and then OpenAI for synthetic corpus generation under one $20 preparation cap. GPT-6 Luna is the current cost-effective OpenAI selection, verified against official documentation on 3 October 2026. Credentials live only in gitignored local configuration. The runner supports explicit provider/model selection, common prompts and output validation, jittered exponential backoff, per-attempt reservations and a shared ledger. No benchmark budget or new cash purchase is implied.

## Scenario

A payment authorization service calls a fraud decision service before accepting a payment. A change proposal replaces an ambiguous timeout result with an explicit pending-review state. Identity context, retry behavior and downstream ledger effects make the change cross-domain. The current implementation, proposed requirement and rollout procedure do not all describe the same release.

Extend the existing world through a separate overlay build. Reuse payment-auth, identity-auth, ledger-post and gateway-edge, and add a fraud-decision service and fraud domain. Do not replace existing facts silently. New attributes describe this journey specifically; record any conflict with the base world before adding them.

## Private scenario ledger

These proposed truths and intentional gaps belong in evaluator-side authoring material. Private identifiers and this ledger must not appear in hub-visible artifacts. Audit generated code before treating implementation claims as gold.

| Subject | Proposed state | Evidence distinction |
|---|---|---|
| R41 fraud timeout | Payment authorization returns a generic dependency error | Old implementation; not the proposed behavior |
| R42 current path | Configured fraud HTTP transport timeout is 800 ms; timeout still returns the generic error. No total end-to-end deadline is established | Current code; old design describes a 500 ms target |
| Proposed change | Timeout produces pending-review, never an approved payment | Requirement, not deployed implementation |
| Retry identity | Attempts for one authorization preserve an idempotency key | Procedure and code must be inspected separately |
| Identity context | Tenant and authenticated subject are required inputs to the fraud request | Shared interface contract |
| Ledger behavior | Only approved authorization may produce a posting; pending-review cannot | Cross-service constraint |
| Rollout | Feature flag starts disabled, with tenant-scoped canary and rollback | Reviewed proposed rollout procedure |
| Investigation | One session suspects duplicate posting from retries, then retracts the hypothesis | Session history is not a verified defect |
| Deliberate gap | Exact production capacity and the required canary duration are unknown | Correct answers must identify missing evidence |
| Naming ambiguity | “Auth” may refer to payment or identity authorization | Memory should preserve domain distinctions |

Do not reuse these evaluation facts as development questions. Before task authoring, create separate development facts and audit that neither gold IDs nor evaluation prompts enter generated content.

## Initial artifact inventory

Model update: Gemini 3.8 Flash generated eight artifacts, then repeatedly returned HTTP 503 UNAVAILABLE for the design packet, explicitly reporting high demand. Bounded jittered retries did not clear that failure. The user subsequently authorized OpenAI, selected the latest cost-effective model, and requested provider-independent generation. The OpenAI adapter uses GPT-6 Luna ($0.10 input / $0.50 output per million tokens) with medium reasoning and JSON output. Gemini remains explicitly selectable as 3.8 Flash; do not substitute 3.1 Pro. Completed compatible packets are skipped across providers. Earlier 3.5 Flash drafts remain development evidence. Semantic audit findings on the new code still need resolution before freezing. Failed-call reservations remain held until billing reconciliation; the generation ledger is authoritative for counts and costs. OpenAI generation of the remaining 88 artifacts completed. Saved response hashes match the ledger, and all extracted Python blocks parse; seven code artifacts need Markdown fence extraction during packaging. The 96 selected drafts have an estimated generation charge of $0.06381; all completed preparation calls, including the older development drafts and availability diagnostic, total $0.23967. Unresolved failed/interrupted-call reservations of $18.02 remain held against the $20 cap and are not a claim of actual billed charges. A credential precedence issue was corrected: project-local keys now override inherited environment variables; the interrupted request retained its reservation and provenance note. The private build manifest `build/pdlc-authoring/corpus-draft-summary.json` records counts, models, integrity checks, packaging issues and cost scope. No generation process remains running. Corpus acceptance, hydration and benchmarks remain pending.

Target 24 connected core artifacts plus 72 surrounding artifacts, for 96 authored artifacts alongside existing background material. Use the explicitly selected OpenAI provider for this resume; preserve Gemini 3.8 Flash provenance on completed artifacts. The initial Gemini 3.5 Flash drafts are retained as development evidence, not final corpus content. Add neighboring services, old discussions, incomplete handoffs and mixed-relevance documents; expansion must increase realistic information distribution rather than duplicate answer-bearing passages.

| Hub | Count | Artifacts |
|---|---|---|
| CodeHub | 8 | R41 and R42 authorization handlers; fraud client; identity request schema; ledger consumer; feature-flag config; timeout tests; idempotency tests |
| SkillHub | 4 | Payment change checklist; fraud timeout test procedure; tenant-canary procedure; rollback procedure |
| DocHub | 7 | Old timeout design; current API contract; proposed pending-review requirement; cross-domain review discussion; ledger integration note; unfinished capacity note; unrelated identity-auth guide |
| MemoryHub | 5 | Initial investigation; retracted duplicate-posting hypothesis; design handoff; incomplete rollout discussion; unrelated identity debugging session |

Give each artifact a native path or session reference, author role, chronology, applicability and provenance. Deliberate contradictions must be identifiable in the private ledger while remaining natural in the published material. At least some documents span several services and use inconsistent shorthand. Do not hide all required information behind a single conveniently complete document.

## LLM authoring packets

Prepare separate packet files for a payment developer, fraud developer, identity developer, ledger developer, designer, procedure reviewer and investigation participants. Each receives only the applicable local facts and excerpts available to that role, not the full ledger, question set or answer key. Packets may include intentionally stale knowledge when chronology explains it.

Use this common instruction with each role-specific packet:

> Write the requested fictional engineering artifacts from this author's perspective using only the supplied context. Preserve incomplete knowledge. Use realistic domain vocabulary, uneven detail and ordinary engineering structure. Do not mention benchmark tasks, evaluator labels or private identifiers. Do not make every artifact a summary of all facts. Label proposals and uncertainty naturally. Return native artifact text and a separate manifest of new claims, assumptions and contradictions for audit. Do not invent production observations or approval status not present in the packet.

Role-specific goals:

- Developers produce plausible implementation and tests, including behavior that can be checked. Comments may lag implementation when explicitly assigned; executable behavior must remain inspectable.
- Designers produce a proposal and tradeoffs, distinguishing current behavior from the intended change. Include open questions and partial cross-references.
- Procedure reviewers produce focused normative requirements with stated review status. Do not pretend a proposed procedure is approved.
- Investigation participants produce conversational turns with tentative explanations, corrections, missing context and an unresolved follow-up. Separate speculation from observed evidence.

Generate candidate artifacts once per packet, then revise only for audited problems. Retain declared messiness; do not polish every artifact into a uniform template. Save model identity, prompt, output, timestamp and hashes. A seed alone does not make model generation reproducible.

## Validation and integration sequence

1. Check the proposed ledger against existing world facts and schema constraints. Resolve vocabulary and version mappings before generation.
2. Write local author packets and choose the authoring model and bounded preparation budget.
3. Generate artifacts and retain raw outputs outside hub-visible files. Do not invoke paid generation until the budget is settled.
4. Audit introduced claims, code behavior, contradictions and provenance. Review a sample for realistic voice and information distribution. Update the private ledger or remove unsupported accidental claims.
5. Package accepted content into the existing hub format and add the smallest renderer support needed to preserve generated text and spans. Run world lint, leak checks and provenance checks on a separate build.
6. Seed routing-memory names, places and procedures, freeze corpus hashes, and hand the corpus to independent evaluation-task authorship or review.

All generation and audit costs belong to preparation, separately reported from benchmark cost. The first authoring run used `tools/generate_pdlc_corpus.py` with Gemini 3.5 Flash. Four completed calls produced 24 draft artifacts in the gitignored `build/pdlc-authoring` directory, alongside prompts, responses, hashes, usage and audit findings. The code syntax checks pass. Generated code inconsistencies, unassigned version semantics, invented historical behavior and unnatural instructional comments still need reconciliation. No artifact is promoted to hub evidence; no benchmark has run.

## Hierarchy and ingestion mapping workstream

The user requested LLM-assisted, evidence-grounded hierarchy for code, documents, procedures and session history, including cross-domain repositories and many-to-many team responsibilities. Raw author packets are not repository boundaries. The catalog and all 96 per-artifact mappings have been authored using GPT-6 Luna and passed reference validation under the existing preparation cap. Semantic acceptance remains pending. The shared generator now accepts structured JSON jobs, preserving the same provider adapters, provenance, budget ledger and retry policy.

`tools/map_pdlc_hierarchy.py` prepares a catalog anchored to existing world domains/services, then supplies full source content for per-packet assignments. Each node/relationship distinguishes observed, inferred, proposed synthetic design, and unknown. Synthetic team labels and repository boundaries are proposals, not claims about an actual organization. Reference checks reject cycles, missing parents, duplicate nodes and quotations absent from cited artifacts. Assignments preserve source file hashes, original paths and versions; ownership does not supply access permissions. Final manifest validation requires one mapping for each of the 96 drafts. Semantic audit, renderer integration, ACL assignment and runtime hydration remain separate workstreams.

The private manifest is `build/pdlc-authoring/pdlc-hierarchy.json`: 38 nodes (five domains, nine services, six repositories, six document spaces, seven collections and five proposed teams), 65 relationships and 22 container responsibility assignments. Content-based assignment yields CodeHub 25, DocHub 31, SkillHub 10 and MemoryHub 30; 25 artifacts span multiple domains. Each container has one primary maintainer; some repositories have multiple teams and some teams maintain multiple repositories. Labels and ownership introduced for this fictional pilot are explicitly marked synthetic design. Exact quotations include source fields and character spans. Four quote-only corrections were applied to derived mappings; source artifacts were preserved.

Completed preparation calls now total an estimated $0.29034, including hierarchy work; unresolved reservations remain $18.02. These estimates are distinct from billing reconciliation and the benchmark budget.

Remaining workstreams, in order:
1. Semantic audit: reconcile code/contracts, versions, deliberate conflicts, realism and benchmark leakage; repair only justified gaps.
2. Packaging and hydration: extract code, bind the hierarchy to hub records, define applicable access metadata, integrate the overlay renderer, load and verify retrieval, then freeze a versioned manifest.
3. Claude Code integration: thin MCP bridge, isolated sessions, direct-hub and Sanctum configurations, with System One and memory enabled initially.
4. Evaluation: independently authored tasks and gold evidence, development checks, frozen rubric, paired runs and judging. Benchmark execution remains subject to the separate M8 / D-EXT model-budget decision.

## Independent semantic review

Astra with low reasoning completed the [source-content review](pdlc-semantic-audit-astra-low.md) of all 96 selected artifacts. Nine findings distinguish repairs, intentional messiness and unresolved coverage. The highest-priority findings are incompatible R41 client/test bindings, the difference between a configured transport timeout and a total response deadline, and absent identity schema-to-wire binding. Canonical-service links and public/private identifier separation also need correction before hydration. No generated code or benchmarks were executed, and corpus acceptance remains pending.

## Audit resolution candidate

`python3 tools/resolve_pdlc_audit.py` reproducibly writes the private `build/pdlc-authoring/pdlc-audited-candidate.json`. It preserves all raw generation files and records content revisions, raw hashes, corrected-content hashes, derived hierarchy changes, all nine finding dispositions and gold constraints. Six source artifacts are corrected; exact quotations and navigation are rechecked. The historical timeout branch was exercised with explicit dependency stubs, not a complete deployed package. Astra's focused recheck found no additional concrete source-semantic blocker for the read-only pilot under the recorded gold constraints. Packaging boundaries, human realism review and base-world reconciliation remain pending. This candidate has not replaced the runtime corpus.

The read-only pilot may use explicitly incomplete interfaces and source sketches. It must not score schema/client agreement, authenticated context enforcement, full event transformation, exactly-once posting or complete test execution as established facts. Packaging must preserve snippet boundaries, distinguish private audit IDs from public citation IDs, exclude private claims/rationale, and verify those boundaries before promotion. Human realism assessment and base-world conflict reconciliation remain acceptance checks.

## Pilot ingestion — development candidate

The audited 96-artifact candidate is now packaged at `build/pdlc-pilot`, separately from `build/world`. This first cut is a standalone generated corpus using the existing HubRow schema, HubStore loader, SQLite FTS5 search and MCP servers; it is not a merged world/fact overlay and does not create world-derived gold. That smaller integration preserves authored source text without extending the template renderer. Base-world reconciliation remains required if those worlds are later combined.

Run `PYTHONPATH=src .venv/bin/python tools/ingest_pdlc_corpus.py`, then `PYTHONPATH=src .venv/bin/python tools/verify_pdlc_ingestion.py`. Public rows include opaque citation IDs, paths, versions, chronology, review status and navigation/ownership metadata. Private mappings, source-file lineage, gold constraints and acceptance records stay under the build's private directory. An explicit `pdlc-pilot` read group is assigned equally to both future arms; synthetic teams confer no access rights. MemoryHub notes belong to the single fictional `pdlc-pilot-reader` actor for this pilot, not to the various speakers mentioned in their content. Artifact revision 1 means its sole ingested source version; it does not assert production deployment. The pilot identity directory declares that principal and group for the existing token service.

Counts: CodeHub 25, DocHub 31, SkillHub 10, MemoryHub 30. Three single code fences were unwrapped, three multi-snippet documents retain their boundaries and the other 90 source texts are unchanged from the audited candidate. No snippets are claimed to constitute complete runnable repositories. Publication validation caught an additional private-ID-derived path in pdlc.085; its derived path was corrected without changing raw source content. All published rows exclude the private enumeration.

Verification launched all four existing hub MCP servers over stdio, fetched all 96 records, compared exact text/version/metadata and citation spans, searched each hub, verified six listed code repositories, checked missing-token denial, unrelated-group search exclusion and MemoryHub principal scoping. Public manifest hashes match the files; the loader rejects private build paths. The private verification report is `build/pdlc-pilot/private/ingestion-verification.json`. This required no model calls. Human realism assessment, independent tasks/gold and final freeze remain pending. Claude Code and Sanctum routing integration are not yet connected to this corpus.

## Domain coverage supplement

Six LLM-authored draft procedures were grounded in public hub records, source-inspected and ingested: two Identity onboarding/session checks, two Ledger batch/posting/read-failure checks, and two Platform route-selection/observability/timeout checks. They retain `draft; review pending`; source inspection does not constitute business approval or executed validation. Ledger and Platform now each have two SkillHub artifacts, and Identity has three. All five domains are represented in each of the four hubs, while specific interface/alias/capacity gaps remain.

The separate expanded candidate is `build/pdlc-authoring/pdlc-expanded-candidate.json`, with 102 records; the original audited 96-artifact candidate and raw generation are preserved. Reproduce the supplement with `tools/extend_pdlc_procedures.py prepare`, the shared provider generator using `coverage-procedures.jobs.json`, then `apply`; a source-hash-bound review record permits draft promotion. Load using `tools/ingest_pdlc_corpus.py --candidate build/pdlc-authoring/pdlc-expanded-candidate.json`. All 102 records passed MCP read/search/access/citation verification. Current hub totals: CodeHub 25, DocHub 31, SkillHub 16, MemoryHub 30. Corpus remains a development candidate, not frozen. The ontology harvesting pipeline has refreshed against the expanded snapshot: 504 candidate assertions (232 ABOUT, 156 DENOTES, 103 SELECTS_FOR, 13 PARENT), with five invalid proposals quarantined. It remains inactive pending scoped review, declarations and runtime integration. The six-procedure generation charge is estimated at $0.0034081 in the shared preparation ledger.
