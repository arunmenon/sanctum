"""Offline D4 order report (prompt review §4): no live calls.

For each dev run with D4 decisions in its receipts (rows 8-9 of the prompt campaign), compare the
rules order of the packed evidence with the counterfactual D4 order (packed units sorted by the
D4 probability, calibrated p when present else p_raw, or the score diagnostic's expected level;
stable on ties; units without a D4 answer
keep their rules position relative to each other and follow the scored ones). Reports
coverage@K and first-supporting-unit rank for both orders, with denominators.

Usage: python tools/d4_order_report.py --run <dir> [--run <dir> ...] --cases gold/dev
       [--k 1000 --k 2000 --k 4000] --out docs/reports/system-one-d4-order.md
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sanctum_contracts import EvidenceResponse  # noqa: E402
from sanctum_eval.load import load_gold  # noqa: E402
from sanctum_eval.order_metrics import DEFAULT_K, first_support_rank, prefix_coverage  # noqa: E402
from tools.report import CAVEAT  # noqa: E402


def d4_scores(receipt: dict) -> dict[str, float]:
    """evidence id -> D4 probability from the receipt's per-unit decisions (answered only)."""
    scores = {}
    for decision in receipt.get("decisions", []):
        value = decision.get("value")
        if not isinstance(value, dict) or not str(value.get("item", "")).startswith("d4:"):
            continue
        p = value.get("p") if value.get("p") is not None else value.get("p_raw")
        if p is None:                    # score-primitive diagnostic: order by the expected level
            answer = (value.get("answers") or {}).get(str(value["item"])) or {}
            p = answer.get("score")
        if isinstance(p, (int, float)) and not isinstance(p, bool):
            scores[str(value["item"])[3:]] = float(p)
    return scores


def d4_order(response: EvidenceResponse, scores: dict[str, float]) -> EvidenceResponse:
    indexed = list(enumerate(response.evidence))
    scored = sorted((item for item in indexed if item[1].evidence_id in scores),
                    key=lambda item: (-scores[item[1].evidence_id], item[0]))
    rest = [item for item in indexed if item[1].evidence_id not in scores]
    return response.model_copy(update={"evidence": [unit for _, unit in scored + rest]})


def _load(run_dir: Path) -> tuple[dict, dict]:
    responses = {json.loads(l)["request_id"]: json.loads(l)
                 for l in (Path(run_dir) / "responses.jsonl").read_text().splitlines() if l.strip()}
    receipts = {json.loads(l)["request_id"]: json.loads(l)
                for l in (Path(run_dir) / "receipts.jsonl").read_text().splitlines() if l.strip()}
    return responses, receipts


def run_order_metrics(run_dirs, cases_dir: Path, ks=DEFAULT_K) -> dict:
    """One row from one run dir, or from several dirs of the same row that scored disjoint cases
    (a partial run plus its completion): per request, the dir whose receipt has D4 scores is used.
    The rules order must agree wherever dirs overlap; disagreements are counted, not hidden."""
    dirs = [Path(d) for d in (run_dirs if isinstance(run_dirs, (list, tuple)) else [run_dirs])]
    golds = {g.request.request_id: g for g in (load_gold(p) for p in sorted(Path(cases_dir).glob("*.yaml")))}
    chosen: dict[str, tuple[dict, dict]] = {}
    order_mismatches = 0
    for run_dir in dirs:
        responses, receipts = _load(run_dir)
        for request_id, response in responses.items():
            receipt = receipts.get(request_id, {})
            if request_id in chosen:
                previous = chosen[request_id][0]
                if [u["evidence_id"] for u in previous["evidence"]] != [u["evidence_id"] for u in response["evidence"]]:
                    order_mismatches += 1
                if d4_scores(chosen[request_id][1]) or not d4_scores(receipt):
                    continue
            chosen[request_id] = (response, receipt)
    result = {order: {"coverage": {k: [] for k in ks}, "ranks": [], "no_support": 0} for order in ("rules", "d4")}
    scored_requests = 0
    for request_id, (raw, receipt) in sorted(chosen.items()):
        gold = golds.get(request_id)
        if gold is None:
            continue
        response = EvidenceResponse.model_validate(raw)
        scores = d4_scores(receipt)
        scored_requests += bool(scores)
        for order, resp in (("rules", response), ("d4", d4_order(response, scores))):
            for k in ks:
                value = prefix_coverage(gold, resp, k)
                if value is not None:
                    result[order]["coverage"][k].append(value)
            rank = first_support_rank(gold, resp)
            if rank is None:
                result[order]["no_support"] += int(gold.answerable)
            else:
                result[order]["ranks"].append(rank)
    result["scored_requests"] = scored_requests
    result["scored_units"] = sum(len(d4_scores(receipt)) for _, receipt in chosen.values())
    result["order_mismatches"] = order_mismatches
    return result


def _mean(values: list) -> Optional[float]:
    return sum(values) / len(values) if values else None


def render(runs: dict[str, dict], ks) -> str:
    lines = ["# System One D4: order-sensitive measurement (offline)", "", f"> {CAVEAT}", "",
             "Computed from saved receipts only, no live calls. Rules order is the packed evidence as returned; "
             "D4 order sorts the same packed units by the D4 probability (the only change D4 may make). Coverage@K "
             "is over answerable cases (n); first-support rank is over cases with any supporting unit.", "",
             "| run | order | scored requests (units) | " + " | ".join(f"coverage@{k}" for k in ks)
             + " | first support rank (mean, n) | answerable without support |",
             "|---|---|---|" + "---|" * len(ks) + "---|---|"]
    for name, metrics in runs.items():
        for order in ("rules", "d4"):
            m = metrics[order]
            cells = []
            for k in ks:
                mean = _mean(m["coverage"][k])
                cells.append("-" if mean is None else f"{mean:.3f} (n={len(m['coverage'][k])})")
            rank = _mean(m["ranks"])
            rank_cell = "-" if rank is None else f"{rank:.2f} (n={len(m['ranks'])})"
            lines.append(f"| {name} | {order} | {metrics['scored_requests']} ({metrics.get('scored_units', '-')}) | " + " | ".join(cells)
                         + f" | {rank_cell} | {m['no_support']} |")
    return "\n".join(lines + ["", f"> {CAVEAT}", ""])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", action="append", required=True, help="run dir, or comma-separated dirs of one row")
    parser.add_argument("--cases", type=Path, default=ROOT / "gold" / "dev")
    parser.add_argument("--k", type=int, action="append", default=None)
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "reports" / "system-one-d4-order.md")
    arguments = parser.parse_args()
    ks = tuple(arguments.k or DEFAULT_K)
    runs = {}
    for spec in arguments.run:                     # "dir" or "dir1,dir2" (a row and its completion)
        dirs = [Path(part) for part in str(spec).split(",")]
        runs[dirs[0].name + ("+completion" if len(dirs) > 1 else "")] = run_order_metrics(dirs, arguments.cases, ks)
    arguments.out.write_text(render(runs, ks), encoding="utf-8")
    print(f"wrote {arguments.out}")
