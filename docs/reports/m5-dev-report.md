# Sanctum Lab report

> SYNTHETIC, NOT PRODUCTION EVIDENCE. 60 dev + 40 holdout questions support directional results and debugging only, not population estimates.

Ranker: `lexical_smoke` in every arm; the B* cross-encoder profile is deferred (discrepancy register 18), so these are lexical-ranker results.

## Runs and provenance

| config | run | world sha256 | seed | memory release | failure profile | git commit | dirty | integrity |
|---|---|---|---|---|---|---|---|---|
| C1-naive | `C1-naive` | `452b57d9686b` | 20260930 | none | none | `1b720dfffe` | True | True |
| C1-fair | `C1-fair` | `452b57d9686b` | 20260930 | none | none | `1b720dfffe` | True | True |
| C2 | `C2` | `452b57d9686b` | 20260930 | none | none | `1b720dfffe` | True | True |
| C4 | `C4` | `452b57d9686b` | 20260930 | r1 | none | `1b720dfffe` | True | True |
| C4a-equivalent | `C4a-equivalent` | `452b57d9686b` | 20260930 | r1 | none | `1b720dfffe` | True | True |
| C4a-label-only | `C4a-label-only` | `452b57d9686b` | 20260930 | r1 | none | `1b720dfffe` | True | True |

## Config matrix

| config | routing | assembly | resolution | translation | procedures | memory_store | decision_provider |
|---|---|---|---|---|---|---|---|
| C1-naive | fanout_all | concatenate | none | False | False | none | none |
| C1-fair | fanout_all | common | none | False | False | none | none |
| C2 | rules | common | none | False | registry_only | none | none |
| C4 | rules | common | denotes | True | memory | relations | none |
| C4a-equivalent | rules | common | denotes | True | memory | tables | none |
| C4a-label-only | rules | common | label_only | True | memory | tables | none |

## Gates (pass/fail, never averaged)

| config | leakage | scope | wrong_entity |
|---|---|---|---|
| C1-naive | PASS | PASS | PASS |
| C1-fair | PASS | PASS | PASS |
| C2 | PASS | PASS | PASS |
| C4 | PASS | PASS | PASS |
| C4a-equivalent | PASS | PASS | PASS |
| C4a-label-only | PASS | PASS | **FAIL** |

## Per-family results

| family | n | C1-naive success | C1-naive recall | C1-fair success | C1-fair recall | C2 success | C2 recall | C4 success | C4 recall | C4a-equivalent success | C4a-equivalent recall | C4a-label-only success | C4a-label-only recall |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| conflicting_sources | 6 | 0.17 | 0.83 | 0.33 | 0.92 | 0.33 | 0.92 | 0.83 | 0.92 | 0.83 | 0.92 | 0.83 | 0.92 |
| historical | 6 | 0.00 | 0.67 | 0.00 | 0.67 | 0.00 | 0.67 | 0.17 | 0.58 | 0.17 | 0.58 | 0.17 | 0.58 |
| hub_specific_name | 8 | 0.75 | 0.96 | 0.75 | 0.96 | 0.38 | 0.83 | 0.75 | 0.96 | 0.75 | 0.96 | 0.75 | 0.96 |
| multi_hub | 6 | 0.33 | 1.00 | 0.83 | 1.00 | 0.83 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| named_service | 10 | 0.30 | 0.85 | 0.60 | 0.90 | 0.60 | 0.85 | 0.80 | 0.85 | 0.80 | 0.85 | 0.80 | 0.85 |
| no_source | 6 | 0.83 | - | 0.67 | - | 0.67 | - | 0.50 | - | 0.50 | - | 0.50 | - |
| restricted_content | 4 | 0.75 | 1.00 | 0.75 | 1.00 | 0.75 | 1.00 | 0.25 | 0.00 | 0.25 | 0.00 | 0.00 | 0.00 |
| same_name_two_meanings | 6 | 0.00 | 0.38 | 0.17 | 0.50 | 0.17 | 0.50 | 0.83 | 1.00 | 0.83 | 1.00 | 0.17 | 0.57 |
| vague | 4 | 0.00 | 0.40 | 0.00 | 0.71 | 0.00 | 0.58 | 0.00 | 0.46 | 0.00 | 0.46 | 0.00 | 0.46 |
| verify_claim | 4 | 0.00 | 1.00 | 0.75 | 1.00 | 0.50 | 1.00 | 0.75 | 1.00 | 0.75 | 1.00 | 0.75 | 1.00 |
| all | 60 | 0.33 | 0.78 | 0.50 | 0.84 | 0.43 | 0.80 | 0.63 | 0.84 | 0.63 | 0.84 | 0.55 | 0.79 |

## Paired comparisons (b minus a, 95% cluster bootstrap by family and entity)

### Q2_routing: C1-fair vs C2

