# Independent review: PDLC domain coverage and memory candidate

2026-10-03 · requested Astra low review · local inspection and narrow tests only.

**Conclusion:** the six new procedures are acceptable as explicitly unapproved, unexecuted synthetic drafts for read-only development. The expanded 102-artifact corpus and 504-proposal memory candidate can remain available for development review. Do not describe them as approved business procedures, measured semantic coverage, a complete ontology, or activation-ready memory. Four concrete pipeline limitations below need resolution before their affected capabilities are used. No new blocker was found in the six draft procedure texts themselves.

## Findings and dispositions

### DCM-01 — High before scoped approval — review records identify a reviewer but do not enforce delegated scope

Evidence: `src/sanctum_ref/harvest.py:311`, `review_bundle`, checks exact candidate hash, a nonempty `reviewed_by`, recognized assertion IDs and accepted/rejected decisions. It does not check who delegated which source/entity/relation scope to that reviewer. `apply_owner_declarations` similarly checks a nonempty owner and a harvested source, not an owner binding. HLD §12.1 says human review establishes decisions “within the reviewer's delegated scope”; §11.6 requires scoped owner approval for identity.

A narrow in-memory reproduction supplied `reviewed_by: unscoped-label` with the correct snapshot hash and accepted a DENOTES edge. This is not evidence of unauthorized remote access: these are local trusted-input functions. It demonstrates that the pipeline currently relies on an external trust convention rather than implementing the stated scoped governance.

Disposition: **repair before accepting operational assertions**, or explicitly make verified reviewer scope a prerequisite at the trusted CLI boundary with retained evidence. Keep the present 504 proposed assertions unchanged until actual review. No owner declarations or accepted assertions were present, so this does not compromise the current inactive candidate.

### DCM-02 — Medium — semantic proposal application loses artifact version

Evidence: `src/sanctum_ref/harvest.py:227`, `apply_semantic_results`, indexes source artifacts by `(source_id, artifact_id)` although collection permits distinct `(artifact_id, version)` records. `tools/harvest_pdlc_memory.py:99` includes versions in visible source input, but its proposal schema omits version. Application therefore selects whichever version last occupied that dictionary key.

Reproduction using the existing local fixture, one ID with R41 and R42 text: a valid quote unique to R41 was quarantined as “not an exact source substring” because lookup used R42. A quote shared by both versions could instead acquire the wrong version's provenance without rejection.

Disposition: **repair before harvesting multiple versions of one native artifact**. Include version (preferably content hash too) in proposal identity and lookup; validate against the exact prompted item. This did not demonstrate contamination of today's 102 records, whose inspected snapshot uses distinct public IDs for the relevant historical excerpts. It is a general pipeline correctness issue, not a reason to discard the current proposals.

### DCM-03 — High before authority activation — reviewed authority is outside the immutable release

Evidence: `project_release` emits entities, terms, places, contexts, procedures, relations, artifacts and descriptors, but never projects AUTHORITATIVE_FOR. `Release` in `src/sanctum_ref/memory.py` has no authority field. `tools/harvest_pdlc_memory.py:123` writes accepted authority to top-level `reviewed-authority.json` alongside `reviewed-ontology.json`; these paths are replaced on later reviewed assembly rather than stored in the release directory. The immutable `releases/<id>/release.yaml` is protected against overwrite, but does not contain that authority data or an explicit sidecar reference/hash.

Consequence: accepting authority declarations cannot yet establish HLD §12.6's one coherent immutable release containing vocabulary, procedures, registry and authority. The sidecar is useful review output, not a pinned runtime authority registry. Existing all-proposed release has no authority to lose.

Disposition: **repair before claiming operational authority or whole-release rollback**. Include authority in the versioned release contract or a release-local immutable referenced artifact and connect the runtime consumer. Preserve absence as an explicit current gap; do not manufacture declarations to fill it.

### DCM-04 — Medium before nonuniform access — new subject lookup guards snapshot visibility, not live revocation

Evidence: `_subjects_for` at `src/sanctum_ref/memory.py:191` correctly matches source, artifact, version and content hash, intersects caller groups with stored `visibility_groups`, and enforces stored principal. It has no live ACL or revocation dependency. The pilot connector sets `visibility_groups=['pdlc-pilot']` for fetched records and sets the memoryhub principal to the pilot reader; it does not copy arbitrary row ACLs. These choices match the current single-reader fixture but are not source-neutral permission preservation.

