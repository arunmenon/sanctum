"""Shared hub interfaces (plan M2 decisions 4, 6, 7).

Hub servers (`servers.py`), the token service (`tokens.py`), failure knobs (`failure.py`),
the admin API (`admin.py`) and the runner's gateway all meet here. Nothing in this module
reads files or holds secrets.

Transport metadata (never tool arguments):

- `META_HUB_TOKEN` carries the hub-scoped token in the MCP request `_meta`.
- `META_REQUEST_ID` carries the runner's request id; hubs count calls per
  `(request_id, tool)` to form the failure draw's `call_index`.

Token contract (implemented by `tokens.py`):

- Tokens are HMAC-SHA256 signed JSON with claims `{sub, groups, aud, exp, jti}`.
- Caller tokens have `aud == CALLER_AUDIENCE`; hub tokens have `aud == <hub_id>`.
- A hub calls `verifier.verify(token, audience=<hub_id>)` on every tool call and gets
  `TokenClaims` or a `TokenRejected`; it never tells the caller which reason applied
  (every rejection becomes the same `denied_or_not_found` body as an unknown id).

Failure contract (implemented by `failure.py`):

- `FailureInjector.draw(request_id, hub, tool, call_index)` is a pure function of the run
  seed and those four values. The hub sleeps `latency_ms * time_scale / 1000` seconds, then
  applies the outcome: `timeout` and `error` raise `HubError`, `partial` truncates results
  to `draw.kept(len(results))` and marks the tool output `partial: true`.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Optional, Protocol, runtime_checkable

META_HUB_TOKEN = "lab/hub_token"
META_REQUEST_ID = "lab/request_id"
CALLER_AUDIENCE = "sanctum"


# ---- errors ------------------------------------------------------------------------------
class ErrorCode(StrEnum):
    DENIED_OR_NOT_FOUND = "denied_or_not_found"    # no token, bad token, no access, or unknown id
    CAPABILITY_UNSUPPORTED = "capability_unsupported"  # version read or filter the hub does not declare
    TIMEOUT = "timeout"                            # seeded timeout; distinct from an empty result
    UPSTREAM_ERROR = "upstream_error"              # seeded hub failure
    INVALID_ARGUMENT = "invalid_argument"          # malformed argument (bad top_k, empty query)


# Fixed message per code so that bodies never vary with the hidden cause (existence, ACL,
# token reason). Only codes whose cause is not secret may add detail.
ERROR_MESSAGES = {
    ErrorCode.DENIED_OR_NOT_FOUND: "not found or access denied",
    ErrorCode.CAPABILITY_UNSUPPORTED: "capability not supported by this hub",
    ErrorCode.TIMEOUT: "hub timed out",
    ErrorCode.UPSTREAM_ERROR: "hub error",
    ErrorCode.INVALID_ARGUMENT: "invalid argument",
}
DETAIL_ALLOWED = frozenset({ErrorCode.CAPABILITY_UNSUPPORTED, ErrorCode.INVALID_ARGUMENT})


class HubError(Exception):
    """A typed hub failure, returned to the MCP client as an error result carrying `body()`."""

    def __init__(self, code: ErrorCode, detail: Optional[str] = None):
        self.code = ErrorCode(code)
        self.detail = detail if self.code in DETAIL_ALLOWED else None
        super().__init__(self.message)

    @property
    def message(self) -> str:
        base = ERROR_MESSAGES[self.code]
        return f"{base}: {self.detail}" if self.detail else base

    def body(self) -> dict[str, Any]:
        return {"error": {"code": self.code.value, "message": self.message}}


def denied_or_not_found() -> HubError:
    return HubError(ErrorCode.DENIED_OR_NOT_FOUND)


# ---- tokens --------------------------------------------------------------------------------
class TokenRejectionReason(StrEnum):
    MISSING = "missing"
    MALFORMED = "malformed"
    BAD_SIGNATURE = "bad_signature"
    WRONG_AUDIENCE = "wrong_audience"
    EXPIRED = "expired"
    REVOKED = "revoked"
    UNKNOWN_PRINCIPAL = "unknown_principal"


class TokenRejected(Exception):
    """Raised by a verifier. The reason is for lab logs and tests, never for hub responses."""

    def __init__(self, reason: TokenRejectionReason):
        self.reason = TokenRejectionReason(reason)
        super().__init__(self.reason.value)


class AuthUnavailable(Exception):
    """The token service is down (EX-09c). Callers must fail closed."""


@dataclass(frozen=True)
class TokenClaims:
    """Verified claims of a token. `exp` is Unix seconds; `groups` is sorted."""
    sub: str
    groups: tuple[str, ...]
    aud: str
    exp: int
    jti: str

    def to_dict(self) -> dict[str, Any]:
        return {"sub": self.sub, "groups": list(self.groups), "aud": self.aud,
                "exp": self.exp, "jti": self.jti}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TokenClaims":
        return cls(sub=str(data["sub"]), groups=tuple(sorted(str(group) for group in data["groups"])),
                   aud=str(data["aud"]), exp=int(data["exp"]), jti=str(data["jti"]))


@runtime_checkable
class TokenVerifier(Protocol):
    def verify(self, token: Optional[str], audience: str) -> TokenClaims:
        """Return the claims of a valid token for `audience`.

        Raises `TokenRejected` when the token is missing, malformed, badly signed, for another
        audience (including a caller token presented to a hub), expired, or names a revoked
        or unknown principal. Must not raise anything else for bad input."""
        ...


# ---- failure knobs --------------------------------------------------------------------------
class FailureOutcome(StrEnum):
    OK = "ok"
    TIMEOUT = "timeout"
    ERROR = "error"
    PARTIAL = "partial"


@dataclass(frozen=True)
class FailureDraw:
    """One seeded draw for one tool call."""
    outcome: FailureOutcome
    latency_ms: float = 0.0
    keep_fraction: float = 1.0     # used only when outcome is PARTIAL

    def kept(self, result_count: int) -> int:
        """How many results a partial call keeps: floor(n * keep_fraction), always dropping
        at least one row when there is one to drop."""
        if self.outcome is not FailureOutcome.PARTIAL or result_count == 0:
            return result_count
        return max(0, min(result_count - 1, math.floor(result_count * self.keep_fraction)))


@runtime_checkable
class FailureInjector(Protocol):
    time_scale: float    # multiplies real sleeping; 0 disables sleeping (unit tests)

    def draw(self, request_id: str, hub: str, tool: str, call_index: int) -> FailureDraw:
        """Deterministic in (run seed, request_id, hub, tool, call_index)."""
        ...


class NoFailures:
    """The `none` profile: every call succeeds immediately."""
    time_scale = 0.0

    def draw(self, request_id: str, hub: str, tool: str, call_index: int) -> FailureDraw:
        return FailureDraw(FailureOutcome.OK)
