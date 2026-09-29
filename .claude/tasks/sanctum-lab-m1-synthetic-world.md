# Plan: Sanctum Lab M1, the synthetic world

## Task Description

Build M1 of the Sanctum Lab inside `sanctum-lab-m0/`: the single authored ground-truth file (`world/world.yaml`), a world linter, a deterministic renderer that turns the world into per-hub corpora (~3,000 artifacts with hub-specific vocabulary), and the machinery that derives gold (`sanctum_eval.gold.GoldCase`) from the world plus a small question spec.

Source of requirements: `docs/design/sanctum-lab-plan.md` §5 (world schema, scale, owner manifests, linter, rendering) and §8.3 (gold rules); acceptance in `docs/milestones.md` (M1). Working assumptions in `docs/decisions.md` apply (D-GOAL: real slice + directional evidence; D-GOLD: developer validation until an auditor is named). D8 (LLM paraphrasing) is **off** for M1.

Task type: feature. Complexity: medium-complex.

## Objective

When this plan is complete:

- `world/world.yaml` holds 4-6 core services, ~26 filler services, releases R40, R41, R42 plus an experiment branch, 3-4 principals, facts, per-hub names and places, and every planted situation.
- `python tools/build_world.py --seed 20260930` writes hub corpora and a private provenance index to `build/world/`, byte-identical across runs with the same seed.
- `python tools/lint_world.py` passes on the real world and fails on each deliberately broken variant.
- `python tools/derive_gold.py` turns one sample question spec per family (10 specs) into `GoldCase` files that validate against the existing M0 gold model.
- All existing 44 tests still pass; new tests cover schema, rendering, determinism, linter, gold derivation and extended isolation.

## Problem Statement

M0 proved the evaluator can score, but only on 3 hand-written gold cases whose spans and artifact IDs were invented. Every later milestone (hubs at M2, questions and `sanctum-ref` at M3, memory at M4) needs a shared, realistic corpus and gold that is *derived* rather than authored by the same person who writes the SUT. The world is also where the lab's hard cases (homonyms, conflicts, versions, leaks, injections, gaps) are planted; if they are missing or leak into the wrong hub, every downstream result is meaningless.

## Solution Approach

One authoring package, `src/sanctum_world/`, sits on the evaluator side of the isolation boundary:

```
world/world.yaml  ──▶ schema.py (Pydantic, validates + resolves refs)
                          │
                          ▼
                 render.py + templates/ + filler.py  (seeded RNG)
                          │
          ┌───────────────┼─────────────────────────────┐
          ▼               ▼                             ▼
 build/world/hubs/<hub>/  build/world/private/          build/world/manifest.json
 artifacts.jsonl          provenance.jsonl              (seed, world hash, per-file sha256)
 (hub-visible only)       entity_refs.json
                          │
          lint.py ◀───────┤ (world + corpora + provenance)
          gold.py ◀───────┘ (+ questions/specs/*.yaml) ──▶ gold/m1/*.yaml (GoldCase)
```

Key decisions:

1. **Spans come from the renderer, not from guessing.** Templates insert each fact assertion through a helper that records `(artifact_id, version, fact_id, value, start, end)` into the provenance index while building the text. Gold `SpanRef`s are copied straight from that index, so gold offsets are correct by construction.
2. **Hub-visible output carries no provenance.** `artifacts.jsonl` rows hold only what a real hub would expose: `artifact_id` (opaque, seeded hash), native path/space/repo, version/ref, environment, ACL groups, title, text, and native metadata. Fact IDs, entity IDs and planted-situation labels live only under `build/world/private/`.
3. **Opaque entity refs.** Each entity gets `ent-<short hash of (seed, entity id)>`; the map lives in `private/entity_refs.json` and is what gold's `entity_ref` uses (matching the M0 `ent-17` style).
4. **Hub vocabulary is enforced by data, not convention.** Each hub's names/places come only from `hubs.<hub>` in the world file; the renderer refuses to write a name into a hub that does not declare it, and the linter double-checks.
5. **Determinism.** A single `random.Random(seed)` is split per hub/service with derived sub-seeds; no set iteration order, no timestamps, sorted output, JSON dumped with `sort_keys=True`. Determinism is tested by building twice and comparing `manifest.json`.
6. **Gold derivation is a pure function** `derive(world, provenance, entity_refs, spec) -> GoldCase`, then validated with `sanctum_eval.gold.GoldCase.model_validate`. Question specs are structured (entity, attribute, as_of, principal, family, text), not free text, so derivation never needs NLP. The 60 dev questions come at M3; M1 ships 10 sample specs (one per family) to prove every family is derivable.
7. **Build output is not committed.** `build/` is gitignored; the committed evidence is `world.yaml`, templates, code, tests, and `gold/m1/` samples.

