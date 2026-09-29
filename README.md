# sanctum-lab (M0 scaffold, M1 synthetic world, M2 simulated hubs)

An evaluation harness for the Sanctum HLD (v5.1). It will run a reference Sanctum
against simulated knowledge hubs built from a synthetic world, and score it with an
independent evaluator. **This is M0: contracts, gold model, evaluator, stub, and the
experiment definition.** M1 adds the synthetic world: one authored ground-truth file, a
deterministic renderer into per-hub corpora, a world linter, and gold derived from the
world. M2 serves the rendered corpora as simulated hubs over MCP (token service, query-time
ACLs, version reads, seeded failure knobs, lab admin API) and adds a runner that observes
every hub call itself. M3 adds `sanctum_ref` (C1-naive, C1-fair, C2), run out of process behind a gateway proxy.

> Every result this repo produces is **SYNTHETIC — NOT PRODUCTION EVIDENCE**.

## Layout

```
src/sanctum_contracts/   public wire contracts (HLD v5.1 §6.6, §7.1, §12.0–12.3) + JSON Schemas
src/sanctum_eval/        independent evaluator: private gold model, metrics, observed traces
src/sanctum_stub/        independent stub SUT with canned responses (proves the evaluator is scoreable)
src/sanctum_hubs/        simulated hubs (M2): corpus store, FTS5 index, ACLs, versions, MCP servers,
                         token service, failure knobs, lab admin API, change feed (reads build/world/hubs only)
src/sanctum_run/         runner (M2, evaluator side): HubGateway, SUT protocol, observed traces, run output;
                         M3: gateway proxy (proxy.py) and out-of-process SUT launcher (process_sut.py)
src/sanctum_ref/         reference Sanctum (M3): C1-naive, C1-fair, C2; runs as its own process, reaches
                         hubs only through the gateway proxy (discrepancy register 16)
owners/manifests/        owner manifests (registry): authority per fact kind, places, must-consult
owners/memory_seed/      memory releases (M4): ACTIVE pointer, r1 (DENOTES, SELECTS_FOR, MEMBER_OF, procedure,
                         descriptors, reviewed project contexts); r1/entities.yaml feeds evaluator-side alignment
src/sanctum_world/       world schema, seeded renderer, filler, linter, gold derivation (evaluator side)
world/world.yaml         authored ground truth: services, releases, principals, facts, hub names, planted situations
world/filler.yaml        filler services, artifact counts per hub, noise vocabulary
world/templates/         per-hub text templates with {{fact:<id>}} slots
questions/specs/sample/  10 structured question specs, one per family (M1)
gold/m0/                 3 hand-authored gold cases (evaluator-only)
gold/m1/                 gold derived from the world and sample specs (evaluator-only)
build/world/             render output, gitignored: hubs/<hub>/artifacts.jsonl (hub-visible),
                         private/ (provenance, entity refs, canaries, planted index), manifest.json
tests/fixtures/m0/       hand-written observed traces (runner-produced from M2)
configs/hubs.yaml        hub list, held-back hubs (IncidentHub), max_results
configs/failure_profiles.yaml  seeded failure profiles: none, flaky, degraded, skillhub_timeout
configs/m0_principal_aliases.yaml  gold/m0 principal -> world principal (provisional)
configs/matrix.yaml      configuration arms and the only switches each comparison may change
docs/                    measurement plan, scenario register, capability matrix, discrepancies, decisions
tools/                   schema export, config diff, M0 fixture builder, M0 scoring, world build/lint, gold derivation
```

Planned later (not present): `gen/`.

## Boundaries (enforced by tests at M0; by runtime images from M1)

