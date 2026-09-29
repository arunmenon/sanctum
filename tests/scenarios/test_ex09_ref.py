"""EX-09 on sanctum-ref (C2): registry unavailable fails closed (EX-09c registry half), the caller
cannot be verified (EX-09c auth half, through the proxy), and a mandatory SkillHub timeout is a
visible gap rather than "no answer" (EX-09d)."""
import json

import anyio
import pytest

from sanctum_contracts import RetrieveRequest
from sanctum_eval.load import load_gold
from sanctum_hubs.tokens import TokenService
from sanctum_run.gateway import HubGateway, released_hub_ids
from sanctum_run.process_sut import ProcessSUT
from sanctum_run.runner import DEFAULT_HUBS_CONFIG
from sanctum_run.sut import SUTContext

from .conftest import ROOT, SCENARIO_GOLD, run_ref, scenario_cases

EX09_CASE = scenario_cases()["EX-09"][0]


@pytest.mark.parametrize("registry_state", ["missing", "invalid"])
def test_registry_unavailable_fails_closed(scenario_world, tmp_path, registry_state):
    registry = tmp_path / "manifests"
    registry.mkdir()
    if registry_state == "invalid":
        (registry / "skillhub.yaml").write_text("hub_id: skillhub\nunexpected: true\n")
    result = run_ref(scenario_world, tmp_path / "run", registry=registry)
    assert result.integrity_ok
    for line in (result.out_dir / "responses.jsonl").read_text().splitlines():
        response = json.loads(line)
        assert response["evidence_status"] == "unknown"
        assert response["evidence"] == [] and response["sources"] == []
    for line in (result.out_dir / "traces.jsonl").read_text().splitlines():
        assert json.loads(line)["calls"] == []          # no hub call, so no wider access


async def _retrieve_with_auth_down(world, request: RetrieveRequest, principal: str):
    token_service = TokenService(world / "identity" / "principals.json", "ex09c-ref-secret")
    caller_token = token_service.issue_caller_token(principal)
    token_service.available = False
    sut = ProcessSUT(["--config", "C2"])
    async with HubGateway(world, released_hub_ids(DEFAULT_HUBS_CONFIG), token_service) as gateway:
        async with sut.open(gateway, world):
            context = SUTContext(caller_token=caller_token, gateway=gateway.handle(request.request_id, caller_token))
            with gateway.sut_call(request.request_id):
                response, receipt = await sut.retrieve(request, context)
        return response, receipt, gateway.trace(request.request_id), gateway.anomalies()


def test_auth_unavailable_fails_closed_through_proxy(scenario_world):
    gold = load_gold(SCENARIO_GOLD / f"{EX09_CASE}.yaml")
    request = RetrieveRequest.model_validate(gold.request.model_dump())
    response, receipt, trace, anomalies = anyio.run(_retrieve_with_auth_down, scenario_world, request, gold.principal)
    assert response.evidence_status.value == "unknown" and response.evidence == []
    assert trace.calls == [] and receipt.calls == []
    assert anomalies == []


def test_mandatory_skillhub_timeout_is_a_visible_gap(scenario_world, tmp_path):
    """EX-09d: SkillHub (must-consult for payments procedure facts) times out on every call."""
    result = run_ref(scenario_world, tmp_path / "run", failure_profile="skillhub_timeout", time_scale=0.01)
    case_ids = result.manifest["cases"]
    responses = [json.loads(line) for line in (result.out_dir / "responses.jsonl").read_text().splitlines()]
    traces = [json.loads(line) for line in (result.out_dir / "traces.jsonl").read_text().splitlines()]
    index = case_ids.index(EX09_CASE)
    response, trace = responses[index], traces[index]
    skillhub = next(source for source in response["sources"] if source["source_id"] == "skillhub")
    assert skillhub["status"] == "timeout"
    assert "required_source_unavailable" in skillhub["reasons"]
    assert "required_source_unavailable" in response["reasons"]
    assert response["evidence_status"] != "sufficient"
    assert all(unit["source_id"] != "skillhub" for unit in response["evidence"])
    skill_calls = [call for call in trace["calls"] if call["source_id"] == "skillhub"]
    assert skill_calls and all(call["outcome"] == "timeout" for call in skill_calls)
    # the other hubs still answered (X-BACKEND-INDEP): an outage of one hub does not disable others
    assert any(call["outcome"] == "ok" for call in trace["calls"] if call["source_id"] != "skillhub")
    score = next(score for score in result.scores if score.case_id == EX09_CASE)
    assert "mandatory_source" not in score.gates_failed and score.receipt_honest
