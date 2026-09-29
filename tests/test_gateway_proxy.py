"""Gateway proxy and out-of-process SUT boundary (discrepancy register 16, M3)."""
import anyio
import pytest

from sanctum_hubs.tokens import TokenService
from sanctum_run.gateway import HubGateway, released_hub_ids
from sanctum_run.process_sut import child_environment
from sanctum_run.proxy import CALLER_TOOL, CAPABILITIES_TOOL, GatewayProxy
from sanctum_run.runner import DEFAULT_HUBS_CONFIG
from tests.scenarios.conftest import scenario_world  # noqa: F401  (session world build)

PRINCIPAL = "kestrel-payments"


def test_child_environment_drops_secrets(monkeypatch):
    monkeypatch.setenv("SANCTUM_LAB_TOKEN_SECRET", "top-secret")
    monkeypatch.setenv("SANCTUM_LAB_ADMIN_SECRET", "admin-secret")
    environment = child_environment()
    assert "top-secret" not in environment.values() and "admin-secret" not in environment.values()
    assert set(environment) <= {"PATH", "HOME", "TMPDIR", "LANG", "TIKTOKEN_CACHE_DIR", "SYSTEMROOT", "PYTHONPATH"}


async def _exercise(world):
    token_service = TokenService(world / "identity" / "principals.json", "proxy-test-secret")
    caller_token = token_service.issue_caller_token(PRINCIPAL)
    out = {}
    async with HubGateway(world, released_hub_ids(DEFAULT_HUBS_CONFIG), token_service) as gateway:
        proxy = await GatewayProxy.create(gateway, world)
        out["tools"] = {tool.name for tool in proxy._tools}
        out["unbound"] = await proxy.dispatch("codehub.list_repos", {}, "req-a", caller_token)
        proxy.bind("req-a", caller_token, gateway.handle("req-a", caller_token))
        with gateway.sut_call("req-a"):
            out["ok"] = await proxy.dispatch("codehub.list_repos", {}, "req-a", caller_token)
            out["stale"] = await proxy.dispatch("codehub.list_repos", {}, "req-b", caller_token)
            out["forged"] = await proxy.dispatch("codehub.list_repos", {}, "req-a", "forged-token")
            out["groups"] = await proxy.dispatch(CALLER_TOOL, {}, "req-a", caller_token)
            out["groups_forged"] = await proxy.dispatch(CALLER_TOOL, {}, "req-a", "forged-token")
            out["capabilities"] = await proxy.dispatch(CAPABILITIES_TOOL, {}, "req-a", caller_token)
        out["trace"] = gateway.trace("req-a")
        out["anomalies"] = proxy.anomalies() + gateway.anomalies()
    return out


def test_proxy_serves_only_the_bound_request(scenario_world):  # noqa: F811
    out = anyio.run(_exercise, scenario_world)
    assert "codehub.search_code" in out["tools"] and "skillhub.get_skill" in out["tools"]
    assert not any(name.startswith("incidenthub.") for name in out["tools"])     # held back
    assert out["ok"].get("items")
    for key in ("unbound", "stale", "forged"):
        assert out[key]["error"]["code"] == "denied_or_not_found", key
    assert set(out["groups"]) == {"groups", "reader"} and "payments-eng" in out["groups"]["groups"]
    assert out["groups"]["reader"].startswith("reader-")                   # opaque per-caller id
    assert PRINCIPAL not in str(out["groups"])                               # groups only, never the principal
    assert "error" in out["groups_forged"]
    assert set(out["capabilities"]["hubs"]) == set(released_hub_ids(DEFAULT_HUBS_CONFIG))
    outcomes = [(call.source_id, call.outcome, call.audience_valid) for call in out["trace"].calls]
    assert outcomes == [("codehub", "ok", True), ("codehub", "denied", False), ("codehub", "denied", False)]
    kinds = [entry["kind"] for entry in out["anomalies"]]
    assert kinds.count("proxy_call_outside_binding") == 3


async def _request_id_reuse(world):
    """Codex M3-M8 #1: bind caller A, then try to create an admin context with the same request id
    and dispatch with A's token. Credentials must stay A's, and every attempt is an anomaly."""
    from sanctum_run.gateway import DuplicateRequestBinding
    token_service = TokenService(world / "identity" / "principals.json", "reuse-secret")
    token_a = token_service.issue_caller_token(PRINCIPAL)
    admin = token_service.issue_caller_token("admin-probe")
    out = {}
    async with HubGateway(world, released_hub_ids(DEFAULT_HUBS_CONFIG), token_service) as gateway:
        proxy = await GatewayProxy.create(gateway, world)
        handle_a = gateway.handle("req-x", token_a)
        proxy.bind("req-x", token_a, handle_a)
        try:
            gateway.handle("req-x", admin)
            out["gateway_duplicate"] = "accepted"
        except DuplicateRequestBinding:
            out["gateway_duplicate"] = "refused"
        other = gateway.handle("req-y", admin)
        try:
            proxy.bind("req-x", admin, other)
            out["proxy_duplicate"] = "accepted"
        except DuplicateRequestBinding:
            out["proxy_duplicate"] = "refused"
        gateway.bind("req-x", admin)                        # legacy rebind: no effect, anomaly
        out["repos"] = await proxy.dispatch("codehub.list_repos", {}, "req-x", token_a)
        proxy.unbind("req-x", other)                         # someone else's handle: no effect
        out["still_bound"] = await proxy.dispatch("codehub.list_repos", {}, "req-x", token_a)
        proxy.unbind("req-x", handle_a)
        gateway.release(handle_a)
        out["stale"] = await handle_a.call("codehub", "list_repos", {})
        out["anomalies"] = [entry["kind"] for entry in proxy.anomalies() + gateway.anomalies()]
    return out


def test_request_id_reuse_cannot_cross_callers(scenario_world):  # noqa: F811
    out = anyio.run(_request_id_reuse, scenario_world)
    assert out["gateway_duplicate"] == "refused" and out["proxy_duplicate"] == "refused"
    for key in ("repos", "still_bound"):
        repos = out[key]["items"]
        assert repos and not [repo for repo in repos if repo.startswith("repo:identity/")], key
    assert out["stale"]["error"]["code"] == "denied_or_not_found"
    assert out["anomalies"].count("duplicate_request_binding") == 2          # gateway handle + legacy rebind
    assert "binding_request_mismatch" in out["anomalies"]                     # proxy bind with another id's handle
    assert "call_on_inactive_binding" in out["anomalies"]
