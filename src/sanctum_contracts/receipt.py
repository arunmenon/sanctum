"""Receipt fields the evaluator needs (HLD v5.1 §9.5 step 8, §9.6; lab review L11)."""
from typing import Optional

from pydantic import Field

from .base import Strict
from .decision import DecisionResult
from .enums import ResolutionOrigin


class TermResolution(Strict):
    term: str
    candidates: list[str]              # opaque entity refs visible to this caller
    chosen: list[str]                  # empty = unresolved; >1 = separated interpretations
    origin: ResolutionOrigin
    assertion_refs: list[str] = Field(default_factory=list)  # e.g. DENOTES@v3


class Activation(Strict):
    kind: str                          # procedure | selector | authority | source_exclusion
    ref: str                           # procedure_id, selector, authority declaration
    entity_ref: str                    # the entity whose resolution caused it
    source_id: Optional[str] = None


class QueryPlan(Strict):
    source_id: str
    original_query: str
    selectors: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    as_of: Optional[str] = None


class SelfReportedCall(Strict):
    source_id: str
    tool: str
    status: str
    started_ms: int
    ended_ms: int


class Receipt(Strict):
    receipt_id: str
    request_id: str
    config_id: str
    contract_revision: str
    memory_release_id: Optional[str] = None
    resolutions: list[TermResolution] = Field(default_factory=list)
    activations: list[Activation] = Field(default_factory=list)
    query_plans: list[QueryPlan] = Field(default_factory=list)
    decisions: list[DecisionResult] = Field(default_factory=list)
    calls: list[SelfReportedCall] = Field(default_factory=list)
    complete: bool = True
    timings_ms: dict[str, int] = Field(default_factory=dict)