Consequence: caller-supplied current groups alone cannot reflect an artifact unshare that changes the source ACL while the caller remains in the same group. HLD §12.6 explicitly leaves authorization/revocation live. Accepted subject provenance can include source quotations, so the permission check matters even for metadata lookup. The broader existing name/place/descriptor projection also has no per-artifact ACL fields; do not infer full metadata isolation from the new ABOUT checks.

Disposition: **retain for the declared uniform synthetic pilot; unresolved/repair before broader ACLs or activation**. Require a successful live authorization/read check before exposing accepted bindings, or an explicit invalidation/deny-on-revocation boundary. Add a changed-source-ACL case when that boundary is implemented. The saved ingestion checks demonstrate fixture access controls, not this future revocation scenario. No runtime leakage was exercised or observed.

## Six procedure reviews

All source references below resolved to public records in the hydrated corpus. The added public records retain `review_status: draft; review pending`, version `draft-1`, synthetic labels and source references. Their instructions are proposed checks rather than completed test outcomes.

| Supplement / public artifact | Grounding reviewed | Disposition |
|---|---|---|
| `supplement.identity.1` / `artifact-edb7d6d0e61cf4959ef4` — `skills/identity/invite-multi-tab-validation.md` | First-login notes (`artifact-b6d5d29a568b7732ec5d`, 3.8.0) and two-tab discussion (`artifact-7d44ed2b7e763e1d7883`, 3.8.x). Correctly separates one-use invite exchange, refresh-cookie renewal, captured display name, and reported absence of acceptance broadcast. Does not reinstate the backed-out admin-preview behavior. | **Retain draft.** Browser procedure has not been executed. |
| `supplement.identity.2` / `artifact-5141fd5e768c6db2b6d0` — `skills/identity/onboarding-status-investigation.md` | Provisioning client (`artifact-fde0f248cddc804189cc`, 3.8.1), first-login notes, migration (`artifact-b757a13dc46c4c5fbf76`, 3.8.0). Accurate timeout-to-ProvisioningUnavailable, X-Request-ID, HTTP-error propagation and dictionary/state validation. Preserves distinct public/client routes; does not claim indexes are unique or migration deployed. | **Retain draft**, route binding unresolved. |
| `supplement.ledger.1` / `artifact-74c80ee9677eb64f5166` — `skills/ledger/validate-batch-posting-boundary.md` | Draft batch worker (`artifact-2ffdf808316fcad5452b`), partial tests (`artifact-fe7a1df802e3c92f5169`), batch notes and scratch-export session. Existing tests cover approved versus pending; empty/mixed/failure cases are proposed additions. Amount/currency/reference checks are conditioned on adapter confirmation. | **Retain draft**, not synchronous-path coverage or retry safety. |
| `supplement.ledger.2` / `artifact-c0df39f7f1ed431131b8` — `skills/ledger/investigate-event-reader-failures.md` | Event reader (`artifact-5dafdbdb3f5f3fdf7d76`, unreleased working tree) correctly describes Requests Timeout translation, raise_for_status and non-dict rejection. Notes leave coordinator handling open. Step 4's malformed-response-to-writer check is a proposed integration test, not a sourced claim that this wiring exists. | **Retain draft**, coordinator/adapter unresolved. |
| `supplement.platform.1` / `artifact-a2c732f368950b6c4ce5` — `skills/platform/route-selector-validation.md` | Selector (`artifact-a6faa4fd4010458f77cc`), tests (`artifact-bec341318b30faa78eb9`) and routing session (`artifact-253aeca23de3fca90d39`). Correct first available candidate, RouteUnavailable, five test scenarios, three table entries and untraced eu/realm aliases. | **Retain draft**, no canonical service identity inferred from generic keys. |
| `supplement.platform.2` / `artifact-6489887bee9f3051132d` — `skills/platform/gateway-observability-validation.md` | Metrics proposal (`artifact-a262117805f94008fb7a`) and adapter (`artifact-cf9eb6d69635fba1733e`). Metric spellings remain proposed; timeout translates to GatewayTimeout with route; non-timeout exception test is a valid proposed check of the uncaught path. No thresholds or implementation outcomes invented. | **Retain draft**, shared helper/exporter current behavior unresolved. |

