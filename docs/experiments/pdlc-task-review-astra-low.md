# One-pass review of thirty PDLC task drafts

Date: 2026-10-03. Review scope: the six Luna task jobs and thirty result drafts, authoring manifest, complete 102-artifact authorized synthetic corpus, harness specification and pilot plan. This is the requested single Astra-low task review, not acceptance of gold, implementation review, execution evidence or a benchmark result. Source drafts were preserved.

**Recommendation: needs substantive reauthoring.** Several individual tasks are useful, and literal citation hygiene is good. The set does not yet implement six distinct PDLC families or reliable 18/6/6 evidence boundaries. Most importantly, three partial tasks manufacture missing evidence by treating author-packet truncation as the runtime corpus boundary. A better-retrieving agent could be penalized for finding the answer. Repairing IDs alone will not resolve this.

## Severity-ranked findings

### High — full-corpus evidence invalidates important proposed gold

References below use `family/FAMILY-NN`, because IDs collide.

- **testing/FAMILY-04:** `R42_RETRY_ASSERTIONS_REQUIRE_FULL_ARTIFACT` calls the test truncated and leaves its assertions unresolved. The complete `artifact-637995f6113db1f1fc83`, R42, `tests/test_retry_idempotency.py`, contains both handler invocations, failure then approval assertions, expected tenant/subject/idempotency context, `timeout_ms=800`, call count two and `assert_has_calls`. The second invocation is explicitly client-triggered. `artifact-af43e17a8af944b34668`, R42 handler, contains one fraud call per handler invocation, not an internal retry loop. These sources support a useful test-review task; they do not establish production deduplication or a successful test run. Remove the false truncation boundary and score the actual assertions and their limits.
- **uncertainty/FAMILY-04:** `FACT-PROVISIONING-CLIENT-TIMEOUT-AND-EXCEPTION-PATH-INCOMPLETE` is false for the available artifact. Complete `artifact-fde0f248cddc804189cc`, 3.8.1, catches `requests.Timeout`, logs the request ID and raises `ProvisioningUnavailable(request_id)` with exception chaining; it propagates HTTP errors, rejects a non-dictionary or missing-`state` JSON body, and returns the payload. The 2/5-second connect/read tuple and `X-Request-ID` are visible. `artifact-5141fd5e768c6db2b6d0` also describes these checks. A real unresolved question is the relationship between this client's URL and the first-login page's URL, not an unavailable handler tail.
- **implementation/FAMILY-04:** the contract snapshot really does omit timeout policy, but the corpus does not. The R42 handler above configures an **800 ms transport timeout**, returns `FAILED`/`GENERIC_DEPENDENCY_ERROR` on a timeout with the flag off, and raises `NotImplementedError` on the unfinished enabled path. The complete fraud client (`artifact-55979f9d4f411fa48913`) converts the argument to seconds for Requests; regression tests (`artifact-2b6034bb9a3a5f2fffe3`) assert 800 and the failure result. This is source-described behavior, not a measured end-to-end deadline or deployment proof. Gold must distinguish that available behavior from a still-unapproved proposed policy; it must not require leaving all R42 disposition details unresolved.
- **behavior/FAMILY-01:** the cited full regression procedure (`artifact-6e839431d7ee2c9123df`, Draft 0.2) explicitly says to assert pending review, non-approval and an unsatisfied posting guard, then run existing idempotency cases. Its review note says the excerpt lacks a complete expected outcome, while gold stops after request construction and failure injection. This omits the central behavior the requested plan needs. Representation/schema details remain open, but the proposed invariant does not.

All four illustrate why matching literal quotes is insufficient. Authoring requested grounding only in excerpts; full-corpus review must replace excerpt-relative obligations before acceptance. No fictional source should be rewritten to eliminate genuine uncertainty.

### High — the nominal family and scope quotas are not substantively met

All five behavior prompts request plans or planning notes; none primarily asks the developer to explain actual source-described behavior. implementation/03 is a test-plan request; rollout/03 is selector validation without rollout or recovery; uncertainty/03 is principally reader test planning. Twenty-nine prompts request a plan, checklist or planning assessment; rollout/05 is the sole direct status inquiry. Planning is appropriate in evidence-only mode, but does not replace the required behavior, dependency and conflict reasoning mix.

The six jobs each emitted three `in_scope`, one `partial` and one `out_of_scope`, giving the intended labels **18/6/6**. These counts are not accepted evidence classifications:

