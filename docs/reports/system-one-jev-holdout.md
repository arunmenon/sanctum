# Sanctum Lab report

> SYNTHETIC, NOT PRODUCTION EVIDENCE. 60 dev + 40 holdout questions support directional results and debugging only, not population estimates.

Ranker: `lexical_smoke` in every arm; the B* cross-encoder profile is deferred (discrepancy register 18), so these are lexical-ranker results.

## Runs and provenance

| config | run | world sha256 | seed | memory release | failure profile | git commit | dirty | integrity |
|---|---|---|---|---|---|---|---|---|
| C2 | `C2` | `452b57d9686b` | 20260930 | none | none | `ed73e77f1e` | True | True |
| C3 | `C3-jev` | `452b57d9686b` | 20260930 | none | none | `ed73e77f1e` | False | True |
| C4 | `C4` | `452b57d9686b` | 20260930 | r1 | none | `ed73e77f1e` | True | True |
| C5 | `C5-jev` | `452b57d9686b` | 20260930 | r1 | none | `ed73e77f1e` | True | True |

## Config matrix

| config | routing | assembly | resolution | translation | procedures | memory_store | decision_provider | provider |
|---|---|---|---|---|---|---|---|---|
| C2 | rules | common | none | False | registry_only | none | none | none |
| C3 | rules | common | none | False | registry_only | none | named | standin |
| C4 | rules | common | denotes | True | memory | relations | none | none |
| C5 | rules | common | denotes | True | memory | relations | named | standin |

## Gates (pass/fail, never averaged)

| config | leakage | scope | wrong_entity | budget |
|---|---|---|---|---|
| C2 | PASS | PASS | PASS | PASS |
| C3 | PASS | PASS | PASS | PASS |
| C4 | PASS | PASS | PASS | PASS |
| C5 | PASS | PASS | PASS | PASS |

## Per-family results

| family | n | C2 success | C2 recall | C3 success | C3 recall | C4 success | C4 recall | C5 success | C5 recall |
|---|---|---|---|---|---|---|---|---|---|
| conflicting_sources | 4 | 0.25 | 0.88 | 0.25 | 0.88 | 0.50 | 0.88 | 0.50 | 0.88 |
| historical | 4 | 0.00 | 0.75 | 0.00 | 0.75 | 0.00 | 0.75 | 0.00 | 0.75 |
| hub_specific_name | 6 | 0.33 | 1.00 | 0.33 | 0.83 | 0.83 | 1.00 | 0.83 | 0.83 |
| multi_hub | 4 | 0.25 | 1.00 | 0.25 | 1.00 | 0.75 | 1.00 | 0.75 | 1.00 |
| named_service | 6 | 0.83 | 0.80 | 0.83 | 0.80 | 0.83 | 1.00 | 0.83 | 1.00 |
| no_source | 3 | 0.67 | - | 1.00 | - | 0.67 | - | 1.00 | - |
| restricted_content | 3 | 1.00 | 1.00 | 1.00 | 1.00 | 0.33 | 0.00 | 0.33 | 0.00 |
| same_name_two_meanings | 4 | 0.75 | 0.75 | 0.75 | 0.75 | 1.00 | 1.00 | 1.00 | 1.00 |
| vague | 3 | 0.33 | 0.83 | 0.33 | 0.83 | 0.33 | 0.83 | 0.33 | 0.83 |
| verify_claim | 3 | 0.67 | 1.00 | 0.67 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| all | 40 | 0.50 | 0.88 | 0.53 | 0.85 | 0.65 | 0.91 | 0.68 | 0.88 |

## Paired comparisons (b minus a, 95% cluster bootstrap by family and entity)

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

### Q4_provider: C2 vs C3