The source-inspection review record's `pass_for_readonly_draft` and `business_review: pending` are consistent with this assessment. The procedures use uniform Purpose/Checks/Evidence templates and frequent caveats. That is acceptable for a deliberately authored procedure pack, though broader human realism review remains appropriate. No invented API or falsely completed test was found. These documents are retrieval evidence in SkillHub, not automatically sanctioned executable routing policies.

## Coverage and semantic candidate assessment

The public metadata contains artifacts for all five domains in all four hubs:

| Domain | CodeHub | DocHub | SkillHub | MemoryHub |
|---|---:|---:|---:|---:|
| Payments | 9 | 7 | 8 | 10 |
| Identity | 5 | 6 | 3 | 10 |
| Ledger | 4 | 5 | 2 | 6 |
| Platform | 5 | 7 | 2 | 7 |
| Fraud and Risk | 5 | 7 | 3 | 10 |

These are overlapping **metadata associations**, not disjoint artifact totals, complete business coverage or measured retrieval coverage. The manifest totals remain 25/31/16/30 = 102. Specifically, the new Ledger and Platform SkillHub presence consists of draft procedures. It must not be described as reviewed operational coverage.

The 504 assertions are all proposed: 232 ABOUT, 156 DENOTES, 103 SELECTS_FOR and 13 PARENT; no MEMBER_OF. Inspected all 64 content-generated ABOUT proposals; they are topical associations, including topics mentioned in retracted hypotheses. That is valid ABOUT evidence and must not become claim truth. There are **no LLM-generated DENOTES assertions** in this snapshot. The 156 DENOTES assertions come from structured subject metadata, not independent discoveries of native aliases. Their recorded `source_subject_metadata_requires_review` basis is appropriate, but quote validity alone cannot approve them. Likewise the 103 location/subject associations are proposals, not owner-approved selectors. No clear additional semantic proposal blocker was found beyond maintaining these distinctions.

Five fabricated/nonexact quotes are quarantined, not active assertions. Retain their rejection records. Empty membership, authority, procedures and measured coverage are honest missing inputs. The release's 62 compacted terms and 50 places do not mean 112 approved runtime mappings.

## Snapshot, publication and verification

Independently checked the current manifest's eight file hashes against disk and the candidate snapshot hash against the summary. Release ID `pilot-memory-5e4e4b1c4362` matches its YAML; status is candidate; no ACTIVE file exists under `build/pdlc-memory`. The release contains 102 artifact records. The projector fingerprint participates in the release ID, and existing different release content is refused rather than overwritten. Generation assembly checks receipt prompt hash, raw response hash and parsed-result equality; this review inspected that logic without repeating paid calls.

All six related-source IDs resolve. Public records inspected preserve draft/version and synthetic navigation/ownership qualifications. A narrow public-record scan found none of the checked private markers (`supplement.identity`, `pdlc.090`, `introduced_claims`, `gold_constraints`); this is not a universal secret scanner. The private ingestion record reports 102 MCP reads, searches, missing-token denial and unrelated-group hiding, with memoryhub principal checks and no model calls. I inspected that record rather than rerunning MCP retrieval. No ACTIVE pointer or business approval should be inferred from it.

Ran `.venv/bin/python -m pytest -q tests/test_memory_harvest.py tests/test_sanctum_ref_memory.py`: **25 passed**. These verify the implemented proposal gate, ABOUT separation, stale-hash and group/principal denial, changed snapshot rejection, quote quarantine, cursor/completeness boundaries, identity conflict, explicit declaration and selector validation, and duplicate-support compaction. Two additional isolated in-memory probes reproduced DCM-01 and DCM-02. Neither mutated corpus artifacts or releases. Initial standalone probe lacked PYTHONPATH; rerunning with `PYTHONPATH=src` completed as reported.

Coverage limits: focused on six additions, their already-reviewed source excerpts/public identities, the new harvest/projection paths and accepted-only subject lookup. Did not repeat the full base96 semantic audit, run six domain procedures, compile generated snippets, execute database changes, inspect credentials, call external APIs, invoke paid generation, run a benchmark, or approve any assertion. Did not prove live revocation or runtime authority integration. The HLD's full VERSION_OF/DUPLICATE_OF, applicable-time and reconstruction/governance story is not delivered by this candidate; those omissions should remain explicit rather than being counted as validated ontology completeness.