| Package | May import | Must never see |
|---|---|---|
| `sanctum_contracts` | stdlib, pydantic, pyyaml | anything else in this repo |
| `sanctum_ref` | `sanctum_contracts`, stdlib, `mcp` (with its `anyio`), pydantic, pyyaml, tiktoken | `sanctum_eval`, `sanctum_world`, `sanctum_stub`, `sanctum_run`, `sanctum_hubs`, `gold/`, `world/`, `build/world`, holdout, question specs |
| `sanctum_stub` | `sanctum_contracts` | `sanctum_eval`, `sanctum_world`, `gold/`, `world/`, `build/world/private`, traces |
| `sanctum_world` | `sanctum_eval` (gold model), stdlib, pydantic, pyyaml | nothing runtime-side; runtime packages must not import it |
| `sanctum_eval` | `sanctum_contracts` | `sanctum_stub`, `sut_ref` internals |
| `sanctum_hubs` | `sanctum_contracts`, pydantic, pyyaml, mcp | `sanctum_eval`, `sanctum_world`, `sanctum_stub`, `sanctum_run`, `private/`, `world.yaml`, `gold/` |
| `sanctum_run` | `sanctum_contracts`, `sanctum_eval`, `sanctum_hubs`, `sanctum_stub` (adapter) | `sanctum_world` |

A static import scan is **not** sufficient isolation (lab review L03). Allowlisted runtime
images and canary probes arrive at M1.

## Run

```bash
python -m pip install -e ".[dev]"
pytest                                   # M0 (44) + M1 tests
PYTHONPATH=src:. python tools/score_m0.py
python tools/config_diff.py              # show and check comparison diffs
PYTHONPATH=src python tools/export_schemas.py   # after any contract change; review the diff
```

### M1: world, linter, gold

```bash
PYTHONPATH=src python tools/build_world.py --seed 20260930 --out build/world    # render corpora + private index
PYTHONPATH=src python tools/build_world.py --seed 20260930 --out build/world2 \
  && diff build/world/manifest.json build/world2/manifest.json                   # determinism: no output
PYTHONPATH=src python tools/lint_world.py --build build/world                   # non-zero exit on any finding
PYTHONPATH=src python -m sanctum_world.lint --leak-scan build/world             # hub-visible leak scan only
PYTHONPATH=src python tools/derive_gold.py --build build/world --specs questions/specs/sample --out gold/m1
```

### M2: hubs and runner

`<u>` = `uv run --no-project --python 3.12 --with pydantic==2.9.2 --with pyyaml==6.0.2 --with pytest==8.3.3 --with mcp==1.12.4`
(the MCP pin is discrepancy register row 10).

```bash
<u> python -m pytest -q                                                          # full suite
PYTHONPATH=src <u> python tools/build_world.py --seed 20260930 --out build/world # also emits identity/principals.json
SANCTUM_LAB_TOKEN_SECRET=<secret> PYTHONPATH=src <u> python -m sanctum_hubs codehub --build build/world
                                          # stdio hub; exits on EOF; the secret comes from the env, never argv
PYTHONPATH=src:. <u> python tools/run_lab.py --sut stub --cases gold/m0 --failure-profile none --seed 1 --out runs/m2-smoke
PYTHONPATH=src:. <u> python tools/score_m0.py                                    # M0 scoring unchanged
```

A run directory holds `manifest.json`, `responses.jsonl`, `receipts.jsonl`, `traces.jsonl`
(observed by the gateway, never self-reported) and `scores.jsonl`. The admin API
(`sanctum_hubs.admin.AdminClient`) is lab-only, needs the admin secret, is not an MCP tool,
and appends hub-visible events to `runs/<id>/change_feed.jsonl`.

Linter rules: `planted_missing`, `fact_unasserted`, `coverage_gap_asserted`, `span_mismatch`,
`restricted_leak`, `vocabulary_leak`, `private_id_leak`, `filler_collision` (see
`src/sanctum_world/lint.py`). The leak scan reads only the exact identifiers listed under
`build/world/private/`.

### M3: sanctum-ref

`<u>` gains `--with tiktoken==0.9.0` (discrepancy register row 9).

