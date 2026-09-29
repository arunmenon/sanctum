"""HLD v5.1 §6.6."""
from typing import Any, Optional

from pydantic import Field, model_validator

from .base import Strict
from .enums import DecisionStatus, Disposition


class DecisionRequest(Strict):
    decision_type: str                 # e.g. "D2"
    schema_version: str = "1.0"
    rubric_version: str
    candidate_ids: list[str]
    bounded_state: dict[str, Any]      # scope-filtered; never gold or world data
    classification: str = "internal"
    deadline_ms: int = Field(gt=0)
    provider_policy_version: str


class DecisionResult(Strict):
    status: DecisionStatus
    value: Optional[Any] = None
    target: str                        # what the probability estimates
    distribution: Optional[dict[str, float]] = None
    calibration: Optional[dict[str, str]] = None
    disposition: Disposition
    provider: str
    model_version: Optional[str] = None
    policy_version: str
    latency_ms: int = Field(ge=0)
    cost: float = Field(ge=0)

    @model_validator(mode="after")
    def _failure_is_not_a_score(self):
        if self.status in (DecisionStatus.unavailable, DecisionStatus.invalid) and self.value is not None:
            raise ValueError("unavailable/invalid results carry no value (never a zero score)")
        if self.status == DecisionStatus.answered and self.value is None:
            raise ValueError("answered results need a value")
        return self
