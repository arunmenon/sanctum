# Plan: System One provider layer and the Jev handshake

## Task Description

Make Jev the Tier 1 (System One) model in Sanctum's decision cascade (rules, then System One, then LLM), behind a provider strategy interface with adapters, so the hosted closed model (TypeSafe Jev) and open models (Laya, OpenJevPro, decider-4b, Tev1, CLM, Kev) are interchangeable. Specify the Jev handshake in a dedicated design page cross-referenced from the split HLD set in `docs/intelligence-layer/`. Then integrate it in `sanctum-ref`, calibrate on dev, and rerun the C3/C5 comparisons.

Task type: feature. Complexity: medium-complex.

## Objective

- A design page `docs/intelligence-layer/system-one-providers.md` that specifies the provider interface, the `/v1/systemone` wire protocol, how Sanctum decisions map to protocol primitives, and the handshake nuances (auth, model pinning, batching, deadlines, retries, calibration, data classes, validation, receipts, replay), with cross-references from `hld.md`, `contracts-and-scenarios.md`, `memory-design.md`, `lab-spike.md`, `spike-plan.md`, `README.md` and `section-map.md`.
- `sanctum_ref` decision providers are strategy objects selected by config; one `SystemOneHttpAdapter` serves every `/v1/systemone` backend; capability differences (batching, primitives, max options, usage reporting) are declared per provider, not special-cased in the pipeline.
- The Jev API key never reaches the SUT process: a runner-side System One broker (proxy tool) holds credentials, enforces data-class eligibility and output validation, and records every call in the observed trace.
- C3 and C5 run with Jev on dev (calibrated on dev only), results reported against C2/C4, then one holdout run.

## Problem Statement

M6 showed the local stand-in cannot confidently skip any source, so H1 (does a System One model route better?) is untested. The HLD names Jev but leaves the handshake implicit, and one live call already shows gaps that matter: `jev-latest` resolves to `jev-1.13.0` (calibration is version-specific), a two-question call took ~530 ms against the HLD's 150 ms Round 2 budget, and a `choice` answer's `confidence` (0.24) is not its top probability (0.50). Without a written contract, integrations will silently mis-threshold, leak state to a hosted provider, or break when switching providers.

## Solution Approach

### 1. The cascade and where providers sit

```
decision request (typed, from pipeline rounds)
   │
   ▼
Tier 0  rules            deterministic; answers or abstains
   │ abstain
   ▼
Tier 1  System One       ProviderStrategy.decide(batch) → calibrated p per decision
   │ in uncertain band / unavailable
   ▼
Tier 2  LLM escalation   budgeted; optional; may be off
   │
   ▼
safe default             e.g. D2 uncertain or unavailable → keep source (never drop)
```

### 2. Provider strategy interface (sanctum_ref)

```python
class SystemOneProvider(Protocol):
    name: str                        # "typesafe-jev", "laya", "openjevpro", "standin", ...
    capabilities: ProviderCapabilities  # primitives, max_options, max_questions_per_call,
                                     # batching, reports_usage, data_classes_allowed, hosted
    def decide(self, batch: DecisionBatch, deadline_ms: int) -> list[DecisionResult]: ...
```

Adapters:
- `SystemOneHttpAdapter`: any `/v1/systemone` backend (TypeSafe Jev natively; Laya via `laya-serve`; OpenJevPro, decider, Tev1, CLM, Kev via shims). Config supplies base URL, model id, credential reference and capabilities. Splits batches when a backend lacks batching; maps `score` to `choice` when a backend lacks it.
- `StandinProvider`: existing local TF-IDF + logistic (kept as the no-network control).
- `LLMEscalationProvider`: Tier 2 interface only in this plan (not wired to a model; TODO until an LLM budget is decided).
- Providers are declared in `configs/system_one_providers.yaml`; arms pick one by name (matrix switch `decision_provider: named` plus `provider: <name>`).
- First implementation scope: D2 live with `typesafe-jev` and the stand-in; a local protocol server for deterministic adapter tests; D1 and D3 documented as later shadow experiments (measured separately from D2 if ever run, since shadow calls add cost and exposure); D4, D6 and memory proposal ranking as future design only.

### 3. Mapping Sanctum decisions to protocol primitives

