"""Private gold model (lab-plan review §3.1). Never shipped to runtime images."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sanctum_contracts import RetrieveRequest
from sanctum_contracts.enums import EvidenceStatus, RelationType, SourceStatus


class _G(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SpanRef(_G):
    source_id: str
    artifact_id: str
    version: str
    start: int
    end: int


class Bundle(_G):
    """All spans are required together."""
    spans: list[SpanRef]


class Obligation(_G):
    obligation_id: str
    interpretation_id: str
    weight: float = Field(gt=0)
    bundles: list[Bundle] = Field(min_length=1, description="Any one complete bundle satisfies")
    acceptable_gap_reasons: list[str] = Field(default_factory=list)
    obtainable: bool = True            # False when the scenario makes it unobtainable


class InterpretationPolicy(str, Enum):
    unique = "unique"
    clarify = "clarify"
    separate_alternatives = "separate_alternatives"


class GoldInterpretation(_G):
    interpretation_id: str
    entity_ref: str                    # the opaque ref the SUT would expose


class ExpectedSourceOutcome(str, Enum):
    attempted = "attempted"
    denied_gap = "denied_gap"
    unavailable_gap = "unavailable_gap"
    capability_gap = "capability_gap"


class SourceObligation(_G):
    source_id: str
    mandatory: bool
    expected: ExpectedSourceOutcome
    substitutes: list[str] = Field(default_factory=list)


class RelationGold(_G):
    relation_id: str
    relation_type: RelationType
    witness_a: Bundle
    witness_b: Bundle


class Forbidden(_G):
    canaries: list[str] = Field(default_factory=list)          # must never appear on public surfaces
    wrong_entities: list[str] = Field(default_factory=list)
    prohibited_activations: list[str] = Field(default_factory=list)


class Expected(_G):
    evidence_status: EvidenceStatus
    required_reasons: list[str] = Field(default_factory=list)
    source_status: dict[str, SourceStatus] = Field(default_factory=dict)


class GoldCase(_G):
    case_id: str
    bundle_id: str                     # independent scenario bundle (resampling unit)
    family: str
    request: RetrieveRequest           # public part; request_id is opaque
    principal: str                     # private: runner injects via transport
    scenario_script: Optional[str] = None
    answerable: bool
    interpretation_policy: InterpretationPolicy
    interpretations: list[GoldInterpretation]
    obligations: list[Obligation] = Field(default_factory=list)
    source_obligations: list[SourceObligation] = Field(default_factory=list)
    relations: list[RelationGold] = Field(default_factory=list)
    forbidden: Forbidden = Forbidden()
    expected: Expected

    @model_validator(mode="after")
    def _consistent(self):
        ids = {i.interpretation_id for i in self.interpretations}
        for o in self.obligations:
            if o.interpretation_id not in ids:
                raise ValueError(f"obligation {o.obligation_id} names unknown interpretation")
        if self.interpretation_policy == InterpretationPolicy.separate_alternatives and len(ids) < 2:
            raise ValueError("separate_alternatives needs at least two interpretations")
        if str(self.case_id) in self.request.request_id:
            raise ValueError("request_id must not encode the case id")
        return self

    @property
    def allowed_entities(self) -> set[str]:
        return {i.entity_ref for i in self.interpretations}
