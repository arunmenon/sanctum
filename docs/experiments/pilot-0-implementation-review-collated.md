# Pilot-0 implementation review: findings and dispositions

3 October 2026. One parallel review round, followed by implementation fixes and verification; no repeated review loop and no paid Claude benchmark.

Both reviewers received the same immutable 539-file snapshot, `build/implementation-review/snapshot-01`. Snapshot manifest SHA256: `b81d39ebe0be359e97671c41c627c43fa4a33e9aaca5595eea8d744d32d23b25`. Astra verified all listed hashes. The coordinator verified the snapshot; Claude did not independently hash it. Candidate canonical JSON SHA256 is `2d3388bae6e9141edc879f982a0d019bdead70710862cc6e2e8e56241e758642`; this deliberately differs from the byte-level file hash. Correct proposal count: 578 structured/navigation + 79 content + 31 lab declarations = 688.

Astra low completed its review: `build/implementation-review/astra-low-review.md` and `astra-low-recommendations.json`. Claude `claude-fable-5-1`, low, emitted `claude-low-review.md`, then terminated at its SDK spend limit. That review is **partial**, not a full second acceptance. It inspected the scorer, runner, public tasks and selected probe/policy summaries, but not private gold, fixture cases or most runtime code. The actual hosted model identifier was observed. Its SDK cost estimate was $3.76373275 against a $3 requested limit; this is not a billed invoice and demonstrates that the SDK limit is not a hard monetary ceiling. No second review was launched.

## Implementation findings

| Finding | Disposition and verification |
|---|---|
| Astra F1: stale semantic review could bless changed prose | Fixed. Reviews must carry the recomputed judge-packet SHA256; changed prose, claims or gold invalidate old credit. Scorer regression cases pass. |
| Astra F2: stale scores or missing terminal results could enter comparison | Fixed. Report verifies task, attempt, answer, gold and judge-packet bindings; missing results/answers invalidate completeness. Fixture exclusion also uses the ledger. Report regressions pass. |
| Astra F3: instructions omitted from frozen schedule | Fixed. Instruction bytes are hashed in schedule/report basis; edits require a new schedule. |
| Astra F4 / Claude M4: direct proof only listed repositories | Fixed. `bundle-connections-04` performs direct search and full-file reads on both bundles. `scorer-delivery-direct-01` scores an actual direct-delivered citation, including wrong-version rejection. |
| Claude H1: two public evidence-ID namespaces | Fixed. Normalization exposes only the controller evidence ID; original router receipt remains private. Delivery regression passes. |
| Claude H2: null model/effort and unbound CLI evidence | Paid validation already rejected null identifiers. Current ready bundle explicitly pins model/effort and 32 tool calls; isolation/turn proofs and current CLI executable hash are now verified before paid dispatch. |
| Claude H3: self-attested human acceptance | Fixed. Final completion requires a pinned human-reviewer registry, authorized role and reviewer different from the semantic adjudicator. No human acceptance is fabricated. |
| Claude M1: arm visible through query/call patterns | Fixed. Judge packet exposes aggregate source outcomes, without queries/tool-call patterns. This reduces explicit arm cues; semantic answer content can still reveal style. |
| Claude M2: generic refusal after arbitrary call earned boundary credit | Fixed. Requires boundary claim type, a scoped boundary record and successful relevant-source search/read. Listing, unrelated sources and failed calls cannot satisfy this prerequisite. Semantic absence adjudication remains necessary. |
| Claude M5: ABOUT stamps alone did not prove routing memory | Stronger live proof now exercises denotation resolution, must-consult activation, accepted ABOUT bindings and actual Jev usage. It exposed and repaired namespace access declarations and empty-selector source-wide rules. `accepted-runtime-03` passes. This proves operation, not benefit. |
| Claude M7: readiness booleans lacked proof bindings | Isolation and turn proofs are now hash-pinned and tied to the CLI executable/model. Schedule pins config/tasks/gold/corpus/instructions. Paid budget additionally requires the existing spend/pricing ledger. Operator declarations remain trusted inputs, not financial approval from a model. |
| Claude L1/L2/L3/L4 | Empty required-fact sets and duplicate citation keys rejected; unsupported extra claims with severity “none” become material; tool-call limit explicit in current config. |
| Claude L6/L7 | Living readiness/checklist reconciled to latest evidence; canonical-content and file hashes labelled distinctly. Historical logs/snapshots remain preserved. |

## Declared rules, disagreements and limits

Claude M3: all content shown to the agent, including metadata and repeated evidence, consumes the common delivery budget in both arms. This is the intended rule. Internal router token estimates are not controller totals; budget exhaustion is reported and prevents claiming complete execution under the stipulated limits. No overhead advantage or throughput claim follows from fixtures.

Claude M6: accepted CodeHub authority means what that versioned source says, including a draft version. It does not certify deployed behavior or authorize a draft procedure. Version/status evidence and common instructions preserve this distinction. Astra's scoped recommendation agrees with versioned-source authority; the coordinator retains that scope rather than declaring drafts deployed.

Claude L5: no hosted task timing study establishes that eight rounds fit within 120 seconds. That is a future experiment limit, not a proven performance result. D2 remains uncalibrated shadow/preserve mode. No routing-benefit claim is made.

## Scoped data disposition

Astra F5 remains an explicit scope limit. Accept **350 exact assertion IDs** only: 195 DENOTES, 31 PARENT, 15 unknown-subject ABOUT, 31 synthetic lab policy declarations and 78 content ABOUT. **338 stay unreviewed**: 337 metadata-derived ABOUT/SELECTS_FOR plus `assertion-9288c33ae133556d34d72b32`. No unsupported canonical subject was guessed.

This scoped read-only development release is `pilot-reviewed-317cbcc55f5e`, activated only in `build/agent-bundles/pdlc-ready-development-02`. Review, separate delegation and synthetic source-owner records are persisted and pinned. Namespace ACL declarations cover 56 native namespace/location pairs; they grant lab visibility, not domain membership or enterprise approval. Original control seeds and proposed candidate remain preserved.

All thirty tasks were source-verified against the 120-record corpus. Astra recommends eighteen supported tasks for development use; twelve partial/out-of-scope gold rows still need independent semantic absence acceptance before frozen evaluation. All eleven scorer fixture labels were independently inspected as development test oracles. Neither task gold nor fixtures certify a semantic model judge or human sign-off. Seven tasks share R42-related facts, and current caller requirements are empty: report these diversity limits and use fresh independently authored evaluation tasks when pursuing generalization.

## Verification and closure

Broad regression: `full-regression-04.log`, **635 passed, two live-provider checks skipped, six existing expected failures**. Subsequent fixes: `post-review-fixes-01.log`, **73 passed**. Direct and Sanctum connection reuse: `bundle-connections-04`, four completed fixture attempts across PDLC and shipping. Scorer delivery: `scorer-delivery-02` and `scorer-delivery-direct-01`, supported paraphrase credited and wrong version rejected; hand-authored answers, no inference or operational completion. Accepted memory/System One: `accepted-runtime-03`, successful real synthetic Jev call and routing activations, zero Claude calls.

Confirmed implementation blockers are fixed and verified. Remaining frozen-gold, human adjudication, provider pricing/authentication and M8/D-EXT budget gates belong to paid development/evaluation readiness. The [readiness report](pilot-0-readiness.md) supplies commands and preserves these limits.
