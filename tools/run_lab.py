"""Run a SUT over gold cases against the simulated hubs and print a score table."""
import argparse
from dataclasses import asdict
from pathlib import Path

from sanctum_eval import METRICS_REVISION
from sanctum_eval.provenance import effective_configuration, record_effective
from sanctum_run.runner import DEFAULT_WORLD_BUILD, DEFAULT_M0_PRINCIPAL_ALIASES, RunConfig, load_principal_aliases, run
from sanctum_run.process_sut import ProcessSUT, SUTProcessError
from sanctum_run.sut import MissingCannedResponse, StubSUTAdapter, load_call_plan

ROOT = Path(__file__).resolve().parents[1]
M0_TRACES = ROOT / "tests" / "fixtures" / "m0" / "traces"


MEMORY_CONFIGS = ("C4", "C4a-equivalent", "C4a-label-only", "C5")
REF_CONFIGS = ("C1-naive", "C1-fair", "C2", "C3", "C4", "C4a-equivalent", "C4a-label-only", "C5")


def make_sut(name: str, config_id: str = "stub", registry=None, decision_provider=None, memory_release=None,
             round3: str = "none", round3_provider=None):
    """`stub` runs in process (trusted, canned); `ref` runs out of process behind the gateway proxy."""
    if name == "stub":
        return StubSUTAdapter(load_call_plan(M0_TRACES))
    if name == "ref":
        if config_id not in REF_CONFIGS:
            raise SystemExit(f"sanctum_ref implements {', '.join(REF_CONFIGS)}; got --config {config_id!r}")
        arguments = ["--config", config_id]
        if registry is not None:
            arguments += ["--registry", str(Path(registry).resolve())]
        if decision_provider is not None:
            arguments += ["--decision-provider", decision_provider]
        if memory_release is not None:
            arguments += ["--memory-release", memory_release]
        if round3 != "none":
            arguments += ["--round3", round3, "--round3-provider", round3_provider or ""]
        return ProcessSUT(arguments)
    raise SystemExit(f"unknown SUT {name!r}")


