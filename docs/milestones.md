# Lab milestones (source of truth)

Supersedes the milestone numbering in `docs/design/sanctum-lab-plan.md` §10. Each milestone ends in a demo.

| Milestone | Deliverables | Done when |
|---|---|---|
| **M0** Contracts and evaluator | Frozen wire contracts + JSON Schemas; `sanctum_eval`; stub SUT; `configs/matrix.yaml`; 44 tests incl. 17 evaluator mutations and static isolation | Done |
| **M1** Synthetic world | `world/world.yaml` (4-6 core services, ~26 filler, R40-R42 + experiment branch, all planted situations); world linter; renderer to per-hub corpora (~3,000 artifacts, hub-specific vocabulary, deterministic by seed); gold-derivation machinery (world + question spec → gold) | Linter green; every planted situation rendered; same seed gives identical output; gold derivable for a sample question per family |
| **M2** Hubs and runner | CodeHub, SkillHub, DocHub, MemoryHub as MCP servers (FTS5/BM25); token service; ACL; version reads; capability files; failure knobs; admin API; conformance suite; runner producing observed traces | Conformance green per hub; honest miss on unknown alias |
| **M3** Questions and sanctum-ref C1/C2 | 60 dev questions with derived gold; holdout author assigned and 40 holdout drafted (by that author, not the SUT team); `sanctum_ref` C1-naive, C1-fair, C2; receipts; SUT runs out of process and reaches hubs only through an MCP gateway proxy holding the token secret (discrepancy register 16) | Scenario tests EX-01..04, 06..10, FX-24 pass on C2. Result: 8/10 pass; EX-04 (unscoped historical) and EX-06 (ambiguous explore) are strict xfail on C2 and move to C4 at M4 |
| **M4** Memory v0 (C4, C4a) | Memory store, seed release `r1` (deliberately incomplete), name resolution with ambiguity, per-source query plans, procedures + ladder, C4a-equivalent and C4a-label-only controls | FX-16..23, EX-05, EX-15 pass; C4 and C4a runs complete. Result: on C4 (out of process, entity alignment) EX-05, EX-09b, EX-15, FX-16 (both cases), FX-17, FX-19 case 2, FX-20 pass; FX-18 and FX-23 unit-tested; FX-19 case 1, FX-21, EX-04, EX-06 strict xfail; FX-22 not built. Scenarios (22 cases): C2 15, C4 18, C4a-equivalent 18, C4a-label-only 15. Dev (60): C2 26, C4 38, C4a-equivalent 38, C4a-label-only 33. Q3b plan equivalence holds (test) |
| **M5** First paired report | Leak scanner, paired clustered stats, per-family report, B* profile (pinned cross-encoder) | C1-fair vs C2 vs C4 vs C4a report on dev + one holdout run; leakage gate evaluated. Report states results, whichever direction they go |
| **M6** Decision provider (C3, C5) and failures | `DecisionProvider` with rules and local stand-in (Jev only if approved); failure-injection runs | C3, C5 reports; EX-09 variants pass under injected failure |
| **M7** Fifth hub onboarding | IncidentHub via adapter + manifest, no core edits | EX-12 passes; previously `insufficient` questions now answered |
| **M8** Stretch | Agent-level H0 (direct hub access vs Sanctum C2/C4); release swap and rollback during requests | H0 report; FX-23 under concurrent load |

Holdout is run once per milestone from M5 on, by the holdout owner, and never used for tuning.
