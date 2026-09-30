# Sanctum Lab report

> SYNTHETIC, NOT PRODUCTION EVIDENCE. 60 dev + 40 holdout questions support directional results and debugging only, not population estimates.

Ranker: `lexical_smoke` in every arm; the B* cross-encoder profile is deferred (discrepancy register 18), so these are lexical-ranker results.

## Runs and provenance

| config | run | world sha256 | seed | memory release | failure profile | git commit | dirty | integrity |
|---|---|---|---|---|---|---|---|---|
| C2 | `C2` | `452b57d9686b` | 20260930 | none | none | `ed73e77f1e` | False | True |
| C3 | `C3-jev` | `452b57d9686b` | 20260930 | none | none | `ed73e77f1e` | False | True |
| C4 | `C4` | `452b57d9686b` | 20260930 | r1 | none | `ed73e77f1e` | False | True |
| C5 | `C5-jev` | `452b57d9686b` | 20260930 | r1 | none | `ed73e77f1e` | False | True |

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
| conflicting_sources | 2 | 0.00 | 0.75 | 0.00 | 0.75 | 0.50 | 0.75 | 0.50 | 0.75 |
| historical | 1 | 0.00 | 1.00 | 0.00 | 1.00 | 0.00 | 1.00 | 0.00 | 1.00 |
| hub_specific_name | 4 | 0.25 | 0.88 | 0.25 | 0.88 | 0.75 | 1.00 | 0.75 | 1.00 |
| multi_hub | 1 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| named_service | 8 | 0.62 | 1.00 | 0.62 | 1.00 | 0.75 | 1.00 | 0.75 | 1.00 |
| no_source | 3 | 1.00 | - | 1.00 | - | 0.33 | - | 0.33 | - |
| same_name_two_meanings | 1 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| all | 20 | 0.50 | 0.88 | 0.50 | 0.88 | 0.65 | 0.97 | 0.65 | 0.97 |

## Paired comparisons (b minus a, 95% cluster bootstrap by family and entity)

### Q3a_memory_package: C2 vs C4

| metric | scope | n | clusters | a | b | delta | interval | b better | a better |
|---|---|---|---|---|---|---|---|---|---|
| safe_grounded_success | pooled | 20 | 14 | 0.50 | 0.65 | 0.15 | [-0.10, 0.41] | 5 | 2 |
| safe_grounded_success | conflicting_sources | 2 | 2 | 0.00 | 0.50 | 0.50 | [0.00, 1.00] | 1 | 0 |
| safe_grounded_success | historical | 1 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | hub_specific_name | 4 | 4 | 0.25 | 0.75 | 0.50 | [0.00, 1.00] | 2 | 0 |
| safe_grounded_success | multi_hub | 1 | 1 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | named_service | 8 | 3 | 0.62 | 0.75 | 0.12 | [0.00, 0.33] | 1 | 0 |
| safe_grounded_success | no_source | 3 | 2 | 1.00 | 0.33 | -0.67 | [-1.00, -0.50] | 0 | 2 |
| safe_grounded_success | same_name_two_meanings | 1 | 1 | 0.00 | 1.00 | 1.00 | [1.00, 1.00] | 1 | 0 |
| recall | pooled | 17 | 12 | 0.88 | 0.97 | 0.09 | [0.00, 0.25] | 2 | 0 |
| recall | conflicting_sources | 2 | 2 | 0.75 | 0.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | historical | 1 | 1 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | hub_specific_name | 4 | 4 | 0.88 | 1.00 | 0.12 | [0.00, 0.38] | 1 | 0 |
| recall | multi_hub | 1 | 1 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | named_service | 8 | 3 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | same_name_two_meanings | 1 | 1 | 0.00 | 1.00 | 1.00 | [1.00, 1.00] | 1 | 0 |
| sources_attempted | pooled | 20 | 14 | 2.60 | 2.60 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | conflicting_sources | 2 | 2 | 3.00 | 3.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | historical | 1 | 1 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | hub_specific_name | 4 | 4 | 3.25 | 3.25 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | multi_hub | 1 | 1 | 3.00 | 3.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | named_service | 8 | 3 | 2.62 | 2.62 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | no_source | 3 | 2 | 1.67 | 1.67 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | same_name_two_meanings | 1 | 1 | 3.00 | 3.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | pooled | 20 | 14 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | conflicting_sources | 2 | 2 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | historical | 1 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | hub_specific_name | 4 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | multi_hub | 1 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | named_service | 8 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | no_source | 3 | 2 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | same_name_two_meanings | 1 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |

### Q4_provider: C2 vs C3