```bash
PYTHONPATH=src:. <u> python tools/run_lab.py --sut ref --config C2 --cases gold/scenarios --out runs/m3-c2
PYTHONPATH=src:. <u> python tools/run_lab.py --sut ref --config C1-fair --cases gold/dev --out runs/m3-c1fair
<u> python -m pytest -q tests/scenarios                     # EX-01..04, 06..10, FX-24 on C2; EX-09c/d
```

`--sut ref` launches `python -m sanctum_ref` as a child process with no secrets in its
environment; `sanctum.retrieve` travels over its stdio and hub calls over two inherited pipes to
the runner's gateway proxy. Receipts carry the `config_id`.

### M4: memory v0

```bash
PYTHONPATH=src:. <u> python tools/run_lab.py --sut ref --config C4 --cases gold/dev --out runs/m4-c4
# also C4a-equivalent, C4a-label-only; memory arms are scored through the entity alignment
```

C4 stores the release as typed relations, C4a-equivalent as flat tables (same plans, checked by
the Q3b test), C4a-label-only resolves through one flat label table. Each request pins the release
named by `owners/memory_seed/ACTIVE`; place unshares and renames arrive through the proxy's
`change_events` tool (per-reader `ChangeFeed.events_for`) and stop the affected selectors.

| Arm | Scenarios (22) | Dev (60) |
|---|---|---|
| C2 | 15 | 26 |
| C4 | 18 | 38 |
| C4a-equivalent | 18 | 38 |
| C4a-label-only | 15 | 33 |

### M6: decision provider (SUT side)

```bash
PYTHONPATH=src:. <u> python tools/fit_d2_standin.py            # refit D2 calibration on dev runs only
PYTHONPATH=src:. <u> python tools/run_lab.py --sut ref --config C3 --decision-provider standin --cases gold/dev --out runs/m6-c3
```

`DecisionProvider.decide(DecisionRequest) -> DecisionResult` for D2 (source usefulness) over
optional sources only: `rules`, `standin` (local TF-IDF over pinned descriptors plus logistic
calibration, `configs/d2_standin.yaml` with provenance), `jev` (refuses: not approved).
Uncertain answers keep the source; an unavailable layer keeps every candidate and reports
`decision_layer_unavailable`. Receipts carry the decisions.

| Arm | Scenarios (22) | Dev (60) | Sources per dev case |
|---|---|---|---|
| C2 | 15 | 26 | 2.57 |
| C3 (standin) | 15 | 26 | 2.57 |
| C4 | 18 | 38 | 2.57 |
| C5 (standin) | 18 | 38 | 2.57 |

### M7: IncidentHub onboarding

IncidentHub joins with no `sanctum_ref` code change: an owner manifest
(`owners/manifests/incidenthub.yaml`) and memory release `r2` (queue places, pinned descriptor),
selected per run with `--memory-release r2` (ACTIVE stays `r1` so M0-M6 results reproduce). It stays
held back in `configs/hubs.yaml`; release it per run with `tools/run_lab.py --release-hub incidenthub
--memory-release r2` (the proxy exposes only released hubs).

| Arm | Dev held back | Dev released |
|---|---|---|
| C2 | 26 | 24 |
| C4 | 38 | 37 |

Dev gold was derived with IncidentHub held back, so it cannot credit incident evidence; EX-12
(released vs held back) is the onboarding test.

## M0 exit criteria (lab plan revised §10)

