# Independent semantic audit of the synthetic PDLC corpus

Date: 2026-10-03. Review requested as Astra low independent review. Scope: selected 96 artifacts in `build/pdlc-authoring/pdlc-hierarchy.json`, scenario specification and pilot plan. This is a source-content review, not benchmark execution, executable validation, independent human gold approval, or corpus acceptance.

**Recommendation: do not freeze implementation gold yet.** Preserve the deliberate version and authority conflicts. Resolve the concrete client/test inconsistency, qualify the timeout claim, and document missing interface bindings before treating this as a coherent executable journey. Most surrounding uncertainty is useful and should remain.

## Prioritized findings

### SA-01 — High — R41 regression cannot use the supplied client specification (repair)

Evidence: pdlc.005, `tests/test_fraud_timeout_regression.py`, creates `MagicMock(spec=FraudServiceClient)` and then sets `mock_fraud.check_risk_legacy.side_effect`. Its import is the same client supplied by pdlc.003, `services/payment_auth/clients/fraud_client.py`, whose only request method is `evaluate_risk`. pdlc.001, `services/payment_auth/handlers/v41_auth.py`, also calls `check_risk_legacy` and reads `fraud_result.is_approved`; pdlc.003 returns `FraudResult.approved`.

Consequence: static inspection identifies a missing mock attribute before the advertised R41 timeout assertion can run. Actual R41 use with this client would hit the broad exception branch and return INTERNAL_ERROR. Version differences are legitimate, but the R42 regression suite explicitly combines these incompatible sources without an R41 adapter.

Disposition: supply/version-pin the legacy interface and bind the regression to it, or clearly label the legacy excerpt and test dependency as unavailable. Do not erase R41 history by silently rewriting it to R42. The missing AuthRequest/AuthResponse/ErrorCode and FeatureFlags implementations also prevent claiming a runnable complete package; preserve those as dependency gaps until packaging addresses them.

### SA-02 — High — 800 ms setting is not evidence of a total fraud response deadline (repair claim or explicitly unresolved)

Evidence: pdlc.002, `services/payment_auth/handlers/v42_auth.py`, says “R42 sets an explicit 800ms fraud response deadline” and passes `timeout_ms=800`. pdlc.003 converts it to `timeout_seconds` and supplies scalar `requests.post(..., timeout=timeout_seconds)`. pdlc.005 only asserts the supplied keyword value using an immediately raised mock exception.

Consequence: the code establishes a Requests transport timeout setting. It does not establish a monotonic, end-to-end 800 ms response deadline; connection/read phases and data arrival can exceed that overall interval. This matters because the private scenario ledger calls it a response deadline.

Disposition: decide whether intended gold is “configured timeout is 800 ms” or an actual total deadline. For the former, qualify the private ledger and implementation descriptions. For the latter, add the appropriate implementation and meaningful validation before gold. Retain the stale 500 ms R41 design target. No transport timing was measured in this review.

### SA-03 — High — identity request schema is not bound to payment wire format (unresolved interface, repair before asserting agreement)

Evidence: pdlc.007, `services/identity_context/schemas/fraud_eval.py`, requires `evaluation_id`, `tenant_id`, nested `subject: AuthenticatedSubjectContext`, `ip_address`, and `request_payload_digest`, with `extra: forbid`. Its subject requires `subject_id`, issuer and token timestamp. pdlc.003 sends `{"payload": request_payload, "context": context}`; pdlc.002's context contains `tenant_id`, string `auth_subject`, and `idempotency_key`. Neither source constructs or validates FraudEvaluationRequest. pdlc.010, `contracts/R42/fraud-request.md`, requires tenant and authenticated subject but intentionally omits field-level mapping. pdlc.003 defaults absent header values to empty strings.

Consequence: these cannot be represented as a verified single schema/client contract. They could be separate internal and external representations, but no adapter or version relationship demonstrates that. The code transports a caller-provided subject; it does not establish its authentication or missing-context rejection. pdlc.007 additionally introduces “payments-engine service” without reconciling it to payment-auth.

Disposition: record schema-to-wire binding, validation ownership and payments-engine alias as unresolved, or add a coherent explicitly fictional adapter/contract with provenance. Do not infer missing-identity acceptance by the remote service; its implementation is absent. Do not treat the negative cases proposed in pdlc.017 as existing tested behavior.

