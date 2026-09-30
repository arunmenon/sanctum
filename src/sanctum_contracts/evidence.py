"""HLD v5.1 §7.1 and §7.5."""
from typing import Optional

from pydantic import Field, model_validator

from .base import Strict
from .enums import ApplicabilityStatus, EvidenceKind, EvidenceRole


class Applicability(Strict):
    branch: Optional[str] = None
    environment: Optional[str] = None
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    applicability_status: ApplicabilityStatus = ApplicabilityStatus.unknown

    @model_validator(mode="after")
    def _status_consistent(self):
        filled = [self.branch, self.environment, self.effective_from]
        if self.applicability_status == ApplicabilityStatus.known and not all(filled):
            raise ValueError("applicability 'known' requires branch, environment and effective_from")
        if self.applicability_status == ApplicabilityStatus.unknown and any(filled):
            raise ValueError("applicability 'unknown' must not carry context; use 'partial'")
        return self


class Span(Strict):
    start: int = Field(ge=0)
    end: int = Field(ge=0)

    @model_validator(mode="after")
    def _ordered(self):
        if self.end < self.start:
            raise ValueError("span end < start")
        return self


class EvidenceUnit(Strict):
    evidence_id: str
    source_id: str
    artifact_id: str
    source_version: Optional[str] = Field(description="The hub's version of the artifact; null when the hub read none")
    native_ref: str
    span: Span
    content_hash: str
    text: str
    kind: EvidenceKind
    role: EvidenceRole
    applicability: Applicability = Applicability()
    occurred_at: Optional[str] = None
    recorded_at: Optional[str] = None
    retrieved_at: str
    classification: str = "internal"
    authority_assertion_ref: Optional[str] = None
    exact_token_count: int = Field(ge=0)
    tokenizer_id: str
    duplicates: list[str] = Field(default_factory=list, description="Other copies, each keeps provenance")
