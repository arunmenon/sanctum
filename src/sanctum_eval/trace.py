"""Runner-observed hub calls and System One model calls. The evaluator trusts these, not the SUT's self-report."""
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ObservedCall(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    source_id: str
    tool: str
    outcome: str          # ok | timeout | error | denied
    audience_valid: bool = True


class ModelCall(BaseModel):
    """A System One provider call made by the runner-side broker for this request. Kept apart from
    source calls: never a source attempted, never evidence-bearing retrieval (handshake point 10)."""
    model_config = ConfigDict(extra="forbid", frozen=True, protected_namespaces=())
    provider: str
    model: Optional[str] = None          # resolved version from the response, when there is one
    profile: str                         # strict | relaxed
    round: str
    questions: list[str]
    outcome: str                         # ok | unavailable
    reason: Optional[str] = None         # the CallOutcome unavailable_reason, when unavailable
    elapsed_ms: float
    usage: Optional[dict] = None
    calls: int = 0                       # HTTP calls made, retries included
    invalid_ids: list[str] = []          # questions refused, dropped or answered invalidly


class ObservedTrace(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, protected_namespaces=())
    request_id: str
    calls: list[ObservedCall] = []
    elapsed_ms: Optional[float] = None    # runner wall clock around the SUT call (M6 latency)
    model_calls: list[ModelCall] = []

    def sources_attempted(self) -> set[str]:
        return {c.source_id for c in self.calls}
