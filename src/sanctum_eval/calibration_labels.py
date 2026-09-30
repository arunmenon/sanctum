"""Calibration labels for Round 3 decisions (lab plan E3), evaluator side only.

Labels come from gold and are handed to the calibration fit (tools/fit_system_one.py); the SUT
never sees them.

- D6: a candidate pair (a, b) is a true conflict iff, in either orientation, unit a covers one
  witness bundle and unit b the other witness bundle of some expected relation of the case.
- D4: a candidate evidence unit is necessary iff its span overlaps a necessary-evidence span
  (any obligation bundle span: same source, artifact and version, intersecting ranges).
"""
import json
from pathlib import Path
from typing import Iterable, Optional

from sanctum_contracts import EvidenceUnit

from .gold import Bundle, GoldCase
from .load import load_gold
from .metrics import bundle_satisfied

DECISIONS = ("d6", "d4")


def pair_matches_relation(gold: GoldCase, unit_a: EvidenceUnit, unit_b: EvidenceUnit):
    """The expected relation this pair witnesses, or None."""
    for relation in gold.relations:
        a_first = bundle_satisfied(relation.witness_a, [unit_a]) and bundle_satisfied(relation.witness_b, [unit_b])
        b_first = bundle_satisfied(relation.witness_a, [unit_b]) and bundle_satisfied(relation.witness_b, [unit_a])
        if a_first or b_first:
            return relation
    return None


def d6_labels(gold: GoldCase, units: Iterable[EvidenceUnit], pairs: Iterable[tuple[str, str]]) -> dict[tuple[str, str], int]:
    by_id = {unit.evidence_id: unit for unit in units}
    return {(a, b): int(a in by_id and b in by_id and pair_matches_relation(gold, by_id[a], by_id[b]) is not None)
            for a, b in pairs}


def _overlaps(unit: EvidenceUnit, bundle: Bundle) -> bool:
    return any(unit.source_id == span.source_id and unit.artifact_id == span.artifact_id
               and unit.source_version == span.version
               and unit.span.start < span.end and span.start < unit.span.end
               for span in bundle.spans)


def d4_labels(gold: GoldCase, units: Iterable[EvidenceUnit]) -> dict[str, int]:
    bundles = [bundle for obligation in gold.obligations for bundle in obligation.bundles]
    return {unit.evidence_id: int(any(_overlaps(unit, bundle) for bundle in bundles)) for unit in units}


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _d6_pairs(receipt: Optional[dict], response: dict) -> list[tuple[str, str]]:
    """Rule-produced candidate pairs: from D6 decisions when the receipt has them, else the
    response's flagged conflicts."""
    pairs = []
    for decision in (receipt or {}).get("decisions", []):
        target = str(decision.get("target", ""))
        value = decision.get("value")
        if (target == "D6" or target.startswith("d6")) and isinstance(value, dict) and value.get("pair"):
            pairs.append(tuple(value["pair"]))
    if not pairs:
        pairs = [(conflict["a"], conflict["b"]) for conflict in response.get("conflicts", [])]
    return list(dict.fromkeys(pairs))


def labels_from_run(decision: str, run_dir: Path, cases_dir: Path) -> dict[tuple[str, str], int]:
    """(case_id, key) -> 0/1 for a dev run; key is "a|b" for d6 and the evidence id for d4."""
    if decision not in DECISIONS:
        raise ValueError(f"labels exist for {DECISIONS}, not {decision!r}")
    golds = {gold.request.request_id: gold for gold in (load_gold(p) for p in sorted(Path(cases_dir).glob("*.yaml")))}
    receipts = {row["request_id"]: row for row in _read_jsonl(Path(run_dir) / "receipts.jsonl")}
    labels: dict[tuple[str, str], int] = {}
    for response in _read_jsonl(Path(run_dir) / "responses.jsonl"):
        gold = golds.get(response["request_id"])
        if gold is None:
            continue
        units = [EvidenceUnit.model_validate(unit) for unit in response.get("evidence", [])]
        if decision == "d6":
            for (a, b), label in d6_labels(gold, units, _d6_pairs(receipts.get(response["request_id"]), response)).items():
                labels[(gold.case_id, f"{a}|{b}")] = label
        else:
            for evidence_id, label in d4_labels(gold, units).items():
                labels[(gold.case_id, evidence_id)] = label
    return labels
