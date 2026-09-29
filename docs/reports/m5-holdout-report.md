# Sanctum Lab report

> SYNTHETIC, NOT PRODUCTION EVIDENCE. 60 dev + 40 holdout questions support directional results and debugging only, not population estimates.

Ranker: `lexical_smoke` in every arm; the B* cross-encoder profile is deferred (discrepancy register 18), so these are lexical-ranker results.

## Runs and provenance

| config | run | world sha256 | seed | memory release | failure profile | git commit | dirty | integrity |
|---|---|---|---|---|---|---|---|---|
| C1-fair | `C1-fair` | `452b57d9686b` | 20260930 | none | none | `90c11dd580` | True | True |
| C2 | `C2` | `452b57d9686b` | 20260930 | none | none | `90c11dd580` | True | True |
| C4 | `C4` | `452b57d9686b` | 20260930 | r1 | none | `90c11dd580` | True | True |
| C4a-equivalent | `C4a-equivalent` | `452b57d9686b` | 20260930 | r1 | none | `90c11dd580` | True | True |

## Config matrix

| config | routing | assembly | resolution | translation | procedures | memory_store | decision_provider |
|---|---|---|---|---|---|---|---|
| C1-fair | fanout_all | common | none | False | False | none | none |
| C2 | rules | common | none | False | registry_only | none | none |
| C4 | rules | common | denotes | True | memory | relations | none |
| C4a-equivalent | rules | common | denotes | True | memory | tables | none |

## Gates (pass/fail, never averaged)

| config | leakage | scope | wrong_entity |
|---|---|---|---|
| C1-fair | PASS | PASS | PASS |
| C2 | PASS | PASS | PASS |
| C4 | PASS | PASS | PASS |
| C4a-equivalent | PASS | PASS | PASS |

## Per-family results

| family | n | C1-fair success | C1-fair recall | C2 success | C2 recall | C4 success | C4 recall | C4a-equivalent success | C4a-equivalent recall |
|---|---|---|---|---|---|---|---|---|---|
| conflicting_sources | 4 | 0.50 | 1.00 | 0.25 | 0.88 | 0.50 | 0.88 | 0.50 | 0.88 |
| historical | 4 | 0.00 | 1.00 | 0.00 | 0.75 | 0.00 | 0.75 | 0.00 | 0.75 |
| hub_specific_name | 6 | 0.83 | 1.00 | 0.33 | 1.00 | 0.83 | 1.00 | 0.83 | 1.00 |
| multi_hub | 4 | 1.00 | 1.00 | 0.25 | 1.00 | 0.75 | 1.00 | 0.75 | 1.00 |
| named_service | 6 | 1.00 | 1.00 | 0.83 | 0.80 | 0.83 | 1.00 | 0.83 | 1.00 |
| no_source | 3 | 0.33 | - | 0.67 | - | 0.67 | - | 0.67 | - |
| restricted_content | 3 | 1.00 | 1.00 | 1.00 | 1.00 | 0.33 | 0.00 | 0.33 | 0.00 |
| same_name_two_meanings | 4 | 0.75 | 0.75 | 0.75 | 0.75 | 1.00 | 1.00 | 1.00 | 1.00 |
| vague | 3 | 0.33 | 0.83 | 0.33 | 0.83 | 0.33 | 0.83 | 0.33 | 0.83 |
| verify_claim | 3 | 0.67 | 1.00 | 0.67 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| all | 40 | 0.68 | 0.96 | 0.50 | 0.88 | 0.65 | 0.91 | 0.65 | 0.91 |

## Paired comparisons (b minus a, 95% cluster bootstrap by family and entity)

### Q2_routing: C1-fair vs C2

