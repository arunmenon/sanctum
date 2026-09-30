> History of the design set, kept outside design/. Section and example numbers in this page are the numbers in use when each entry was written.

# Sanctum review history and restructuring record

Overview and reading guide · Section map

> Status: proposed research design, version 5.3.1 (reorganized from v5.1). Scope: routing intelligence. Lab work is experimental. Original section numbers are retained where sections survive.

This page preserves the source's review dispositions, the v5.1 change record, and the holistic review (R-Holistic) with its v5.2.1 dispositions. “Accepted” in these historical tables means a finding was accepted/addressed in that document; it does not establish stakeholder approval, executable verification, or production acceptance.

## Restructuring record

- Source: unchanged v5.1 document.
- Preserved all 23 numbered top-level sections, diagrams, tables, examples, and fixtures. Section numbers remain stable across pages.
- Added audience guidance, proposal/spike framing, explicit status caveats, navigation, and a phase-based execution guide.
- Converted section/example/fixture references to links where targets are known, without rewriting code or diagrams.
- Q9 wording aligned with §9.7: DENOTES approval requires the native-term owner and canonical-entity owner, or explicit delegated stewardship.
- Q16 remains an open decision. Its proposed default now follows Example 9 for a missing must-consult source (`insufficient`) and explicitly leaves procedure-conflict behavior to be resolved; no blanket `partial` override.
- Replaced the unavailable bare `sanctum-lab-plan-revised.md` pointer with the existing scaffold plan and documented its age.
- The original engineering proposal was not provided; comparison with it remains unresolved. No architecture adoption or experiment result is inferred.
- Section ownership map and [machine-readable preservation check](preservation-check.json) record coverage and the source hash.

---

<a id="section-19"></a>

## 19. Review disposition (F01–F23)

| Finding | Topic | Disposition | Where addressed |
|---|---|---|---|
| F01 | Authorization vs. learned eligibility | **Accepted** | §4 principle 1, §6.4 D2, Ex. 6 |
| F02 | Unknown / sufficiency semantics | **Accepted** | §6.4, §6.6, Ex. 7, 8 |
| F03 | D3 depends on D1/D2 in same call | **Accepted** | §6.3 rounds |
| F04 | `calibrated_p` meaning | **Accepted** | §6.4, §6.6 |
| F05 | Calibration and labels | **Accepted** | §6.5, §6.7 |
| F06 | Duplicates used to skip sources | **Accepted** | Ex. 2 |
| F07 | Authority too coarse | **Accepted, right-sized** | §7.2 fact-kind authority |
| F08 | Metadata sensitivity | **Accepted** | §8.6 scoped IDs, §9.7 governance, §14.1 (removed in v5.3.1) |
| F09 | Mixed-signal Beta | **Accepted** | §9.10 separate signals, Ex. 13 |
| F10 | Routing as subset decision | **Accepted** | §9.10, E5 |
| F11 | Ranking and time semantics | **Accepted** | §7.1, §7.3, §7.5, Ex. 4 |
| F12 | Token packing | **Accepted** | §7.4, Ex. 3 |
| F13 | Model weakening governance | **Accepted** | §13 (removed in v5.3), Ex. 11 |
| F14 | Write idempotency | **Accepted, deferred to write note** | §13 (removed in v5.3), Ex. 11 |
| F15 | Token passthrough | **Accepted** | §5.3, §14.1 (removed in v5.3.1) |
| F16 | Untrusted evidence | **Accepted** | Ex. 10, §14.1 (removed in v5.3.1) |
| F17 | Latency arithmetic | **Accepted** | §6.3, §14.2 (removed in v5.3.1) |
| F18 | Replay guarantees | **Accepted, right-sized** | §11, §15 (removed in v5.3) |
| F19 | Degradation | **Accepted** | Ex. 9 |
| F20 | Bundled comparisons | **Accepted** | §16.2 (lab) ladder |
| F21 | Contract versions | **Accepted** | §6.6, §7.1, §12.2 |
| F22 | Adapter contract | **Accepted** | §12.3, Ex. 12 |
| F23 | Relationship to earlier "C6" proposal | **Needs input** | Q1 |

