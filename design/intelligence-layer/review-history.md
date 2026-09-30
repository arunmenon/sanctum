# Sanctum review history and restructuring record

[Overview and reading guide](README.md) · [Section map](section-map.md)

> Status: proposed research design, version 5.2 (reorganized from v5.1). Lab work is experimental. Original section numbers are retained.

This page preserves the source's review dispositions, the v5.1 change record, and the v5.2 holistic review (R-Holistic) with its dispositions. “Accepted” in these historical tables means a finding was accepted/addressed in that document; it does not establish stakeholder approval, executable verification, or production acceptance.

## Restructuring record

- Source: [unchanged v5.1 document](hld.md).
- Preserved all 23 numbered top-level sections, diagrams, tables, examples, and fixtures. Section numbers remain stable across pages.
- Added audience guidance, proposal/spike framing, explicit status caveats, navigation, and a phase-based execution guide.
- Converted section/example/fixture references to links where targets are known, without rewriting code or diagrams.
- Q9 wording aligned with §9.7: DENOTES approval requires the native-term owner and canonical-entity owner, or explicit delegated stewardship.
- Q16 remains an open decision. Its proposed default now follows Example 9 for a missing must-consult source (`insufficient`) and explicitly leaves procedure-conflict behavior to be resolved; no blanket `partial` override.
- Replaced the unavailable bare `sanctum-lab-plan-revised.md` pointer with the existing scaffold plan and documented its age.
- The original engineering proposal was not provided; comparison with it remains unresolved. No architecture adoption or experiment result is inferred.
- [Section ownership map](section-map.md) and [machine-readable preservation check](preservation-check.json) record coverage and the source hash.

---

<a id="section-19"></a>

## 19. Review disposition (F01–F23)

