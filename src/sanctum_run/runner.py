"""Run a SUT over gold cases against the simulated hubs and score it with `sanctum_eval`.

Output directory: `manifest.json`, `responses.jsonl`, `receipts.jsonl`, `traces.jsonl`
(one `ObservedTrace` per case), `scores.jsonl`, `anomalies.jsonl` (gateway integrity
findings; any entry fails the run's integrity check).
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from contextlib import AsyncExitStack
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import anyio
import yaml

from sanctum_contracts import RetrieveRequest
from sanctum_eval import METRICS_REVISION
from sanctum_eval.alignment import apply_alignment
from sanctum_eval.gold import GoldCase
from sanctum_eval.load import load_gold
from sanctum_eval.metrics import CaseScore, score_case
from sanctum_hubs.failure import load_failure_injector
from sanctum_hubs.interfaces import FailureInjector, NoFailures
from sanctum_hubs.tokens import TokenService

from .gateway import HubGateway, TokenMode, released_hub_ids
from .process_sut import SUTTimeout
from .sut import SUTContext, SystemUnderTest
from .system_one_broker import DEFAULT_DESCRIPTORS as DEFAULT_SYSTEM_ONE_DESCRIPTORS
from .system_one_broker import DEFAULT_PROVIDERS as DEFAULT_SYSTEM_ONE_PROVIDERS
from .system_one_broker import SystemOneBroker, load_descriptors, load_provider, load_secret

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_HUBS_CONFIG = ROOT / "configs" / "hubs.yaml"
DEFAULT_FAILURE_PROFILES = ROOT / "configs" / "failure_profiles.yaml"
DEFAULT_WORLD_BUILD = ROOT / "build" / "world"
NO_FAILURE_PROFILE = "none"
DEFAULT_M0_PRINCIPAL_ALIASES = ROOT / "configs" / "m0_principal_aliases.yaml"


def load_principal_aliases(path: Path) -> dict[str, str]:
    """Gold principal -> world principal. Only for frozen gold sets that predate the world."""
    document = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return {str(gold): str(world) for gold, world in (document.get("aliases") or {}).items()}


@dataclass(frozen=True)
class RunConfig:
    cases_dir: Path
    out_dir: Path
    seed: int
    sut_name: str
    config_id: str = "stub"
    failure_profile: str = NO_FAILURE_PROFILE
    world_build_dir: Path = DEFAULT_WORLD_BUILD
    hubs_config_path: Path = DEFAULT_HUBS_CONFIG
    failure_profiles_path: Path = DEFAULT_FAILURE_PROFILES
    token_secret: str = "lab-run-secret"
    include_held_back: bool = False
    time_scale: Optional[float] = None
    token_mode: TokenMode = TokenMode.EXCHANGE
    # gold principal -> world principal, for gold sets written before the world's identities
    principal_aliases: Optional[dict[str, str]] = None
    # SUT memory entity id -> world entity ref (`alignment.load_alignment`); scoring only
    entity_alignment: Optional[dict[str, str]] = None
    # System One (runner-side broker): provider name from configs/system_one_providers.yaml, the
    # latency profile (strict | relaxed), and the data class of this run's data (trusted, not the SUT's)
    budget_tokens: Optional[int] = None      # override every case's response budget (budget stress)
    system_one_provider: Optional[str] = None
    system_one_profile: str = "strict"
    data_class: str = "synthetic"
    system_one_providers_path: Path = DEFAULT_SYSTEM_ONE_PROVIDERS
    system_one_descriptors_path: Path = DEFAULT_SYSTEM_ONE_DESCRIPTORS    # pinned D2 descriptors


@dataclass
class RunResult:
    out_dir: Path
    manifest: dict
    scores: list[CaseScore]
    anomalies: list[dict]

    @property
    def integrity_ok(self) -> bool:
        return not self.anomalies


def _git(*arguments: str) -> Optional[bytes]:
    try:
        return subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None


def git_state() -> dict:
    """Commit, whether tracked files differ from it, and a hash of that diff."""
    commit = _git("rev-parse", "HEAD")
    diff = _git("diff", "HEAD", "--binary")
    return {"git_commit": commit.decode().strip() if commit else "unknown",
            "git_dirty": bool(diff) if diff is not None else None,
            "git_diff_sha256": hashlib.sha256(diff).hexdigest() if diff else None}


def world_manifest_hash(world_build_dir: Path) -> str:
    return hashlib.sha256((Path(world_build_dir) / "manifest.json").read_bytes()).hexdigest()


def load_cases(cases_dir: Path) -> list[GoldCase]:
    return [load_gold(path) for path in sorted(Path(cases_dir).glob("*.yaml"))]


def public_request(gold: GoldCase) -> RetrieveRequest:
    """Only the public request crosses to the SUT; principal and gold stay here."""
    return RetrieveRequest.model_validate(gold.request.model_dump())


def _failure_injector(config: RunConfig) -> FailureInjector:
    if config.failure_profile == NO_FAILURE_PROFILE:
        return NoFailures()
    return load_failure_injector(config.failure_profiles_path, config.failure_profile, config.seed,
                                 config.time_scale)


SYSTEM_ONE_ROUNDS_PER_REQUEST = 3     # D2, then a Round 3 decision (D6 or D4), plus slack


def failed_case_score(gold: GoldCase, reason: str) -> CaseScore:
    """A case whose SUT call failed: no response to score, so nothing is credited and the reason
    is a failed gate."""
    return CaseScore(case_id=gold.case_id, recall=0.0 if gold.answerable else None,
                     complete_support=False if gold.answerable else None,
                     harmful_omission=True if gold.answerable else None, silent_omission=True,
                     conflict_witnesses=0.0 if gold.relations else None, false_conflicts=0,
                     ambiguity_handled=False if gold.interpretation_policy.value != "unique" else None,
                     false_ambiguity=None, mandatory={}, status={"all": False}, wrong_entity=[], leaks=[],
                     within_budget=True, receipt_honest=False, precision=None, sources_attempted=0, tokens_used=0,
                     gates_failed=[reason], safe_grounded_success=False)


def _system_one_broker(config: RunConfig, hub_ids: list[str]) -> SystemOneBroker:
    spec, profile = load_provider(config.system_one_provider, config.system_one_profile,
                                  config.system_one_providers_path)
    return SystemOneBroker(spec=spec, profile=profile, data_class=config.data_class, allowed_sources=list(hub_ids),
                           descriptors=load_descriptors(config.system_one_descriptors_path),
                           store_dir=Path(config.out_dir) / "system_one", secret=load_secret(spec.api_key_env))


def _system_one_manifest(config: RunConfig, traces: list[dict]) -> Optional[dict]:
    """Provider, profile, data class and the resolved model versions seen (never the credential)."""
    if config.system_one_provider is None:
        return None
    calls = [call for trace in traces for call in trace.get("model_calls", [])]
    spec, _profile = load_provider(config.system_one_provider, config.system_one_profile,
                                   config.system_one_providers_path)
    return {"provider": spec.name, "requested_model": spec.requested_model(dict(os.environ)),
            "profile": config.system_one_profile,
            "data_class": config.data_class, "resolved_models": sorted({c["model"] for c in calls if c.get("model")}),
            "model_calls": len(calls)}


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


async def run_cases(sut: SystemUnderTest, config: RunConfig) -> RunResult:
    cases = load_cases(config.cases_dir)
    if config.budget_tokens is not None:
        # budget stress (prompt review §4): the same cases at a fixed, predeclared response budget;
        # scoring (budget gate, D4 reorder-only gate) uses the same budget
        cases = [gold.model_copy(update={"request": gold.request.model_copy(
            update={"budget_tokens": config.budget_tokens})}) for gold in cases]
    check_supported = getattr(sut, "check_supported", None)
    if check_supported is not None:
        check_supported([public_request(gold) for gold in cases])
    hub_ids = released_hub_ids(config.hubs_config_path, config.include_held_back)
    token_service = TokenService(config.world_build_dir / "identity" / "principals.json", config.token_secret)
    responses, receipts, traces, scores = [], [], [], []
    aligned_responses, aligned_receipts = [], []
    sut_failures: list[dict] = []
    async with HubGateway(config.world_build_dir, hub_ids, token_service, _failure_injector(config),
                          config.token_mode) as gateway, AsyncExitStack() as sut_stack:
        if config.system_one_provider is not None:
            gateway.system_one = _system_one_broker(config, hub_ids)
            if hasattr(sut, "extra_timeout_seconds"):
                # each request may run a few System One rounds, each up to the profile deadline
                sut.extra_timeout_seconds = SYSTEM_ONE_ROUNDS_PER_REQUEST * gateway.system_one.profile.deadline_ms / 1000.0
        # An out-of-process SUT (`process_sut.ProcessSUT`) starts its process and gateway proxy here.
        open_sut = getattr(sut, "open", None)
        if open_sut is not None:
            await sut_stack.enter_async_context(open_sut(gateway, config.world_build_dir))
        for gold in cases:
            request = public_request(gold)
            principal = (config.principal_aliases or {}).get(gold.principal, gold.principal)
            if principal not in token_service.principals:
                raise ValueError(f"case {gold.case_id}: principal {principal!r} is not in the world build")
            caller_token = token_service.issue_caller_token(principal)
            context = SUTContext(caller_token=caller_token,
                                 gateway=gateway.handle(request.request_id, caller_token))
            started = time.perf_counter()
            try:
                with gateway.sut_call(request.request_id):
                    response, receipt = await sut.retrieve(request, context)
            except SUTTimeout as error:
                # one slow request fails its case, not the run (register row 24)
                gateway.release(context.gateway)
                sut_failures.append({"request_id": request.request_id, "case_id": gold.case_id,
                                     "kind": "sut_timeout", "message": str(error)})
                scores.append(failed_case_score(gold, "sut_timeout"))
                continue
            elapsed_ms = round((time.perf_counter() - started) * 1000.0, 3)
            gateway.release(context.gateway)       # the invocation ends with the case
            trace = gateway.trace(request.request_id).model_copy(update={"elapsed_ms": elapsed_ms})
            responses.append(response.model_dump(mode="json"))
            receipts.append(receipt.model_dump(mode="json"))
            traces.append(trace.model_dump(mode="json"))
            if config.entity_alignment is not None:
                response, receipt = apply_alignment(response, receipt, config.entity_alignment)
                aligned_responses.append(response.model_dump(mode="json"))
                aligned_receipts.append(receipt.model_dump(mode="json"))
            scores.append(score_case(gold, response, receipt, trace))
        anomalies = gateway.anomalies() + list(getattr(sut, "anomalies", lambda: [])())

    out_dir = Path(config.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "world_manifest_sha256": world_manifest_hash(config.world_build_dir),
        "seed": config.seed,
        "config_id": config.config_id,
        "sut": config.sut_name,
        "failure_profile": config.failure_profile,
        **git_state(),
        "integrity": {"ok": not anomalies, "anomalies": len(anomalies)},
        "metrics_revision": METRICS_REVISION,
        "hubs": hub_ids,
        "cases": [gold.case_id for gold in cases],
        "sut_failures": len(sut_failures),
        "budget_tokens": config.budget_tokens,
        "system_one": _system_one_manifest(config, traces),
        "entity_alignment": None if config.entity_alignment is None else {
            "table": "entity_alignment.json", "aligned": len(config.entity_alignment)},
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n",
                                           encoding="utf-8")
    _write_jsonl(out_dir / "responses.jsonl", responses)
    _write_jsonl(out_dir / "receipts.jsonl", receipts)
    _write_jsonl(out_dir / "traces.jsonl", traces)
    _write_jsonl(out_dir / "scores.jsonl", [asdict(score) for score in scores])
    _write_jsonl(out_dir / "anomalies.jsonl", anomalies)
    _write_jsonl(out_dir / "sut_failures.jsonl", sut_failures)
    if config.entity_alignment is not None:
        # raw SUT outputs above stay as emitted; scoring used these aligned copies
        (out_dir / "entity_alignment.json").write_text(
            json.dumps(config.entity_alignment, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        _write_jsonl(out_dir / "responses.aligned.jsonl", aligned_responses)
        _write_jsonl(out_dir / "receipts.aligned.jsonl", aligned_receipts)
    return RunResult(out_dir=out_dir, manifest=manifest, scores=scores, anomalies=anomalies)


def run(sut: SystemUnderTest, config: RunConfig) -> RunResult:
    return anyio.run(run_cases, sut, config)