| Criterion | Where | Status |
|---|---|---|
| Enum and reason-code mappings frozen | `enums.py`, `reason_codes.yaml`, `test_contracts.py` | Done, pending D-SCHEMA approval |
| Required fields frozen; JSON Schemas committed | `schema/`, `test_schema_freeze.py` | Done |
| Every metric has observable inputs | `metrics.py` reads only response, receipt, observed trace, gold | Done (precision is an M0 proxy) |
| Independent stub scores | `test_stub_scoring.py` | Done |
| Evaluator resists gaming (preview of M1) | `test_evaluator_mutations.py` (17 mutations) | Done |
| Unsupported verify/replay/capabilities advertised accurately | `StubSUT.capabilities()`, `capability-matrix.yaml` | Done |
| Config diffs mechanical; comparisons change one thing | `configs/matrix.yaml`, `test_config_matrix.py` | Done |
| Scenario register with separate alignment and execution status | `scenario-register.yaml`, `test_scenario_register.py` | Done; nothing marked as run |
| Owner decisions recorded | `docs/decisions.md` | Open: D-GOAL, D-GOLD, D-SCHEMA block M1 |

## M1 exit criteria (lab plan §5, §8.3)

| Criterion | Where | Status |
|---|---|---|
| World validates: 4-6 core services, ~26 filler, R40-R42 + experiment branch, 3-4 principals, 12 planted situations | `world/world.yaml`, `schema.py`, `test_world_schema.py` | Done |
| 2,700-3,300 artifacts across CodeHub, SkillHub, DocHub, MemoryHub (IncidentHub held back) | `render.py`, `filler.py`, `test_world_render.py` | Done (3,000) |
| Same seed gives identical `manifest.json`; other seed changes filler only | `test_world_render.py` | Done |
| Every provenance span renders its value | `test_world_render.py`, linter `span_mismatch` | Done |
| Linter clean on the real world; each mutation trips its rule | `lint.py`, `test_world_lint.py` | Done |
| No fact id, entity id, planted label or canary in hub-visible output | `--leak-scan`, `test_world_lint.py` | Done |
| 10 sample gold files validate against the unchanged M0 `GoldCase` | `gold.py`, `gold/m1/`, `test_gold_derivation.py` | See test run |
| Runtime packages cannot import `sanctum_world` or name world/private paths | `test_isolation_static.py` | Done |
| Independent gold audit (D-GOLD) | `docs/decisions.md` | Open: developer validation only |

## M2 exit criteria (lab plan §6.2, plan `sanctum-lab-m2-simulated-hubs`)

| Criterion | Where | Status |
|---|---|---|
| `mcp` pinned; full suite passes under the pinned environment | discrepancy register row 10 | Done |
| Every hub serves its tools over MCP (in-memory and stdio) from `build/world/hubs/<hub>/` only | `servers.py`, `__main__.py`, `test_hub_mcp_stdio.py`, `corpus.py` path guard | Done |
| Conformance green for all 5 hubs (scope isolation, restricted absence in results/lists/counts/errors, version reads, honest miss, determinism, failure knobs, capabilities) | `tests/hubs/test_conformance.py` | Done |
| Passthrough, wrong audience, expired, tampered, revoked and missing tokens denied | `tokens.py`, `tests/hubs/test_tokens.py` | Done |
| Failure profiles reproducible by seed; rates within tolerance | `failure.py`, `tests/hubs/test_failure.py` | Done |
| Admin mutations visible on the next call; change feed leak-free | `admin.py`, `change_feed.py`, `tests/hubs/test_admin.py` | Done |
| Runner writes manifest, responses, receipts, traces; stub scores match `score_m0.py` | `sanctum_run/`, `tools/run_lab.py`, `test_runner.py` | Done |
| EX-09c (auth half) fails closed and is marked in the register; later-milestone rows cannot claim a run | `test_ex09c.py`, `scenario-register.yaml`, `test_scenario_register.py` | Done; registry half at M3 |
| Hubs cannot import evaluator/world/stub/run packages or name private build paths | `test_isolation_static.py` | Done (static scan only) |

## What M0 does not prove

M0 proves the contracts are executable and the evaluator can score and resist the listed
gaming strategies on three hand-authored cases. It proves nothing about Sanctum's behavior,
hubs, routing, or memory. Gold here is hand-written by the same author as the stub; from
M1, gold is generated from the world file and independently audited.
