"""Lab token service (plan M2 decision 4, HLD §14.1).

Tokens are `<payload>.<signature>`: base64url JSON claims `{sub, groups, aud, exp, jti}` and
a base64url HMAC-SHA256 over the payload bytes. The caller holds a token for audience
`sanctum`; the runner exchanges it for a hub-scoped token (`aud == <hub_id>`) on the caller's
behalf. Hubs never accept caller tokens (no passthrough).

- `TokenService` owns principals, issuance, exchange, revocation and the availability switch
  used by EX-09c. Its `verify` also rejects revoked and unknown principals.
- `verifier_from_secret(secret)` is for out-of-process hubs that only share the secret: it
  checks signature, audience and expiry, nothing stateful.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import itertools
import json
import time
from pathlib import Path
from typing import Callable, Optional

from .interfaces import (
    CALLER_AUDIENCE,
    AuthUnavailable,
    TokenClaims,
    TokenRejected,
    TokenRejectionReason,
)

DEFAULT_CALLER_TTL_SECONDS = 3600
DEFAULT_HUB_TTL_SECONDS = 300

Clock = Callable[[], float]


def _encode_segment(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _decode_segment(segment: str) -> bytes:
    padding = "=" * (-len(segment) % 4)
    return base64.b64decode(segment + padding, altchars=b"-_", validate=True)


def _secret_bytes(secret: str | bytes) -> bytes:
    secret_bytes = secret.encode("utf-8") if isinstance(secret, str) else bytes(secret)
    if not secret_bytes:
        raise ValueError("token secret must not be empty")
    return secret_bytes


def sign_claims(claims: TokenClaims, secret: str | bytes) -> str:
    payload = json.dumps(claims.to_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(_secret_bytes(secret), payload, hashlib.sha256).digest()
    return f"{_encode_segment(payload)}.{_encode_segment(signature)}"


class SignedTokenVerifier:
    """Stateless verifier: signature, audience and expiry. Satisfies `TokenVerifier`."""

    def __init__(self, secret: str | bytes, clock: Clock = time.time):
        self._secret = _secret_bytes(secret)
        self._clock = clock

    def decode(self, token: Optional[str]) -> TokenClaims:
        """Signature-checked claims, without audience or expiry checks."""
        if not token:
            raise TokenRejected(TokenRejectionReason.MISSING)
        if not isinstance(token, str) or token.count(".") != 1:
            raise TokenRejected(TokenRejectionReason.MALFORMED)
        payload_segment, signature_segment = token.split(".")
        try:
            payload = _decode_segment(payload_segment)
            signature = _decode_segment(signature_segment)
        except (binascii.Error, ValueError):
            raise TokenRejected(TokenRejectionReason.MALFORMED) from None
        expected_signature = hmac.new(self._secret, payload, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected_signature):
            raise TokenRejected(TokenRejectionReason.BAD_SIGNATURE)
        try:
            data = json.loads(payload)
            if not isinstance(data, dict) or not isinstance(data.get("groups"), list):
                raise ValueError("claims shape")
            return TokenClaims.from_dict(data)
        except (ValueError, KeyError, TypeError):
            raise TokenRejected(TokenRejectionReason.MALFORMED) from None

    def verify(self, token: Optional[str], audience: str) -> TokenClaims:
        claims = self.decode(token)
        if claims.aud != audience:
            raise TokenRejected(TokenRejectionReason.WRONG_AUDIENCE)
        if claims.exp <= self._clock():
            raise TokenRejected(TokenRejectionReason.EXPIRED)
        return claims


def verifier_from_secret(secret: str | bytes, clock: Clock = time.time) -> SignedTokenVerifier:
    return SignedTokenVerifier(secret, clock=clock)


def load_principals(principals_path: Path) -> dict[str, tuple[str, ...]]:
    """`identity/principals.json` as {principal: sorted groups}."""
    entries = json.loads(Path(principals_path).read_text(encoding="utf-8"))
    return {str(entry["principal"]): tuple(sorted(str(group) for group in entry["groups"]))
            for entry in entries}


class TokenService:
    """Issues caller tokens, exchanges them for hub tokens, and revokes principals."""

    def __init__(self, principals_path: Path, secret: str | bytes, clock: Clock = time.time,
                 caller_ttl_seconds: int = DEFAULT_CALLER_TTL_SECONDS,
                 hub_ttl_seconds: int = DEFAULT_HUB_TTL_SECONDS):
        self._secret = _secret_bytes(secret)
        self._clock = clock
        self._signed_verifier = SignedTokenVerifier(self._secret, clock=clock)
        self._groups_by_principal = load_principals(principals_path)
        self._revoked_principals: set[str] = set()
        self._jti_counter = itertools.count(1)
        self.caller_ttl_seconds = caller_ttl_seconds
        self.hub_ttl_seconds = hub_ttl_seconds
        self.available = True

    # ---- state -----------------------------------------------------------------------------
    @property
    def principals(self) -> list[str]:
        return sorted(self._groups_by_principal)

    def groups_of(self, principal: str) -> tuple[str, ...]:
        return self._groups_by_principal[principal]

    def is_revoked(self, principal: str) -> bool:
        return principal in self._revoked_principals

    def revoke(self, principal: str) -> None:
        """Takes effect immediately: exchange and `verify` reject the principal from now on."""
        if principal not in self._groups_by_principal:
            raise KeyError(f"unknown principal {principal}")
        self._revoked_principals.add(principal)

    def _require_available(self) -> None:
        if not self.available:
            raise AuthUnavailable("token service unavailable")

    def _mint(self, principal: str, audience: str, ttl_seconds: int) -> str:
        claims = TokenClaims(sub=principal, groups=self._groups_by_principal[principal], aud=audience,
                             exp=int(self._clock()) + ttl_seconds,
                             jti=f"{audience}-{next(self._jti_counter):08d}")
        return sign_claims(claims, self._secret)

    def _check_principal(self, claims: TokenClaims) -> None:
        if claims.sub not in self._groups_by_principal:
            raise TokenRejected(TokenRejectionReason.UNKNOWN_PRINCIPAL)
        if claims.sub in self._revoked_principals:
            raise TokenRejected(TokenRejectionReason.REVOKED)

    # ---- operations ------------------------------------------------------------------------
    def issue_caller_token(self, principal: str) -> str:
        self._require_available()
        if principal not in self._groups_by_principal:
            raise TokenRejected(TokenRejectionReason.UNKNOWN_PRINCIPAL)
        if principal in self._revoked_principals:
            raise TokenRejected(TokenRejectionReason.REVOKED)
        return self._mint(principal, CALLER_AUDIENCE, self.caller_ttl_seconds)

    def exchange(self, caller_token: Optional[str], audience: str) -> str:
        """Validate a caller token and return a hub token for `audience` with current groups."""
        self._require_available()
        if not audience or audience == CALLER_AUDIENCE:
            raise TokenRejected(TokenRejectionReason.WRONG_AUDIENCE)
        claims = self._signed_verifier.verify(caller_token, CALLER_AUDIENCE)
        self._check_principal(claims)
        return self._mint(claims.sub, audience, self.hub_ttl_seconds)

    def verify(self, token: Optional[str], audience: str) -> TokenClaims:
        """`TokenVerifier` for in-process hubs: stateless checks plus revocation.

        Verification of already-minted tokens does not depend on `available`: an outage stops
        new exchanges (EX-09c fails closed at the gateway), not hubs checking signatures."""
        claims = self._signed_verifier.verify(token, audience)
        self._check_principal(claims)
        return claims