- testing/04 and uncertainty/04 have materially more support than their partial rubrics acknowledge; implementation/04 needs the code-versus-contract distinction above.
- **testing/05** has only a boundary obligation and calls the invite/cross-tab test plan outside scope. Corpus evidence includes first-login notes (`artifact-b6d5d29a568b7732ec5d`), the renewal-tab conversation (`artifact-7d44ed2b7e763e1d7883`) and a dedicated validation procedure (`artifact-edb7d6d0e61cf4959ef4`). The conversation reports broadcast after renewal, not invite exchange, and a reverted acceptance-broadcast proposal owing to admin-preview behavior. These are not an authoritative final product requirement, but they support a substantial bounded investigation/test plan. This is partial, not wholly unsupported, as presently phrased.
- **behavior/05** and **impact/05** combine supported interpretation/triage with unavailable production settings or verified incident cause. They are mixed requests and should be partial unless rewritten around the unavailable deliverable.
- **uncertainty/05** explicitly requests a verification and decision plan. Such a plan is supported, although current enablement approval is unavailable. Asking for a plan and labeling it unanswerable rewards generic caution rather than boundary detection.
- **behavior/04** and **impact/04** ask to identify missing rollout inputs, a supported task in their own right. Merely mentioning missing inputs does not make the requested work partially answerable. In contrast, rollout/04 actually requests concrete unsupported capacity and duration, so its partial label is credible.
- **implementation/05** combines a complete service, production execution and an absolute duplicate-posting certificate, then asks for a plan. The unavailable guarantee is real, but this is an unusually conspicuous negative compared with realistic supported tasks. Replace it with a credible unsupported engineering decision rather than a stack of impossible demands.
- **rollout/05** is a defensible negative: snapshots and proposal records do not establish current production enablement or authorized go-live approval. Preserve useful historical context without treating it as live evidence.

Full-corpus inspection found no authoritative current production approval/capacity/duration record, verified callback incident resolution, settled cross-tab product requirement, or complete executable service/production safety certificate. That bounded finding applies to this pinned corpus only. Existing drafts have not recorded a frozen per-task absence inventory, searched aliases, alternative support and reasons for rejecting nearby evidence.

### High — overlap and missing essential evidence weaken discrimination

Only **29 of 102 artifacts** supply required positive citations. By distinct hub count, **23 tasks require one hub, five require two, one requires three, and one requires none**. This is not intrinsically wrong, but the supposed cross-domain tasks often concatenate cautions instead of tracing interfaces.

Examples of semantic overlap hidden by different fact IDs:

- behavior/04, impact/04, rollout/04 and uncertainty/01 repeatedly test proposed/off flag, absent capacity/duration and no readiness conclusion.
- rollout/01 and rollout/02 share the same checklist obligation and near-identical pre-merge/canary work; rollout/05 and uncertainty/05 repeat live approval uncertainty.
- testing/02 and rollout/03 both test ordered selector behavior/sample-policy limits.
- implementation/01 and uncertainty/03 both center on failed batch reads not authorizing postings and an open coordinator interface.
- The R41 500 ms historical-budget distinction recurs in impact/01, implementation/04 and uncertainty/02, with another rendering in behavior/05.

The corpus can support stronger diversity without expansion: R41/R42 code/test comparison; identity invite versus renewal and read-only provisioning; batch screening budget versus synchronous fraud transport; selector caller-key/region aliases; Requests versus httpx failure seams; rollback state reconciliation; and contradictory endpoint/header/ownership notes. These are replacement directions, not new accepted tasks.

Critical omissions also weaken existing plans. impact/01 should consult the actual handler/client/context and ledger consumer (`artifact-c6c4c63a6c4c6a86f05f`), distinguishing the stream consumer from batch reconciliation. testing/02 omits fallback, service separation, unknown pair and no-available-route cases present in its cited procedure and `artifact-bec341318b30faa78eb9`. rollout/01 and /02 require a rollback path but never capture the available rollback procedure's stop-expansion, disable/readback and already-created-state limitation (`artifact-e9ebe35874224f9ad39c`). implementation/01 and uncertainty/03 omit concrete event-reader conversion and validation behavior. An answer can therefore satisfy much of the draft gold while missing the engineering substance.

### High — rubric and scoring contracts are not ready for use

The drafts contain **74 distinct dimension names**, rather than mapping mandatory items into the shared five dimensions (scope/dependencies, proposed change, validation, rollout/recovery, uncertainty). They do not freeze per-task applicability/N/A or task-specific 0/1/2 anchors. Names such as `handling`, `communication` and `figure_interpretation` cannot simply become extra equally weighted dimensions. Requiring every dimension to score 2 makes this ambiguity consequential.