| metric | scope | n | clusters | a | b | delta | interval | b better | a better |
|---|---|---|---|---|---|---|---|---|---|
| safe_grounded_success | pooled | 20 | 14 | 0.50 | 0.50 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | conflicting_sources | 2 | 2 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | historical | 1 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | hub_specific_name | 4 | 4 | 0.25 | 0.25 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | multi_hub | 1 | 1 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | named_service | 8 | 3 | 0.62 | 0.62 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | no_source | 3 | 2 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | same_name_two_meanings | 1 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | pooled | 17 | 12 | 0.88 | 0.88 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | conflicting_sources | 2 | 2 | 0.75 | 0.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | historical | 1 | 1 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | hub_specific_name | 4 | 4 | 0.88 | 0.88 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | multi_hub | 1 | 1 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | named_service | 8 | 3 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | same_name_two_meanings | 1 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | pooled | 20 | 14 | 2.60 | 2.30 | -0.30 | [-0.67, -0.05] | 0 | 4 |
| sources_attempted | conflicting_sources | 2 | 2 | 3.00 | 3.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | historical | 1 | 1 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | hub_specific_name | 4 | 4 | 3.25 | 2.50 | -0.75 | [-1.50, 0.00] | 0 | 2 |
| sources_attempted | multi_hub | 1 | 1 | 3.00 | 1.00 | -2.00 | [-2.00, -2.00] | 0 | 1 |
| sources_attempted | named_service | 8 | 3 | 2.62 | 2.50 | -0.12 | [-0.33, 0.00] | 0 | 1 |
| sources_attempted | no_source | 3 | 2 | 1.67 | 1.67 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | same_name_two_meanings | 1 | 1 | 3.00 | 3.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | pooled | 20 | 14 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | conflicting_sources | 2 | 2 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | historical | 1 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | hub_specific_name | 4 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | multi_hub | 1 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | named_service | 8 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | no_source | 3 | 2 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | same_name_two_meanings | 1 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |

### Q4_provider_memory: C4 vs C5

| metric | scope | n | clusters | a | b | delta | interval | b better | a better |
|---|---|---|---|---|---|---|---|---|---|
| safe_grounded_success | pooled | 20 | 14 | 0.65 | 0.65 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | conflicting_sources | 2 | 2 | 0.50 | 0.50 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | historical | 1 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | hub_specific_name | 4 | 4 | 0.75 | 0.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | multi_hub | 1 | 1 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | named_service | 8 | 3 | 0.75 | 0.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | no_source | 3 | 2 | 0.33 | 0.33 | 0.00 | [0.00, 0.00] | 0 | 0 |
| safe_grounded_success | same_name_two_meanings | 1 | 1 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | pooled | 17 | 12 | 0.97 | 0.97 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | conflicting_sources | 2 | 2 | 0.75 | 0.75 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | historical | 1 | 1 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | hub_specific_name | 4 | 4 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | multi_hub | 1 | 1 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | named_service | 8 | 3 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| recall | same_name_two_meanings | 1 | 1 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | pooled | 20 | 14 | 2.60 | 2.25 | -0.35 | [-0.72, -0.10] | 0 | 5 |
| sources_attempted | conflicting_sources | 2 | 2 | 3.00 | 3.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | historical | 1 | 1 | 1.00 | 1.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | hub_specific_name | 4 | 4 | 3.25 | 2.25 | -1.00 | [-1.75, -0.25] | 0 | 3 |
| sources_attempted | multi_hub | 1 | 1 | 3.00 | 1.00 | -2.00 | [-2.00, -2.00] | 0 | 1 |
| sources_attempted | named_service | 8 | 3 | 2.62 | 2.50 | -0.12 | [-0.33, 0.00] | 0 | 1 |
| sources_attempted | no_source | 3 | 2 | 1.67 | 1.67 | 0.00 | [0.00, 0.00] | 0 | 0 |
| sources_attempted | same_name_two_meanings | 1 | 1 | 3.00 | 3.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | pooled | 20 | 14 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | conflicting_sources | 2 | 2 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | historical | 1 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | hub_specific_name | 4 | 4 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | multi_hub | 1 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | named_service | 8 | 3 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | no_source | 3 | 2 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |
| wrong_entity | same_name_two_meanings | 1 | 1 | 0.00 | 0.00 | 0.00 | [0.00, 0.00] | 0 | 0 |

## System One model calls (reported, not gated)

Runner-side broker observations, separate from source calls. Latency includes broker, network, validation, batching and retries; from a laptop to a hosted endpoint it is not evidence about the fast path.

