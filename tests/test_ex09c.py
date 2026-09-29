"""EX-09c, auth half: when the token service is unavailable, retrieval fails closed (HLD §10
Ex9, §14.1). The registry half lands with `sanctum-ref` at M3.

The gateway is driven directly (not through `run`) so the token service can be taken down
after the caller token is issued, which is the outage the scenario describes."""
from pathlib import Path

import anyio
import pytest

from sanctum_contracts import RetrieveRequest
from sanctum_contracts.enums import EvidenceStatus
from sanctum_eval.load import load_gold
from sanctum_hubs.tokens import TokenService
from sanctum_run.gateway import HubGateway, TokenMode, released_hub_ids
from sanctum_run.runner import DEFAULT_HUBS_CONFIG
from sanctum_run.sut import SUTContext
from sanctum_world.render import build
from tests.helpers.probe_sut import FanOutProbeSUT

ROOT = Path(__file__).resolve().parents[1]
SEED = 20260930
PRINCIPAL = "kestrel-payments"


class EvidenceGatedProbeSUT(FanOutProbeSUT):
    """Fans out like the probe, then refuses to claim evidence it did not receive."""

    async def retrieve(self, request, context):
        response, receipt = await super().retrieve(request, context)
        received_data = any("error" not in payload for payload in self.payloads.values())
        if not received_data:
            response = response.model_copy(update={
                "evidence": [], "evidence_status": EvidenceStatus.insufficient,
                "reasons": ["auth_unavailable"]})
        return response, receipt


@pytest.fixture(scope="module")
def world_build(tmp_path_factory) -> Path:
    out_dir = tmp_path_factory.mktemp("ex09c-build") / "world"
    build(ROOT / "world", SEED, out_dir)
    return out_dir


@pytest.fixture
def request_model() -> RetrieveRequest:
    gold = load_gold(ROOT / "gold" / "m0" / "m0-001.yaml")
    return RetrieveRequest.model_validate(gold.request.model_dump())


async def _probe(world_build: Path, request: RetrieveRequest, token_mode: TokenMode,
                 auth_available: bool):
    token_service = TokenService(world_build / "identity" / "principals.json", "ex09c-secret")
    caller_token = token_service.issue_caller_token(PRINCIPAL)
    token_service.available = auth_available
    probe = EvidenceGatedProbeSUT()
    async with HubGateway(world_build, released_hub_ids(DEFAULT_HUBS_CONFIG), token_service,
                          token_mode=token_mode) as gateway:
        context = SUTContext(caller_token=caller_token, gateway=gateway.handle(request.request_id, caller_token))
        response, _receipt = await probe.retrieve(request, context)
        trace = gateway.trace(request.request_id)
    return probe, response, trace


def _run(*arguments):
    return anyio.run(_probe, *arguments)


def test_auth_unavailable_fails_closed(world_build, request_model):
    probe, response, trace = _run(world_build, request_model, TokenMode.EXCHANGE, False)
    released = released_hub_ids(DEFAULT_HUBS_CONFIG)
    assert sorted(probe.payloads) == released
    for hub_id, payload in probe.payloads.items():
        assert set(payload) == {"error"}, hub_id
        assert payload["error"]["code"] == "denied_or_not_found"
    assert len(trace.calls) == len(released)
    assert all(call.outcome == "denied" and not call.audience_valid for call in trace.calls)
    assert response.evidence_status != EvidenceStatus.sufficient
    assert response.evidence == []


def test_auth_available_control_returns_data(world_build, request_model):
    probe, response, trace = _run(world_build, request_model, TokenMode.EXCHANGE, True)
    assert all(call.outcome == "ok" and call.audience_valid for call in trace.calls)
    assert all("error" not in payload for payload in probe.payloads.values())


@pytest.mark.parametrize("token_mode", [TokenMode.NONE, TokenMode.PASSTHROUGH])
def test_missing_token_and_passthrough_denied(world_build, request_model, token_mode):
    probe, response, trace = _run(world_build, request_model, token_mode, True)
    assert trace.calls
    assert all(call.outcome == "denied" and call.audience_valid is False for call in trace.calls)
    assert all(payload["error"]["code"] == "denied_or_not_found" for payload in probe.payloads.values())
    assert response.evidence_status != EvidenceStatus.sufficient