### Planted situations (all must be present and linted)

| Planted | Where | Consumed by |
|---|---|---|
| Homonym "Auth Service" (Payments vs Identity namespaces) | SkillHub | FX-16, same-name family |
| Four names for one service: `svc.payment-auth` = "Auth Service"/Payments (SkillHub), "PA-svc" (MemoryHub), `repo:payments/payment-auth` (CodeHub), `space:PA` (DocHub) | all hubs | EX-05, hub-specific-name family |
| Policy/implementation conflict: retry limit 5 in code at R42 vs 3 in procedure | CodeHub vs SkillHub | EX-03, conflicting-sources family |
| Version branching: 3 at R40, 5 at R42 prod, 7 on experiment branch | CodeHub | EX-04, historical family |
| Newer artifact not applicable (experiment value newer than prod) | CodeHub | FX-24 |
| Exact duplicate document | DocHub + CodeHub | EX-02 |
| Composite subject skill about both auth services | SkillHub | FX-17 |
| Coverage gap: `svc.fx-quote` has facts but no asserting artifact | none | EX-08, no-source family |
| Prompt injection document | DocHub | EX-10 |
| Restricted space `space:Incidents` with canary strings | DocHub | leakage gate, restricted family |
| DocHub `space:PA` without version reads | capabilities | capability-gap source outcomes |
| One multi-hub fact needing code + doc together | CodeHub + DocHub | needs-two-hubs family |

## Relevant Files

Use these files to complete the task:

- `docs/design/sanctum-lab-plan.md` §5, §8 - world schema sketch, scale targets, linter rules, rendering rules, gold rules.
- `docs/design/sanctum-intelligence-layer-hld-v5.1.md` §7.1, §7.5, §8.5, §10 - evidence units, version applicability, names vs subjects vs places, worked examples the planted situations must support.
- `docs/milestones.md` - M1 acceptance.
- `docs/decisions.md` - working assumptions.
- `docs/scenario-register.yaml` - which scenarios need which planted situations.
- `src/sanctum_eval/gold.py` - `GoldCase`, `SpanRef`, `Obligation`, `RelationGold`, `Forbidden`; derived gold must validate against these unchanged.
- `src/sanctum_contracts/enums.py` - `RelationType`, `EvidenceStatus`, `SourceStatus`, mode enums.
- `src/sanctum_contracts/request.py` - `RetrieveRequest` used inside `GoldCase.request`.
- `gold/m0/*.yaml` - reference shape for derived gold files.
- `tests/test_isolation_static.py` - extend `RULES` so runtime packages may not import `sanctum_world`, and forbidden literals include `build/world/private`.
- `tests/conftest.py`, `pyproject.toml` - test paths; no new runtime dependencies needed (stdlib + pydantic + pyyaml).

### New Files

- `world/world.yaml` - authored ground truth.
- `world/templates/<hub>/<kind>.txt` - text templates (Java-ish code, skill markdown, Confluence-ish page, session note), using `{{fact:<id>}}`-style slots.
- `world/filler.yaml` - filler service names, artifact counts per hub, noise vocabulary.
- `src/sanctum_world/__init__.py`
- `src/sanctum_world/schema.py` - Pydantic models for the world file with cross-reference validation.
- `src/sanctum_world/rng.py` - seeded sub-RNG derivation and opaque ID hashing.
- `src/sanctum_world/render.py` - world to corpora, span recording, manifest.
- `src/sanctum_world/filler.py` - noise services and artifacts.
- `src/sanctum_world/lint.py` - linter returning a list of typed findings.
- `src/sanctum_world/gold.py` - question spec model and `derive()`.
- `questions/specs/sample/*.yaml` - 10 sample question specs, one per family.
- `gold/m1/*.yaml` - derived sample gold.
- `tools/build_world.py`, `tools/lint_world.py`, `tools/derive_gold.py` - CLIs.
- `tests/test_world_schema.py`, `tests/test_world_render.py`, `tests/test_world_lint.py`, `tests/test_gold_derivation.py`.
- `.gitignore` entry for `build/`.

