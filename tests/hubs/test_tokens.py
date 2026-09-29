"""Token service: passthrough, wrong audience, expired, tampered, revoked, missing (plan M2 task 3)."""
import base64
import json
from pathlib import Path

import pytest

from sanctum_hubs.interfaces import (
    CALLER_AUDIENCE,
    AuthUnavailable,
    TokenRejected,
    TokenRejectionReason,
    TokenVerifier,
)
from sanctum_hubs.tokens import TokenService, verifier_from_secret

SECRET = "lab-token-secret"


class ManualClock:
    def __init__(self, now: float = 1_900_000_000.0):
        self.now = now

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def principals_path(tmp_path: Path) -> Path:
    path = tmp_path / "principals.json"
    path.write_text(json.dumps([
        {"principal": "kestrel-payments", "groups": ["platform-eng", "payments-eng"]},
        {"principal": "kestrel-identity", "groups": ["identity-eng", "platform-eng"]},
    ]))
    return path


@pytest.fixture
def clock() -> ManualClock:
    return ManualClock()


@pytest.fixture
def service(principals_path: Path, clock: ManualClock) -> TokenService:
    return TokenService(principals_path, SECRET, clock=clock)


def rejection_reason(verifier, token, audience) -> TokenRejectionReason:
    with pytest.raises(TokenRejected) as rejected:
        verifier.verify(token, audience)
    return rejected.value.reason


def test_exchange_yields_hub_token_with_groups(service):
    hub_token = service.exchange(service.issue_caller_token("kestrel-payments"), "codehub")
    claims = service.verify(hub_token, "codehub")
    assert claims.sub == "kestrel-payments"
    assert claims.aud == "codehub"
    assert claims.groups == ("payments-eng", "platform-eng")
    assert isinstance(service, TokenVerifier)
    assert isinstance(verifier_from_secret(SECRET), TokenVerifier)


def test_caller_token_passthrough_denied(service, clock):
    caller_token = service.issue_caller_token("kestrel-payments")
    assert service.verify(caller_token, CALLER_AUDIENCE).aud == CALLER_AUDIENCE
    assert rejection_reason(service, caller_token, "codehub") is TokenRejectionReason.WRONG_AUDIENCE
    assert rejection_reason(verifier_from_secret(SECRET, clock=clock), caller_token,
                            "codehub") is TokenRejectionReason.WRONG_AUDIENCE


def test_wrong_audience_hub_token_denied(service):
    hub_token = service.exchange(service.issue_caller_token("kestrel-payments"), "codehub")
    assert rejection_reason(service, hub_token, "dochub") is TokenRejectionReason.WRONG_AUDIENCE


def test_exchange_refuses_hub_token_as_caller_token(service):
    hub_token = service.exchange(service.issue_caller_token("kestrel-payments"), "codehub")
    with pytest.raises(TokenRejected) as rejected:
        service.exchange(hub_token, "dochub")
    assert rejected.value.reason is TokenRejectionReason.WRONG_AUDIENCE
    with pytest.raises(TokenRejected):
        service.exchange(service.issue_caller_token("kestrel-payments"), CALLER_AUDIENCE)


def test_expired_token_denied(service, clock):
    hub_token = service.exchange(service.issue_caller_token("kestrel-payments"), "codehub")
    clock.now += service.hub_ttl_seconds + 1
    assert rejection_reason(service, hub_token, "codehub") is TokenRejectionReason.EXPIRED
    assert rejection_reason(verifier_from_secret(SECRET, clock=clock), hub_token,
                            "codehub") is TokenRejectionReason.EXPIRED


def test_tampered_token_denied(service, principals_path):
    hub_token = service.exchange(service.issue_caller_token("kestrel-payments"), "codehub")
    payload_segment, signature_segment = hub_token.split(".")
    payload = json.loads(base64.urlsafe_b64decode(payload_segment + "=" * (-len(payload_segment) % 4)))
    payload["groups"] = ["identity-eng", "payments-eng", "platform-eng", "restricted-incidents"]
    forged_payload = base64.urlsafe_b64encode(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).rstrip(b"=").decode()
    forged_token = f"{forged_payload}.{signature_segment}"
    assert rejection_reason(service, forged_token, "codehub") is TokenRejectionReason.BAD_SIGNATURE
    other_service = TokenService(principals_path, "another-secret")
    other_secret_token = other_service.exchange(other_service.issue_caller_token("kestrel-payments"),
                                                "codehub")
    assert rejection_reason(verifier_from_secret(SECRET), other_secret_token,
                            "codehub") is TokenRejectionReason.BAD_SIGNATURE



@pytest.mark.parametrize("token,reason", [
    (None, TokenRejectionReason.MISSING),
    ("", TokenRejectionReason.MISSING),
    ("not-a-token", TokenRejectionReason.MALFORMED),
    ("a.b.c", TokenRejectionReason.MALFORMED),
    ("!!!.???", TokenRejectionReason.MALFORMED),
])
def test_missing_and_malformed_tokens_denied(service, token, reason):
    assert rejection_reason(service, token, "codehub") is reason
    assert rejection_reason(verifier_from_secret(SECRET), token, "codehub") is reason


def test_revoked_principal_denied_immediately(service):
    caller_token = service.issue_caller_token("kestrel-payments")
    hub_token = service.exchange(caller_token, "codehub")
    service.revoke("kestrel-payments")
    assert rejection_reason(service, hub_token, "codehub") is TokenRejectionReason.REVOKED
    with pytest.raises(TokenRejected) as rejected:
        service.exchange(caller_token, "dochub")
    assert rejected.value.reason is TokenRejectionReason.REVOKED
    with pytest.raises(TokenRejected):
        service.issue_caller_token("kestrel-payments")
    other_hub_token = service.exchange(service.issue_caller_token("kestrel-identity"), "codehub")
    assert service.verify(other_hub_token, "codehub").sub == "kestrel-identity"


def test_unknown_principal_denied(service):
    with pytest.raises(TokenRejected) as rejected:
        service.issue_caller_token("mallory")
    assert rejected.value.reason is TokenRejectionReason.UNKNOWN_PRINCIPAL


def test_auth_unavailable_fails_closed(service):
    caller_token = service.issue_caller_token("kestrel-payments")
    service.available = False
    with pytest.raises(AuthUnavailable):
        service.exchange(caller_token, "codehub")
    with pytest.raises(AuthUnavailable):
        service.issue_caller_token("kestrel-identity")
    service.available = True
    assert service.exchange(caller_token, "codehub")


def test_loads_built_principals():
    principals_path = Path(__file__).resolve().parents[2] / "build" / "world" / "identity" / "principals.json"
    if not principals_path.exists():
        pytest.skip("world not built")
    service = TokenService(principals_path, SECRET)
    assert "kestrel-payments" in service.principals
    assert "restricted-incidents" in service.groups_of("admin-probe")