| Finding | Topic | Disposition | Where addressed |
|---|---|---|---|
| F01 | Authorization vs. learned eligibility | **Accepted** | [§4](hld.md#section-4) principle 1, [§6.4](hld.md#section-6-4) D2, [Ex. 6](contracts-and-scenarios.md#example-6) |
| F02 | Unknown / sufficiency semantics | **Accepted** | [§6.4](hld.md#section-6-4), [§6.6](hld.md#section-6-6), [Ex. 7](contracts-and-scenarios.md#example-7), 8 |
| F03 | D3 depends on D1/D2 in same call | **Accepted** | [§6.3](hld.md#section-6-3) rounds |
| F04 | `calibrated_p` meaning | **Accepted** | [§6.4](hld.md#section-6-4), [§6.6](hld.md#section-6-6) |
| F05 | Calibration and labels | **Accepted** | [§6.5](hld.md#section-6-5), [§6.7](hld.md#section-6-7) |
| F06 | Duplicates used to skip sources | **Accepted** | [Ex. 2](contracts-and-scenarios.md#example-2) |
| F07 | Authority too coarse | **Accepted, right-sized** | [§7.2](hld.md#section-7-2) fact-kind authority |
| F08 | Metadata sensitivity | **Accepted** | [§8.6](memory-design.md#section-8-6) scoped IDs, [§9.7](memory-design.md#section-9-7) governance, [§14.1](hld.md#section-14-1) |
| F09 | Mixed-signal Beta | **Accepted** | [§9.10](memory-design.md#section-9-10) separate signals, [Ex. 13](contracts-and-scenarios.md#example-13) |
| F10 | Routing as subset decision | **Accepted** | [§9.10](memory-design.md#section-9-10), E5 |
| F11 | Ranking and time semantics | **Accepted** | [§7.1](hld.md#section-7-1), [§7.3](hld.md#section-7-3), [§7.5](hld.md#section-7-5), [Ex. 4](contracts-and-scenarios.md#example-4) |
| F12 | Token packing | **Accepted** | [§7.4](hld.md#section-7-4), [Ex. 3](contracts-and-scenarios.md#example-3) |
| F13 | Model weakening governance | **Accepted** | [§13](hld.md#section-13), [Ex. 11](contracts-and-scenarios.md#example-11) |
| F14 | Write idempotency | **Accepted, deferred to write note** | [§13](hld.md#section-13), [Ex. 11](contracts-and-scenarios.md#example-11) |
| F15 | Token passthrough | **Accepted** | [§5.3](hld.md#section-5-3), [§14.1](hld.md#section-14-1) |
| F16 | Untrusted evidence | **Accepted** | [Ex. 10](contracts-and-scenarios.md#example-10), [§14.1](hld.md#section-14-1) |
| F17 | Latency arithmetic | **Accepted** | [§6.3](hld.md#section-6-3), [§14.2](hld.md#section-14-2) |
| F18 | Replay guarantees | **Accepted, right-sized** | [§11](hld.md#section-11), [§15](hld.md#section-15) |
| F19 | Degradation | **Accepted** | [Ex. 9](contracts-and-scenarios.md#example-9) |
| F20 | Bundled comparisons | **Accepted** | §16.2 (lab) ladder |
| F21 | Contract versions | **Accepted** | [§6.6](hld.md#section-6-6), [§7.1](hld.md#section-7-1), [§12.2](contracts-and-scenarios.md#section-12-2) |
| F22 | Adapter contract | **Accepted** | [§12.3](contracts-and-scenarios.md#section-12-3), [Ex. 12](contracts-and-scenarios.md#example-12) |
| F23 | Relationship to earlier "C6" proposal | **Needs input** | Q1 |

---

### Memory review disposition (M01–M13)

| Finding | Topic | Disposition | Where addressed |
|---|---|---|---|
| M01 | Names vs. subjects vs. places | **Accepted** | [§8.5](memory-design.md#section-8-5), [§8.6](memory-design.md#section-8-6), [Ex. 5](contracts-and-scenarios.md#example-5), [Fixture 17](contracts-and-scenarios.md#fixtures-16-25) |
| M02 | Ambiguity within an org | **Accepted**; agent default is separated interpretations | [§9.2](memory-design.md#section-9-2), [Fixture 16](contracts-and-scenarios.md#fixtures-16-25) |
| M03 | Allowed uses of each relation | **Accepted** | [§8.7](memory-design.md#section-8-7), [Fixture 18](contracts-and-scenarios.md#fixtures-16-25) |
| M04 | Procedure grammar and precedence | **Accepted** | [§9.4](memory-design.md#section-9-4), [Fixture 20](contracts-and-scenarios.md#fixtures-16-25) |
| M05 | Fallback and query plans | **Accepted** | [§9.3](memory-design.md#section-9-3), [Fixture 19](contracts-and-scenarios.md#fixtures-16-25) |
| M06 | Descriptors change routing | **Accepted**; pinned in v0 | [§9.7](memory-design.md#section-9-7), [Fixture 21](contracts-and-scenarios.md#fixtures-16-25) |
| M07 | Revocation and probe trust | **Accepted**; depends on adapter capabilities (Q15) | [§9.1](memory-design.md#section-9-1), Fixtures 21, 22 |
| M08 | Memory releases | **Accepted**, right-sized to a versioned manifest | [§9.6](memory-design.md#section-9-6), [Fixture 23](contracts-and-scenarios.md#fixtures-16-25) |
| M09 | Version applicability | **Accepted** | [§7.5](hld.md#section-7-5), [Fixture 24](contracts-and-scenarios.md#fixtures-16-25) |
| M10 | Reconstruction | **Accepted**; reconstruction window declared | [§8.4](memory-design.md#section-8-4), [§9.9](memory-design.md#section-9-9) |
| M11 | Jev ranks, does not establish identity | **Accepted** | [§9.10](memory-design.md#section-9-10), [Ex. 14](contracts-and-scenarios.md#example-14) |
| M12 | Counterfactuals and baseline | **Accepted** | §17.1 (lab) E6, §17.2 (lab) alias-table comparison, [Ex. 14](contracts-and-scenarios.md#example-14) |
| M13 | Holdout reuse | **Accepted**; matters from E7 | [§9.8](memory-design.md#section-9-8), [§9.10](memory-design.md#section-9-10), [Fixture 25](contracts-and-scenarios.md#fixtures-16-25) |

---

<a id="section-22"></a>

## 22. What changed in v5.1

v5.1 is a contract-consistency patch. It changes no architecture. It closes gaps found while checking the lab plan against v5.

| # | Gap in v5 | v5.1 change | Where |
|---|---|---|---|
| 1 | [§7.5](hld.md#section-7-5) needs branch, environment and effective time, but the [§7.1](hld.md#section-7-1) EvidenceUnit sketch lacked them | `applicability` block with `applicability_status`; no fabricated context | [§7.1](hld.md#section-7-1) |
| 2 | Verify mode promised verdicts while D7 is deferred | Pilot `verify` returns evidence and conflict flags; `verdicts` absent until D7; advertised as `partial` | [§12.1](contracts-and-scenarios.md#section-12-1), [Ex. 7](contracts-and-scenarios.md#example-7), [§12.3](contracts-and-scenarios.md#section-12-3) |
| 3 | `frozen_corpus` appeared as a replay level but not in the response enum | Declared a research execution profile, not a wire value | [§15](hld.md#section-15) |
| 4 | Prose used statuses (`unresolved`, `insufficient_budget`, `unsupported_for_as_of`) not in the [§12.2](contracts-and-scenarios.md#section-12-2) enums | Enums stay closed; detail moves to versioned reason codes | [§12.2](contracts-and-scenarios.md#section-12-2), [§9.3](memory-design.md#section-9-3), [Ex. 4](contracts-and-scenarios.md#example-4), [Fixture 19](contracts-and-scenarios.md#fixtures-16-25) |
| 5 | No response shape for separated interpretations ([§9.2](memory-design.md#section-9-2)) | `interpretations[]` in the response; `caller_profile` in the request | [§12.0](contracts-and-scenarios.md#section-12-0), [§12.2](contracts-and-scenarios.md#section-12-2) |
| 6 | No request contract; credentials could be read as tool arguments | `RetrieveRequest` defined; credentials only in transport or session | [§12.0](contracts-and-scenarios.md#section-12-0), [§14.1](hld.md#section-14-1) |
| 7 | Sanctum did not advertise partial support | Sanctum capability manifest with supported / partial / unsupported | [§12.3](contracts-and-scenarios.md#section-12-3) |
| 8 | Lab configs let C1 and C4a be unfair controls | C1-fair, C1-naive, C4a-equivalent, C4a-label-only; hybrid DocHub before H5 conclusions; adapter survey and Kestrel-shaped questions in the minimum | §17.2 (lab) |

---

<a id="v5-2"></a>

## v5.2: holistic review (R-Holistic)

The holistic review read all design pages and the lab implementation and asked whether the design is complete enough for a production-generic cascade. v5.2 answers its three first-priority changes and the missing `ABOUT` layer. It adds contracts; it does not change the architecture's layers or boundaries. Disposition values: **adopted** (changed as proposed), **adapted** (the intent is adopted in a different form), **deferred** (accepted as a gap, not addressed in v5.2), **rejected** (not a design change, with the reason).

| Finding | Topic | Disposition | Where, or why |
|---|---|---|---|
| R-H 1.1 | One trusted request execution context and budget ledger | **Adopted** | [HLD §5.4](hld.md#section-5-4): ExecutionContext, absolute deadline, ledger spanning rules, searches, fetches, model calls, retries and serialization; explicit scope narrowing; pinned versions |
| R-H 1.2 | Safe defaults inconsistent; conflict packing loses flags | **Adopted** | [Contracts §12.4](contracts-and-scenarios.md#section-12-4) transition matrix for D1 to D9; conflict records kept with explicit omission; status defaults reconciled; [HLD §6.4](hld.md#section-6-4), [§7.4](hld.md#section-7-4), [Ex. 9](contracts-and-scenarios.md#example-9), Q16 aligned |
| R-H 1.3 | Independent D2 probabilities do not define subset selection | **Deferred** | Accepted as a gap: a small planner around independent predictions (marginal value, minimum coverage, bounded exploration) needs its own design and evidence; D2's safe default is unchanged |
| R-H 1.4 | Round information contracts, cache keys, observation ids | **Adapted** | Cache keys, stable observation ids and retention rules adopted in [HLD §5.4](hld.md#section-5-4) and [§14](hld.md#section-14); typed per-round state schemas deferred with the decision executor (R-H 4.2) |
| R-H 2.1 | Release pinning is not correctness under concurrent change | **Adopted** | [Memory §9.6](memory-design.md#section-9-6): content-addressed dependency closures, live policy epoch, change-feed watermarks and gap detection, freshness limits, recheck before egress |
| R-H 2.2 | Governance lacks an enforceable assertion model | **Adopted** | [Memory §9.11](memory-design.md#section-9-11): assertion envelope and publication checks |
| R-H 2.3 | Retention boundaries for receipts and inference replay | **Adopted** | [HLD §5.4](hld.md#section-5-4) retention table: assertion storage, routing observations, retained evidence, inference replay |
| R-H 3.1 | Identity and replay capabilities not negotiated | **Adopted** | [Contracts §12.3](contracts-and-scenarios.md#section-12-3) capability-aware identity, filter and temporal contract with honest partial support |
| R-H 3.2 | Metadata visibility inferred from readable places | **Adopted** | [Memory §9.11](memory-design.md#section-9-11): namespace, applicability and metadata permission kept apart; places are not proof of name visibility |
| R-H 3.3 | Hub vocabulary leaks into subjects and selectors | **Adopted** | [Memory §8.10](memory-design.md#section-8-10) attributed subjects; typed selector semantics in [Contracts §12.3](contracts-and-scenarios.md#section-12-3) |
| R-H 4.1 | Broker purpose is architectural, implementation harness-specific | **Adapted** | The broker's authority stays as specified in [System One providers §6](system-one-providers.md#6-isolation-the-system-one-broker); v5.2 adds exact-version evidence handles ([Contracts §12.3](contracts-and-scenarios.md#section-12-3)) and a per-request data-class ceiling ([HLD §5.4](hld.md#section-5-4)); trusted template rendering and physical placement are implementation choices |
| R-H 4.2 | Selected decisions, not a generic cascade | **Deferred** | Discriminated decision schemas and one shared decision executor across tiers are accepted as the next contract change; v5.2 limits itself to the four changes above |
| R-H 4.3 | Invariants weaker in the implementation than stated | **Rejected** as a design change | The stated invariants stand; the gaps are implementation defects, tracked with the lab |
| R-H 4.4 | Lab assumptions in the core | **Rejected** as a design change | The design already puts vocabularies, preferences and temporal terms in owner and adapter data; removing them from code is implementation work |
| R-H 5.1 | Activation needs decision-specific economic gates; D6 displacement | **Adapted** | D6 displacement bounded in [Contracts §12.4](contracts-and-scenarios.md#section-12-4); per-decision economic activation gates (benefit over a no-model control, spend, omission risk, candidate recall) deferred to the next System One providers revision |
| R-H 5.2 | Runtime calibration matching weaker than the binding | **Adapted** | The execution context pins complete calibration bindings and cache keys include them ([HLD §5.4](hld.md#section-5-4)); runtime matching is implementation; drift monitoring deferred |
| R-H 5.3 | Long outages and LLM escalation policies | **Deferred** | Circuit breaking, sustained fallback capacity and purpose-bound LLM use need an operations design; request-level safe fallback is unchanged |

The review's memory-fidelity table and judgments describe the lab implementation and need no design disposition.