## Implementation Phases

### Phase 1: Foundation

World schema models, seeded RNG and opaque ID helpers, and the authored `world.yaml` with all core services, principals, releases, facts, hub names/places/capabilities and planted situations.

### Phase 2: Core Implementation

Templates, renderer with span recording, filler generation to reach ~3,000 artifacts, manifest and determinism; then linter and gold derivation in parallel, both reading the rendered output.

### Phase 3: Integration & Polish

CLIs, isolation test extension, sample specs and gold, README update (layout, run commands, M1 row in exit table), full test run, validation.

## Team Orchestration

- You operate as the team lead and orchestrate the team to execute the plan.
- You're responsible for deploying the right team members with the right context to execute the plan.
- IMPORTANT: You NEVER operate directly on the codebase. You use `Task` and `Task*` tools to deploy team members to the building, validating, testing, deploying, and other tasks.
  - This is critical. Your job is to act as a high level director of the team, not a builder.
  - Your role is to validate all work is going well and make sure the team is on track to complete the plan.
  - You'll orchestrate this by using the Task\* Tools to manage coordination between the team members.
  - Communication is paramount. You'll use the Task\* Tools to communicate with the team members and ensure they're on track to complete the plan.
- Take note of the session id of each team member. This is how you'll reference them.

### Team Members

- Specialist
  - Name: builder-world
  - Role: World schema, authored `world.yaml`, linter, CLIs, isolation test and README updates
  - Agent Type: backend-engineer
  - Resume: true
- Specialist
  - Name: builder-render
  - Role: Templates, renderer with span provenance, filler, manifest and determinism
  - Agent Type: backend-engineer
  - Resume: true
- Specialist
  - Name: builder-gold
  - Role: Question spec model, gold derivation, 10 sample specs and derived gold
  - Agent Type: backend-engineer
  - Resume: true
- Quality Engineer (Validator)
  - Name: validator
  - Role: Validate completed work against acceptance criteria (read-only inspection mode)
  - Agent Type: quality-engineer
  - Resume: false

## Step by Step Tasks

- IMPORTANT: Execute every step in order, top to bottom. Each task maps directly to a `TaskCreate` call.
- Before you start, run `TaskCreate` to create the initial task list that all team members can see and execute.

### 1. World schema and helpers

- **Task ID**: world-schema
- **Depends On**: none
- **Assigned To**: builder-world
- **Agent Type**: backend-engineer
- **Parallel**: false
- Create `src/sanctum_world/schema.py` with frozen, `extra="forbid"` Pydantic models: `Principal`, `Entity` (service/domain/topic, `member_of`), `FactValue` (value, from release, optional env/branch), `Fact` (entity, `fact_kind` in implemented/procedure/policy/incident, attribute, values), `HubName` (native, namespace, denotes), `HubPlace` (native, selects_for, acl), `HubSpec` (names, places, capabilities), `ArtifactVersion` (ref, env, asserts `fact@release[/env]`), `Artifact` (hub, path, kind, versions, about, acl), `Planted` (tagged union of the 12 situations in the Solution Approach table), `FillerSpec`, `World`.
- `World` validator resolves every reference (entity, fact, release, hub, principal group, artifact) and raises with the offending path.
- Create `src/sanctum_world/rng.py`: `sub_rng(seed, *labels)` via sha256 of labels, `opaque_id(seed, prefix, key)` producing `art-xxxxxx` / `ent-xxxxxx`.
- Unit tests in `tests/test_world_schema.py`: valid minimal world loads; each dangling reference type fails.

### 2. Author world.yaml

