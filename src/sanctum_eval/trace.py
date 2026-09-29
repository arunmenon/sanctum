"""Runner-observed hub calls. The evaluator trusts these, not the SUT's self-report."""
from pydantic import BaseModel, ConfigDict


class ObservedCall(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    source_id: str
    tool: str
    outcome: str          # ok | timeout | error | denied
    audience_valid: bool = True


class ObservedTrace(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    request_id: str
    calls: list[ObservedCall] = []

    def sources_attempted(self) -> set[str]:
        return {c.source_id for c in self.calls}
