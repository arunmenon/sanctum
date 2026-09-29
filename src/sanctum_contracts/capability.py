"""HLD v5.1 §12.3."""
from pydantic import Field

from .base import Strict
from .enums import ReplayLevel, SupportLevel


class SanctumCapabilities(Strict):
    contract_revision: str
    reason_codes_version: str
    modes: dict[str, SupportLevel]
    features: dict[str, SupportLevel]
    replay_levels: list[ReplayLevel]


class HubCapabilities(Strict):
    hub_id: str
    version_reads: bool
    filters: list[str] = Field(default_factory=list)
    max_results: int = Field(gt=0)
    principal_scoped: bool = False
    error_semantics: str = "timeout_distinct_from_empty"
