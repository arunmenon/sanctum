# Plan: Sanctum Lab M2, simulated hubs and runner

## Task Description

Build M2 of the Sanctum Lab in `sanctum-lab-m0/` (M1 committed at `710274f`): the four released hubs (CodeHub, SkillHub, DocHub, MemoryHub) plus held-back IncidentHub as local MCP servers over the M1 corpora, with honest SQLite FTS5 BM25 search, a lab token service, query-time ACLs, declared version reads, capability files, seeded failure knobs, a lab-only admin API with a change feed, a hub conformance suite, and a runner that produces observed traces the M0 evaluator already understands. Covers scenario EX-09c (auth unavailable fails closed; the registry half lands with `sanctum-ref` at M3).

Sources: `docs/design/sanctum-lab-plan.md` §6 (tools, shared behavior, conformance), §2.1 (isolation), `docs/design/sanctum-intelligence-layer-hld-v5.1.md` §9.1 (change feed), §12.3 (adapter contract), §14.1 (token exchange, no passthrough), `docs/milestones.md` M2, `docs/scenario-register.yaml` EX-09c.

Task type: feature. Complexity: complex.

## Objective

When complete:

- Each hub starts as an MCP server (stdio and in-memory) serving only `build/world/hubs/<hub>/`, exposing the §6.1 tools.
- Search is plain FTS5 BM25: an alias a hub does not use (e.g. "PA-svc" in SkillHub) genuinely misses.
- Hubs accept only hub-scoped tokens minted by the token service; caller tokens, wrong-audience, expired or missing tokens are denied; restricted items never show in results, counts or errors.
- Failure profiles make latency, timeouts, errors and partial results reproducible by seed.
- The conformance suite passes for all 5 hubs.
- `python tools/run_lab.py --sut stub --cases gold/m0 --out runs/<id>` writes responses, receipts and observed traces, and the M0 evaluator scores them.
- EX-09c passes (auth half) and is recorded in the scenario register.
- All 120 existing tests still pass.

## Problem Statement

Until now nothing answers a query: the evaluator scores hand-written traces and the world exists only as JSONL files. `sanctum-ref` (M3) needs realistic backends whose search, permissions, versions and failures behave like the real systems, and the evaluator needs traces it can trust because they are observed by the runner rather than self-reported by the SUT. If hubs are too helpful (synonyms, cross-hub vocabulary) or leak restricted items through counts or error messages, every later comparison is inflated.

## Solution Approach

```
             caller token                         hub-scoped tokens (aud=<hub>)
 runner ──────────────────▶ SUT (stub now, sanctum-ref at M3)
   │  holds gold privately        │ HubGateway (runner-owned, records ObservedCall)
   │                              ▼
   │                     token service ── exchange(caller, aud) ──▶ HMAC token
   │                              │
   │          ┌──────────┬────────┴─┬───────────┬──────────────┐
   │          ▼          ▼          ▼           ▼              ▼
   │      CodeHub    SkillHub    DocHub     MemoryHub    IncidentHub (held back)
   │      FTS5/BM25 index built from build/world/hubs/<hub>/artifacts.jsonl
   │      + capabilities.json + failure profile + ACL filter
   │                                   ▲
   └── admin API (lab only) ── mutations ─┴─▶ change_feed.jsonl
   └── writes runs/<id>/{manifest,responses,receipts,traces}.jsonl ──▶ sanctum_eval
```

Key decisions:

