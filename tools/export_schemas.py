"""Export JSON Schemas for the frozen wire contracts. Run after any contract change."""
import json
from pathlib import Path

from sanctum_contracts import (
    DecisionRequest, DecisionResult, EvidenceResponse, HubCapabilities, Receipt,
    RetrieveRequest, SanctumCapabilities,
)

OUT = Path(__file__).resolve().parents[1] / "src" / "sanctum_contracts" / "schema"
MODELS = [RetrieveRequest, EvidenceResponse, Receipt, DecisionRequest, DecisionResult,
          SanctumCapabilities, HubCapabilities]


def render() -> dict[str, str]:
    return {f"{m.__name__}.json": json.dumps(m.model_json_schema(), indent=2, sort_keys=True) + "\n"
            for m in MODELS}


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, text in render().items():
        (OUT / name).write_text(text)
    print(f"wrote {len(MODELS)} schemas to {OUT}")