### SA-04 — Medium — approved response and ledger event need a missing transformation (retain gap, constrain gold)

Evidence: pdlc.002 returns status `APPROVED` with `auth_id`. pdlc.008, `ledger_engine/consumers/payment_auth_consumer.py`, accepts `PAYMENT_AUTH_APPROVED`, requires `event_id` and `authorization_id`, and reads account/amount/currency. The producer is absent. pdlc.013, `integration/authorization-posting-note.md`, states the approval guard but not this transformation. pdlc.006 repeats the same request/key in two direct handler calls; pdlc.008 does not visibly deduplicate events or supply an HTTP idempotency header.

Consequence: the sources support the local posting guard and caller-key preservation, not an end-to-end producer integration or exactly-once/retry guarantee. No conclusion of duplicate posting follows: downstream enforcement and the event producer are missing.

Disposition: preserve as explicit coverage gaps. Gold should distinguish “only this accepted status reaches posting” from “every approved handler result reaches ledger exactly once.” Retain pdlc.021 and pdlc.087 retractions; do not turn the absent deduplication excerpt into the defect they expressly fail to establish.

### SA-05 — Medium — navigation over-resolves service identity (repair derived links)

Evidence: hierarchy mappings pdlc.043–046 associate both `svc.payment-auth` and `svc.identity-auth`. pdlc.043, `services/gateway_routing/selector.py`, supplies only generic `payment`/`identity` keys and sample route strings. pdlc.044, `docs/operations/gateway-route-metrics.md`, discusses generic service labels and does not identify either canonical service. pdlc.046 expressly asks whether identity is a caller key or dashboard label and leaves realm/region and old `eu` alias unresolved. pdlc.036, `docs/auth/token-cache-ops.md`, mentions a gateway dashboard but does not establish the particular gateway-edge service that the mapping attaches.

Consequence: routing metadata can resolve precisely the identity ambiguity the corpus is supposed to preserve, even when each quote exists. This is a semantic issue beyond quotation validity.

Disposition: retain broad domain associations; mark specific canonical service bindings as synthetic design or unresolved unless additional source evidence supports them. Do not equate generic labels or a dashboard location with canonical service identity. Likewise the hierarchy's global unresolved statement that full pdlc.024/.046/.091 contents “are not supplied here” is stale at final-manifest scope: the full source exists and was reviewed. Rewrite that statement as an actual unresolved relationship rather than an availability claim.

### SA-06 — Medium — artifact-ID-derived path needs a publication boundary check (repair packaging)

Evidence: pdlc.090's derived logical path is `payments/fraud-timeout/sessions/pdlc.090.md`; its original source has session `chat://fraud-payments/2024-10-23#trace-fields` and no file path. The scenario specification says private identifiers must not appear in hub-visible artifacts.

Consequence: publishing this derived path exposes the private enumeration inside an otherwise ordinary source location. It is not itself an answer-key leak, but violates identifier separation if pdlc IDs remain evaluator-private.

Disposition: give it a neutral source-derived session path, preserve private mapping separately, and clarify whether any public citation IDs intentionally differ from evaluator IDs. Do not publish `introduced_claims`, private hierarchy rationale, authoring prompts or this audit as ordinary source evidence. No hydrated payload exists in this review, so final leakage remains unverified.

### SA-07 — Medium — code-fence extraction alone does not create runnable source files (repair packaging plan)

Evidence: pdlc.054, `fraud-review-notes/tools/snapshot_fetch_test.py`, contains one implementation block and another block importing `from snapshot_fetch import ...`, although no separate snapshot_fetch.py is supplied. pdlc.093, `gateway/client/http_status.py`, contains implementation and a separately labeled `# test_http_status.py` block importing http_status and requiring a `session` fixture not defined there. pdlc.039 imports `ledger_reconciliation.worker...` while its displayed path uses `ledger-reconciliation/worker/...`.

Consequence: Python syntax checks and fence removal cannot establish file/module/fixture completeness. These are acceptable sketches for retrieval but cannot be reported as runnable tests without explicit packaging decisions.

Disposition: preserve snippet boundaries and draft status; define module layout, split files and fixture dependencies only if execution is required. Do not invent execution success from parse success.