---

### Memory review disposition (M01–M13)

| Finding | Topic | Disposition | Where addressed |
|---|---|---|---|
| M01 | Names vs. subjects vs. places | **Accepted** | §8.5, §8.6, Ex. 5, Fixture 17 |
| M02 | Ambiguity within an org | **Accepted**; agent default is separated interpretations | §9.2, Fixture 16 |
| M03 | Allowed uses of each relation | **Accepted** | §8.7, Fixture 18 |
| M04 | Procedure grammar and precedence | **Accepted** | §9.4, Fixture 20 |
| M05 | Fallback and query plans | **Accepted** | §9.3, Fixture 19 |
| M06 | Descriptors change routing | **Accepted**; pinned in v0 | §9.7, Fixture 21 |
| M07 | Revocation and probe trust | **Accepted**; depends on adapter capabilities (Q15) | §9.1, Fixtures 21, 22 |
| M08 | Memory releases | **Accepted**, right-sized to a versioned manifest | §9.6, Fixture 23 |
| M09 | Version applicability | **Accepted** | §7.5, Fixture 24 |
| M10 | Reconstruction | **Accepted**; reconstruction window declared | §8.4, §9.9 |
| M11 | Jev ranks, does not establish identity | **Accepted** | §9.10, Ex. 14 |
| M12 | Counterfactuals and baseline | **Accepted** | §17.1 (lab) E6, §17.2 (lab) alias-table comparison, Ex. 14 |
| M13 | Holdout reuse | **Accepted**; matters from E7 | §9.8, §9.10, Fixture 25 |

---

<a id="section-22"></a>

## 22. What changed in v5.1

v5.1 is a contract-consistency patch. It changes no architecture. It closes gaps found while checking the lab plan against v5.

| # | Gap in v5 | v5.1 change | Where |
|---|---|---|---|
| 1 | §7.5 needs branch, environment and effective time, but the §7.1 EvidenceUnit sketch lacked them | `applicability` block with `applicability_status`; no fabricated context | §7.1 |
| 2 | Verify mode promised verdicts while D7 is deferred | Pilot `verify` returns evidence and conflict flags; `verdicts` absent until D7; advertised as `partial` | §12.1, Ex. 7, §12.3 |
| 3 | `frozen_corpus` appeared as a replay level but not in the response enum | Declared a research execution profile, not a wire value | §15 (removed in v5.3) |
| 4 | Prose used statuses (`unresolved`, `insufficient_budget`, `unsupported_for_as_of`) not in the §12.2 enums | Enums stay closed; detail moves to versioned reason codes | §12.2, §9.3, Ex. 4, Fixture 19 |
| 5 | No response shape for separated interpretations (§9.2) | `interpretations[]` in the response; `caller_profile` in the request | §12.0, §12.2 |
| 6 | No request contract; credentials could be read as tool arguments | `RetrieveRequest` defined; credentials only in transport or session | §12.0, §14.1 (removed in v5.3.1) |
| 7 | Sanctum did not advertise partial support | Sanctum capability manifest with supported / partial / unsupported | §12.3 |
| 8 | Lab configs let C1 and C4a be unfair controls | C1-fair, C1-naive, C4a-equivalent, C4a-label-only; hybrid DocHub before H5 conclusions; adapter survey and Kestrel-shaped questions in the minimum | §17.2 (lab) |

---

<a id="v5-2-1"></a>

## v5.2.1: holistic review (R-Holistic), reduced scope

**v5.2.1 supersedes v5.2.** v5.2 answered the holistic review with production contracts (execution context, assertion envelope, a full evidence-preservation matrix, capability negotiation). The owner judged that over-engineered: this is a research and MVP stage, the HLD is a design for proving the tenets, and production hardening is out of scope rather than deferred work. v5.2.1 keeps status honesty and conflict retention, `ABOUT` as an operational binding, the rule that a readable place is not name visibility, and the rule that D6 never displaces rules-packed evidence. v5.2 remains in history.