| metric | scope | n | clusters | a | b | delta | interval | b better | a better |
|---|---|---|---|---|---|---|---|---|---|
| safe_grounded_success | pooled | 40 | 31 | 0.50 | 0.53 | 0.03 | [0.00, 0.07] | 1 | 0 |
| safe_grounded_success | conflicting_sources | 4 | 3 | 0.25 | 0.25 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | historical | 4 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | hub_specific_name | 6 | 4 | 0.33 | 0.33 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | multi_hub | 4 | 4 | 0.25 | 0.25 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | named_service | 6 | 5 | 0.83 | 0.83 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | no_source | 3 | 1 | 0.67 | 1.00 | 0.33 | [0.33, 0.33] | 1 | 0 |
| safe_grounded_success | restricted_content | 3 | 2 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | same_name_two_meanings | 4 | 2 | 0.75 | 0.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | vague | 3 | 3 | 0.33 | 0.33 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | verify_claim | 3 | 3 | 0.67 | 0.67 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | pooled | 34 | 28 | 0.88 | 0.85 | -0.03 | [-0.09, 0.00] | 0 | 1 |
| recall | conflicting_sources | 4 | 3 | 0.88 | 0.88 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | historical | 4 | 4 | 0.75 | 0.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | hub_specific_name | 6 | 4 | 1.00 | 0.83 | -0.17 | [-0.43, 0.00] | 0 | 1 |
| recall | multi_hub | 4 | 4 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | named_service | 5 | 4 | 0.80 | 0.80 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | restricted_content | 1 | 1 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | same_name_two_meanings | 4 | 2 | 0.75 | 0.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | vague | 3 | 3 | 0.83 | 0.83 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | verify_claim | 3 | 3 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | pooled | 40 | 31 | 2.75 | 2.38 | -0.38 | [-0.57, -0.19] | 0 | 12 |
| sources_attempted | conflicting_sources | 4 | 3 | 2.75 | 2.50 | -0.25 | [-0.50, 0.00] | 0 | 1 |
| sources_attempted | historical | 4 | 4 | 2.50 | 2.00 | -0.50 | [-1.00, 0.00] | 0 | 2 |
| sources_attempted | hub_specific_name | 6 | 4 | 2.83 | 2.17 | -0.67 | [-1.29, 0.00] | 0 | 3 |
| sources_attempted | multi_hub | 4 | 4 | 2.50 | 2.50 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | named_service | 6 | 5 | 2.83 | 2.83 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | no_source | 3 | 1 | 2.00 | 1.33 | -0.67 | [-0.67, -0.67] | 0 | 1 |
| sources_attempted | restricted_content | 3 | 2 | 3.00 | 2.33 | -0.67 | [-2.00, 0.00] | 0 | 1 |
| sources_attempted | same_name_two_meanings | 4 | 2 | 3.25 | 2.75 | -0.50 | [-0.50, -0.50] | 0 | 2 |
| sources_attempted | vague | 3 | 3 | 2.67 | 2.33 | -0.33 | [-1.00, 0.00] | 0 | 1 |
| sources_attempted | verify_claim | 3 | 3 | 3.00 | 2.67 | -0.33 | [-1.00, 0.00] | 0 | 1 |
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

### Q4_provider_memory: C4 vs C5

