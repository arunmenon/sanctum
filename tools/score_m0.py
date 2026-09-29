"""Score the independent stub against the M0 gold cases and print a small report."""
from dataclasses import asdict
from pathlib import Path

from sanctum_contracts import RetrieveRequest
from sanctum_eval import METRICS_REVISION
from sanctum_eval.load import load_gold, load_trace
from sanctum_eval.metrics import score_case
from sanctum_stub.stub import StubSUT

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    sut = StubSUT()
    print(f"SYNTHETIC — NOT PRODUCTION EVIDENCE · metrics {METRICS_REVISION} · SUT=stub\n")
    print(f"{'case':8} {'recall':>6} {'conflict':>8} {'srcs':>4} {'tokens':>6}  gates  safe_success")
    for g in sorted((ROOT / "gold" / "m0").glob("*.yaml")):
        gold = load_gold(g)
        resp, receipt = sut.retrieve(RetrieveRequest.model_validate(gold.request.model_dump()))
        trace = load_trace(ROOT / "tests" / "fixtures" / "m0" / "traces" / f"{gold.request.request_id}.json")
        s = asdict(score_case(gold, resp, receipt, trace))
        fmt = lambda v: "-" if v is None else f"{v:.2f}"
        print(f"{s['case_id']:8} {fmt(s['recall']):>6} {fmt(s['conflict_witnesses']):>8} "
              f"{s['sources_attempted']:>4} {s['tokens_used']:>6}  {','.join(s['gates_failed']) or 'none':5}  "
              f"{s['safe_grounded_success']}")