Some mandatory criteria are unnecessary or overprescriptive: repeated “unverified private draft” language (especially uncertainty tasks) is generation scaffolding, not task quality; rollout/03's requirement to identify the artifact as synthetic is not requested engineering work; implementation/03 prescribes a fake instead of allowing an equivalent controlled transport seam. Source recommendations should retain their local status rather than becoming universal policy. testing/02's exact file location can be useful navigation, but should not make an otherwise complete, grounded test plan fail solely for omitting the spelling.

Positive facts frequently bundle several obligations into one score (notably `ROLLOUT-PAYMENT-CHANGE-CHECKLIST`), while other tasks split small config values into separate facts. Equal weighting then gives very different credit for comparable work. Canonicalize and split independently verifiable claims consistently. Keep genuine boundary obligations separate; no fictional absence citation is needed.

Alternative support must be explicit or admitted through arm-blind adjudication: ledger code/integration notes for the posting guard; R42 code/tests for timeout behavior; first-login/session/procedure evidence for identity; selector code/tests/procedure for selection. A quote mentioning an assumption is not alone proof of release status (rollout/03's draft-status fact relies partly on version metadata). Short quotes such as `return True` in testing/03 require surrounding function context to entail the stated successful path.

The spec plans delivered-reference/span validation plus semantic and human adjudication. Draft evidence has no frozen span/hash references and no accepted boundary records, so these rubrics cannot yet be mechanically scored as the final contract. No hidden source-consultation policy should be inferred from gold locations. Both arms need identical public caller obligations and answer format.

### Medium — integrity and realistic prompt language need repair

All jobs use literal `FAMILY-01` through `FAMILY-05`: thirty rows have only five unique task IDs. The generator prompt itself says to use these literal IDs; fix the template as well as downstream identities. Several equivalent facts have different IDs across families; conversely uncertainty/01 and /05 reuse `FACT-PENDING-REVIEW-FLAG-DRAFT-STATE` with different granularity. Freeze canonical fact meaning and retain version/status qualifiers.

All cited hub IDs and declared domain IDs are valid. Domain appearances are Payments 20, Fraud/Risk 16, Ledger 7, Platform 5 and Identity 4 (multi-domain counts overlap). No Identity-primary task is marked sufficiently supported: its two primary tasks are testing/05 and uncertainty/04; impact/05 is a negative with an identity incident, while rollout/03 adds Identity via the sample route table. implementation/03 has no domain. Do not fabricate a domain for generic engineering evidence, but record its role consistently. Domain labels alone overstate depth of coverage.

Difficulty uses six labels (`easy`, `moderate`, `medium`, `hard`, `high`, `expert`), and answerability uses twelve renderings, including scope values and “from excerpts” variants. Required fields for draft generation are present, but these are not final public-task/private-gold bundle records: caller requirements, answer format, matrix/version-conflict demands, canonical references and fixed scoring anchors still need assembly. This is a freeze gap, not evidence of a runtime schema failure.

Prompts repeatedly reveal the desired caution: non-release status, presumed-deadline rejection, sample-table limits, “do not treat … as measured,” and private/unverified handling. Some contextual constraints are legitimate, but their density makes generic qualified planning unusually competitive and weakens measurement of discovery. Keep common insufficiency permissions in shared instructions; public tasks should pose the decision without telling the agent the key factual conclusion. No actual runtime leakage was established by this review; isolation of authoring packets/private gold from public hubs and routing memory still needs a bundle-level check.

## Disposition of all thirty drafts

“Retain” preserves the task concept, subject to the common ID/schema/rubric cleanup and independent acceptance. “Revise” requires material prompt/gold/scope changes. “Replace” changes the primary demand to restore diversity. Numbers refer to colliding `FAMILY-NN` IDs within the named job.

| Job/family | ID | Disposition | Main reason |
|---|---|---|---|
| behavior | 01 | Replace | Testing demand; omits supported proposed outcomes. |
| behavior | 02 | Revise | Useful retracted-claim investigation; make behavior/evidence reasoning primary. |
| behavior | 03 | Revise | Useful diagnostic boundary; focus on current evidence and handoff meaning. |
| behavior | 04 | Replace | Rollout planning duplicate, supported gap-identification prompt mislabeled partial. |
| behavior | 05 | Replace | Mixed planning negative; not behavior understanding. |
| impact | 01 | Revise | Add actual handler/client/consumer chain and separate batch path. |
| impact | 02 | Revise | Useful copy/adapter release boundary; broaden full-source support, reduce coaching. |
| impact | 03 | Retain | Clear adapter/caller contract impact, with focused validation. |
| impact | 04 | Replace | Repeated rollout-readiness gap task; scope does not match deliverable. |
| impact | 05 | Revise | Identity/payment disambiguation useful; treat mixed demand as partial or narrow negative. |
| implementation | 01 | Revise | Good batch boundary; include concrete code/test gaps and unresolved integration. |
| implementation | 02 | Revise | Config review is thin; connect settings to client/runner contract without overclaiming. |
| implementation | 03 | Replace | Test-design request lacks implementation decision. |
| implementation | 04 | Revise | R42 code supplies behavior omitted by packet-derived boundary. |
| implementation | 05 | Replace | Contrived production/certification bundle and plan/answerability mismatch. |
| testing | 01 | Revise | Add source-described test outcomes and preserve current/proposed separation. |
| testing | 02 | Revise | Add essential selector failure/fallback/isolation cases; avoid duplicate rollout task. |
| testing | 03 | Retain | Concrete distinct probe success and failure paths. |
| testing | 04 | Revise | Full test and handler available; score assertions and limits, not truncation. |
| testing | 05 | Revise | Considerable identity evidence exists; partial requirement investigation. |
| rollout | 01 | Revise | Add concrete rollback/reconciliation limits and unresolved controls. |
| rollout | 02 | Replace | Near-duplicate of 01; use another domain/recovery decision. |
| rollout | 03 | Replace | Selector validation belongs elsewhere; no rollout/recovery demand. |
| rollout | 04 | Retain | Credible partial request for unavailable capacity/duration; allow justified conditional proposals. |
| rollout | 05 | Retain | Defensible current-production-status negative; freeze bounded absence record. |
| uncertainty | 01 | Replace | Repeats flag/readiness facts; use genuine conflicting evidence chain. |
| uncertainty | 02 | Revise | Compare available R42 code with R41 budget, not blanket unresolved policy. |
| uncertainty | 03 | Replace | Primarily repeats batch test planning; use a distinct ambiguity. |
| uncertainty | 04 | Revise | Complete handler exists; retain actual URL/integration uncertainty if wanted. |
| uncertainty | 05 | Replace | Verification plan is supported and duplicates rollout/05 status issue. |

Totals: **4 retain, 15 revise, 11 replace**. These dispositions are not task edits and do not by themselves rebuild the quota matrix.

## Verification record and smallest next steps

Read the complete text of all 102 corpus artifacts, including nearby aliases, historical proposals, unrelated lookalikes and the full code/test records omitted from author excerpts. Inspected all thirty prompts, 92 proposed obligations (79 evidence and 13 boundary), and their private plan checklists. Mechanically checked **83 evidence references** for exact artifact existence, hub, version and literal contiguous quote: all pass. Semantic review found the contextual errors and omissions above; literal success is not gold acceptance.

The authoring manifest pins corpus-manifest SHA-256 `5b3cc2376b6588083ae4c4ff2724d2cf9653a272c5ad497f138d7a49a0d7d621`, which matches the current manifest bytes. All eight file hashes listed by the corpus manifest match. Corpus status remains `loaded_development_candidate_not_frozen`; authoring remains `thirty_drafts_generated_not_verified`. These are coherent development pins, not an immutable accepted task/gold bundle. Independent source provenance beyond the synthetic corpus and runtime isolation were not audited here. No code was executed as a service, no benchmark or paid provider call was run, and no memory was activated.

Before freeze:

1. Reauthor the eleven replacement demands and materially repair the fifteen revisions from full artifacts. Preserve sources and deliberate uncertainty. Build the six-family matrix from actual reasoning requirements; add sufficiently supported Identity work and a recovery task outside the repeated payment canary plan.
2. Recalculate scope from each requested deliverable, then deliberately fill 18 supported/six partial/six outside-scope slots. Record the inspected corpus/aliases/versions and nearby rejected support for each negative. Do not preserve incorrect labels to satisfy a quota.
3. Canonicalize task/fact IDs, split compound obligations consistently, accept alternative evidence, map to the five shared dimensions and freeze applicability plus 0/1/2 anchors. Remove authoring scaffolding from public prompts and pin spans/hashes privately.
4. Have the designated independent gold owner accept the repaired bundle before freeze; assign the human adjudicator and verify scorer fixtures and public/private separation as the harness requires. This review does not authorize a second model-review loop or benchmark dispatch. The thirty-task, one-scenario study remains directional and cannot establish a deployment guarantee or narrow statistical margin.