Disposition values: **adopted** (in the design), **out of scope (research stage)** (removed; recorded here with its concern), **rejected** (not a design change, with the reason).

| Finding | Topic | Disposition | Where, or why |
|---|---|---|---|
| R-H 1.1 | One trusted execution context and budget ledger | **Out of scope (research stage)** | See the items below |
| R-H 1.2 | Safe defaults inconsistent; conflict packing loses flags | **Adopted** (reduced) | Status defaults and conflict retention in HLD §7.4, Ex. 9, `conflict_witness_omitted` in §12.2; D6 row in §6.4 reconciled |
| R-H 1.3 | Independent D2 probabilities do not define subset selection | **Out of scope (research stage)** | See the items below |
| R-H 1.4 | Round contracts, cache keys, observation ids | **Out of scope (research stage)** | See the items below |
| R-H 2.1 | Release pinning is not correctness under concurrent change | **Adopted** (one rule); rest out of scope | A feed gap means freshness unknown (memory §9.6) |
| R-H 2.2 | Governance lacks an enforceable assertion model | **Out of scope (research stage)** | See the items below |
| R-H 2.3 | Retention boundaries | **Out of scope (research stage)** | See the items below |
| R-H 3.1 | Identity and replay capabilities not negotiated | **Adopted** (one sentence); rest out of scope | Adapters declare version reads and identity stability (§12.3) |
| R-H 3.2 | Metadata visibility inferred from readable places | **Adopted** | Memory §9.2 |
| R-H 3.3 | Hub vocabulary leaks into subjects and selectors | **Adopted** (subjects); selectors out of scope | Memory §8.10 |
| R-H 4.1 | Broker purpose architectural, implementation harness-specific | **Out of scope (research stage)** | The broker's authority is unchanged in System One providers §6 |
| R-H 4.2 | Selected decisions, not a generic cascade | **Out of scope (research stage)** | See the items below |
| R-H 4.3 | Invariants weaker in the implementation | **Rejected** as a design change | Implementation defects, tracked with the lab |
| R-H 4.4 | Lab assumptions in the core | **Rejected** as a design change | Implementation work; the design already puts vocabularies in owner and adapter data |
| R-H 5.1 | Economic activation gates; D6 displacement | **Adopted** (one sentence); gates out of scope | D6 promotion never displaces rules-packed evidence (HLD §7.4) |
| R-H 5.2 | Runtime calibration matching | **Adopted** (unchanged) | The binding rule in System One providers §8 stands |
| R-H 5.3 | Long outages and LLM escalation | **Out of scope (research stage)** | See the items below |

**Removed items, each out of scope (research stage), with the concern it addressed:**