### SA-08 — Low — audience claim is described in the wrong JWT part (repair or declared stale error)

Evidence: pdlc.036, `docs/auth/token-cache-ops.md`, tells the reader to compare “the `aud` value in the decoded header”. JWT audience is a payload claim, not the ordinary JOSE header field.

Consequence: the document contains an accidental technical error alongside deliberately stale dashboard guidance. Marking the entire document stale does not distinguish this from the intended historical mismatch.

Disposition: correct “header” to “payload/claims”, or explicitly record this as an intentional erroneous instruction in the private ledger. Do not normalize the separate stale metric names.

### SA-09 — Medium — surrounding corpus repeats evaluator-oriented cautions more than ordinary source diversity (retain meaning, consider realism revision)

Evidence: pdlc.002's code comment includes “canary duration and prod capacity still unverified”; pdlc.008 includes “Interface concern vs defect check” and says payment schedules “remain unknown to this service.” pdlc.014 repeats that 500 ms is not capacity. pdlc.049/.050/.052 repeatedly disclaim approved values and deployed review workflow; pdlc.085/.088/.090 repeatedly return to unknown rollout duration in handoff conversations.

Consequence: no literal benchmark prompt or gold key was observed in the reviewed source text, but many artifacts teach the same desired answer posture directly. That can reduce the information-distribution challenge and conflate retrieval competence with recognition of repeated caution language. Uncertainty itself is appropriate; its uniform framing is the realism concern.

Disposition: retain factual uncertainty and authority distinctions; selectively remove out-of-place global knowledge from code comments and let some surrounding artifacts carry genuinely local information without reciting all evaluation cautions. Freeze tasks only after this decision. This review does not establish generation-input or evaluation-prompt isolation.

## Deliberate messiness to retain

- pdlc.009's archived 500 ms design target versus pdlc.002's current 800 ms setting; do not collapse design target and implementation.
- pdlc.011 proposal-local `fraud_timeout_review_v1`, pdlc.004 `enable_pending_review_on_timeout`, pdlc.023 remembered `fraud_pending_review`, and pdlc.079/.083 `payments.new_flow`/`pay-v2`. These do not establish aliases. Current disabled behavior and proposed behavior remain distinct.
- pdlc.016 is a reviewed checklist requiring canary/rollback planning; pdlc.018/.019 are draft operational details. This is coherent, not a demand to approve unfinished procedures. Missing duration/capacity and explicitly rejected “30m / 2 tenants,” “one shift,” and “one day” should remain.
- pdlc.025–029 offline two-second budget versus synchronous payment timeout; pdlc.037–041 draft batch posting versus released consumer; identity renewal's competing headers/routes and owner uncertainty; unresolved display-name/sub/exporter relationships in pdlc.091/.092/.096.
- pdlc.034's ordinary index does not enforce its comment's one-invite assertion, but the adjacent “not a uniqueness constraint” makes this incomplete enforcement context, not sufficient evidence for a confirmed production bug.

## Hierarchy and ownership assessment

The explicitly designed repository boundaries, teams, container maintainers and co-maintainers are valid fictional navigation choices. Their `synthetic_design` status and “ownership does not imply access” rule are appropriate. Do not require proof of a real organization to accept designed structure. Many-to-many container assignments exist, including payment repository co-maintenance and shared test guidance maintenance.

The grouping of pdlc.007 under identity-provisioning and pdlc.008 under ledger-reconciliation is explicitly navigation-only; reasons state that real repository boundaries are unknown and that the latter does not assert batch implementation. Retain those qualifications through rendering. Team roles on artifacts are sparse while container ownership is populated; ingestion must expose their different scopes rather than imply observed per-file ownership. A container's synthetic primary domain must not erase the artifact's additional domains. No ACL inference is justified.

## Coverage and limits

Read selected source bodies for pdlc.001–096, recovering sections truncated in initial batch output; reviewed core code, relevant tests and linked contracts most closely. Read scenario/plan content and hierarchy mappings, selected mapping explanations and ownership structures. Used only local reads and wrote this report. No source artifact edits, network/API calls, credentials/.env reads, benchmark runs, generated-code execution, or paid generation occurred. No applicable on-disk AGENTS.md was found in the checked ancestor locations; supplied task instructions were followed.

