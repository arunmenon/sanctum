# Sanctum Lab M3 (data half)

Owner: backend-engineer (M3 data). Status: review.

## Scope
1. World: group payments-code on the four payments code repos (codehub places; payments-eng kept),
   principal kestrel-codeonly with groups [payments-code] only. Reads payments code, not
   payments skills/docs/memory. Update configs/m0_principal_aliases.yaml p-code-only.
2. 60 dev specs in questions/specs/dev/ per plan 8.2:
   named_service 10, hub_specific_name 8, same_name_two_meanings 6, historical 6,
   conflicting_sources 6, verify_claim 4, vague 4, no_source 6, multi_hub 6, restricted_content 4.
   Paraphrases, typos, hub-native names, mixed principals (kestrel-codeonly for
   required-source-denied). Gold to gold/dev/ via tools/derive_gold.py.
3. Scenario specs in questions/specs/scenarios/ (gold/scenarios/) for EX-01..04, 06..10, FX-24;
   mapping docs/scenario-cases.yaml.
4. Tests (tests/test_dev_questions.py): size and family counts, gold validates, opaque
   request_ids, family x principal-type coverage, scenario mapping resolves.

## Out of bounds
src/sanctum_ref, holdout/, questions/specs/holdout.

## Steps
- [x] world + alias change, rebuild, lint, run suite, record changed expectations
- [x] dev specs + derive
- [x] scenario specs + mapping + derive
- [x] tests, full suite, lint, commit

## Changed test expectations
- tests/test_world_schema.py: principal count bound 3..4 -> 3..5 (kestrel-codeonly).
- No other expectation changed; gold/m1 and gold/m0 unchanged.

## Result
60 dev + 11 scenario cases derived; 282 passed; lint 0 findings.
