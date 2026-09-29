"""Closed enum sets from HLD v5.1 §6.6, §7.1, §12.0–§12.3, §15.

These sets do not grow when a new situation appears. Detail goes into
versioned reason codes (reason_codes.yaml).
"""
from enum import Enum

__all__ = [
    "Mode", "CallerProfile", "EvidenceStatus", "SourceStatus", "ConflictStatus",
    "RelationType", "ReplayLevel", "EvidenceKind", "EvidenceRole",
    "ApplicabilityStatus", "DecisionStatus", "Disposition", "SupportLevel",
    "ResolutionOrigin",
]


class Mode(str, Enum):
    scoped = "scoped"
    explore = "explore"
    verify = "verify"


class CallerProfile(str, Enum):
    agent = "agent"
    interactive = "interactive"


class EvidenceStatus(str, Enum):
    sufficient = "sufficient"
    partial = "partial"
    insufficient = "insufficient"
    unknown = "unknown"


class SourceStatus(str, Enum):
    called = "called"
    skipped = "skipped"
    timeout = "timeout"
    error = "error"
    unsupported_for_mode = "unsupported_for_mode"


class ConflictStatus(str, Enum):
    possible_conflict = "possible_conflict"
    confirmed_conflict = "confirmed_conflict"
    resolved = "resolved"


class RelationType(str, Enum):
    """Typed relation between two evidence units (lab review L04)."""
    contradiction = "contradiction"                  # same fact kind, scope, time
    policy_implementation_divergence = "policy_implementation_divergence"
    environment_difference = "environment_difference"
    version_difference = "version_difference"


class ReplayLevel(str, Enum):
    # frozen_corpus is a research execution profile, NOT a wire value (HLD v5.1 §15)
    none = "none"
    recompute_on_candidates = "recompute_on_candidates"
    exact_bundle = "exact_bundle"


class EvidenceKind(str, Enum):
    code = "code"
    doc = "doc"
    skill = "skill"
    memory = "memory"
    ticket = "ticket"


class EvidenceRole(str, Enum):
    implemented_behavior = "implemented_behavior"
    intended_procedure = "intended_procedure"
    observed_event = "observed_event"
    reference = "reference"
    session_history = "session_history"


class ApplicabilityStatus(str, Enum):
    known = "known"
    partial = "partial"
    unknown = "unknown"


class DecisionStatus(str, Enum):
    answered = "answered"
    abstained = "abstained"
    unavailable = "unavailable"
    invalid = "invalid"


class Disposition(str, Enum):
    use = "use"
    preserve_candidate = "preserve_candidate"
    escalate = "escalate"
    abstain = "abstain"


class SupportLevel(str, Enum):
    supported = "supported"
    partial = "partial"
    unsupported = "unsupported"


class ResolutionOrigin(str, Enum):
    denotes = "denotes"                  # accepted DENOTES assertion
    request_context = "request_context"  # scope/project context disambiguated
    alias_table = "alias_table"          # C4a-label-only
    none = "none"                        # unresolved