| metric | scope | n | clusters | a | b | delta | interval | b better | a better |
|---|---|---|---|---|---|---|---|---|---|
| safe_grounded_success | pooled | 60 | 31 | 0.50 | 0.43 | -0.07 | [-0.16, 0.02] | 1 | 5 |
| safe_grounded_success | conflicting_sources | 6 | 2 | 0.33 | 0.33 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | historical | 6 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | hub_specific_name | 8 | 4 | 0.75 | 0.38 | -0.38 | [-0.80, 0.25] | 1 | 4 |
| safe_grounded_success | multi_hub | 6 | 4 | 0.83 | 0.83 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | named_service | 10 | 4 | 0.60 | 0.60 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | no_source | 6 | 1 | 0.67 | 0.67 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | restricted_content | 4 | 3 | 0.75 | 0.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | same_name_two_meanings | 6 | 2 | 0.17 | 0.17 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | vague | 4 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | verify_claim | 4 | 4 | 0.75 | 0.50 | -0.25 | [-0.75, 0.00] | 0 | 1 |
| recall | pooled | 51 | 28 | 0.84 | 0.80 | -0.04 | [-0.09, 0.00] | 0 | 3 |
| recall | conflicting_sources | 6 | 2 | 0.92 | 0.92 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | historical | 6 | 4 | 0.67 | 0.67 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | hub_specific_name | 8 | 4 | 0.96 | 0.83 | -0.12 | [-0.38, 0.00] | 0 | 1 |
| recall | multi_hub | 6 | 4 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | named_service | 10 | 4 | 0.90 | 0.85 | -0.05 | [-0.17, 0.00] | 0 | 1 |
| recall | restricted_content | 1 | 1 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | same_name_two_meanings | 6 | 2 | 0.50 | 0.50 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | vague | 4 | 3 | 0.71 | 0.58 | -0.12 | [-0.50, 0.00] | 0 | 1 |
| recall | verify_claim | 4 | 4 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | pooled | 60 | 31 | 3.55 | 2.57 | -0.98 | [-1.19, -0.78] | 0 | 47 |
| sources_attempted | conflicting_sources | 6 | 2 | 3.33 | 2.67 | -0.67 | [-1.00, -0.60] | 0 | 4 |
| sources_attempted | historical | 6 | 4 | 2.67 | 2.33 | -0.33 | [-1.00, 0.00] | 0 | 2 |
| sources_attempted | hub_specific_name | 8 | 4 | 3.62 | 2.25 | -1.38 | [-1.86, -0.67] | 0 | 7 |
| sources_attempted | multi_hub | 6 | 4 | 4.00 | 2.67 | -1.33 | [-1.60, -1.00] | 0 | 6 |
| sources_attempted | named_service | 10 | 4 | 3.40 | 2.30 | -1.10 | [-2.00, -0.62] | 0 | 7 |
| sources_attempted | no_source | 6 | 1 | 3.50 | 2.33 | -1.17 | [-1.17, -1.17] | 0 | 5 |
| sources_attempted | restricted_content | 4 | 3 | 4.00 | 3.00 | -1.00 | [-1.00, -1.00] | 0 | 4 |
| sources_attempted | same_name_two_meanings | 6 | 2 | 4.00 | 3.00 | -1.00 | [-1.00, -1.00] | 0 | 6 |
| sources_attempted | vague | 4 | 3 | 4.00 | 3.25 | -0.75 | [-1.00, 0.00] | 0 | 3 |
| sources_attempted | verify_claim | 4 | 4 | 3.25 | 2.50 | -0.75 | [-1.00, -0.25] | 0 | 3 |
| wrong_entity | pooled | 60 | 31 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | conflicting_sources | 6 | 2 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | historical | 6 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | hub_specific_name | 8 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | multi_hub | 6 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | named_service | 10 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | no_source | 6 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | restricted_content | 4 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | same_name_two_meanings | 6 | 2 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | vague | 4 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | verify_claim | 4 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |

### Q3a_memory_package: C2 vs C4