| config | provider | resolved model | profile | tool calls | outcomes | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|
| C3 | typesafe-jev | jev-1.13.0 | relaxed | 20 | ok 20 | 364.0 | 427.0 |
| C5 | typesafe-jev | jev-1.13.0 | relaxed | 20 | ok 20 | 358.0 | 471.0 |

## Failures

**C2**: 10 of 20 cases not safe-grounded-successful
- a-002 (named_service): quality [receipt](../../runs/acceptance/C2/receipts.jsonl#L2)
- a-003 (named_service): quality [receipt](../../runs/acceptance/C2/receipts.jsonl#L3)
- a-004 (named_service): quality [receipt](../../runs/acceptance/C2/receipts.jsonl#L4)
- a-010 (hub_specific_name): quality [receipt](../../runs/acceptance/C2/receipts.jsonl#L10)
- a-011 (same_name_two_meanings): quality [receipt](../../runs/acceptance/C2/receipts.jsonl#L11)
- a-012 (hub_specific_name): quality [receipt](../../runs/acceptance/C2/receipts.jsonl#L12)
- a-013 (hub_specific_name): quality [receipt](../../runs/acceptance/C2/receipts.jsonl#L13)
- a-018 (historical): quality [receipt](../../runs/acceptance/C2/receipts.jsonl#L18)
- a-019 (conflicting_sources): quality [receipt](../../runs/acceptance/C2/receipts.jsonl#L19)
- a-020 (conflicting_sources): quality [receipt](../../runs/acceptance/C2/receipts.jsonl#L20)

**C3**: 10 of 20 cases not safe-grounded-successful
- a-002 (named_service): quality [receipt](../../runs/acceptance/C3-jev/receipts.jsonl#L2)
- a-003 (named_service): quality [receipt](../../runs/acceptance/C3-jev/receipts.jsonl#L3)
- a-004 (named_service): quality [receipt](../../runs/acceptance/C3-jev/receipts.jsonl#L4)
- a-010 (hub_specific_name): quality [receipt](../../runs/acceptance/C3-jev/receipts.jsonl#L10)
- a-011 (same_name_two_meanings): quality [receipt](../../runs/acceptance/C3-jev/receipts.jsonl#L11)
- a-012 (hub_specific_name): quality [receipt](../../runs/acceptance/C3-jev/receipts.jsonl#L12)
- a-013 (hub_specific_name): quality [receipt](../../runs/acceptance/C3-jev/receipts.jsonl#L13)
- a-018 (historical): quality [receipt](../../runs/acceptance/C3-jev/receipts.jsonl#L18)
- a-019 (conflicting_sources): quality [receipt](../../runs/acceptance/C3-jev/receipts.jsonl#L19)
- a-020 (conflicting_sources): quality [receipt](../../runs/acceptance/C3-jev/receipts.jsonl#L20)

**C4**: 7 of 20 cases not safe-grounded-successful
- a-002 (named_service): quality [receipt](../../runs/acceptance/C4/receipts.jsonl#L2)
- a-004 (named_service): quality [receipt](../../runs/acceptance/C4/receipts.jsonl#L4)
- a-012 (hub_specific_name): quality [receipt](../../runs/acceptance/C4/receipts.jsonl#L12)
- a-016 (no_source): quality [receipt](../../runs/acceptance/C4/receipts.jsonl#L16)
- a-017 (no_source): quality [receipt](../../runs/acceptance/C4/receipts.jsonl#L17)
- a-018 (historical): quality [receipt](../../runs/acceptance/C4/receipts.jsonl#L18)
- a-019 (conflicting_sources): quality [receipt](../../runs/acceptance/C4/receipts.jsonl#L19)

**C5**: 7 of 20 cases not safe-grounded-successful
- a-002 (named_service): quality [receipt](../../runs/acceptance/C5-jev/receipts.jsonl#L2)
- a-004 (named_service): quality [receipt](../../runs/acceptance/C5-jev/receipts.jsonl#L4)
- a-012 (hub_specific_name): mandatory_source [receipt](../../runs/acceptance/C5-jev/receipts.jsonl#L12)
- a-016 (no_source): quality [receipt](../../runs/acceptance/C5-jev/receipts.jsonl#L16)
- a-017 (no_source): quality [receipt](../../runs/acceptance/C5-jev/receipts.jsonl#L17)
- a-018 (historical): quality [receipt](../../runs/acceptance/C5-jev/receipts.jsonl#L18)
- a-019 (conflicting_sources): quality [receipt](../../runs/acceptance/C5-jev/receipts.jsonl#L19)

> SYNTHETIC, NOT PRODUCTION EVIDENCE. 60 dev + 40 holdout questions support directional results and debugging only, not population estimates.
