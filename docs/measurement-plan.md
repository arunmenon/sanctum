# Measurement plan (M0)

Status: **frozen structure, open values.** Items marked TBD are owner decisions (see `decisions.md`) and must be fixed before any acceptance run.

## Estimands

| Question | Comparison (configs/matrix.yaml) | Estimand |
|---|---|---|
| Q1 contract | all supported arms × scenario register | Pass/fail per scenario invariant |
| Q2 routing | `Q2_routing` (C1-fair vs C2) | Paired difference in safe grounded success and in sources attempted, at equal assembly and budgets |
| Q3a memory package | `Q3a_memory_package` (C2 vs C4) | Paired difference in safe grounded success; labeled a package effect |
| Q3a semantics | `Q3a_semantics_ablation` (C4a-equivalent vs C4a-label-only) | Paired difference in wrong-entity activation and ambiguity handling |
| Q3b storage | `Q3b_storage_equivalence` (C4 vs C4a-equivalent) | Plan equivalence (unit test), then cost/latency |
| Q4 provider | `Q4_provider`, `Q4_provider_memory` | Deferred (M6) |

## Primary and secondary outcomes

- **Primary:** safe grounded success (answerable cases); correct handling rate (clarify/separate cases).
- **Gates (pass/fail, never averaged):** confidentiality, wrong-entity activation, budget, receipt honesty, mandatory-source handling, token audience.
- **Secondary:** necessary-evidence recall, harmful and silent omission, conflict witnesses kept, false conflicts, false ambiguity, evidence precision, sources attempted, tokens, latency.

Definitions: lab-plan review §3.2 (normative), implemented in `src/sanctum_eval/metrics.py` at `METRICS_REVISION`.

## Open values (TBD)

| Value | Owner | Needed by |
|---|---|---|
| Non-inferiority margin for safe grounded success | Decision owner | M5 |
| Smallest useful gain | Decision owner | M5 |
| Response/candidate/call budgets for primary comparisons | Lab lead | M3 |
| Cost model for simulated backend calls | Lab lead | M3 |
| Decision goal: "safe to build real slice" vs "superiority" | Sponsor | Before M1 |

## Statistics

Resampling unit: independent scenario **bundle** (`bundle_id` in gold). Paired across arms; bundles never split. Development runs report paired counts and bootstrap intervals over bundles; acceptance runs happen only after freeze and are logged in the access ledger. An inconclusive result is an allowed outcome.

## Known M0 approximations

- `evidence_precision` uses gold-span coverage as the relevance proxy; a fixed relevance annotation policy replaces it at M1.
- Observed traces for M0 fixtures are hand-written; the runner produces them from M2.