1. **New package `src/sanctum_hubs/`** (runtime side of the boundary): may import only `sanctum_contracts`, stdlib, `mcp`, pydantic, pyyaml. Never `sanctum_eval`, `sanctum_world`, `sanctum_stub`. The corpus loader accepts a single hub directory and refuses any path containing `private` or `world/`.
2. **Public inputs come from the build, not from `world/`.** Extend the M1 renderer to also emit `build/world/hubs/<hub>/capabilities.json` (hub-visible) and `build/world/identity/principals.json` (for the token service only, which is lab infrastructure like an IdP). Both are derived from `world.yaml` and are covered by the linter's leak rules.
3. **Capabilities vs the frozen contract.** `HubCapabilities` is a boolean `version_reads` and is frozen (D-SCHEMA). DocHub has per-place version reads (`space:PA` has none). `capabilities.json` is `{"contract": <HubCapabilities>, "place_version_reads": {"space:PA": false}}`; the contract part validates unchanged; the extension is recorded in `docs/discrepancy-register.md`.
4. **Identity travels in transport metadata, never as a tool argument.** Hub tokens go in the MCP request `_meta` key `lab/hub_token` (HTTP mode may also accept `Authorization: Bearer`). Tokens are HMAC-SHA256 signed JSON: `{sub, groups, aud, exp, jti}`. Hubs verify signature, audience and expiry; caller tokens (aud `sanctum`) presented to a hub are denied (no passthrough). Denials and not-found share one response shape so existence is not revealed.
5. **Honest search.** Per hub, an in-memory SQLite FTS5 table (`unicode61` tokenizer, no porter stemming, no synonyms) over title + text + native path/location. Queries are tokenized and each token quoted, OR-joined, so user text cannot inject FTS syntax. ACL and filters are applied inside the SQL before `LIMIT`, so result counts never include restricted rows. Results: `artifact_id, title, location, path, version, environment, snippet, score` (BM25).
6. **Versions.** Default read returns the current version: highest `metadata.revision` in environment `prod` (or null environment). A `ref`/`version` argument is honored only where declared; otherwise the hub returns a typed `capability_unsupported` error, never silently the current version.
7. **Failure knobs.** `configs/failure_profiles.yaml` defines profiles (`none`, `flaky`, `degraded`, `skillhub_timeout`) with per hub per tool: latency (lognormal median and p95), `timeout_rate`, `error_rate`, `partial_rate`. Draws are seeded by `(run_seed, request_id, hub, tool, call_index)`. A `time_scale` (default 1.0; 0 in unit tests) controls real sleeping. Timeout is distinct from empty (`error_semantics: timeout_distinct_from_empty`).
8. **Admin API and change feed.** `sanctum_hubs.admin.AdminClient` (lab only, needs an admin secret, not exposed as an MCP tool on hub servers) supports: rename path, unshare place (change ACL), revoke principal, change owner, publish new version. Each mutation updates the live hub store and appends a hub-visible event `{seq, hub, kind, subject, at_revision}` to `runs/<id>/change_feed.jsonl`; a read-only `ChangeFeed` reader exists for the SUT at M4. Revocation takes effect in the token service immediately.
9. **Runner owns observation.** `src/sanctum_run/` (evaluator side): `HubGateway` wraps MCP client sessions to each hub, exchanges tokens on the SUT's behalf and records `ObservedCall(source_id, tool, outcome ∈ ok|timeout|error|denied, audience_valid)`. SUT protocol: `retrieve(request, context) -> (EvidenceResponse, Receipt)` where `context` carries the caller token and gateway; the principal comes from the private gold case and never enters the request. An adapter lets the current `StubSUT` run unchanged. Output per run: `manifest.json` (world manifest hash, seed, config id, failure profile, git commit), `responses.jsonl`, `receipts.jsonl`, `traces.jsonl` (`ObservedTrace`), then scored with `sanctum_eval.metrics`.
10. **MCP SDK pin.** Pin the current `mcp` release in `pyproject.toml` (the M0 placeholder), verified to install under Python 3.12 with pydantic 2.9.2; if the SDK needs a newer pydantic, record it in the discrepancy register and pin the lowest compatible pydantic, re-running `test_schema_freeze`.

### Tools per hub (from lab plan §6.1)

| Hub | Tools | Filters | Version reads |
|---|---|---|---|
| CodeHub | `search_code(query, repo?, ref?, top_k)`, `get_file(path, ref?)`, `list_repos()` | repo, ref | yes |
| SkillHub | `search_skills(query, path_prefix?, top_k)`, `get_skill(path, version?)`, `list_tree(prefix?)` | path_prefix | yes |
| DocHub | `search(query, space?, top_k)`, `get_page(page_id)`, `list_spaces()` | space | per place (`space:PA` none) |
| MemoryHub | `search_sessions(query, top_k)`, `get_session(id)` | principal (implicit) | no |
| IncidentHub | `search_incidents(query, service?, since?)`, `get_incident(id)` | queue, service, since | no; held back |

`list_*` tools also filter by ACL.

## Relevant Files

