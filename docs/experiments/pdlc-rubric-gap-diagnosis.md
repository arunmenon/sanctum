# PDLC rubric gaps: first trace diagnosis

The corrected comparison contains all 90 direct-hub and 90 unconstrained Sanctum answers. Unconstrained coverage exceeds direct access by 13.63 percentage points overall. This is a historical, same-corpus pilot comparison with human and independent-gold acceptance pending; it is not a causal production claim.

## Where the advantage appears

These family means combine supported, partial and boundary tasks. Each family contains only five tasks and fifteen answers per condition; inspect the scope breakdown before interpreting them.

| Task family | Direct hubs | Unconstrained Sanctum |
| --- | ---: | ---: |
| Behavior | 85.56% | 100.00% |
| Dependency/impact | 100.00% | 97.78% |
| Implementation/design | 72.78% | 90.56% |
| Rollout/recovery | 76.67% | 90.00% |
| Testing | 76.67% | 93.33% |
| Uncertainty | 58.67% | 80.44% |

Explicit HLD tasks average 69.44% direct versus 90.74% unconstrained (three tasks). LLD averages 77.78% versus 90.28% (two tasks). These small groups identify investigation priorities, not reliable family-level winners.

## What still fails

The ledger contains 37 observations across 16 tasks: eleven exact gold targets not delivered, six delivered targets without fact credit, five required target sources not called, three boundary-credit disputes, ten incomplete plan items and two material unsupported claims. Repetitions share facts; the categories do not estimate independent population failure rates.

- **Selection:** fraud-client uncertainty answers miss the MemoryHub retraction of a duplicate-posting/retry hypothesis. Jev considered all four hubs but selected DocHub alone. Richer descriptions may help it recognize prior-investigation evidence.
- **Retrieval:** a payment testing answer omits the client conversion from a library timeout to `FraudServiceTimeout`. CodeHub was selected, but the needed client evidence was not delivered. A selected hub is insufficient when search misses the module.
- **Answer completeness:** ledger batch evidence was delivered, but a rollout answer did not establish that batch processing is separate from the synchronous payment path. This calls for answer/rubric diagnosis, not automatically more retrieval.
- **Judgment disputes:** some boundary facts were marked met without claim references, so mechanical credit was correctly withheld under the current contract. Another judgment may require one exact code artifact even though equivalent entailing evidence is permitted. These require individual review; no automatic credit repair is justified.
- **Unsupported claims:** two answers overstate draft ledger follow-up behavior or claim an identity prototype is unaffected by routing changes without supporting evidence. Retain the penalties unless a specific source establishes the claim.

Saved traces expose delivered passages but not the entire pre-packing candidate pool. For undelivered targets, fetching versus packing remains unresolved. Missing an exact gold artifact also does not prove that no alternate supporting evidence was available.

## Changes under test

The existing Jev descriptions mostly report artifact and location counts. Four content-grounded descriptions now summarize evidence kinds, observed topics and limitations, supported by exact source quotations. The second variation operationalizes 52 already-grounded place mappings; it introduces no new entity identity, authority declaration or forced source. Both are isolated experimental inputs.

Jev continues to decide freely among all four hubs, including selecting none. The follow-up tests unchanged routing, descriptions alone, memory alone and their combination. Development retrieval probes precede fresh task verification and answer-quality evaluation. Extra calls are not the optimization target.

## Development probe outcome

All 144 probes completed. Exact, citable, source/artifact/version-bound target recall is 24/36 for unchanged routing, 20/36 for descriptions, 24/36 for memory, and 20/36 for both. A saved-evidence credit audit found no change when tightening the target check from text matching to exact artifact identity. These scores are retrieval diagnostics, not answer-quality scores.

Descriptions improve MemoryHub target-source selection from 5/10 to 7/10, but reduce SkillHub from 8/10 to 3/10 and DocHub from 3/8 to 2/8. CodeHub remains 8/8. Reviewed memory changes five native selector query plans, but the selected targets were already delivered in those cases, so this probe shows no added recall. Most probe requests do not resolve a canonical subject; accepting places alone does not solve that problem.

Neither variation is promoted. A 48-attempt randomized, same-corpus development follow-up now tests twelve new questions, one attempt per variant, to distinguish retrieval diagnostics from full answer outcomes. Task-family drift and an exact repeated development fact were repaired; shared alias and error-boundary premises are explicitly disclosed. HLD, LLD, six supported, three partial and three boundary questions are represented. Independent acceptance is pending, and this is not an independent generalization evaluation.

Reproduction tools: `tools/analyze_rubric_gaps.py`, `tools/build_routing_descriptor_jobs.py`, `tools/validate_routing_descriptors.py`, `tools/prepare_reviewed_place_memory.py`, `tools/prepare_rubric_variants.py`, `tools/probe_rubric_variants.py`, and `tools/prepare_fresh_rubric_tasks.py`. Raw evidence remains local under `build/rubric-gap-audit/`; no source credentials or answer-key records are published in this document.
