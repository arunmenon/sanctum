# One-shot harness plan review — Astra low

Reviewed 3 October 2026. Scope: `claude-code-harness-spec.md`, the PDLC pilot plan, and selective inspection of `src/sanctum_run/{gateway,proxy,process_sut}.py`. This is a single design review, not a runtime audit or implementation verification. No model benchmark calls, secrets inspection, or runtime changes were performed.

## Recommendation

Proceed with the small, unpaid bundle/MCP implementation slices, incorporating the findings below. Do not dispatch paid development or evaluation runs yet. The specification correctly identifies the launcher, Claude MCP bridge and final-answer scorer as unimplemented; its readiness gates are requirements, not evidence that isolation, accounting or scoring already works.

The basic design is sound: equal evidence-supported fact coverage, separate completion criteria, explicit uncertainty obligations, delivered-evidence citation checks, blinded adjudication and task-level pairing address major evaluation pitfalls. Repository data belongs in bundles, and a single Claude adapter behind a small interface is sufficient. Deferred coding mode, additional agents, databases and hosted services should remain deferred.

## Findings

### H1 — The monetary ceiling has no enforceable dispatch contract

The example declares total inference spend and requires a budget check, but does not define how the controller reserves cost for an in-flight Claude attempt plus nested System One calls, retries and judging. A 120-second deadline and evidence-token limit do not bound inference cost. Missing usage is correctly marked unknown, but the specification does not say whether further dispatch stops when the remaining budget can no longer be established.

**Action:** Before paid dispatch, define the budget scope, approved pricing basis, per-attempt maximum or conservative reservation, nested-call limits, retry reservation and reconciliation rule. Stop new dispatch when accounting is unknown or a reservation cannot fit. If the provider cannot provide a hard spending bound, state the possible in-flight overshoot and require that exposure to fit the approved ceiling. Keep judge spend reserved or separately capped. This is an implementation requirement, not a request for a new billing framework.

### H2 — Shared limits and evidence normalization remain underspecified

The specification warns that CLI turns differ from agent rounds, but never defines a harness round, parallel-tool accounting, or how repeated Sanctum requests consume any internal retrieval limits. It also does not explicitly define the common delivered-evidence unit for direct hub search results versus Sanctum responses. This affects both fairness and whether the scorer can reliably prove that a cited passage was actually delivered. Counting only assembled passages could leave evidence-bearing search snippets, metadata or error bodies outside the limit.

**Action:** Freeze one concrete round definition and the adapter mapping before trials. Define a common evidence record with source/artifact/version/hash and actual delivered coordinates; specify treatment of search snippets, structured/text duplicates, partial units, metadata and concurrent results. Apply an atomic cumulative counter before delivery. State separately which internal backend/System One work is capped and which is merely costed. Add saved fixtures covering equivalent direct/Sanctum references and budget exhaustion during parallel calls.

### M1 — Failed and incomplete pairs lack a primary-analysis rule

The terminal ledger preserves failures, but neither document specifies their numerical treatment in the primary aggregate. Excluding a launch failure, protocol failure, truncated answer or missing arm can change the paired result, especially if one treatment fails more often. Three repeats per task and directional claims are handled appropriately, but are not a substitute for this rule.

**Action:** Freeze the planned-attempt denominator, partial-answer scoring, failure categories and incomplete-pair treatment before execution. Report reliability over all dispatched attempts and distinguish outcome failures from infrastructure-invalid comparisons. Choose and record one task-clustered paired uncertainty method; report exclusions and their arm distribution. Do not turn unexecuted tasks after an infrastructure stop into successful or silently excluded evaluation observations.

### M2 — Existing process transport is not the promised isolation/lifecycle implementation

`ProcessSUT` passes through `HOME`, launches from the repository root, and its `_stop` terminates the immediate process; it does not demonstrate descendant termination. That is not itself a defect for the current trusted router, but reuse must not be mistaken for Claude workspace/config isolation or process-tree containment. The specification correctly leaves actual CLI verification pending.

**Action:** Keep trusted router transport separate from the Claude launcher boundary. Add an explicit acceptance matrix for inherited user/project configuration, hooks/skills/memory, extra MCP discovery, built-in tools, local corpus access, authentication and descendant cleanup. Verify using harmless canaries and an owned child-process fixture with the pinned installed CLI; save effective settings and observed results. Require pending calls and caller bindings to close on cancellation. Tool inventory alone is insufficient evidence for configuration isolation.

## Nonblocking clarifications

- Freeze an actual answer-envelope schema and the disposition of malformed answers. The current “prefer” language conflicts with a first scoring stage that requires that envelope. Preserve prose and report schema failure; decide in advance whether recoverable prose receives graded scores while remaining protocol-incomplete.
- Specify the unit of claim segmentation and the trigger for “judge disagreements.” A single semantic judge plus human review is sufficient for this pilot; do not introduce a multi-judge service solely to satisfy that phrase.
- The all-dimensions-score-2 completion rule is strict but defensible as a secondary endpoint if task-specific mandatory items are frozen, public instructions request the applicable work, and human anchors distinguish sound recommendations from unsupported factual assertions. Keep graded coverage primary.

Independent gold ownership, human adjudication, reviewed routing memory, runtime subject integration, selected System One settings and approved spend remain acknowledged open prerequisites. This review does not close them or approve activation. One implementation/disposition pass is appropriate; no second review loop is requested.