| Decision (HLD §6.4) | Primitive | Question key | Notes |
|---|---|---|---|
| D2 source usefulness | `noul` per candidate source | `d2:<source_id>` | one call, all optional candidates batched; `noul` = P(source returns necessary evidence) |
| D1 intent (multi-label) | `noul` per label | `d1:<label>` | challenger to rules only |
| D3 ambiguity | `noul` | `d3` | query only |
| D4 relevance (later) | `score` or `noul` per chunk | `d4:<unit>` | out of scope for the first integration |
| D5 exact duplicate | none | | exact hash only; no model |
| D6 possible conflict (later) | `noul` per bounded pair | `d6:<pair>` | out of scope for the first integration |
| Route preference (optional) | `choice` over sources | `route` | diagnostic only; bands use per-source `noul`, never `choice.confidence` |

### 4. Handshake nuances the design page must pin down

1. **Auth:** `Authorization: Bearer <key>`; key from a secret store or env on the broker side only; never in the SUT process, receipts, logs or manifests.
2. **Model pinning:** request an exact version where the provider allows it; always record the resolved `model` from the response (`jev-latest` → `jev-1.13.0`); calibration parameters are keyed by provider + resolved model version and are invalid after a version change.
3. **Request shape:** `{state, model, questions}`; `state` is a minimal, sanitized projection (query, caller's allowed source ids, pinned descriptors); questions carry `type`, `instructions`, `criteria` (choice/score).
4. **Response shape and semantics:** `answers[qid]` with `noul` (probability true), or `choice` + `probabilities` + `confidence`, or `score`; `usage` may be null for open backends. Bands use calibrated probabilities; `confidence` is recorded but not used for thresholds until its definition is confirmed with TypeSafe.
5. **Batching and limits:** a round has a total-call limit and one shared deadline across all batches; per-provider `max_questions_per_call` and `max_options`; split and merge when exceeded. Converting `score` to `choice` (or the reverse) is never automatic: it needs an explicit, tested mapping declared for that provider.
6. **Deadline and retries:** the call inherits the round's remaining budget; at most one retry and only if time remains (the benchmark client's 5-retry exponential backoff is wrong for the request path); timeout or error → `status: unavailable`, safe default, `decision_layer_unavailable` in the response.
7. **Latency is measured, not gated (owner decision).** The lab runs locally against a hosted endpoint, so elapsed time mostly reflects the network and is not representative of a deployment next to the model. Two run profiles: *strict deadline* (the HLD budget, records timeout frequency and fallback overhead) and *relaxed research deadline* (measures prediction quality with enough time). Elapsed time always includes broker, network, validation, batching and retries. Quality results from the relaxed profile are reported as quality results; they are not evidence about the fast path, and latency does not decide whether Jev is adopted in this spike. p50/p95 are reported per profile.
8. **Output validation:** only question ids that were asked; `choice` must be an offered option; probabilities in [0,1]; anything else → treated as unavailable for that decision, never partially trusted.
9. **Data classes:** provider eligibility follows the highest data class in the full state (HLD §14.1); hosted Jev allowed for synthetic lab data (recorded owner decision), real data pending Q6/Q13; restricted names and other-principal data never enter `state`.
10. **Observability and replay:** receipts carry provider, resolved model version, question ids, calibrated p, raw p, latency, usage and a request hash. Model calls are recorded as `model_call` observations, separate from knowledge-source calls, so they never inflate source counts or count as evidence-bearing retrieval. The broker stores request/response pairs (credentials excluded) for replaying the provider's answers; this replays the decision layer only, not the whole Sanctum response. Retention: run directory lifetime, synthetic data only; a retention rule is required before any real data.
11. **Calibration:** fitted on dev only, with calibration fitting and band (threshold) selection separated by cross-validation over dev splits. A calibration is bound to provider, resolved model version, question template and rubric text, descriptor and memory release, and decoding settings; a change to any of these invalidates it. With no matching calibration the provider runs shadow-only (answers logged, candidates preserved). Configuration is frozen before the acceptance run. Live calibration has a total call and spend cap, retries included, recorded in the fit provenance.
12. **Provider swap:** switching provider or model version requires recalibration and a rerun of the comparison; the pairing check treats provider and model version as recorded effective inputs. A backend is advertised as supported only after it passes the adapter conformance checks against the protocol; until then it is experimental.
13. **What the model can and cannot lose.** Must-consult sources are always retained. Uncertain or failed predictions preserve the candidate. Confident skips remain fallible: an optional source may hold the only necessary evidence, and a confidently wrong prediction can skip it. H1 therefore measures harmful omissions directly, and source-call savings are accepted only within an agreed evidence-quality tolerance (D-MARGIN).

