# Sanctum review history and restructuring record

[Overview and reading guide](README.md) · [Section map](section-map.md)

> Status: proposed research design, reorganized from v5.1. Lab work is experimental. Original section numbers are retained.

This page preserves the source's review dispositions and v5.1 change record. “Accepted” in these historical tables means a finding was accepted/addressed in that document; it does not establish stakeholder approval, executable verification, or production acceptance.

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
