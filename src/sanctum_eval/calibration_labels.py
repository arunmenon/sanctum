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


# ---- the fit tool's interface: REF dicts from receipt decision values -----------------------------
# REF = {"source_id", "artifact_id", "version", "start", "end"} (offsets into the hub artifact text).

def _ref_covers(ref: dict, bundle: Bundle) -> bool:
    return all(ref.get("source_id") == span.source_id and ref.get("artifact_id") == span.artifact_id
               and str(ref.get("version")) == span.version
               and int(ref.get("start", 0)) <= span.start and int(ref.get("end", -1)) >= span.end
               for span in bundle.spans)


def _ref_overlaps(ref: dict, bundle: Bundle) -> bool:
    return any(ref.get("source_id") == span.source_id and ref.get("artifact_id") == span.artifact_id
               and str(ref.get("version")) == span.version
               and int(ref.get("start", 0)) < span.end and span.start < int(ref.get("end", -1))
               for span in bundle.spans)


def d6_relation_type(gold: GoldCase, a: dict, b: dict):
    """The type of the expected relation whose two witness bundles refs a and b cover (either
    order), or None."""
    for relation in gold.relations:
        if ((_ref_covers(a, relation.witness_a) and _ref_covers(b, relation.witness_b))
                or (_ref_covers(a, relation.witness_b) and _ref_covers(b, relation.witness_a))):
            return relation.relation_type
    return None


def d6_pair_label(gold: GoldCase, a: dict, b: dict) -> int:
    return int(d6_relation_type(gold, a, b) is not None)


def d4_unit_label(gold: GoldCase, ref: dict) -> int:
    """1 when the ref overlaps a span of any bundle of any obligation (necessary evidence)."""
    return int(any(_ref_overlaps(ref, bundle) for obligation in gold.obligations for bundle in obligation.bundles))


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
        if (target.upper() == "D6" or target.lower().startswith("d6")) and isinstance(value, dict) and value.get("pair"):
            pair = value["pair"]
            if isinstance(pair, str):                      # "d6:<a>|<b>"
                pair = pair.split(":", 1)[-1].split("|", 1)
            pairs.append(tuple(pair))
    if not pairs:
        pairs = [(conflict["a"], conflict["b"]) for conflict in response.get("conflicts", [])]
    return list(dict.fromkeys(pairs))


def _item_and_refs(value: dict) -> tuple[str, list[dict]]:
    """A Round 3 decision value's question id and REFs: {"item", "refs": [...]} (the SUT's
    receipts), or the earlier {"pair", "a", "b"} / {"unit", "ref"} shape."""
    if "item" in value and isinstance(value.get("refs"), list):
        return str(value["item"]), [ref for ref in value["refs"] if isinstance(ref, dict)]
    if "pair" in value and isinstance(value.get("a"), dict) and isinstance(value.get("b"), dict):
        return str(value["pair"]), [value["a"], value["b"]]
    if "unit" in value and isinstance(value.get("ref"), dict):
        return str(value["unit"]), [value["ref"]]
    return "", []


def labels_from_run(decision: str, run_dir: Path, cases_dir: Path) -> dict[tuple[str, str], int]:
    """(case_id, key) -> 0/1 for a dev run.

    Preferred source: the receipt decisions of a shadow-collect run, whose values carry REF
    provenance ({"item": "d6:<a>|<b>" or "d4:<ev>", "refs": [REF, ...]}), so pairs and units the
    rules did not pack are labelled too. Fallback for runs without them: the response's evidence
    units. Keys are "a|b" for d6 and the evidence id for d4 in both cases."""
    if decision not in DECISIONS:
        raise ValueError(f"labels exist for {DECISIONS}, not {decision!r}")
    golds = {gold.request.request_id: gold for gold in (load_gold(p) for p in sorted(Path(cases_dir).glob("*.yaml")))}
    receipts = {row["request_id"]: row for row in _read_jsonl(Path(run_dir) / "receipts.jsonl")}
    labels: dict[tuple[str, str], int] = {}
    labelled_from_refs: set[str] = set()
    for request_id, receipt in receipts.items():
        gold = golds.get(request_id)
        for item in (receipt.get("decisions", []) if gold is not None else []):
            value = item.get("value")
            if not isinstance(value, dict):
                continue
            item, refs = _item_and_refs(value)
            if decision == "d6" and item.startswith("d6:") and len(refs) == 2:
                labels[(gold.case_id, item[3:])] = d6_pair_label(gold, refs[0], refs[1])
                labelled_from_refs.add(request_id)
            elif decision == "d4" and item.startswith("d4:") and len(refs) == 1:
                labels[(gold.case_id, item[3:])] = d4_unit_label(gold, refs[0])
                labelled_from_refs.add(request_id)
    for response in _read_jsonl(Path(run_dir) / "responses.jsonl"):
        gold = golds.get(response["request_id"])
        if gold is None or response["request_id"] in labelled_from_refs:
            continue
        units = [EvidenceUnit.model_validate(unit) for unit in response.get("evidence", [])]
        if decision == "d6":
            for (a, b), label in d6_labels(gold, units, _d6_pairs(receipts.get(response["request_id"]), response)).items():
                labels[(gold.case_id, f"{a}|{b}")] = label
        else:
            for evidence_id, label in d4_labels(gold, units).items():
                labels[(gold.case_id, evidence_id)] = label
    return labels


def relation_types_from_run(run_dir: Path, cases_dir: Path) -> dict[tuple[str, str], Optional[str]]:
    """Diagnostic for the D6 fit: (case_id, "a|b") -> the gold relation type a labelled-positive pair
    witnesses (any of the four types counts as positive), or None for negatives. Only the type is
    exposed; no other gold content."""
    golds = {gold.request.request_id: gold for gold in (load_gold(p) for p in sorted(Path(cases_dir).glob("*.yaml")))}
    types: dict[tuple[str, str], Optional[str]] = {}
    for receipt in _read_jsonl(Path(run_dir) / "receipts.jsonl"):
        gold = golds.get(receipt["request_id"])
        for item in (receipt.get("decisions", []) if gold is not None else []):
            value = item.get("value")
            if not isinstance(value, dict):
                continue
            key, refs = _item_and_refs(value)
            if key.startswith("d6:") and len(refs) == 2:
                relation = d6_relation_type(gold, refs[0], refs[1])
                types[(gold.case_id, key[3:])] = relation.value if relation is not None else None
    return types