14. **Batching strategy:** one call per decision round, questions grouped per request only (never across callers), split only on provider limits with one shared deadline and a per-round total-call limit; the `state` is sent once per call so per-question cost falls with batch size; a cache keyed on the full calibration binding (provider, resolved model, template, descriptor release, query, source id) reuses identical answers across arms and reruns at temperature 0. Rounds 1 and 2 may merge into one call once D1/D3 shadow exists (both need only query plus policy output). Round 3 pairs (D6) batch per request, future.
15. **Batch measurement (once, relaxed profile):** latency and usage against batch size 1, 2, 5, 10, 20 questions per provider, cold and warm; reported as measurements, used to set `max_questions_per_call` and to size the cache.
16. **Local Laya on CPU (Unsloth Decision API, `http://localhost:8888/v1/systemone`)** as a provider arm `laya-local`: same adapter, no key, model and runtime version pinned and recorded. Two safeguards: Laya and Jev compute `confidence` differently (bands use calibrated `noul` only, calibration per provider, never transferred); the Laya runtime is reported to truncate oversized inputs silently, so the broker enforces declared context and option budgets and refuses over-limit payloads rather than trusting a truncated answer. Claims about Unsloth/Laya (RAM, latency, checkpoints) come from vendor docs and are not measured here until the run.

### 5. Isolation: System One broker in the runner

The SUT runs out of process with no secrets. The gateway proxy gains a `system_one.decide` tool using the existing per-request binding. The broker (runner side) independently binds each call to: the active request and caller; the candidate sources the caller is allowed to use and their descriptors (taken from the gateway's own view, not from the SUT's claim); the data-class declaration from trusted run configuration (a caller saying its state is synthetic is not enough); and the allowed provider, model, payload size, call count and deadline. It builds the `/v1/systemone` request, calls the provider with the key from `.env`, validates output, records a `model_call` observation and returns results. This keeps the key out of the SUT and makes every model call visible to the evaluator.

## Relevant Files

- `docs/intelligence-layer/hld.md` (§6.2 single Jev call, §6.4 catalog, §6.5 escalation, §6.6 decision result, §6.7 calibration, §14.1 data classes, §14.2 latency), `contracts-and-scenarios.md` (Ex. 1, Ex. 9), `memory-design.md` (layer 5, M11), `lab-spike.md` (E1, C3/C5), `spike-plan.md`, `README.md`, `section-map.md`.
- `src/sanctum_contracts/decision.py` (DecisionRequest/DecisionResult; frozen, extend only via discrepancy register if needed).
- `src/sanctum_ref/decision.py` (current rules/standin/jev-refusal), `src/sanctum_ref/pipeline.py`, `configs/d2_standin.yaml`, `tools/fit_d2_standin.py`.
- `src/sanctum_run/proxy.py`, `gateway.py`, `process_sut.py` (broker tool), `configs/matrix.yaml`, `src/sanctum_eval/provenance.py`.
- `/Users/arunmenon/projects/jev-benchmarks/jevbench/client.py`, `servers/openjev_shim.py` (reference wire protocol and open-backend shims; read only).
- `.env` (gitignored; holds `TYPESAFE_API_KEY`).

### New Files

- `docs/intelligence-layer/system-one-providers.md`
- `configs/system_one_providers.yaml` (typesafe-jev, laya-local, standin, local-test), `configs/calibration/<provider>@<model>.yaml`
- `tools/measure_system_one_batches.py` (batch-size measurement, once per provider)
- `src/sanctum_ref/providers/{__init__,interface,http_systemone,standin,llm_escalation}.py`
- `src/sanctum_run/system_one_broker.py`
- `tools/fit_system_one.py`
- `tests/test_system_one_providers.py`, `tests/test_system_one_broker.py`, `tests/helpers/systemone_server.py` (local protocol server for tests only)

## Implementation Phases