- `docs/design/sanctum-lab-plan.md` §2.1, §6, §9 - hub behavior, conformance, runner outputs.
- `docs/design/sanctum-intelligence-layer-hld-v5.1.md` §9.1, §12.3, §14.1 - change feed, adapter contract, token exchange.
- `docs/milestones.md`, `docs/scenario-register.yaml`, `docs/discrepancy-register.md`, `docs/decisions.md`.
- `configs/matrix.yaml` - `auth: test_issuer_broker`, `failure_profile: from_run_manifest`, budgets.
- `src/sanctum_contracts/capability.py` - `HubCapabilities`.
- `src/sanctum_contracts/{request,response,receipt}.py` - SUT I/O.
- `src/sanctum_eval/{trace,metrics,load}.py` - `ObservedTrace`, scoring entry points.
- `src/sanctum_stub/stub.py` - SUT to run through the runner.
- `src/sanctum_world/render.py`, `lint.py` - extend outputs and leak coverage.
- `tools/score_m0.py` - existing scoring flow to mirror.
- `tests/test_isolation_static.py`, `tests/test_scenario_register.py` - boundary rules and register states.
- `build/world/hubs/*/artifacts.jsonl` - row keys `acl, artifact_id, environment, kind, location, metadata, path, text, title, version`.

### New Files

- `src/sanctum_hubs/__init__.py`, `corpus.py` (loader + guard), `index.py` (FTS5), `access.py` (token verify, ACL), `versions.py`, `failure.py`, `tokens.py` (token service), `admin.py`, `change_feed.py`, `servers.py` (FastMCP factory per hub), `__main__.py` (`python -m sanctum_hubs <hub> --build build/world`).
- `src/sanctum_run/__init__.py`, `gateway.py`, `runner.py`, `sut.py` (SUT protocol + stub adapter).
- `configs/hubs.yaml` (hub list, held_back, max_results), `configs/failure_profiles.yaml`.
- `tools/run_lab.py`.
- `tests/hubs/conftest.py`, `tests/hubs/test_conformance.py` (parametrized over 5 hubs), `tests/hubs/test_tokens.py`, `tests/hubs/test_failure.py`, `tests/hubs/test_admin.py`, `tests/test_runner.py`, `tests/test_ex09c.py`, `tests/test_hub_mcp_stdio.py`.

## Implementation Phases

### Phase 1: Foundation

Pin `mcp`; renderer emits `capabilities.json` and `principals.json`; hub configs; shared interfaces (`HubStore`, `TokenClaims`, `FailureDraw`) so hub, auth and runner work proceeds in parallel.

### Phase 2: Core Implementation

Hub core (corpus, FTS index, versions, ACL-filtered tools, MCP servers) in parallel with token service, failure knobs, admin API and change feed.

### Phase 3: Integration & Polish

Conformance suite across all hubs, runner and gateway with stub SUT, EX-09c, isolation rules, docs and register, validation, then one Codex review.

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
  - Name: builder-hubs
  - Role: Foundation, hub core (corpus, FTS search, versions, ACL tools, MCP servers), conformance suite
  - Agent Type: backend-engineer
  - Resume: true
- Specialist
  - Name: builder-auth
  - Role: Token service, failure knobs, admin API, change feed, EX-09c
  - Agent Type: backend-engineer
  - Resume: true
- Specialist
  - Name: builder-run
  - Role: Runner, hub gateway, SUT protocol and stub adapter, run outputs and scoring, docs and register
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

### 1. Foundation and interfaces

- **Task ID**: foundation
- **Depends On**: none
- **Assigned To**: builder-hubs
- **Agent Type**: backend-engineer
- **Parallel**: false
- Pin `mcp` in `pyproject.toml`; confirm install with Python 3.12 + pydantic 2.9.2 via uv; record any pin conflict in `docs/discrepancy-register.md`.
- Extend `src/sanctum_world/render.py` to emit `hubs/<hub>/capabilities.json` (decision 3) and `identity/principals.json` (`[{principal, groups}]`); include both in `manifest.json`; extend linter leak coverage to them; keep M1 tests green.
- Add `configs/hubs.yaml` and `configs/failure_profiles.yaml` (decision 7).
- Create `src/sanctum_hubs/` skeleton with typed interfaces: `HubRow`, `HubStore` (load, current version, version lookup, mutate), `TokenClaims`, `TokenVerifier` protocol, `FailureDraw`, error codes (`denied_or_not_found`, `capability_unsupported`, `timeout`, `upstream_error`, `invalid_argument`).

### 2. Hub core and MCP servers