Static source inspection supports the findings; no Python package, database migration, Java compilation, external service behavior, deployment, runtime retrieval, ACL behavior or mechanical quote/hash revalidation was performed. Provenance/hash results in existing manifests were treated as existing evidence, not independently rerun. The current/future distinction is represented in authored text, not independently observed production deployment. Base-world conflict reconciliation was not exhaustively checked. Full authoring prompts and any frozen evaluation set were not audited, so absence of visible answer keys is not a comprehensive contamination certification.

The corpus offers behavior, impact, test-plan, rollout and uncertainty evidence, but lacks verified end-to-end interface bindings, deployed-event producer evidence and demonstrated executable test coverage. These limitations should become private gold constraints or resolved findings before freeze; they need not be “fixed” by making every document agree.

## Candidate resolution recheck — 2026-10-03

Reviewed `build/pdlc-authoring/pdlc-audited-candidate.json` and `tools/resolve_pdlc_audit.py` against SA-01–09. Independently compared candidate text with the selected raw source objects: exactly six artifacts differ (001, 002, 003, 005, 008, 036). Recomputed the referenced raw-file hashes and confirmed agreement with candidate provenance. Inspected the concrete replacements, derived mappings, dispositions and gold constraints. Did not rerun the resolver, its isolated branch exercise, or a package/test suite; its recorded verification is supporting evidence with that limited scope.

| Finding | Recheck result for read-only pilot |
|---|---|
| SA-01 | Resolved at interface/excerpt level: `LegacyFraudClient` declares `check_risk_legacy`, `LegacyFraudResult` declares `is_approved`/`score`, and the historical regression mock uses that protocol. Missing transport/model/config dependencies remain explicitly excluded from executable-completeness claims. The supplied resolver exercise uses stub dependencies and does not establish a package run. |
| SA-02 | Resolved as a constrained implementation claim: candidate comments and exception description now say transport timeout, with gold explicitly constrained to configured 800 ms rather than total deadline. Propagate this qualification into final task/rubric and rendered metadata; the original scenario wording must not silently regain authority. The legacy constant name and an injected test exception string containing “deadline” do not themselves demonstrate elapsed-time enforcement. |
| SA-03 | Appropriately unresolved: candidate disposition explicitly excludes schema agreement and missing-identity rejection guarantees, including authentication ownership and payments-engine alias. This is acceptable missing evidence for read-only questions, not repaired integration. |
| SA-04 | Appropriately unresolved: producer/status transformation and deduplication are explicitly unknown; no exactly-once gold. Local approval guard and repeated caller key remain usable evidence within their demonstrated scope. |
| SA-05 | Resolved for the identified derived-link errors: 043–046 retain gateway-routing but remove canonical payment-auth/identity-auth bindings; 036 removes gateway-edge. The stale “full contents not supplied” rationale is absent. Broad domains and synthetic navigation remain valid. |
| SA-06 | Identified logical path repaired to `payments/fraud-timeout/sessions/2024-10-23-trace-fields.md`. Public citation identifiers and exclusion of private IDs/authoring metadata remain a packaging verification obligation; the private candidate naturally still contains private IDs. |
| SA-07 | Correctly deferred: snippets remain sketches with dependency gaps. The candidate makes no complete executable-repository claim. Packaging must preserve boundaries and status or explicitly supply module/fixture layout if later execution is desired. |
| SA-08 | Resolved: pdlc.036 now says decoded payload; unrelated stale operational guidance is retained. |
| SA-09 | Partially resolved: the concrete evaluator-oriented capacity/defect commentary was removed from 002 and 008. Broader repetition and source realism still require the planned human assessment; this recheck does not certify realism or contamination isolation. |

No additional concrete source-semantic blocker was found in these targeted resolutions for a **read-only pilot with the stated gold constraints**. This is permission to carry the audited candidate forward into packaging, not a declaration of final corpus acceptance or benchmark readiness. Remaining obligations include propagating constraints into tasks and citations, publication-boundary checks, snippet and review-status preservation, retrieval/ACL verification, and human realism review. Original raw generation provenance remains preserved; corrected candidate content must retain its separate content hash and transformation lineage when frozen.