### Phase 1: Design page (first, reviewed before code)
Write `system-one-providers.md` from sections 1-5 above plus measured values; add cross-references; record the owner decision (Jev allowed on synthetic lab data) in `docs/decisions.md`.

### Phase 2: Providers and broker
Provider interface and adapters, config registry, runner-side broker tool with validation, data-class check, trace recording, replay store; tests against a local `/v1/systemone` test server (no live calls in CI).

### Phase 3: Calibration and runs
Fit Jev calibration on dev (live calls, cost logged), run C3/C5 with `typesafe-jev` on dev and scenarios, compare with C2/C4 and the stand-in, measure latency, then one holdout run tagged `M6-jev`; update reports, milestones, register.

## Team Orchestration

- Lead writes nothing in code; delegates as below. Cost-conscious: two builders reused from the lab team.

### Team Members

- Specialist: **m3-ref** (resume). Role: design page, provider interface and adapters, pipeline wiring, calibration fit. Agent type: backend-engineer.
- Specialist: **m3-data** (resume). Role: runner-side broker, trace/provenance fields, evaluator/report updates, holdout run. Agent type: backend-engineer.
- Validator: none separate (cost); lead runs the suite and live smoke checks.

## Step by Step Tasks

### 1. Design page and cross-references
- **Task ID**: design-page
- **Depends On**: none
- **Assigned To**: m3-ref
- **Parallel**: false
- Write the page; cross-link; decisions.md entry; lead reviews before Phase 2.

### 2. Provider interface and HTTP adapter
- **Task ID**: providers
- **Depends On**: design-page
- **Assigned To**: m3-ref
- **Parallel**: true (with broker)

### 3. System One broker in the runner
- **Task ID**: broker
- **Depends On**: design-page
- **Assigned To**: m3-data
- **Parallel**: true (with providers)

### 4. Calibration and runs
- **Task ID**: calibrate-run
- **Depends On**: providers, broker
- **Assigned To**: m3-ref (fit, SUT runs), m3-data (reports, holdout)
- **Parallel**: false

## Acceptance Criteria

- Design page covers all twelve handshake points with measured values and is linked from every relevant page.
- Switching `provider:` between `typesafe-jev`, `standin` and a local test server needs no pipeline code change; tests prove it.
- The API key is absent from the SUT environment, repo, receipts, traces, manifests and logs (test scans for the key prefix).
- Timeout, error, invalid output and data-class refusal each yield `unavailable` plus the safe default; D2 never drops a source on uncertainty.
- Receipts record provider, resolved model version, raw and calibrated p, latency, usage.
- Dev and holdout reports include C3/C5 with Jev; results reported whichever direction they go; harmful-omission rate and sources-called are the primary H1 metrics, latency is reported per profile but is not a gate.
- Acceptance blockers carried from M6: the residual status overclaims on C4/C5 under failure (dev-018, dev-052) must be fixed before any favourable Jev result is accepted; a Jev score cannot override a known failure to report missing mandatory evidence.
- Holdout exposure: the M5 holdout has been run and rerun once (forced) and its results were seen by the lead; for the Jev claim, use a fresh acceptance set of ~20 cases authored by the holdout agent (never seen by the lead or SUT team before the run) in addition to the existing holdout.

## Validation Commands

- Full pinned suite (plus `--with httpx`).
- `tools/run_lab.py --sut ref --config C3 --decision-provider typesafe-jev ...` on dev; report vs C2.
- Secret scan: `git grep -n "apikey_"` returns nothing; run dirs scanned likewise.

## Notes

- Live Jev calls cost money; calibration uses dev only (60 questions x ~3 optional sources x a few rounds); every call is logged with usage.
- Open models: Laya runs on CPU through Unsloth's Decision API (owner-supplied research, unverified here), so a CPU-first Laya arm is in scope; GPU hosting (jev-benchmarks vast.ai scripts) only if CPU measurements show it is needed. Running the Laya arm needs the owner to install Unsloth and enable Settings > API > Decision API > Serve requests (CPU); until then the local protocol test server covers the adapter.
- The key was shared in chat. Codex recommends rotating it before further live use; the owner has chosen to proceed with the current key for the lab and rotate afterwards. Secret verification is not only a prefix scan: the SUT environment is scrubbed by construction, and a test asserts that no environment variable or output file contains the configured key value.