- **Task ID**: author-world
- **Depends On**: world-schema
- **Assigned To**: builder-world
- **Agent Type**: backend-engineer
- **Parallel**: true
- Write `world/world.yaml` (seed 20260930) following `docs/design/sanctum-lab-plan.md` §5.1: principals `kestrel-payments`, `kestrel-identity`, `kestrel-both`, `admin-probe`; core services `svc.payment-auth`, `svc.identity-auth`, `svc.fx-quote`, `svc.ledger-post`, `svc.gateway-edge` (5); domains; topic entities; releases R40, R41, R42, branch `exp-branch`; environments prod and experiment.
- Author facts and core artifacts so every planted situation in the Solution Approach table is present; add each to `planted:`.
- Write `world/filler.yaml`: 26 filler service names that do not collide with core names or aliases, per-hub artifact counts sized to ~3,000 total.
- Must load through `World.model_validate` with no errors.

### 3. Templates, renderer, filler

- **Task ID**: renderer
- **Depends On**: world-schema
- **Assigned To**: builder-render
- **Agent Type**: backend-engineer
- **Parallel**: true (with author-world; use a small fixture world in tests until `world.yaml` lands)
- Templates per hub and kind under `world/templates/`; slots `{{fact:<id>}}`, `{{name}}`, `{{place}}`, plus noise paragraphs.
- `render.py`: `render(world, seed, out_dir)`. Builds text with a `TextBuilder` that records exact `[start, end)` of every fact assertion; writes `hubs/<hub>/artifacts.jsonl` (hub-visible fields only), `private/provenance.jsonl`, `private/entity_refs.json`, `manifest.json` (seed, sha256 of world.yaml, per-file sha256, artifact counts per hub).
- Injection artifact contains an instruction string; restricted artifacts contain canary tokens listed in `private/canaries.json`.
- Exact duplicate is byte-identical text in both hubs with different native IDs.
- DocHub `space:PA` artifacts carry one current version only, matching its capability.
- `filler.py`: seeded noise services and artifacts reusing templates with filler vocabulary; no filler artifact asserts a core fact.
- Tests in `tests/test_world_render.py`: provenance slices of `text[start:end]` equal the rendered value; hub-visible rows have no keys outside the allowlist; two builds give identical manifests; total artifacts 2,700-3,300.

### 4. World linter

- **Task ID**: linter
- **Depends On**: author-world, renderer
- **Assigned To**: builder-world
- **Agent Type**: backend-engineer
- **Parallel**: true (with gold-derivation)
- `lint.py`: `lint(world, build_dir) -> list[Finding]` implementing `docs/design/sanctum-lab-plan.md` §5.4 plus: every `planted` entry rendered and detectable; every fact asserted by at least one artifact unless it is a planted coverage gap; no restricted canary, title or native name appears in any unrestricted artifact; no hub text contains a name that hub does not declare (vocabulary separation); no fact ID, entity ID or planted label appears in hub-visible output; filler names do not collide with core names.
- `tools/lint_world.py` exits non-zero with findings printed.
- `python -m sanctum_world.lint --leak-scan <build_dir>` runs only the hub-visible leak rule, using exact identifiers read from `private/` (no regex guessing).
- `tests/test_world_lint.py`: real world lints clean; one mutated copy per rule (drop a planted artifact, leak a canary, leak a fact ID, remove an asserting artifact, cross-hub name) each produces the expected finding.

### 5. Gold derivation

- **Task ID**: gold-derivation
- **Depends On**: author-world, renderer
- **Assigned To**: builder-gold
- **Agent Type**: backend-engineer
- **Parallel**: true (with linter)
- `src/sanctum_world/gold.py`: `QuestionSpec` (id, family, principal, text, mode, scope, as_of, target entity or name, attribute, optional expected ambiguity) and `derive(world, build_dir, spec) -> GoldCase`.
- Derivation rules: interpretations = entities the named term denotes and the principal may see; obligations = provenance spans asserting the fact applicable at `as_of`/prod for each interpretation (bundles for alternatives such as exact duplicates); source obligations from must-consult (SkillHub for procedure facts) and capability gaps; relations from differing values of the same attribute (code vs procedure = `policy_implementation_divergence`, release = `version_difference`, env = `environment_difference`); `forbidden.canaries` from restricted canaries, `wrong_entities` from homonym siblings; `answerable`/`expected.evidence_status` from whether any obligation is obtainable for the principal.
- `request.request_id` is an opaque hash, never containing case id or family.
- Write 10 specs in `questions/specs/sample/` (families from `docs/design/sanctum-lab-plan.md` §8.2) and derived output in `gold/m1/`.
- `tools/derive_gold.py` builds all specs; `tests/test_gold_derivation.py` validates every output with `sanctum_eval.gold.GoldCase` and checks family-specific expectations (homonym gives `separate_alternatives`, coverage gap gives `answerable: false`, restricted gives non-empty canaries, historical R40 yields value 3).