| metric | scope | n | clusters | a | b | delta | interval | b better | a better |
|---|---|---|---|---|---|---|---|---|---|
| safe_grounded_success | pooled | 60 | 31 | 0.43 | 0.63 | 0.20 | [0.04, 0.35] | 15 | 3 |
| safe_grounded_success | conflicting_sources | 6 | 2 | 0.33 | 0.83 | 0.50 | [0.40, 1.00] | 3 | 0 |
| safe_grounded_success | historical | 6 | 4 | 0.00 | 0.17 | 0.17 | [0.00, 0.30] | 1 | 0 |
| safe_grounded_success | hub_specific_name | 8 | 4 | 0.38 | 0.75 | 0.38 | [0.09, 0.80] | 3 | 0 |
| safe_grounded_success | multi_hub | 6 | 4 | 0.83 | 1.00 | 0.17 | [0.00, 0.30] | 1 | 0 |
| safe_grounded_success | named_service | 10 | 4 | 0.60 | 0.80 | 0.20 | [0.00, 0.43] | 2 | 0 |
| safe_grounded_success | no_source | 6 | 1 | 0.67 | 0.50 | -0.17 | [-0.17, -0.17] | 0 | 1 |
| safe_grounded_success | restricted_content | 4 | 3 | 0.75 | 0.25 | -0.50 | [-1.00, 0.00] | 0 | 2 |
| safe_grounded_success | same_name_two_meanings | 6 | 2 | 0.17 | 0.83 | 0.67 | [0.60, 1.00] | 4 | 0 |
| safe_grounded_success | vague | 4 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | verify_claim | 4 | 4 | 0.50 | 0.75 | 0.25 | [0.00, 0.75] | 1 | 0 |
| recall | pooled | 51 | 28 | 0.80 | 0.84 | 0.04 | [-0.08, 0.16] | 4 | 3 |
| recall | conflicting_sources | 6 | 2 | 0.92 | 0.92 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | historical | 6 | 4 | 0.67 | 0.58 | -0.08 | [-0.15, 0.00] | 0 | 1 |
| recall | hub_specific_name | 8 | 4 | 0.83 | 0.96 | 0.12 | [0.00, 0.38] | 1 | 0 |
| recall | multi_hub | 6 | 4 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | named_service | 10 | 4 | 0.85 | 0.85 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | restricted_content | 1 | 1 | 1.00 | 0.00 | -1.00 | [-1.00, -1.00] | 0 | 1 |
| recall | same_name_two_meanings | 6 | 2 | 0.50 | 1.00 | 0.50 | [0.00, 0.60] | 3 | 0 |
| recall | vague | 4 | 3 | 0.58 | 0.46 | -0.12 | [-0.25, 0.00] | 0 | 1 |
| recall | verify_claim | 4 | 4 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | pooled | 60 | 31 | 2.57 | 2.57 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | conflicting_sources | 6 | 2 | 2.67 | 2.67 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | historical | 6 | 4 | 2.33 | 2.33 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | hub_specific_name | 8 | 4 | 2.25 | 2.25 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | multi_hub | 6 | 4 | 2.67 | 2.67 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | named_service | 10 | 4 | 2.30 | 2.30 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | no_source | 6 | 1 | 2.33 | 2.33 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | restricted_content | 4 | 3 | 3.00 | 3.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | same_name_two_meanings | 6 | 2 | 3.00 | 3.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | vague | 4 | 3 | 3.25 | 3.25 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | verify_claim | 4 | 4 | 2.50 | 2.50 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | pooled | 60 | 31 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | conflicting_sources | 6 | 2 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | historical | 6 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | hub_specific_name | 8 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | multi_hub | 6 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | named_service | 10 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | no_source | 6 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | restricted_content | 4 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | same_name_two_meanings | 6 | 2 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | vague | 4 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | verify_claim | 4 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |

### Q3a_semantics_ablation: C4a-equivalent vs C4a-label-only

| metric | scope | n | clusters | a | b | delta | interval | b better | a better |
|---|---|---|---|---|---|---|---|---|---|
| safe_grounded_success | pooled | 60 | 31 | 0.63 | 0.55 | -0.08 | [-0.20, 0.00] | 0 | 5 |
| safe_grounded_success | conflicting_sources | 6 | 2 | 0.83 | 0.83 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | historical | 6 | 4 | 0.17 | 0.17 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | hub_specific_name | 8 | 4 | 0.75 | 0.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | multi_hub | 6 | 4 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | named_service | 10 | 4 | 0.80 | 0.80 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | no_source | 6 | 1 | 0.50 | 0.50 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | restricted_content | 4 | 3 | 0.25 | 0.00 | -0.25 | [-1.00, 0.00] | 0 | 1 |
| safe_grounded_success | same_name_two_meanings | 6 | 2 | 0.83 | 0.17 | -0.67 | [-1.00, -0.60] | 0 | 4 |
| safe_grounded_success | vague | 4 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | verify_claim | 4 | 4 | 0.75 | 0.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | pooled | 51 | 28 | 0.84 | 0.79 | -0.05 | [-0.13, 0.00] | 0 | 5 |
| recall | conflicting_sources | 6 | 2 | 0.92 | 0.92 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | historical | 6 | 4 | 0.58 | 0.58 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | hub_specific_name | 8 | 4 | 0.96 | 0.96 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | multi_hub | 6 | 4 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | named_service | 10 | 4 | 0.85 | 0.85 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | restricted_content | 1 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | same_name_two_meanings | 6 | 2 | 1.00 | 0.57 | -0.43 | [-0.50, -0.42] | 0 | 5 |
| recall | vague | 4 | 3 | 0.46 | 0.46 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | verify_claim | 4 | 4 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | pooled | 60 | 31 | 2.57 | 2.55 | -0.02 | [-0.06, 0.00] | 0 | 1 |
| sources_attempted | conflicting_sources | 6 | 2 | 2.67 | 2.67 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | historical | 6 | 4 | 2.33 | 2.33 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | hub_specific_name | 8 | 4 | 2.25 | 2.25 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | multi_hub | 6 | 4 | 2.67 | 2.67 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | named_service | 10 | 4 | 2.30 | 2.30 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | no_source | 6 | 1 | 2.33 | 2.33 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | restricted_content | 4 | 3 | 3.00 | 3.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | same_name_two_meanings | 6 | 2 | 3.00 | 2.83 | -0.17 | [-1.00, 0.00] | 0 | 1 |
| sources_attempted | vague | 4 | 3 | 3.25 | 3.25 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | verify_claim | 4 | 4 | 2.50 | 2.50 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | pooled | 60 | 31 | 0.00 | 0.02 | 0.02 | [0.00, 0.06] | 1 | 0 |
| wrong_entity | conflicting_sources | 6 | 2 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | historical | 6 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | hub_specific_name | 8 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | multi_hub | 6 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | named_service | 10 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | no_source | 6 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | restricted_content | 4 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | same_name_two_meanings | 6 | 2 | 0.00 | 0.17 | 0.17 | [0.00, 1.00] | 1 | 0 |
| wrong_entity | vague | 4 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | verify_claim | 4 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |

### Q3b_storage_equivalence: C4 vs C4a-equivalent

| metric | scope | n | clusters | a | b | delta | interval | b better | a better |
|---|---|---|---|---|---|---|---|---|---|
| safe_grounded_success | pooled | 60 | 31 | 0.63 | 0.63 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | conflicting_sources | 6 | 2 | 0.83 | 0.83 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | historical | 6 | 4 | 0.17 | 0.17 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | hub_specific_name | 8 | 4 | 0.75 | 0.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | multi_hub | 6 | 4 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | named_service | 10 | 4 | 0.80 | 0.80 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | no_source | 6 | 1 | 0.50 | 0.50 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | restricted_content | 4 | 3 | 0.25 | 0.25 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | same_name_two_meanings | 6 | 2 | 0.83 | 0.83 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | vague | 4 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | verify_claim | 4 | 4 | 0.75 | 0.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | pooled | 51 | 28 | 0.84 | 0.84 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | conflicting_sources | 6 | 2 | 0.92 | 0.92 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | historical | 6 | 4 | 0.58 | 0.58 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | hub_specific_name | 8 | 4 | 0.96 | 0.96 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | multi_hub | 6 | 4 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | named_service | 10 | 4 | 0.85 | 0.85 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | restricted_content | 1 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | same_name_two_meanings | 6 | 2 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | vague | 4 | 3 | 0.46 | 0.46 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | verify_claim | 4 | 4 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | pooled | 60 | 31 | 2.57 | 2.57 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | conflicting_sources | 6 | 2 | 2.67 | 2.67 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | historical | 6 | 4 | 2.33 | 2.33 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | hub_specific_name | 8 | 4 | 2.25 | 2.25 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | multi_hub | 6 | 4 | 2.67 | 2.67 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | named_service | 10 | 4 | 2.30 | 2.30 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | no_source | 6 | 1 | 2.33 | 2.33 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | restricted_content | 4 | 3 | 3.00 | 3.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | same_name_two_meanings | 6 | 2 | 3.00 | 3.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | vague | 4 | 3 | 3.25 | 3.25 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | verify_claim | 4 | 4 | 2.50 | 2.50 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | pooled | 60 | 31 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | conflicting_sources | 6 | 2 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | historical | 6 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | hub_specific_name | 8 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | multi_hub | 6 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | named_service | 10 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | no_source | 6 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | restricted_content | 4 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | same_name_two_meanings | 6 | 2 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | vague | 4 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | verify_claim | 4 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |

### descriptive_only: C1-naive vs C1-fair