def principal_aliases_for(cases_dir: Path, aliases_path):
    """gold/m0 predates the world's principals; every later gold set uses them directly."""
    if aliases_path is not None:
        return load_principal_aliases(aliases_path)
    if cases_dir.resolve() == (ROOT / "gold" / "m0").resolve():
        return load_principal_aliases(DEFAULT_M0_PRINCIPAL_ALIASES)
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sut", default="stub", choices=["stub", "ref"])
    parser.add_argument("--cases", type=Path, default=ROOT / "gold" / "m0")
    parser.add_argument("--failure-profile", default="none")
    parser.add_argument("--seed", type=int, default=20260930)
    parser.add_argument("--config", "--config-id", dest="config_id", default=None,
                        help="arm id (ref: C1-naive, C1-fair, C2); defaults to 'stub' for the stub")
    parser.add_argument("--registry", type=Path, default=None, help="owner manifests (ref only)")
    parser.add_argument("--decision-provider", default=None,
                        help="D2 provider for C3/C5 (configs/system_one_providers.yaml names, rules, standin; default: the arm's provider)")
    parser.add_argument("--world-build", type=Path, default=DEFAULT_WORLD_BUILD)
    parser.add_argument("--principal-aliases", type=Path, default=None,
                        help="alias YAML (default: configs/m0_principal_aliases.yaml for gold/m0 only)")
    parser.add_argument("--memory-release", default=None,
                        help="memory release for memory arms (default: owners/memory_seed/ACTIVE, r1); r2 adds IncidentHub")
    parser.add_argument("--round3", default="none", choices=["none", "d6", "d4"],
                        help="Round 3 System One decision for the ref SUT (design page 14)")
    parser.add_argument("--round3-provider", default=None, help="System One provider for --round3 (also pass --system-one-provider)")
    parser.add_argument("--release-hub", action="append", default=[], choices=["incidenthub"],
                        help="release a held-back hub for this run (default: configs/hubs.yaml held_back)")
    parser.add_argument("--system-one-provider", default=None,
                        help="runner-side System One provider (configs/system_one_providers.yaml)")
    parser.add_argument("--system-one-profile", default="strict", choices=["strict", "relaxed"])
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.config_id = arguments.config_id or ("C2" if arguments.sut == "ref" else "stub")
    sut = make_sut(arguments.sut, arguments.config_id, arguments.registry, arguments.decision_provider,
                   arguments.memory_release, arguments.round3, arguments.round3_provider)
    alignment = None
    if arguments.sut == "ref" and arguments.config_id in MEMORY_CONFIGS:
        # evaluator side: map the SUT's memory entity refs to world refs before scoring
        from sanctum_eval.alignment import load_alignment
        from sanctum_world.schema import load_world
        active = arguments.memory_release or (ROOT / "owners" / "memory_seed" / "ACTIVE").read_text().strip()
        alignment, _unaligned = load_alignment(ROOT / "owners" / "memory_seed" / active / "entities.yaml",
                                               load_world(ROOT / "world" / "world.yaml"), arguments.world_build)
    try:
        result = run(sut, RunConfig(
        cases_dir=arguments.cases, out_dir=arguments.out, seed=arguments.seed, sut_name=arguments.sut,
        config_id=arguments.config_id + ("" if arguments.round3 == "none" else f"+{arguments.round3.upper()}"),
        failure_profile=arguments.failure_profile,
        world_build_dir=arguments.world_build, include_held_back=bool(arguments.release_hub),
        principal_aliases=principal_aliases_for(arguments.cases, arguments.principal_aliases),
        entity_alignment=alignment, system_one_provider=arguments.system_one_provider,
        system_one_profile=arguments.system_one_profile))
    except (MissingCannedResponse, SUTProcessError) as error:
        raise SystemExit(f"run_lab: {error}") from None
    memory_release = None
    if arguments.sut == "ref" and arguments.config_id in MEMORY_CONFIGS:
        memory_release = arguments.memory_release or (ROOT / "owners" / "memory_seed" / "ACTIVE").read_text().strip()
    decision_provider = None
    if arguments.sut == "ref" and arguments.config_id in ("C3", "C5"):
        decision_provider = arguments.decision_provider or "standin"
    record_effective(result.out_dir, effective_configuration(
        sut=arguments.sut, config_id=arguments.config_id, hubs=result.manifest["hubs"], cases_dir=arguments.cases,
        registry=(arguments.registry or ROOT / "owners" / "manifests") if arguments.sut == "ref" else None,
        memory_release=memory_release, memory_seed=ROOT / "owners" / "memory_seed",
        decision_provider=decision_provider, decision_params=ROOT / "configs" / "d2_standin.yaml"))
    print(f"SYNTHETIC, NOT PRODUCTION EVIDENCE · metrics {METRICS_REVISION} · SUT={arguments.sut} "
          f"· profile={arguments.failure_profile} · out={result.out_dir}\n")
    print(f"{'case':8} {'recall':>6} {'conflict':>8} {'srcs':>4} {'tokens':>6}  gates  safe_success")
    for score in result.scores:
        s = asdict(score)
        fmt = lambda v: "-" if v is None else f"{v:.2f}"
        print(f"{s['case_id']:8} {fmt(s['recall']):>6} {fmt(s['conflict_witnesses']):>8} "
              f"{s['sources_attempted']:>4} {s['tokens_used']:>6}  {','.join(s['gates_failed']) or 'none':5}  "
              f"{s['safe_grounded_success']}")
    if not result.integrity_ok:
        raise SystemExit(f"run_lab: integrity check failed, {len(result.anomalies)} gateway anomalies "
                         f"(see {result.out_dir / 'anomalies.jsonl'})")
