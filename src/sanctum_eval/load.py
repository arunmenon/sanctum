import json
from pathlib import Path

import yaml

from sanctum_contracts import EvidenceResponse, Receipt

from .gold import GoldCase
from .trace import ObservedTrace


def load_gold(path: Path) -> GoldCase:
    return GoldCase.model_validate(yaml.safe_load(Path(path).read_text()))


def load_response(path: Path) -> tuple[EvidenceResponse, Receipt]:
    data = json.loads(Path(path).read_text())
    return EvidenceResponse.model_validate(data["response"]), Receipt.model_validate(data["receipt"])


def load_trace(path: Path) -> ObservedTrace:
    return ObservedTrace.model_validate(json.loads(Path(path).read_text()))