| metric | scope | n | clusters | a | b | delta | interval | b better | a better |
|---|---|---|---|---|---|---|---|---|---|
| safe_grounded_success | pooled | 60 | 31 | 0.33 | 0.50 | 0.17 | [0.07, 0.28] | 11 | 1 |
| safe_grounded_success | conflicting_sources | 6 | 2 | 0.17 | 0.33 | 0.17 | [0.00, 0.20] | 1 | 0 |
| safe_grounded_success | historical | 6 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | hub_specific_name | 8 | 4 | 0.75 | 0.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | multi_hub | 6 | 4 | 0.33 | 0.83 | 0.50 | [0.25, 1.00] | 3 | 0 |
| safe_grounded_success | named_service | 10 | 4 | 0.30 | 0.60 | 0.30 | [0.11, 0.60] | 3 | 0 |
| safe_grounded_success | no_source | 6 | 1 | 0.83 | 0.67 | -0.17 | [-0.17, -0.17] | 0 | 1 |
| safe_grounded_success | restricted_content | 4 | 3 | 0.75 | 0.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | same_name_two_meanings | 6 | 2 | 0.00 | 0.17 | 0.17 | [0.00, 0.20] | 1 | 0 |
| safe_grounded_success | vague | 4 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | verify_claim | 4 | 4 | 0.00 | 0.75 | 0.75 | [0.25, 1.00] | 3 | 0 |
| recall | pooled | 51 | 28 | 0.78 | 0.84 | 0.06 | [0.02, 0.11] | 7 | 0 |
| recall | conflicting_sources | 6 | 2 | 0.83 | 0.92 | 0.08 | [0.00, 0.50] | 1 | 0 |
| recall | historical | 6 | 4 | 0.67 | 0.67 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | hub_specific_name | 8 | 4 | 0.96 | 0.96 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | multi_hub | 6 | 4 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | named_service | 10 | 4 | 0.85 | 0.90 | 0.05 | [0.00, 0.17] | 1 | 0 |
| recall | restricted_content | 1 | 1 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | same_name_two_meanings | 6 | 2 | 0.38 | 0.50 | 0.12 | [0.05, 0.50] | 2 | 0 |
| recall | vague | 4 | 3 | 0.40 | 0.71 | 0.31 | [0.12, 0.50] | 3 | 0 |
| recall | verify_claim | 4 | 4 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | pooled | 60 | 31 | 3.55 | 3.55 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | conflicting_sources | 6 | 2 | 3.33 | 3.33 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | historical | 6 | 4 | 2.67 | 2.67 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | hub_specific_name | 8 | 4 | 3.62 | 3.62 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | multi_hub | 6 | 4 | 4.00 | 4.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | named_service | 10 | 4 | 3.40 | 3.40 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | no_source | 6 | 1 | 3.50 | 3.50 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | restricted_content | 4 | 3 | 4.00 | 4.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | same_name_two_meanings | 6 | 2 | 4.00 | 4.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | vague | 4 | 3 | 4.00 | 4.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | verify_claim | 4 | 4 | 3.25 | 3.25 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | pooled | 60 | 31 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | conflicting_sources | 6 | 2 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | historical | 6 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | hub_specific_name | 8 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | multi_hub | 6 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | named_service | 10 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | no_source | 6 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | restricted_content | 4 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | same_name_two_meanings | 6 | 2 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | vague | 4 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | verify_claim | 4 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |

## Failures

