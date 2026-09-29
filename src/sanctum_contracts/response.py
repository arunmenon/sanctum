"""HLD v5.1 §12.2."""
from typing import Optional

from pydantic import Field, model_validator

from .base import Strict
from .enums import ConflictStatus, EvidenceStatus, RelationType, ReplayLevel, SourceStatus
from .evidence import EvidenceUnit
from .reasons import validate_reasons

SCHEMA_VERSION = "1.0"


class SourceOutcome(Strict):
    source_id: str
    status: SourceStatus
    reasons: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _reasons(self):
        validate_reasons(self.reasons, "source")
        if self.status == SourceStatus.skipped and not self.reasons:
            raise ValueError("a skipped source must carry a reason")
        if self.status == SourceStatus.unsupported_for_mode and not self.reasons:
            raise ValueError("unsupported_for_mode must carry a reason")
        return self


class Conflict(Strict):
    conflict_id: str
    a: str
    b: str
    relation_type: RelationType
    status: ConflictStatus


class Interpretation(Strict):
    interpretation_id: str
    entity_ref: str
    resolution_origin: str
    evidence_ids: list[str] = Field(default_factory=list)
    conflict_ids: list[str] = Field(default_factory=list)
    evidence_status: EvidenceStatus
    reasons: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _reasons(self):
        validate_reasons(self.reasons, "interpretation")
        return self


class Omitted(Strict):
    ref_id: str
    reason: str


class Budget(Strict):
    requested: int = Field(gt=0)
    used: int = Field(ge=0)
    tokenizer_id: str


class EvidenceResponse(Strict):
    schema_version: str = SCHEMA_VERSION
    request_id: str
    receipt_id: str
    memory_release_id: Optional[str] = None
    effective_scope_ref: str
    policy_versions: dict[str, str] = Field(default_factory=dict)
    replay_level: ReplayLevel
    replay_expiry: Optional[str] = None
    interpretations: list[Interpretation] = Field(default_factory=list)
    evidence: list[EvidenceUnit] = Field(default_factory=list)
    conflicts: list[Conflict] = Field(default_factory=list)
    sources: list[SourceOutcome] = Field(default_factory=list)
    evidence_status: EvidenceStatus
    reasons: list[str] = Field(default_factory=list)
    verdicts: Optional[list[dict]] = Field(default=None, description="verify mode, only once D7 exists")
    omitted: list[Omitted] = Field(default_factory=list)
    budget: Budget
    truncation: bool = False
    degraded_reasons: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _checks(self):
        validate_reasons(self.reasons, "response")
        validate_reasons(self.degraded_reasons, "degraded")
        # Reference closure (§12.2): every referenced ID is present or omitted.
        present = {e.evidence_id for e in self.evidence}
        conflicts = {c.conflict_id for c in self.conflicts}
        omitted = {o.ref_id for o in self.omitted}
        refs = set()
        for c in self.conflicts:
            refs |= {c.a, c.b}
        for e in self.evidence:
            refs |= set(e.duplicates)
        for i in self.interpretations:
            refs |= set(i.evidence_ids)
            missing_c = set(i.conflict_ids) - conflicts - omitted
            if missing_c:
                raise ValueError(f"interpretation references unknown conflicts: {sorted(missing_c)}")
        dangling = refs - present - omitted
        if dangling:
            raise ValueError(f"reference closure violated: {sorted(dangling)}")
        if len(present) != len(self.evidence):
            raise ValueError("duplicate evidence_id")
        return self
