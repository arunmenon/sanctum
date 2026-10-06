# Lab ADR catalog: Astra review and corrections

- **Reviewer:** Astra, medium effort; one independent, read-only pass on 6 October 2026.
- **Reviewed scope:** original catalog and plan, seven bucket indexes, all 22 ADRs, and selective supporting implementation/experiment records.
- **Verdict:** ready with corrections. No wholesale restructuring needed.
- **Prompt:** [Approved review prompt](lab-adr-catalog-review-prompt-20261006.md).
- **Disposition:** corrections applied by the implementation agent; no second review loop or runtime changes.

## Findings and dispositions

| ID | Priority | Finding and evidence | Reader impact | Applied correction |
|---|---|---|---|---|
| F1 | High | Catalog starts with ADRs rather than Sanctum; records use gold, MCP, ontology, projection, ACTIVE, Jev and unnamed task families without context. | Newcomers cannot connect decisions to the answer path or distinguish routing memory from MemoryHub. | Added system orientation, compact glossary, bucket context, first-use explanations and examples; named the six families in ADR-017. |
| F2 | High | ADR-012 omits release-read eligibility override; `pipeline.py` changes unsupported-for-mode plans into callable plans. Active-plan follow-on records why the first campaign was retired. | Earlier eligibility rules could recreate the wrong experiment. | Explained available-revision reads with applicability metadata and no rules fallback for unavailable provider decisions; linked the follow-on section. |
| F3 | Medium | No ADR explains whole-unit evidence packing and conflict preservation, implemented in `assembly.py`. ADR-015 covers harness delivery accounting instead. | Hub selection alone does not explain what evidence reaches Claude. | Added ADR-023 under Evidence and hubs; cross-linked ADR-015 and ADR-018. Catalog now has 23 records in the same seven buckets. |
| F4 | Medium | ADR-011/012 lack local reciprocal links; ADR-011 gives chronology rather than rationale and embeds a campaign-specific skip count. | Historical may look removed; unconstrained may look like a replacement default. | Added reciprocal links, experimental-override wording, plain protection definitions and the rationale for preserving sources. Replaced the count with the enduring tradeoff and linked result. |
| F5 | Medium | ADR-018 leaves checklist scale and acceptance unexplained; explicit judge masking is missing from ADR-018/020 despite `agent_score.py` implementation. | Automated completion could be confused with human acceptance; readers miss the comparison safeguard. | Defined 0/1/2, distinguished independent gold acceptance from answer acceptance, explained neutral aliases and masking, and retained incomplete-blinding/audit limits. |
| F6 | Medium | ADR-006 claims generation is inexpensive relative to establishing evidence without a comparable cost denominator. | An intuitive observation looks like an evidenced economic conclusion. | Replaced it with the factual point that draft generation does not remove checking work. |
| F7 | Low | Correction rules and reconstructed rationale are implicit; ADR-003 title implies a version policy not recorded in its decision. | Editors may overwrite history or infer unsupported compatibility promises. | Added dated amendment versus new-choice rules and retrospective rationale notes; narrowed ADR-003 title to schema synchronization while preserving ID and URL. |

## Bucket assessment

| Bucket | Astra assessment |
|---|---|
| Scope and contracts | Coherent boundaries; explain system/gold and narrow schema title. |
| Evidence and hubs | Coherent representation/preparation; natural home for assembly decision. |
| Routing memory | Strong storage → collection → review sequence; explain subjects, locations and release construction. |
| System One | Appropriate broker/policy separation; define component and connect history. |
| Agent harness | Coherent lifecycle; keep delivery accounting distinct from router assembly. |
| Evaluation | Strong task/scoring/correction/comparison separation; explain scales, acceptance and masking. |
| Operations and documentation | Useful handover decisions and candid reproduction limits; no split needed. |

No buckets need merging. The catalog navigation now labels System One as “System One: model decisions” for easier discovery.

## Record-by-record assessment

| ADR | Astra assessment and correction focus |
|---|---|
| 001 | Sound scope; add Sanctum purpose. |
| 002 | Sound isolation; define gold and gateway. Do not imply hostile-code containment. |
| 003 | Sound schema consistency; narrow version-policy title. |
| 004 | Sound local service; explain hub and MCP. |
| 005 | Clear home/cross-links choice; add code/document example. |
| 006 | Sound audited authoring; remove unsupported comparative cost. |
| 007 | Sound storage; explain ontology and equivalent table queries. |
| 008 | Sound grounding; give relationship/support example. |
| 009 | Strong review/release separation; explain projection and ACTIVE. |
| 010 | Sound broker/accounting; explain internal calls and exact configuration pins. |
| 011 | Correct historical treatment; improve rationale and link 012. |
| 012 | Correct experimental framing; document version-read override and unavailable-provider behavior. |
| 013 | Sound portability; explain bundle and product-development scope. |
| 014 | Sound fresh-session/tool-surface choice; auth belongs to controlled attempt scope. |
| 015 | Sound delivery/accounting; link separate assembly policy. |
| 016 | Strong recovery; explain sent request versus saved final outcome. |
| 017 | Sound diversity; name families and expand design acronyms; pending acceptance candid. |
| 018 | Strong scoring separation; explain scale, acceptance and masking. |
| 019 | Good historical correction record; preserves judgments and identifies recovery exceptions. |
| 020 | Sound task comparisons; explain pairing and task resampling. |
| 021 | Clear operations and honest fresh-clone limitation. |
| 022 | Clear maintainability choice; no substantive issue. |

ADR-023 was added in response to F3 and locally checked against assembly code; it was not part of Astra’s original 22-record review.

## Representative readability changes

- **Orientation:** Claude answers; Sanctum retrieves; Jev helps choose hubs; a separate scorer grades against private criteria.
- **Release construction:** “Build the runtime memory file from links with supporting evidence and an authorized review.”
- **Internal model calls:** Explain that the broker keeps calls inside retrieval visible in experiment usage records.
- **Comparison:** Average attempts for each task/setup, compare the same tasks, then resample tasks with their attempts kept together.
- **Recovery:** Explain the interrupted request before introducing dispatch/final-outcome records.

## Verification limits

Astra’s source checks supported local graph/table parity, unused RELATES_TO, supporting-span validation, reviewed release selection, raw selection threshold, unconstrained override behavior, schema consistency checks and process isolation. It found no invented approval; the owner register supports working-assumption language and the active plan records authorization for the experiment.

Astra did not reconstruct ignored campaign artifacts, numerical results, provider receipts or human acceptance records, and did not rerun link checks. These remain dependent on linked reports. The implementation agent’s post-correction checks cover Markdown structure and relative links, not a second independent review or experiment rerun.

## Local post-correction verification

- 34 Markdown files and 206 relative links/anchors passed checks.
- All 23 ADR IDs, filenames and required sections agree; Markdown fences are balanced.
- `git diff --check` passed. No runtime behavior, scores or experiment inputs changed.