**C1-naive**: 40 of 60 cases not safe-grounded-successful
- dev-002 (named_service): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L2)
- dev-004 (named_service): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L4)
- dev-006 (named_service): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L6)
- dev-007 (named_service): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L7)
- dev-008 (named_service): mandatory_source [receipt](../../runs/m5/C1-naive/receipts.jsonl#L8)
- dev-009 (named_service): mandatory_source [receipt](../../runs/m5/C1-naive/receipts.jsonl#L9)
- dev-010 (named_service): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L10)
- dev-011 (hub_specific_name): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L11)
- dev-017 (hub_specific_name): mandatory_source [receipt](../../runs/m5/C1-naive/receipts.jsonl#L17)
- dev-019 (same_name_two_meanings): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L19)
- dev-020 (same_name_two_meanings): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L20)
- dev-021 (same_name_two_meanings): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L21)
- dev-022 (same_name_two_meanings): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L22)
- dev-023 (same_name_two_meanings): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L23)
- dev-024 (same_name_two_meanings): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L24)
- dev-025 (historical): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L25)
- dev-026 (historical): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L26)
- dev-027 (historical): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L27)
- dev-028 (historical): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L28)
- dev-029 (historical): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L29)
- dev-030 (historical): mandatory_source [receipt](../../runs/m5/C1-naive/receipts.jsonl#L30)
- dev-031 (conflicting_sources): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L31)
- dev-032 (conflicting_sources): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L32)
- dev-034 (conflicting_sources): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L34)
- dev-035 (conflicting_sources): mandatory_source [receipt](../../runs/m5/C1-naive/receipts.jsonl#L35)
- dev-036 (conflicting_sources): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L36)
- dev-037 (verify_claim): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L37)
- dev-038 (verify_claim): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L38)
- dev-039 (verify_claim): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L39)
- dev-040 (verify_claim): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L40)
- dev-041 (vague): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L41)
- dev-042 (vague): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L42)
- dev-043 (vague): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L43)
- dev-044 (vague): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L44)
- dev-050 (no_source): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L50)
- dev-051 (multi_hub): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L51)
- dev-052 (multi_hub): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L52)
- dev-054 (multi_hub): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L54)
- dev-056 (multi_hub): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L56)
- dev-060 (restricted_content): quality [receipt](../../runs/m5/C1-naive/receipts.jsonl#L60)

**C1-fair**: 30 of 60 cases not safe-grounded-successful
- dev-004 (named_service): quality [receipt](../../runs/m5/C1-fair/receipts.jsonl#L4)
- dev-008 (named_service): mandatory_source [receipt](../../runs/m5/C1-fair/receipts.jsonl#L8)
- dev-009 (named_service): mandatory_source [receipt](../../runs/m5/C1-fair/receipts.jsonl#L9)
- dev-010 (named_service): quality [receipt](../../runs/m5/C1-fair/receipts.jsonl#L10)
- dev-011 (hub_specific_name): quality [receipt](../../runs/m5/C1-fair/receipts.jsonl#L11)
- dev-017 (hub_specific_name): mandatory_source [receipt](../../runs/m5/C1-fair/receipts.jsonl#L17)
- dev-019 (same_name_two_meanings): quality [receipt](../../runs/m5/C1-fair/receipts.jsonl#L19)
- dev-020 (same_name_two_meanings): quality [receipt](../../runs/m5/C1-fair/receipts.jsonl#L20)
- dev-021 (same_name_two_meanings): quality [receipt](../../runs/m5/C1-fair/receipts.jsonl#L21)
- dev-023 (same_name_two_meanings): quality [receipt](../../runs/m5/C1-fair/receipts.jsonl#L23)
- dev-024 (same_name_two_meanings): quality [receipt](../../runs/m5/C1-fair/receipts.jsonl#L24)
- dev-025 (historical): quality [receipt](../../runs/m5/C1-fair/receipts.jsonl#L25)
- dev-026 (historical): quality [receipt](../../runs/m5/C1-fair/receipts.jsonl#L26)
- dev-027 (historical): quality [receipt](../../runs/m5/C1-fair/receipts.jsonl#L27)
- dev-028 (historical): quality [receipt](../../runs/m5/C1-fair/receipts.jsonl#L28)
- dev-029 (historical): quality [receipt](../../runs/m5/C1-fair/receipts.jsonl#L29)
- dev-030 (historical): mandatory_source [receipt](../../runs/m5/C1-fair/receipts.jsonl#L30)
- dev-032 (conflicting_sources): quality [receipt](../../runs/m5/C1-fair/receipts.jsonl#L32)
- dev-034 (conflicting_sources): quality [receipt](../../runs/m5/C1-fair/receipts.jsonl#L34)
- dev-035 (conflicting_sources): mandatory_source [receipt](../../runs/m5/C1-fair/receipts.jsonl#L35)
- dev-036 (conflicting_sources): quality [receipt](../../runs/m5/C1-fair/receipts.jsonl#L36)
- dev-040 (verify_claim): quality [receipt](../../runs/m5/C1-fair/receipts.jsonl#L40)
- dev-041 (vague): quality [receipt](../../runs/m5/C1-fair/receipts.jsonl#L41)
- dev-042 (vague): quality [receipt](../../runs/m5/C1-fair/receipts.jsonl#L42)
- dev-043 (vague): quality [receipt](../../runs/m5/C1-fair/receipts.jsonl#L43)
- dev-044 (vague): quality [receipt](../../runs/m5/C1-fair/receipts.jsonl#L44)
- dev-046 (no_source): quality [receipt](../../runs/m5/C1-fair/receipts.jsonl#L46)
- dev-050 (no_source): quality [receipt](../../runs/m5/C1-fair/receipts.jsonl#L50)
- dev-052 (multi_hub): quality [receipt](../../runs/m5/C1-fair/receipts.jsonl#L52)
- dev-060 (restricted_content): quality [receipt](../../runs/m5/C1-fair/receipts.jsonl#L60)

**C2**: 34 of 60 cases not safe-grounded-successful
- dev-004 (named_service): mandatory_source [receipt](../../runs/m5/C2/receipts.jsonl#L4)
- dev-008 (named_service): quality [receipt](../../runs/m5/C2/receipts.jsonl#L8)
- dev-009 (named_service): mandatory_source [receipt](../../runs/m5/C2/receipts.jsonl#L9)
- dev-010 (named_service): quality [receipt](../../runs/m5/C2/receipts.jsonl#L10)
- dev-012 (hub_specific_name): quality [receipt](../../runs/m5/C2/receipts.jsonl#L12)
- dev-013 (hub_specific_name): quality [receipt](../../runs/m5/C2/receipts.jsonl#L13)
- dev-014 (hub_specific_name): quality [receipt](../../runs/m5/C2/receipts.jsonl#L14)
- dev-016 (hub_specific_name): mandatory_source [receipt](../../runs/m5/C2/receipts.jsonl#L16)
- dev-017 (hub_specific_name): quality [receipt](../../runs/m5/C2/receipts.jsonl#L17)
- dev-019 (same_name_two_meanings): quality [receipt](../../runs/m5/C2/receipts.jsonl#L19)
- dev-020 (same_name_two_meanings): quality [receipt](../../runs/m5/C2/receipts.jsonl#L20)
- dev-021 (same_name_two_meanings): quality [receipt](../../runs/m5/C2/receipts.jsonl#L21)
- dev-023 (same_name_two_meanings): quality [receipt](../../runs/m5/C2/receipts.jsonl#L23)
- dev-024 (same_name_two_meanings): quality [receipt](../../runs/m5/C2/receipts.jsonl#L24)
- dev-025 (historical): quality [receipt](../../runs/m5/C2/receipts.jsonl#L25)
- dev-026 (historical): quality [receipt](../../runs/m5/C2/receipts.jsonl#L26)
- dev-027 (historical): quality [receipt](../../runs/m5/C2/receipts.jsonl#L27)
- dev-028 (historical): quality [receipt](../../runs/m5/C2/receipts.jsonl#L28)
- dev-029 (historical): quality [receipt](../../runs/m5/C2/receipts.jsonl#L29)
- dev-030 (historical): quality [receipt](../../runs/m5/C2/receipts.jsonl#L30)
- dev-032 (conflicting_sources): quality [receipt](../../runs/m5/C2/receipts.jsonl#L32)
- dev-034 (conflicting_sources): quality [receipt](../../runs/m5/C2/receipts.jsonl#L34)
- dev-035 (conflicting_sources): quality [receipt](../../runs/m5/C2/receipts.jsonl#L35)
- dev-036 (conflicting_sources): quality [receipt](../../runs/m5/C2/receipts.jsonl#L36)
- dev-039 (verify_claim): quality [receipt](../../runs/m5/C2/receipts.jsonl#L39)
- dev-040 (verify_claim): quality [receipt](../../runs/m5/C2/receipts.jsonl#L40)
- dev-041 (vague): quality [receipt](../../runs/m5/C2/receipts.jsonl#L41)
- dev-042 (vague): quality [receipt](../../runs/m5/C2/receipts.jsonl#L42)
- dev-043 (vague): quality [receipt](../../runs/m5/C2/receipts.jsonl#L43)
- dev-044 (vague): quality [receipt](../../runs/m5/C2/receipts.jsonl#L44)
- dev-046 (no_source): quality [receipt](../../runs/m5/C2/receipts.jsonl#L46)
- dev-050 (no_source): quality [receipt](../../runs/m5/C2/receipts.jsonl#L50)
- dev-052 (multi_hub): quality [receipt](../../runs/m5/C2/receipts.jsonl#L52)
- dev-060 (restricted_content): quality [receipt](../../runs/m5/C2/receipts.jsonl#L60)

**C4**: 22 of 60 cases not safe-grounded-successful
- dev-004 (named_service): mandatory_source [receipt](../../runs/m5/C4/receipts.jsonl#L4)
- dev-009 (named_service): mandatory_source [receipt](../../runs/m5/C4/receipts.jsonl#L9)
- dev-012 (hub_specific_name): quality [receipt](../../runs/m5/C4/receipts.jsonl#L12)
- dev-016 (hub_specific_name): mandatory_source [receipt](../../runs/m5/C4/receipts.jsonl#L16)
- dev-020 (same_name_two_meanings): quality [receipt](../../runs/m5/C4/receipts.jsonl#L20)
- dev-025 (historical): quality [receipt](../../runs/m5/C4/receipts.jsonl#L25)
- dev-026 (historical): quality [receipt](../../runs/m5/C4/receipts.jsonl#L26)
- dev-027 (historical): quality [receipt](../../runs/m5/C4/receipts.jsonl#L27)
- dev-028 (historical): quality [receipt](../../runs/m5/C4/receipts.jsonl#L28)
- dev-029 (historical): quality [receipt](../../runs/m5/C4/receipts.jsonl#L29)
- dev-036 (conflicting_sources): quality [receipt](../../runs/m5/C4/receipts.jsonl#L36)
- dev-040 (verify_claim): quality [receipt](../../runs/m5/C4/receipts.jsonl#L40)
- dev-041 (vague): quality [receipt](../../runs/m5/C4/receipts.jsonl#L41)
- dev-042 (vague): quality [receipt](../../runs/m5/C4/receipts.jsonl#L42)
- dev-043 (vague): quality [receipt](../../runs/m5/C4/receipts.jsonl#L43)
- dev-044 (vague): quality [receipt](../../runs/m5/C4/receipts.jsonl#L44)
- dev-045 (no_source): quality [receipt](../../runs/m5/C4/receipts.jsonl#L45)
- dev-046 (no_source): quality [receipt](../../runs/m5/C4/receipts.jsonl#L46)
- dev-050 (no_source): quality [receipt](../../runs/m5/C4/receipts.jsonl#L50)
- dev-057 (restricted_content): quality [receipt](../../runs/m5/C4/receipts.jsonl#L57)
- dev-058 (restricted_content): quality [receipt](../../runs/m5/C4/receipts.jsonl#L58)
- dev-060 (restricted_content): quality [receipt](../../runs/m5/C4/receipts.jsonl#L60)

**C4a-equivalent**: 22 of 60 cases not safe-grounded-successful
- dev-004 (named_service): mandatory_source [receipt](../../runs/m5/C4a-equivalent/receipts.jsonl#L4)
- dev-009 (named_service): mandatory_source [receipt](../../runs/m5/C4a-equivalent/receipts.jsonl#L9)
- dev-012 (hub_specific_name): quality [receipt](../../runs/m5/C4a-equivalent/receipts.jsonl#L12)
- dev-016 (hub_specific_name): mandatory_source [receipt](../../runs/m5/C4a-equivalent/receipts.jsonl#L16)
- dev-020 (same_name_two_meanings): quality [receipt](../../runs/m5/C4a-equivalent/receipts.jsonl#L20)
- dev-025 (historical): quality [receipt](../../runs/m5/C4a-equivalent/receipts.jsonl#L25)
- dev-026 (historical): quality [receipt](../../runs/m5/C4a-equivalent/receipts.jsonl#L26)
- dev-027 (historical): quality [receipt](../../runs/m5/C4a-equivalent/receipts.jsonl#L27)
- dev-028 (historical): quality [receipt](../../runs/m5/C4a-equivalent/receipts.jsonl#L28)
- dev-029 (historical): quality [receipt](../../runs/m5/C4a-equivalent/receipts.jsonl#L29)
- dev-036 (conflicting_sources): quality [receipt](../../runs/m5/C4a-equivalent/receipts.jsonl#L36)
- dev-040 (verify_claim): quality [receipt](../../runs/m5/C4a-equivalent/receipts.jsonl#L40)
- dev-041 (vague): quality [receipt](../../runs/m5/C4a-equivalent/receipts.jsonl#L41)
- dev-042 (vague): quality [receipt](../../runs/m5/C4a-equivalent/receipts.jsonl#L42)
- dev-043 (vague): quality [receipt](../../runs/m5/C4a-equivalent/receipts.jsonl#L43)
- dev-044 (vague): quality [receipt](../../runs/m5/C4a-equivalent/receipts.jsonl#L44)
- dev-045 (no_source): quality [receipt](../../runs/m5/C4a-equivalent/receipts.jsonl#L45)
- dev-046 (no_source): quality [receipt](../../runs/m5/C4a-equivalent/receipts.jsonl#L46)
- dev-050 (no_source): quality [receipt](../../runs/m5/C4a-equivalent/receipts.jsonl#L50)
- dev-057 (restricted_content): quality [receipt](../../runs/m5/C4a-equivalent/receipts.jsonl#L57)
- dev-058 (restricted_content): quality [receipt](../../runs/m5/C4a-equivalent/receipts.jsonl#L58)
- dev-060 (restricted_content): quality [receipt](../../runs/m5/C4a-equivalent/receipts.jsonl#L60)

**C4a-label-only**: 27 of 60 cases not safe-grounded-successful
- dev-004 (named_service): mandatory_source [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L4)
- dev-009 (named_service): mandatory_source [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L9)
- dev-012 (hub_specific_name): quality [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L12)
- dev-016 (hub_specific_name): mandatory_source [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L16)
- dev-019 (same_name_two_meanings): quality [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L19)
- dev-020 (same_name_two_meanings): quality [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L20)
- dev-021 (same_name_two_meanings): quality [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L21)
- dev-023 (same_name_two_meanings): wrong_entity_activation, mandatory_source [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L23)
- dev-024 (same_name_two_meanings): quality [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L24)
- dev-025 (historical): quality [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L25)
- dev-026 (historical): quality [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L26)
- dev-027 (historical): quality [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L27)
- dev-028 (historical): quality [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L28)
- dev-029 (historical): quality [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L29)
- dev-036 (conflicting_sources): quality [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L36)
- dev-040 (verify_claim): quality [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L40)
- dev-041 (vague): quality [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L41)
- dev-042 (vague): quality [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L42)
- dev-043 (vague): quality [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L43)
- dev-044 (vague): quality [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L44)
- dev-045 (no_source): quality [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L45)
- dev-046 (no_source): quality [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L46)
- dev-050 (no_source): quality [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L50)
- dev-057 (restricted_content): quality [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L57)
- dev-058 (restricted_content): quality [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L58)
- dev-059 (restricted_content): quality [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L59)
- dev-060 (restricted_content): quality [receipt](../../runs/m5/C4a-label-only/receipts.jsonl#L60)

> SYNTHETIC, NOT PRODUCTION EVIDENCE. 60 dev + 40 holdout questions support directional results and debugging only, not population estimates.