| metric | scope | n | clusters | a | b | delta | interval | b better | a better |
|---|---|---|---|---|---|---|---|---|---|
| safe_grounded_success | pooled | 40 | 31 | 0.65 | 0.68 | 0.03 | [0.00, 0.07] | 1 | 0 |
| safe_grounded_success | conflicting_sources | 4 | 3 | 0.50 | 0.50 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | historical | 4 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | hub_specific_name | 6 | 4 | 0.83 | 0.83 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | multi_hub | 4 | 4 | 0.75 | 0.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | named_service | 6 | 5 | 0.83 | 0.83 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | no_source | 3 | 1 | 0.67 | 1.00 | 0.33 | [0.33, 0.33] | 1 | 0 |
| safe_grounded_success | restricted_content | 3 | 2 | 0.33 | 0.33 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | same_name_two_meanings | 4 | 2 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | vague | 3 | 3 | 0.33 | 0.33 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | verify_claim | 3 | 3 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | pooled | 34 | 28 | 0.91 | 0.88 | -0.03 | [-0.09, 0.00] | 0 | 1 |
| recall | conflicting_sources | 4 | 3 | 0.88 | 0.88 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | historical | 4 | 4 | 0.75 | 0.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | hub_specific_name | 6 | 4 | 1.00 | 0.83 | -0.17 | [-0.43, 0.00] | 0 | 1 |
| recall | multi_hub | 4 | 4 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | named_service | 5 | 4 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | restricted_content | 1 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | same_name_two_meanings | 4 | 2 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | vague | 3 | 3 | 0.83 | 0.83 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | verify_claim | 3 | 3 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | pooled | 40 | 31 | 2.75 | 2.33 | -0.42 | [-0.64, -0.21] | 0 | 13 |
| sources_attempted | conflicting_sources | 4 | 3 | 2.75 | 2.50 | -0.25 | [-0.50, 0.00] | 0 | 1 |
| sources_attempted | historical | 4 | 4 | 2.50 | 1.75 | -0.75 | [-1.50, 0.00] | 0 | 2 |
| sources_attempted | hub_specific_name | 6 | 4 | 2.83 | 2.17 | -0.67 | [-1.29, 0.00] | 0 | 3 |
| sources_attempted | multi_hub | 4 | 4 | 2.50 | 2.50 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | named_service | 6 | 5 | 2.83 | 2.83 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | no_source | 3 | 1 | 2.00 | 1.00 | -1.00 | [-1.00, -1.00] | 0 | 2 |
| sources_attempted | restricted_content | 3 | 2 | 3.00 | 2.33 | -0.67 | [-2.00, 0.00] | 0 | 1 |
| sources_attempted | same_name_two_meanings | 4 | 2 | 3.25 | 2.75 | -0.50 | [-0.50, -0.50] | 0 | 2 |
| sources_attempted | vague | 3 | 3 | 2.67 | 2.33 | -0.33 | [-1.00, 0.00] | 0 | 1 |
| sources_attempted | verify_claim | 3 | 3 | 3.00 | 2.67 | -0.33 | [-1.00, 0.00] | 0 | 1 |
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

## System One model calls (reported, not gated)

Runner-side broker observations, separate from source calls. Latency includes broker, network, validation, batching and retries; from a laptop to a hosted endpoint it is not evidence about the fast path.

| config | provider | resolved model | profile | tool calls | outcomes | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|
| C3 | typesafe-jev | jev-1.13.0 | relaxed | 40 | ok 40 | 392.0 | 456.0 |
| C5 | typesafe-jev | jev-1.13.0 | relaxed | 40 | ok 40 | 363.0 | 433.0 |

## Failures