| metric | scope | n | clusters | a | b | delta | interval | b better | a better |
|---|---|---|---|---|---|---|---|---|---|
| safe_grounded_success | pooled | 40 | 31 | 0.68 | 0.50 | -0.17 | [-0.32, -0.05] | 1 | 8 |
| safe_grounded_success | conflicting_sources | 4 | 3 | 0.50 | 0.25 | -0.25 | [-1.00, 0.00] | 0 | 1 |
| safe_grounded_success | historical | 4 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | hub_specific_name | 6 | 4 | 0.83 | 0.33 | -0.50 | [-1.00, -0.14] | 0 | 3 |
| safe_grounded_success | multi_hub | 4 | 4 | 1.00 | 0.25 | -0.75 | [-1.00, -0.25] | 0 | 3 |
| safe_grounded_success | named_service | 6 | 5 | 1.00 | 0.83 | -0.17 | [-0.38, 0.00] | 0 | 1 |
| safe_grounded_success | no_source | 3 | 1 | 0.33 | 0.67 | 0.33 | [0.33, 0.33] | 1 | 0 |
| safe_grounded_success | restricted_content | 3 | 2 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | same_name_two_meanings | 4 | 2 | 0.75 | 0.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | vague | 3 | 3 | 0.33 | 0.33 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | verify_claim | 3 | 3 | 0.67 | 0.67 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | pooled | 34 | 28 | 0.96 | 0.88 | -0.07 | [-0.16, 0.00] | 0 | 3 |
| recall | conflicting_sources | 4 | 3 | 1.00 | 0.88 | -0.12 | [-0.50, 0.00] | 0 | 1 |
| recall | historical | 4 | 4 | 1.00 | 0.75 | -0.25 | [-0.75, 0.00] | 0 | 1 |
| recall | hub_specific_name | 6 | 4 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | multi_hub | 4 | 4 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | named_service | 5 | 4 | 1.00 | 0.80 | -0.20 | [-0.43, 0.00] | 0 | 1 |
| recall | restricted_content | 1 | 1 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | same_name_two_meanings | 4 | 2 | 0.75 | 0.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | vague | 3 | 3 | 0.83 | 0.83 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | verify_claim | 3 | 3 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | pooled | 40 | 31 | 3.88 | 2.75 | -1.12 | [-1.32, -0.93] | 0 | 34 |
| sources_attempted | conflicting_sources | 4 | 3 | 4.00 | 2.75 | -1.25 | [-2.00, -1.00] | 0 | 4 |
| sources_attempted | historical | 4 | 4 | 3.00 | 2.50 | -0.50 | [-1.00, 0.00] | 0 | 2 |
| sources_attempted | hub_specific_name | 6 | 4 | 4.00 | 2.83 | -1.17 | [-1.75, -0.67] | 0 | 5 |
| sources_attempted | multi_hub | 4 | 4 | 4.00 | 2.50 | -1.50 | [-2.00, -1.00] | 0 | 4 |
| sources_attempted | named_service | 6 | 5 | 4.00 | 2.83 | -1.17 | [-1.60, -1.00] | 0 | 6 |
| sources_attempted | no_source | 3 | 1 | 3.67 | 2.00 | -1.67 | [-1.67, -1.67] | 0 | 2 |
| sources_attempted | restricted_content | 3 | 2 | 4.00 | 3.00 | -1.00 | [-1.00, -1.00] | 0 | 3 |
| sources_attempted | same_name_two_meanings | 4 | 2 | 4.00 | 3.25 | -0.75 | [-1.00, -0.50] | 0 | 3 |
| sources_attempted | vague | 3 | 3 | 4.00 | 2.67 | -1.33 | [-2.00, 0.00] | 0 | 2 |
| sources_attempted | verify_claim | 3 | 3 | 4.00 | 3.00 | -1.00 | [-1.00, -1.00] | 0 | 3 |
| wrong_entity | pooled | 40 | 31 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | conflicting_sources | 4 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | historical | 4 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | hub_specific_name | 6 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | multi_hub | 4 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | named_service | 6 | 5 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | no_source | 3 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | restricted_content | 3 | 2 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | same_name_two_meanings | 4 | 2 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | vague | 3 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | verify_claim | 3 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |

### Q3a_memory_package: C2 vs C4