### 6. Integration, isolation, docs

- **Task ID**: integration
- **Depends On**: linter, gold-derivation
- **Assigned To**: builder-world
- **Agent Type**: backend-engineer
- **Parallel**: false
- Add `tools/build_world.py` (`--seed`, `--out build/world`).
- Extend `tests/test_isolation_static.py`: `sanctum_contracts` and `sanctum_stub` may not import `sanctum_world`; forbidden literals add `build/world/private` and `world/`.
- Add `build/` to `.gitignore`.
- Update `README.md`: layout, M1 run commands, M1 exit table.
- Run `pytest` and the three CLIs; fix failures.

### 7. Final validation

- **Task ID**: validate-all
- **Depends On**: world-schema, author-world, renderer, linter, gold-derivation, integration
- **Assigned To**: validator
- **Agent Type**: quality-engineer
- **Parallel**: false
- Run all validation commands.
- Verify every acceptance criterion; spot-check 5 provenance spans by hand and 3 derived gold files against `world.yaml`.
- Grep hub-visible output for fact IDs, entity IDs, planted labels and canaries.
- Operate in validation mode: inspect and report only, do not modify files.

## Acceptance Criteria

- `world/world.yaml` validates; contains 4-6 core services, ~26 filler services, R40-R42 + experiment branch, 3-4 principals, and all 12 planted situations.
- Build produces 2,700-3,300 artifacts across CodeHub, SkillHub, DocHub, MemoryHub (plus IncidentHub corpus generated but marked held back).
- Two builds with the same seed produce identical `manifest.json`; a different seed changes filler but not core facts.
- Every provenance span's `text[start:end]` renders the asserted value.
- Linter passes on the real world and each mutation test triggers its specific finding.
- No fact ID, entity ID, planted label or restricted canary appears in any hub-visible file.
- 10 sample gold files validate against the unchanged M0 `GoldCase` model with the family-specific expectations above.
- All pre-existing tests plus new tests pass.

## Validation Commands

Execute these commands to validate the task is complete:

- `python -m pip install -e ".[dev]"` - install
- `pytest -q` - full suite, including the 44 M0 tests
- `PYTHONPATH=src python tools/build_world.py --seed 20260930 --out build/world` - render
- `PYTHONPATH=src python tools/build_world.py --seed 20260930 --out build/world2 && diff build/world/manifest.json build/world2/manifest.json` - determinism
- `PYTHONPATH=src python tools/lint_world.py --build build/world` - linter clean
- `PYTHONPATH=src python tools/derive_gold.py --build build/world --specs questions/specs/sample --out gold/m1` - gold derivation
- `PYTHONPATH=src python -m sanctum_world.lint --leak-scan build/world` - scans hub-visible files for every fact ID, entity ID, opaque entity ref, planted label and canary listed in `private/`; must report nothing
- `PYTHONPATH=src:. python tools/score_m0.py` - M0 scoring still works

## Notes

- Agent model: all agents run on Opus per project `CLAUDE.md`.
- No new dependencies. D8 paraphrasing is off; typo and paraphrase variants in question text arrive with the 60 dev questions at M3.
- Owner manifests and memory seed (`owners/`) are **not** M1; they are authored from hub-visible structure at M4 so they cannot be copied from the world file.
- IncidentHub corpus is rendered but held back until M7; hubs as MCP servers are M2.
- Gold produced here is "developer validation" until D-GOLD names an independent auditor.
- Keep guardrails light (user direction): no extra approval gates beyond the final validation task.
