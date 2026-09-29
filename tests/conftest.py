import json
from pathlib import Path

import pytest

from sanctum_eval.load import load_gold, load_trace

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "gold" / "m0"
STUB = ROOT / "src" / "sanctum_stub" / "responses"
TRACES = ROOT / "tests" / "fixtures" / "m0" / "traces"
CASES = ["m0-001", "m0-002", "m0-003"]


@pytest.fixture
def case():
    """Returns (gold, response_dict, receipt_dict, trace) for a case id; dicts are mutable copies."""
    def _load(cid):
        gold = load_gold(GOLD / f"{cid}.yaml")
        rid = gold.request.request_id
        raw = json.loads((STUB / f"{rid}.json").read_text())
        return gold, raw["response"], raw["receipt"], load_trace(TRACES / f"{rid}.json")
    return _load
