# Sanctum Lab M3 (SUT half): sanctum-ref C1/C2 and gateway proxy

Owner: backend-engineer (m3-ref). Status: review.

## Scope
1. Out-of-process SUT boundary (register row 16)
   - `src/sanctum_run/proxy.py`: runner-side MCP server over a pipe pair passed to the SUT
     process (fds via `pass_fds`). Tools: `hub_capabilities`, `<hub>.<tool>` for every released
     hub tool. Holds no state the SUT can reach; forwards through `HubGateway` (which holds the
     token service and secret), so every call is an `ObservedCall`. A call is served only when its
     `_meta` request id and caller token match the runner's active binding; else denied + anomaly.
   - `src/sanctum_run/process_sut.py`: `ProcessSUT` spawns `python -m sanctum_ref` with a scrubbed
     environment (no secret), talks `sanctum.retrieve` over its stdio, binds the proxy per case.
   - Runner: `run_cases` enters `sut.session(...)` when present. In-process mode kept for the stub.
2. `owners/manifests/<hub>.yaml`: hub id, authority per fact kind, place selectors, version
   semantics, must-consult procedure (SkillHub, payments procedure facts). May be incomplete.
3. `src/sanctum_ref/` (imports: sanctum_contracts, stdlib, mcp, pydantic, pyyaml, tiktoken)
   - `config.py` arms from matrix switches only (C1-naive, C1-fair, C2); unknown arm refused.
   - `registry.py` load/validate manifests; unavailable or invalid registry fails closed.
   - `intent.py` fact-kind and domain rules; `routing.py` fan-out vs rules + capability checks
     + must-consult; `adapters.py` per-hub search/fetch plans; `assembly.py` exact dedup,
     applicability, lexical ranker (normalized per source), conflict flags, packing with
     conflict-witness reservation (tiktoken cl100k_base); `pipeline.py`; `server.py`/`__main__.py`.
   - Evidence spans: offsets into the fetched artifact text, with artifact_id and version.
   - No LLM, no memory, no name translation (C2 switches: resolution none, translation false).
4. Tests: `tests/sut_ref/` unit tests, `tests/scenarios/` EX-01..04, 06..10, FX-24 on C2
   (cases from docs/scenario-cases.yaml when it lands; gold/m1 until then), EX-09c registry half,
   proxy isolation tests, static isolation for sanctum_ref.
5. `tools/run_lab.py --sut ref --config C2`.
6. Pin tiktoken (pyproject, register row 9); register row 16 status; scenario register statuses.

## Constraints
Do not touch world.yaml, configs/m0_principal_aliases.yaml, questions/, gold/. SUT never reads
gold, world, private build paths or holdout. No commits.

## Steps
- [x] proxy + ProcessSUT + runner session hook
- [x] manifests
- [x] sanctum_ref modules
- [x] tests, run_lab, isolation
- [x] docs (register rows 9, 16; scenario register), full suite

## Result
Full pinned suite 314 passed, 2 strict xfail (EX-04, EX-06 on C2). Scenarios on C2 (out of
process): EX-01, 02, 03, 07, 08, 09, 10, FX-24 (both cases) pass; EX-09c registry and auth halves
and EX-09d pass. Scenario CLI: C1-naive 3/11, C1-fair 7/11, C2 9/11. Dev (in process, 60):
C1-naive 20, C1-fair 30, C2 26 safe grounded success; C2 attempts 2.57 sources vs 3.55.

## Notes
- The author read one gold file (gold/m1/m1-001.yaml) while checking the span model, before
  the no-gold rule was applied; nothing in the SUT is tuned to it.
