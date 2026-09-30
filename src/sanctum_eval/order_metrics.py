"""Order-sensitive D4 measurement (prompt review §4), offline from saved run outputs.

D4 may only reorder, so whole-response recall cannot see it. These metrics read the packed
evidence in response order:

- prefix coverage@K: the weighted share of a case's obligations satisfied by the evidence units
  whose cumulative serialized size (cl100k, as in the budget recount) fits within the first K tokens;
- first support rank: the 1-based position of the first unit that overlaps a necessary-evidence
  span (None when no unit does).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Sequence

from sanctum_contracts import EvidenceResponse

from .budget import serialized_evidence_tokens
from .calibration_labels import d4_labels
from .gold import GoldCase
from .load import load_gold
from .metrics import _credited_units, obligation_sat

DEFAULT_K = (1000, 2000, 4000)


def prefix_units(resp: EvidenceResponse, k: int) -> list:
    kept, used = [], 0
    for unit in resp.evidence:
        cost = serialized_evidence_tokens([unit.model_dump(mode="json")])
        if used + cost > k:
            break
        kept.append(unit)
        used += cost
    return kept


def prefix_coverage(gold: GoldCase, resp: EvidenceResponse, k: int) -> Optional[float]:
    if not gold.answerable or not gold.obligations:
        return None
    prefix_ids = {u.evidence_id for u in prefix_units(resp, k)}
    units = [u for u in _credited_units(resp, gold) if u.evidence_id in prefix_ids]
    total = sum(o.weight for o in gold.obligations)
    return sum(o.weight for o in gold.obligations if obligation_sat(resp, gold, o, units)) / total


def first_support_rank(gold: GoldCase, resp: EvidenceResponse) -> Optional[int]:
    labels = d4_labels(gold, resp.evidence)
    return next((n for n, unit in enumerate(resp.evidence, start=1) if labels.get(unit.evidence_id)), None)


def order_metrics_for_run(run_dir: Path, cases_dir: Path, ks: Sequence[int] = DEFAULT_K) -> dict:
    """Per-run means with denominators: coverage@K over answerable cases, first-support rank over
    cases with any supporting unit, and how many cases had none."""
    golds = {g.request.request_id: g for g in (load_gold(p) for p in sorted(Path(cases_dir).glob("*.yaml")))}
    coverage = {k: [] for k in ks}
    ranks, no_support = [], 0
    for line in (Path(run_dir) / "responses.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        resp = EvidenceResponse.model_validate(json.loads(line))
        gold = golds.get(resp.request_id)
        if gold is None:
            continue
        for k in ks:
            value = prefix_coverage(gold, resp, k)
            if value is not None:
                coverage[k].append(value)
        rank = first_support_rank(gold, resp)
        if rank is None:
            no_support += gold.answerable
        else:
            ranks.append(rank)
    ordered = sorted(ranks)
    return {"coverage": {k: {"mean": sum(v) / len(v) if v else None, "n": len(v)} for k, v in coverage.items()},
            "first_support_rank": {"mean": sum(ranks) / len(ranks) if ranks else None,
                                   "median": ordered[len(ordered) // 2] if ordered else None, "n": len(ranks)},
            "answerable_without_support": no_support}
