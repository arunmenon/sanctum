"""Run a SUT over gold cases against the simulated hubs and print a score table."""
import argparse
from dataclasses import asdict
from pathlib import Path

from sanctum_eval import METRICS_REVISION
from sanctum_run.runner import DEFAULT_WORLD_BUILD, DEFAULT_M0_PRINCIPAL_ALIASES, RunConfig, load_principal_aliases, run
from sanctum_run.process_sut import ProcessSUT, SUTProcessError
from sanctum_run.sut import MissingCannedResponse, StubSUTAdapter, load_call_plan

ROOT = Path(__file__).resolve().parents[1]
M0_TRACES = ROOT / "tests" / "fixtures" / "m0" / "traces"


MEMORY_CONFIGS = ("C4", "C4a-equivalent", "C4a-label-only")
REF_CONFIGS = ("C1-naive", "C1-fair", "C2", "C4", "C4a-equivalent", "C4a-label-only")


def make_sut(name: str, config_id: str = "stub", registry=None):
    """`stub` runs in process (trusted, canned); `ref` runs out of process behind the gateway proxy."""
    if name == "stub":
        return StubSUTAdapter(load_call_plan(M0_TRACES))
    if name == "ref":
        if config_id not in REF_CONFIGS:
            raise SystemExit(f"sanctum_ref implements {', '.join(REF_CONFIGS)}; got --config {config_id!r}")
        arguments = ["--config", config_id]
        if registry is not None:
            arguments += ["--registry", str(Path(registry).resolve())]
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
    parser.add_argument("--world-build", type=Path, default=DEFAULT_WORLD_BUILD)
    parser.add_argument("--principal-aliases", type=Path, default=None,
                        help="alias YAML (default: configs/m0_principal_aliases.yaml for gold/m0 only)")
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    arguments.config_id = arguments.config_id or ("C2" if arguments.sut == "ref" else "stub")
    sut = make_sut(arguments.sut, arguments.config_id, arguments.registry)
    alignment = None
    if arguments.sut == "ref" and arguments.config_id in MEMORY_CONFIGS:
        # evaluator side: map the SUT's memory entity refs to world refs before scoring
        from sanctum_eval.alignment import load_alignment
        from sanctum_world.schema import load_world
        alignment, _unaligned = load_alignment(ROOT / "owners" / "memory_seed" / "r1" / "entities.yaml",
                                               load_world(ROOT / "world" / "world.yaml"), arguments.world_build)
    try:
        result = run(sut, RunConfig(
        cases_dir=arguments.cases, out_dir=arguments.out, seed=arguments.seed, sut_name=arguments.sut,
        config_id=arguments.config_id, failure_profile=arguments.failure_profile,
        world_build_dir=arguments.world_build, principal_aliases=principal_aliases_for(arguments.cases, arguments.principal_aliases),
        entity_alignment=alignment))
    except (MissingCannedResponse, SUTProcessError) as error:
        raise SystemExit(f"run_lab: {error}") from None
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
