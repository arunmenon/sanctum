# sanctum-lab (M0 scaffold)

An evaluation harness for the Sanctum HLD (v5.1). It will run a reference Sanctum
against simulated knowledge hubs built from a synthetic world, and score it with an
independent evaluator. **This is M0: contracts, gold model, evaluator, stub, and the
experiment definition.** No hubs, world, or reference SUT exist yet.

> Every result this repo produces is **SYNTHETIC — NOT PRODUCTION EVIDENCE**.

## Layout

```
src/sanctum_contracts/   public wire contracts (HLD v5.1 §6.6, §7.1, §12.0–12.3) + JSON Schemas
src/sanctum_eval/        independent evaluator: private gold model, metrics, observed traces
src/sanctum_stub/        independent stub SUT with canned responses (proves the evaluator is scoreable)
gold/m0/                 3 hand-authored gold cases (evaluator-only)
tests/fixtures/m0/       hand-written observed traces (runner-produced from M2)
configs/matrix.yaml      configuration arms and the only switches each comparison may change
docs/                    measurement plan, scenario register, capability matrix, discrepancies, decisions
tools/                   schema export, config diff, M0 fixture builder, M0 scoring
```

Planned later (not present): `world/`, `gen/`, `hubs/`, `owners/`, `sut_ref/`, `run/`.

## Boundaries (enforced by tests at M0; by runtime images from M1)

| Package | May import | Must never see |
|---|---|---|
| `sanctum_contracts` | stdlib, pydantic, pyyaml | anything else in this repo |
| `sanctum_stub` / future `sut_ref` | `sanctum_contracts` | `sanctum_eval`, `gold/`, `world/`, traces |
| `sanctum_eval` | `sanctum_contracts` | `sanctum_stub`, `sut_ref` internals |

A static import scan is **not** sufficient isolation (lab review L03). Allowlisted runtime
images and canary probes arrive at M1.

## Run

```bash
python -m pip install -e ".[dev]"
pytest                                   # 44 tests
PYTHONPATH=src:. python tools/score_m0.py
python tools/config_diff.py              # show and check comparison diffs
PYTHONPATH=src python tools/export_schemas.py   # after any contract change; review the diff
```

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

## What M0 does not prove

M0 proves the contracts are executable and the evaluator can score and resist the listed
gaming strategies on three hand-authored cases. It proves nothing about Sanctum's behavior,
hubs, routing, or memory. Gold here is hand-written by the same author as the stub; from
M1, gold is generated from the world file and independently audited.