| metric | scope | n | clusters | a | b | delta | interval | b better | a better |
|---|---|---|---|---|---|---|---|---|---|
| safe_grounded_success | pooled | 40 | 31 | 0.50 | 0.65 | 0.15 | [-0.03, 0.31] | 9 | 3 |
| safe_grounded_success | conflicting_sources | 4 | 3 | 0.25 | 0.50 | 0.25 | [0.00, 0.50] | 1 | 0 |
| safe_grounded_success | historical | 4 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | hub_specific_name | 6 | 4 | 0.33 | 0.83 | 0.50 | [0.14, 1.00] | 3 | 0 |
| safe_grounded_success | multi_hub | 4 | 4 | 0.25 | 0.75 | 0.50 | [0.00, 1.00] | 2 | 0 |
| safe_grounded_success | named_service | 6 | 5 | 0.83 | 0.83 | 0.00 | [-0.60, 0.38] | 1 | 1 |
| safe_grounded_success | no_source | 3 | 1 | 0.67 | 0.67 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | restricted_content | 3 | 2 | 1.00 | 0.33 | -0.67 | [-1.00, 0.00] | 0 | 2 |
| safe_grounded_success | same_name_two_meanings | 4 | 2 | 0.75 | 1.00 | 0.25 | [0.00, 0.50] | 1 | 0 |
| safe_grounded_success | vague | 3 | 3 | 0.33 | 0.33 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | verify_claim | 3 | 3 | 0.67 | 1.00 | 0.33 | [0.00, 1.00] | 1 | 0 |
| recall | pooled | 34 | 28 | 0.88 | 0.91 | 0.03 | [-0.07, 0.12] | 2 | 1 |
| recall | conflicting_sources | 4 | 3 | 0.88 | 0.88 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | historical | 4 | 4 | 0.75 | 0.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | hub_specific_name | 6 | 4 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | multi_hub | 4 | 4 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | named_service | 5 | 4 | 0.80 | 1.00 | 0.20 | [0.00, 0.43] | 1 | 0 |
| recall | restricted_content | 1 | 1 | 1.00 | 0.00 | -1.00 | [-1.00, -1.00] | 0 | 1 |
| recall | same_name_two_meanings | 4 | 2 | 0.75 | 1.00 | 0.25 | [0.00, 0.50] | 1 | 0 |
| recall | vague | 3 | 3 | 0.83 | 0.83 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | verify_claim | 3 | 3 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | pooled | 40 | 31 | 2.75 | 2.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | conflicting_sources | 4 | 3 | 2.75 | 2.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | historical | 4 | 4 | 2.50 | 2.50 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | hub_specific_name | 6 | 4 | 2.83 | 2.83 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | multi_hub | 4 | 4 | 2.50 | 2.50 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | named_service | 6 | 5 | 2.83 | 2.83 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | no_source | 3 | 1 | 2.00 | 2.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | restricted_content | 3 | 2 | 3.00 | 3.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | same_name_two_meanings | 4 | 2 | 3.25 | 3.25 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | vague | 3 | 3 | 2.67 | 2.67 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | verify_claim | 3 | 3 | 3.00 | 3.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | pooled | 40 | 31 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | conflicting_sources | 4 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | historical | 4 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | hub_specific_name | 6 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | multi_hub | 4 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | named_service | 6 | 5 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | no_source | 3 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | restricted_content | 3 | 2 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | same_name_two_meanings | 4 | 2 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | vague | 3 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | verify_claim | 3 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |

### Q3b_storage_equivalence: C4 vs C4a-equivalent

| metric | scope | n | clusters | a | b | delta | interval | b better | a better |
|---|---|---|---|---|---|---|---|---|---|
| safe_grounded_success | pooled | 40 | 31 | 0.65 | 0.65 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | conflicting_sources | 4 | 3 | 0.50 | 0.50 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | historical | 4 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | hub_specific_name | 6 | 4 | 0.83 | 0.83 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | multi_hub | 4 | 4 | 0.75 | 0.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | named_service | 6 | 5 | 0.83 | 0.83 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | no_source | 3 | 1 | 0.67 | 0.67 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | restricted_content | 3 | 2 | 0.33 | 0.33 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | same_name_two_meanings | 4 | 2 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | vague | 3 | 3 | 0.33 | 0.33 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | verify_claim | 3 | 3 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | pooled | 34 | 28 | 0.91 | 0.91 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | conflicting_sources | 4 | 3 | 0.88 | 0.88 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | historical | 4 | 4 | 0.75 | 0.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | hub_specific_name | 6 | 4 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | multi_hub | 4 | 4 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | named_service | 5 | 4 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | restricted_content | 1 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | same_name_two_meanings | 4 | 2 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | vague | 3 | 3 | 0.83 | 0.83 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | verify_claim | 3 | 3 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | pooled | 40 | 31 | 2.75 | 2.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | conflicting_sources | 4 | 3 | 2.75 | 2.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | historical | 4 | 4 | 2.50 | 2.50 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | hub_specific_name | 6 | 4 | 2.83 | 2.83 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | multi_hub | 4 | 4 | 2.50 | 2.50 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | named_service | 6 | 5 | 2.83 | 2.83 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | no_source | 3 | 1 | 2.00 | 2.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | restricted_content | 3 | 2 | 3.00 | 3.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | same_name_two_meanings | 4 | 2 | 3.25 | 3.25 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | vague | 3 | 3 | 2.67 | 2.67 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | verify_claim | 3 | 3 | 3.00 | 3.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | pooled | 40 | 31 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | conflicting_sources | 4 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | historical | 4 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | hub_specific_name | 6 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | multi_hub | 4 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | named_service | 6 | 5 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | no_source | 3 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | restricted_content | 3 | 2 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | same_name_two_meanings | 4 | 2 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | vague | 3 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | verify_claim | 3 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |

## Failures

**C1-fair**: 13 of 40 cases not safe-grounded-successful
- h-009 (hub_specific_name): quality [receipt](../../runs/holdout-m5/C1-fair/receipts.jsonl#L9)
- h-013 (same_name_two_meanings): quality [receipt](../../runs/holdout-m5/C1-fair/receipts.jsonl#L13)
- h-017 (historical): quality [receipt](../../runs/holdout-m5/C1-fair/receipts.jsonl#L17)
- h-018 (historical): quality [receipt](../../runs/holdout-m5/C1-fair/receipts.jsonl#L18)
- h-019 (historical): quality [receipt](../../runs/holdout-m5/C1-fair/receipts.jsonl#L19)
- h-020 (historical): quality [receipt](../../runs/holdout-m5/C1-fair/receipts.jsonl#L20)
- h-021 (conflicting_sources): quality [receipt](../../runs/holdout-m5/C1-fair/receipts.jsonl#L21)
- h-023 (conflicting_sources): quality [receipt](../../runs/holdout-m5/C1-fair/receipts.jsonl#L23)
- h-027 (verify_claim): quality [receipt](../../runs/holdout-m5/C1-fair/receipts.jsonl#L27)
- h-028 (vague): quality [receipt](../../runs/holdout-m5/C1-fair/receipts.jsonl#L28)
- h-029 (vague): quality [receipt](../../runs/holdout-m5/C1-fair/receipts.jsonl#L29)
- h-032 (no_source): quality [receipt](../../runs/holdout-m5/C1-fair/receipts.jsonl#L32)
- h-033 (no_source): quality [receipt](../../runs/holdout-m5/C1-fair/receipts.jsonl#L33)

**C2**: 20 of 40 cases not safe-grounded-successful
- h-005 (named_service): quality [receipt](../../runs/holdout-m5/C2/receipts.jsonl#L5)
- h-007 (hub_specific_name): quality [receipt](../../runs/holdout-m5/C2/receipts.jsonl#L7)
- h-008 (hub_specific_name): quality [receipt](../../runs/holdout-m5/C2/receipts.jsonl#L8)
- h-009 (hub_specific_name): quality [receipt](../../runs/holdout-m5/C2/receipts.jsonl#L9)
- h-012 (hub_specific_name): quality [receipt](../../runs/holdout-m5/C2/receipts.jsonl#L12)
- h-013 (same_name_two_meanings): quality [receipt](../../runs/holdout-m5/C2/receipts.jsonl#L13)
- h-017 (historical): quality [receipt](../../runs/holdout-m5/C2/receipts.jsonl#L17)
- h-018 (historical): quality [receipt](../../runs/holdout-m5/C2/receipts.jsonl#L18)
- h-019 (historical): quality [receipt](../../runs/holdout-m5/C2/receipts.jsonl#L19)
- h-020 (historical): quality [receipt](../../runs/holdout-m5/C2/receipts.jsonl#L20)
- h-021 (conflicting_sources): quality [receipt](../../runs/holdout-m5/C2/receipts.jsonl#L21)
- h-022 (conflicting_sources): quality [receipt](../../runs/holdout-m5/C2/receipts.jsonl#L22)
- h-023 (conflicting_sources): quality [receipt](../../runs/holdout-m5/C2/receipts.jsonl#L23)
- h-027 (verify_claim): quality [receipt](../../runs/holdout-m5/C2/receipts.jsonl#L27)
- h-028 (vague): quality [receipt](../../runs/holdout-m5/C2/receipts.jsonl#L28)
- h-029 (vague): quality [receipt](../../runs/holdout-m5/C2/receipts.jsonl#L29)
- h-033 (no_source): quality [receipt](../../runs/holdout-m5/C2/receipts.jsonl#L33)
- h-034 (multi_hub): quality [receipt](../../runs/holdout-m5/C2/receipts.jsonl#L34)
- h-035 (multi_hub): quality [receipt](../../runs/holdout-m5/C2/receipts.jsonl#L35)
- h-037 (multi_hub): mandatory_source [receipt](../../runs/holdout-m5/C2/receipts.jsonl#L37)

**C4**: 14 of 40 cases not safe-grounded-successful
- h-006 (named_service): quality [receipt](../../runs/holdout-m5/C4/receipts.jsonl#L6)
- h-007 (hub_specific_name): quality [receipt](../../runs/holdout-m5/C4/receipts.jsonl#L7)
- h-017 (historical): quality [receipt](../../runs/holdout-m5/C4/receipts.jsonl#L17)
- h-018 (historical): quality [receipt](../../runs/holdout-m5/C4/receipts.jsonl#L18)
- h-019 (historical): quality [receipt](../../runs/holdout-m5/C4/receipts.jsonl#L19)
- h-020 (historical): quality [receipt](../../runs/holdout-m5/C4/receipts.jsonl#L20)
- h-022 (conflicting_sources): quality [receipt](../../runs/holdout-m5/C4/receipts.jsonl#L22)
- h-023 (conflicting_sources): quality [receipt](../../runs/holdout-m5/C4/receipts.jsonl#L23)
- h-028 (vague): quality [receipt](../../runs/holdout-m5/C4/receipts.jsonl#L28)
- h-029 (vague): quality [receipt](../../runs/holdout-m5/C4/receipts.jsonl#L29)
- h-033 (no_source): quality [receipt](../../runs/holdout-m5/C4/receipts.jsonl#L33)
- h-037 (multi_hub): mandatory_source [receipt](../../runs/holdout-m5/C4/receipts.jsonl#L37)
- h-038 (restricted_content): quality [receipt](../../runs/holdout-m5/C4/receipts.jsonl#L38)
- h-040 (restricted_content): quality [receipt](../../runs/holdout-m5/C4/receipts.jsonl#L40)

**C4a-equivalent**: 14 of 40 cases not safe-grounded-successful
- h-006 (named_service): quality [receipt](../../runs/holdout-m5/C4a-equivalent/receipts.jsonl#L6)
- h-007 (hub_specific_name): quality [receipt](../../runs/holdout-m5/C4a-equivalent/receipts.jsonl#L7)
- h-017 (historical): quality [receipt](../../runs/holdout-m5/C4a-equivalent/receipts.jsonl#L17)
- h-018 (historical): quality [receipt](../../runs/holdout-m5/C4a-equivalent/receipts.jsonl#L18)
- h-019 (historical): quality [receipt](../../runs/holdout-m5/C4a-equivalent/receipts.jsonl#L19)
- h-020 (historical): quality [receipt](../../runs/holdout-m5/C4a-equivalent/receipts.jsonl#L20)
- h-022 (conflicting_sources): quality [receipt](../../runs/holdout-m5/C4a-equivalent/receipts.jsonl#L22)
- h-023 (conflicting_sources): quality [receipt](../../runs/holdout-m5/C4a-equivalent/receipts.jsonl#L23)
- h-028 (vague): quality [receipt](../../runs/holdout-m5/C4a-equivalent/receipts.jsonl#L28)
- h-029 (vague): quality [receipt](../../runs/holdout-m5/C4a-equivalent/receipts.jsonl#L29)
- h-033 (no_source): quality [receipt](../../runs/holdout-m5/C4a-equivalent/receipts.jsonl#L33)
- h-037 (multi_hub): mandatory_source [receipt](../../runs/holdout-m5/C4a-equivalent/receipts.jsonl#L37)
- h-038 (restricted_content): quality [receipt](../../runs/holdout-m5/C4a-equivalent/receipts.jsonl#L38)
- h-040 (restricted_content): quality [receipt](../../runs/holdout-m5/C4a-equivalent/receipts.jsonl#L40)

> SYNTHETIC, NOT PRODUCTION EVIDENCE. 60 dev + 40 holdout questions support directional results and debugging only, not population estimates.