| Removed item | Concern | Finding |
|---|---|---|
| Trusted per-request execution context (tenant, principal, scope with narrowing steps, absolute deadline, pinned versions) | Stages deriving their own deadlines, budgets or versions can disagree within one request | R-H 1.1 |
| Budget ledger across rules, searches, fetches, model calls, retries, decomposition and serialization | Retries and later stages can overrun the caller's budget unnoticed | R-H 1.1 |
| Policy-epoch recheck before egress | A revocation mid-request could let retrieved evidence leave | R-H 2.1 |
| Cache keys covering scope, policy epoch, rule set, release, source versions and model binding | A cache hit under another scope or binding can serve wrong or unauthorized results | R-H 1.4 |
| Stable observation ids per call | Receipts and replay records need to name the same call unambiguously | R-H 1.4 |
| Per-store retention and erasure rules (assertions, observations, retained evidence, inference replay) | Queries and provider payloads can hold sensitive content outside memory | R-H 2.3 |
| HLD §14.1 and §14.3 additions (ledger charges, scope steps, observation ids) | Operating a shared service needs attributable cost and behavior | R-H 1.4 |
| Seven-capability adapter negotiation (identity stability, addressability, version reads, snapshot retention, typed selectors, subject attribution, change feeds) | New hubs differ in what they can promise | R-H 3.1, 3.3 |
| Exact-version evidence handles (`fetch_handle`) | A re-read of the artifact may not be the served version | R-H 4.1 |
| Per-decision behavior matrix for D1 to D9 under uncertain, invalid, denied, failed and budget-exhausted conditions | Safe defaults can drift between decisions without one table | R-H 1.2 |
| Bounded D6 reservation share with displaced units listed | Promotions could crowd out other evidence at a fixed budget | R-H 5.1 |
| Reason codes `displaced_by_conflict_reservation`, `budget_exhausted`, `freshness_unknown` | Make the removed behaviors visible on the wire | R-H 1.2, 2.1 |
| Releases as content-addressed dependency closures | Configuration loaded outside the release can diverge from it | R-H 2.1 |
| Live policy epoch paired with the immutable release | Separates configuration consistency from permission currency | R-H 2.1 |
| Change-feed watermarks, gap reconciliation and freshness limits | A feed gap must not read as unchanged | R-H 2.1 |
| Governed assertion envelope with publication checks | Governance is a workflow until publication enforces reviewer authority and dependency closure | R-H 2.2, 3.2 |
| Governance of `ABOUT` assertions | Reviewed subject bindings would need the same control as names | R-H 3.3 |
| Resolved procedure-conflict status (Q16) | The status for incompatible procedures remains open | R-H 1.2 |
| D2 subset-selection planner | Independent per-source probabilities do not define a set | R-H 1.3 |
| Discriminated decision schemas and one shared decision executor | Keeps calibration, disposition and fallback uniform across tiers | R-H 4.2 |
| Per-decision economic activation gates and drift monitoring | Calibration alone does not show inference is worth paying for | R-H 5.1, 5.2 |
| Outage policy (circuit breaking, sustained fallback, recovery probes, purpose-bound LLM use) | Request-level fallback does not cover long outages | R-H 5.3 |

The review's memory-fidelity table and judgments describe the lab implementation and need no design disposition.

<a id="v5-2-2"></a>

## v5.2.2: focused MVP review

A focused review of the decision cascade and the System One layer, kept to rules that prove or protect a tenet. All five findings are **adopted**.

| Finding | Topic | Disposition | Where |
|---|---|---|---|
| MVP-5 | Policy rules vs judgment rules; per-decision eligibility (a model confined to abstentions cannot correct a confident wrong judgment rule) | **Adopted** | HLD §6.1 |
| MVP-6 | D2 state: no implied graph neighbourhoods; descriptor-only and ontology-enriched layouts as separate variants; the enriched layout defined, not yet exercised | **Adopted** | HLD §6.3, System One providers §14 |
| MVP-7 | Batch efficiency and input size are measured provider-profile properties, not hosting location; checklist for a third provider; a character limit is a backstop | **Adopted** | System One providers §2.1, §13 |
| MVP-8 | Tier 2 consistent in both diagrams (permitted actions only, else the baseline-preserving default); D4 ranker and System One as successive stages, score diagnostic | **Adopted** | HLD §6.4, §6.5, System One providers §1, §12 |
| MVP-9 | Activation per decision against its rules baseline and a named no-model control, with a metric that can observe the effect; no economic framework | **Adopted** | HLD §6.7, System One providers §8 |

---

<a id="v5-3"></a>

## v5.3: routing intelligence only

**v5.3 supersedes v5.2.2.** Owner direction: the policy layer was over-engineered for a research MVP. v5.3 treats policy as an assumed input and keeps two pillars, the cascade and the memory and ontology, operating inside a given allowed set. The request journey is four routing stages (Understand, Select, Retrieve, Assemble), and the Assemble stage keeps the selected, skipped and why explanation because it is how routing is evaluated. Memory design and System One providers are unchanged apart from governance workflow prose and data-class wording.

Every removal, each **out of scope (research stage)**:

| Removed | Where it was |
|---|---|
| Policy layer as a designed layer (identity and token exchange, effective scope, write governance) | HLD §0, §5.2, §5.3 |
| Identity and token exchange, no-passthrough rule (F15) | HLD §5.3, §14.1 |
| Scope intersection mechanics (grants ∩ project scope ∩ registry ∩ data policy) | HLD §5.1, §11, contracts Ex. 1 |
| Delegated credentials on fan-out | HLD §11, contracts Ex. 1 |
| Security and data rules of §14.1, except data-class eligibility as an input | HLD §14.1 |
| Durable receipt before reply (principle 7, read-path step) | HLD §4, §11, §14.2 |
| Replay levels | HLD §15 |
| Write path and reconciliation | HLD §13 |
| Write-governance non-goal and write-target decision (D8 marked out of scope) | HLD §3, §6.4 |
| Asynchronous reconciliation principle | HLD §4 |
| Data-egress anticipated question | HLD §20 |
| Decisions Q3, Q5, Q6, Q9, Q11, Q12, Q13, Q14, Q18 (authority approval, replay level, hosted data classes, identity approval, attestation, authority arbitration, metadata to hosted providers, stale ACLs and retention, release approval) | HLD §21 |
| Request credential rules and caller-token fields | Contracts §12.0 |
| `receipt_id`, `effective_scope_ref`, `replay_level`, `replay_expiry` response fields and the `receipt_incomplete` reason code | Contracts §12.2 |
| Delegated identity and write capabilities of the adapter contract; replay in Sanctum's manifest | Contracts §12.3 |
| Example 10 (a document tries to steer Sanctum): security boundary | Contracts §10 |
| Example 11 (recording a learning): writes | Contracts §10 |
| Example 9 panel "registry or auth down" | Contracts §10 |
| Example 12 approval step, data-class and scope-isolation checks | Contracts §10 |
| Fixture 21 (descriptor poisoning and unshare) and Fixture 22 (probe access context): security boundary | Contracts §10 |
| Governance approval workflow (ownership table, lifecycle diagram, automatic-change risk table) beyond the review rule | Memory §9.7 |
| Approval workflow framing of the improvement loop | Memory §9.10 |
| Approval-scope bullet in name resolution | Memory §9.2 |

**Reworded, kept:** HLD §0, §3 (G1, G5, non-goals), §4 (principle 1), §5.1, §5.2, §5.3, §6.1 (given rules), §6.2, §6.4 (D2 wording), §7.3, §7.5 (copies keep attribution), §11, §14.1 (one line), §14.2 (registry lookup), §14.3, §20, §21 Q16 and Q17; contracts Ex. 1, Ex. 6, Ex. 9, Ex. 12, §12.0, §12.1, §12.2, §12.3, worked trace block 2; memory §9.2 (visibility as an assumed-input-dependent rule), §9.7, §9.10; System One providers §1 and handshake point 9 and the broker's data-class row (assumed input).

---

<a id="v5-3-1"></a>

## v5.3.1: small trim

**v5.3.1 supersedes v5.3.** Moved, kept in the design:

- Data class as an assumed input: from HLD §14.1 to the §5 assumed inputs (item 4).
- Recording what was selected, skipped and why, per request: from HLD §14.3 into the §5.1 Assemble text.
- "Latency is measured, not a design target at this stage": one line in §5.1, and G4 reworded.
- Packing mechanics in §7.4 reduced to one sentence; the status-default and conflict-retention rules are unchanged.
- Evidence unit (§7.1): one `applicability` field (version, branch or environment, period) replaces the four timestamps; historical (`as_of`) and newer-but-inapplicable behavior in §7.5 unchanged.

Removed, each **out of scope (research stage)**:

| Removed | Where it was |
|---|---|
| The four evidence timestamps (`occurred_at`, `recorded_at`, `retrieved_at`, `applicability.effective_from/to`) | HLD §7.1 |
| Packing flow diagram and per-request caps list | HLD §7.4 |
| Section 14 (cross-cutting), including the §14.2 fast-mode latency budget table, stage targets and gantt chart | HLD §14 |
| Decisions Q1, Q2, Q7, Q8, Q10, Q15, Q16, Q17 (compatibility, pilot journey, label ownership, entity ownership, memory storage, adapter survey, failure semantics now answered by §7.4, holdout ownership); Q4 kept as the one cost-versus-completeness question | HLD §21 |

