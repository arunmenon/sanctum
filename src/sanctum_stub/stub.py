import json
from importlib import resources

from sanctum_contracts import (
    CONTRACT_REVISION, EvidenceResponse, Receipt, RetrieveRequest, SanctumCapabilities,
    load_reason_codes,
)
from sanctum_contracts.enums import ReplayLevel, SupportLevel


class StubSUT:
    """Returns canned responses keyed by opaque request_id."""

    def capabilities(self) -> SanctumCapabilities:
        return SanctumCapabilities(
            contract_revision=CONTRACT_REVISION,
            reason_codes_version=load_reason_codes()["version"],
            modes={"scoped": SupportLevel.supported, "explore": SupportLevel.supported,
                   "verify": SupportLevel.partial},
            features={"synthesize": SupportLevel.unsupported, "writes": SupportLevel.unsupported,
                      "separated_interpretations": SupportLevel.supported},
            replay_levels=[ReplayLevel.recompute_on_candidates],
        )

    def retrieve(self, request: RetrieveRequest) -> tuple[EvidenceResponse, Receipt]:
        name = f"{request.request_id}.json"
        data = json.loads(resources.files("sanctum_stub.responses").joinpath(name).read_text())
        return EvidenceResponse.model_validate(data["response"]), Receipt.model_validate(data["receipt"])