- **Task ID**: hub-core
- **Depends On**: foundation
- **Assigned To**: builder-hubs
- **Agent Type**: backend-engineer
- **Parallel**: true (with auth-failure-admin)
- `corpus.py`: load one hub dir; refuse paths with `private` or `world/`.
- `index.py`: FTS5 per decision 5; ACL and filters in SQL before LIMIT; deterministic ordering (score, then artifact_id); `max_results` cap.
- `versions.py`: decision 6, including DocHub per-place overrides.
- `servers.py`: FastMCP server per hub with the tool table above; token from `_meta`; uniform `denied_or_not_found`; MemoryHub scoped to token `sub`; failure hooks called per tool (no-op until task 3 lands, via the `FailureDraw` interface).
- `__main__.py` for stdio launch; `tests/test_hub_mcp_stdio.py` launches one hub over stdio and runs one search.

### 3. Tokens, failures, admin, change feed

- **Task ID**: auth-failure-admin
- **Depends On**: foundation
- **Assigned To**: builder-auth
- **Agent Type**: backend-engineer
- **Parallel**: true (with hub-core)
- `tokens.py`: `TokenService(principals_path, secret)`: `issue_caller_token(principal)` (aud `sanctum`), `exchange(caller_token, audience)` (validates caller token, rejects revoked principals, returns hub token with groups), `revoke(principal)`, `available` flag to simulate outage (raises `AuthUnavailable`). Verifier used by hubs.
- `failure.py`: decision 7; deterministic draws; `time_scale`; partial = truncate results and set `partial: true` in tool output.
- `admin.py` + `change_feed.py`: decision 8; events contain only hub-visible identifiers.
- Tests: `tests/hubs/test_tokens.py` (passthrough denied, wrong audience, expired, tampered, revoked), `tests/hubs/test_failure.py` (rates within tolerance over 2,000 seeded draws; same seed same outcomes; timeout distinct from empty), `tests/hubs/test_admin.py` (each mutation visible to next search; unshare removes item from results and counts; feed events ordered and leak-free).

### 4. Conformance suite