**C2**: 20 of 40 cases not safe-grounded-successful
- h-005 (named_service): quality [receipt](../../runs/holdout-m6-jev/C2/receipts.jsonl#L5)
- h-007 (hub_specific_name): quality [receipt](../../runs/holdout-m6-jev/C2/receipts.jsonl#L7)
- h-008 (hub_specific_name): quality [receipt](../../runs/holdout-m6-jev/C2/receipts.jsonl#L8)
- h-009 (hub_specific_name): quality [receipt](../../runs/holdout-m6-jev/C2/receipts.jsonl#L9)
- h-012 (hub_specific_name): quality [receipt](../../runs/holdout-m6-jev/C2/receipts.jsonl#L12)
- h-013 (same_name_two_meanings): quality [receipt](../../runs/holdout-m6-jev/C2/receipts.jsonl#L13)
- h-017 (historical): quality [receipt](../../runs/holdout-m6-jev/C2/receipts.jsonl#L17)
- h-018 (historical): quality [receipt](../../runs/holdout-m6-jev/C2/receipts.jsonl#L18)
- h-019 (historical): quality [receipt](../../runs/holdout-m6-jev/C2/receipts.jsonl#L19)
- h-020 (historical): quality [receipt](../../runs/holdout-m6-jev/C2/receipts.jsonl#L20)
- h-021 (conflicting_sources): quality [receipt](../../runs/holdout-m6-jev/C2/receipts.jsonl#L21)
- h-022 (conflicting_sources): quality [receipt](../../runs/holdout-m6-jev/C2/receipts.jsonl#L22)
- h-023 (conflicting_sources): quality [receipt](../../runs/holdout-m6-jev/C2/receipts.jsonl#L23)
- h-027 (verify_claim): quality [receipt](../../runs/holdout-m6-jev/C2/receipts.jsonl#L27)
- h-028 (vague): quality [receipt](../../runs/holdout-m6-jev/C2/receipts.jsonl#L28)
- h-029 (vague): quality [receipt](../../runs/holdout-m6-jev/C2/receipts.jsonl#L29)
- h-033 (no_source): quality [receipt](../../runs/holdout-m6-jev/C2/receipts.jsonl#L33)
- h-034 (multi_hub): quality [receipt](../../runs/holdout-m6-jev/C2/receipts.jsonl#L34)
- h-035 (multi_hub): quality [receipt](../../runs/holdout-m6-jev/C2/receipts.jsonl#L35)
- h-037 (multi_hub): mandatory_source [receipt](../../runs/holdout-m6-jev/C2/receipts.jsonl#L37)

**C3**: 19 of 40 cases not safe-grounded-successful
- h-005 (named_service): quality [receipt](../../runs/holdout-m6-jev/C3-jev/receipts.jsonl#L5)
- h-007 (hub_specific_name): quality [receipt](../../runs/holdout-m6-jev/C3-jev/receipts.jsonl#L7)
- h-008 (hub_specific_name): quality [receipt](../../runs/holdout-m6-jev/C3-jev/receipts.jsonl#L8)
- h-009 (hub_specific_name): quality [receipt](../../runs/holdout-m6-jev/C3-jev/receipts.jsonl#L9)
- h-012 (hub_specific_name): quality [receipt](../../runs/holdout-m6-jev/C3-jev/receipts.jsonl#L12)
- h-013 (same_name_two_meanings): quality [receipt](../../runs/holdout-m6-jev/C3-jev/receipts.jsonl#L13)
- h-017 (historical): quality [receipt](../../runs/holdout-m6-jev/C3-jev/receipts.jsonl#L17)
- h-018 (historical): quality [receipt](../../runs/holdout-m6-jev/C3-jev/receipts.jsonl#L18)
- h-019 (historical): quality [receipt](../../runs/holdout-m6-jev/C3-jev/receipts.jsonl#L19)
- h-020 (historical): quality [receipt](../../runs/holdout-m6-jev/C3-jev/receipts.jsonl#L20)
- h-021 (conflicting_sources): quality [receipt](../../runs/holdout-m6-jev/C3-jev/receipts.jsonl#L21)
- h-022 (conflicting_sources): quality [receipt](../../runs/holdout-m6-jev/C3-jev/receipts.jsonl#L22)
- h-023 (conflicting_sources): quality [receipt](../../runs/holdout-m6-jev/C3-jev/receipts.jsonl#L23)
- h-027 (verify_claim): quality [receipt](../../runs/holdout-m6-jev/C3-jev/receipts.jsonl#L27)
- h-028 (vague): quality [receipt](../../runs/holdout-m6-jev/C3-jev/receipts.jsonl#L28)
- h-029 (vague): quality [receipt](../../runs/holdout-m6-jev/C3-jev/receipts.jsonl#L29)
- h-034 (multi_hub): quality [receipt](../../runs/holdout-m6-jev/C3-jev/receipts.jsonl#L34)
- h-035 (multi_hub): quality [receipt](../../runs/holdout-m6-jev/C3-jev/receipts.jsonl#L35)
- h-037 (multi_hub): mandatory_source [receipt](../../runs/holdout-m6-jev/C3-jev/receipts.jsonl#L37)

**C4**: 14 of 40 cases not safe-grounded-successful
- h-006 (named_service): quality [receipt](../../runs/holdout-m6-jev/C4/receipts.jsonl#L6)
- h-007 (hub_specific_name): quality [receipt](../../runs/holdout-m6-jev/C4/receipts.jsonl#L7)
- h-017 (historical): quality [receipt](../../runs/holdout-m6-jev/C4/receipts.jsonl#L17)
- h-018 (historical): quality [receipt](../../runs/holdout-m6-jev/C4/receipts.jsonl#L18)
- h-019 (historical): quality [receipt](../../runs/holdout-m6-jev/C4/receipts.jsonl#L19)
- h-020 (historical): quality [receipt](../../runs/holdout-m6-jev/C4/receipts.jsonl#L20)
- h-022 (conflicting_sources): quality [receipt](../../runs/holdout-m6-jev/C4/receipts.jsonl#L22)
- h-023 (conflicting_sources): quality [receipt](../../runs/holdout-m6-jev/C4/receipts.jsonl#L23)
- h-028 (vague): quality [receipt](../../runs/holdout-m6-jev/C4/receipts.jsonl#L28)
- h-029 (vague): quality [receipt](../../runs/holdout-m6-jev/C4/receipts.jsonl#L29)
- h-033 (no_source): quality [receipt](../../runs/holdout-m6-jev/C4/receipts.jsonl#L33)
- h-037 (multi_hub): mandatory_source [receipt](../../runs/holdout-m6-jev/C4/receipts.jsonl#L37)
- h-038 (restricted_content): quality [receipt](../../runs/holdout-m6-jev/C4/receipts.jsonl#L38)
- h-040 (restricted_content): quality [receipt](../../runs/holdout-m6-jev/C4/receipts.jsonl#L40)

**C5**: 13 of 40 cases not safe-grounded-successful
- h-006 (named_service): quality [receipt](../../runs/holdout-m6-jev/C5-jev/receipts.jsonl#L6)
- h-007 (hub_specific_name): quality [receipt](../../runs/holdout-m6-jev/C5-jev/receipts.jsonl#L7)
- h-017 (historical): quality [receipt](../../runs/holdout-m6-jev/C5-jev/receipts.jsonl#L17)
- h-018 (historical): quality [receipt](../../runs/holdout-m6-jev/C5-jev/receipts.jsonl#L18)
- h-019 (historical): quality [receipt](../../runs/holdout-m6-jev/C5-jev/receipts.jsonl#L19)
- h-020 (historical): quality [receipt](../../runs/holdout-m6-jev/C5-jev/receipts.jsonl#L20)
- h-022 (conflicting_sources): quality [receipt](../../runs/holdout-m6-jev/C5-jev/receipts.jsonl#L22)
- h-023 (conflicting_sources): quality [receipt](../../runs/holdout-m6-jev/C5-jev/receipts.jsonl#L23)
- h-028 (vague): quality [receipt](../../runs/holdout-m6-jev/C5-jev/receipts.jsonl#L28)
- h-029 (vague): quality [receipt](../../runs/holdout-m6-jev/C5-jev/receipts.jsonl#L29)
- h-037 (multi_hub): mandatory_source [receipt](../../runs/holdout-m6-jev/C5-jev/receipts.jsonl#L37)
- h-038 (restricted_content): quality [receipt](../../runs/holdout-m6-jev/C5-jev/receipts.jsonl#L38)
- h-040 (restricted_content): quality [receipt](../../runs/holdout-m6-jev/C5-jev/receipts.jsonl#L40)

> SYNTHETIC, NOT PRODUCTION EVIDENCE. 60 dev + 40 holdout questions support directional results and debugging only, not population estimates.