- **Task ID**: conformance
- **Depends On**: hub-core, auth-failure-admin
- **Assigned To**: builder-hubs
- **Agent Type**: backend-engineer
- **Parallel**: true (with runner)
- `tests/hubs/test_conformance.py` over the in-memory MCP transport, parametrized over all 5 hubs:
  - scope isolation per principal (payments vs identity vs admin-probe);
  - restricted items absent from results, `list_*`, counts; `get` on a restricted id returns the same error body as an unknown id;
  - declared version reads honored; undeclared ones return `capability_unsupported` (DocHub `space:PA`, MemoryHub, IncidentHub);
  - honest miss: each hub searched for another hub's native name for a core service returns no core artifact of that service;
  - determinism: same query twice gives identical ordered results;
  - failure knobs under `flaky` profile produce the configured outcome mix; `none` produces none;
  - `capabilities.json` contract part validates as `HubCapabilities`;
  - canary strings from the restricted place never appear for principals without `restricted-incidents` (test reads canaries from the build's private dir, which is allowed for tests, not for hubs).

### 5. Runner, gateway, stub adapter

- **Task ID**: runner
- **Depends On**: hub-core, auth-failure-admin
- **Assigned To**: builder-run
- **Agent Type**: backend-engineer
- **Parallel**: true (with conformance)
- `src/sanctum_run/` per decision 9; the gateway is the only way a SUT reaches hubs and records every call, including denied and timed-out ones, with `audience_valid`.
- `tools/run_lab.py --sut stub --cases gold/m0 --failure-profile none --seed N --out runs/<id>`; scoring via `sanctum_eval` like `tools/score_m0.py`.
- `tests/test_runner.py`: stub run over `gold/m0` produces schema-valid responses, receipts and traces and scores identically to `tools/score_m0.py`; a test-only fan-out probe SUT (in `tests/helpers/`) calls every released hub through the gateway and yields a trace with one `ok` call per hub; `runs/` is gitignored; SUT never receives gold fields (assert request payload keys).

### 6. EX-09c, isolation, docs

- **Task ID**: integration
- **Depends On**: conformance, runner
- **Assigned To**: builder-auth
- **Agent Type**: backend-engineer
- **Parallel**: false
- `tests/test_ex09c.py`: token service unavailable leads to no hub data returned, every attempted call observed as `denied`, and the probe SUT's response status not `sufficient`; missing token and caller-token passthrough are denied with `audience_valid: false` in the trace.
- Scenario register: EX-09c set to `implemented-and-tested` with note "auth half; registry half at M3"; relax `test_states_valid_and_nothing_claimed_as_run` to allow rows whose milestone is already reached (M0 to M2), keeping the M0 guarantee for later rows.
- `tests/test_isolation_static.py`: add `sanctum_hubs` (forbid `sanctum_eval`, `sanctum_world`, `sanctum_stub`, `sanctum_run`) and `sanctum_run` (forbid `sanctum_world` internals except none needed); forbidden literals for hubs include `private`, `world.yaml`, `gold/`.
- README: layout, M2 commands, exit table; `docs/milestones.md` unchanged; discrepancy register entries (capabilities extension, mcp pin).

### 7. Final validation

- **Task ID**: validate-all
- **Depends On**: foundation, hub-core, auth-failure-admin, conformance, runner, integration
- **Assigned To**: validator
- **Agent Type**: quality-engineer
- **Parallel**: false
- Run all validation commands; verify each acceptance criterion with evidence.
- Independently probe: search restricted canaries as every principal; compare error bodies for restricted vs unknown ids; try FTS syntax injection (`"`, `*`, `NEAR`, `OR`) in queries; present a caller token to a hub; confirm hubs open no files outside their hub dir (e.g. patch `open`/inspect loader).
- Operate in validation mode: inspect and report only, do not modify files.

### 8. Codex review (lead)

- **Task ID**: codex-review
- **Depends On**: validate-all
- **Assigned To**: team lead
- **Agent Type**: n/a
- **Parallel**: false
- One `codex exec -s read-only` review of the uncommitted M2 diff with this plan as context; route findings to the owning builder; commit M2 after fixes.

## Acceptance Criteria

- `mcp` pinned; full suite passes under the pinned uv environment, including the 120 prior tests.
- Every hub serves its §6.1 tools over MCP (in-memory and stdio) from `build/world/hubs/<hub>/` only.
- Conformance suite green for all 5 hubs, covering scope isolation, restricted absence in results/lists/counts/errors, version reads as declared, honest miss, determinism, failure knobs, capabilities validity.
- Token service: passthrough, wrong audience, expired, tampered, revoked and missing tokens are all denied.
- Failure profiles reproducible by seed; measured rates within tolerance.
- Admin mutations take effect on the next call and emit leak-free change-feed events.
- `tools/run_lab.py --sut stub --cases gold/m0` writes manifest, responses, receipts and traces; scores match `tools/score_m0.py`.
- EX-09c passes and is marked in the register; the register test still rejects later-milestone rows claimed as run.
- Isolation tests forbid hub imports of evaluator/world/stub/run packages and references to private build paths.

## Validation Commands

`<u>` below means `uv run --no-project --python 3.12 --with pydantic==2.9.2 --with pyyaml==6.0.2 --with pytest==8.3.3 --with mcp==<pin>`.

- `uv run --no-project --python 3.12 --with pydantic==2.9.2 --with pyyaml==6.0.2 --with pytest==8.3.3 --with mcp==<pin> python -m pytest -q` - full suite
- `PYTHONPATH=src <u> python tools/build_world.py --seed 20260930 --out build/world` then `PYTHONPATH=src <u> python tools/lint_world.py --build build/world` - build and lint clean with new outputs
- `PYTHONPATH=src <u> python -m sanctum_hubs codehub --build build/world` - stdio launch smoke (exits on EOF)
- `PYTHONPATH=src:. <u> python tools/run_lab.py --sut stub --cases gold/m0 --failure-profile none --seed 1 --out runs/m2-smoke` - runner
- `PYTHONPATH=src:. <u> python tools/score_m0.py` - M0 scoring unchanged

## Notes

- All agents run on Opus per project `CLAUDE.md`.
- Hubs are deliberately dumb: no synonyms, no cross-hub knowledge, no LLM. Realism improvements (hybrid DocHub, D-HYBRID) are M4 work.
- The registry half of EX-09c and all routing belong to `sanctum-ref` at M3.
- IncidentHub is conformance-tested now but excluded from the runner's default hub set until M7.
- Codex review is a single pass per user direction; findings are fixed and the fix set is spot-checked, not re-reviewed in full.
