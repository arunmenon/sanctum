"""Gateway robustness (Codex M2 review findings 1, 4, 5)."""
import asyncio
from pathlib import Path

import anyio
import pytest

import sanctum_run.gateway as gateway_module
from sanctum_hubs.interfaces import FailureDraw, FailureOutcome
from sanctum_hubs.tokens import TokenService
from sanctum_run.gateway import HubGateway
from sanctum_run.runner import DEFAULT_M0_PRINCIPAL_ALIASES, RunConfig, load_principal_aliases, run
from sanctum_stub.stub import StubSUT
from sanctum_world.render import build

ROOT = Path(__file__).resolve().parents[1]
SEED = 20260930
PRINCIPAL = "kestrel-payments"


@pytest.fixture(scope="module")
def world_build(tmp_path_factory) -> Path:
    out_dir = tmp_path_factory.mktemp("gateway-build") / "world"
    build(ROOT / "world", SEED, out_dir)
    return out_dir


class SlowHubs:
    """Every call succeeds after one real second."""
    time_scale = 1.0

    def draw(self, request_id, hub, tool, call_index):
        return FailureDraw(FailureOutcome.OK, latency_ms=1000.0)


def _service(world_build: Path) -> TokenService:
    return TokenService(world_build / "identity" / "principals.json", "robustness-secret")


def test_caller_deadline_cancellation_is_recorded_as_timeout(world_build):
    async def scenario():
        service = _service(world_build)
        async with HubGateway(world_build, ["codehub", "skillhub"], service, SlowHubs()) as gateway:
            handle = gateway.handle("req-deadline", service.issue_caller_token(PRINCIPAL))
            with anyio.move_on_after(0.05):
                await handle.call("codehub", "list_repos")
            # a cancelled fan-out: both in-flight calls must still appear once each
            with anyio.move_on_after(0.05):
                async with anyio.create_task_group() as task_group:
                    task_group.start_soon(handle.call, "codehub", "list_repos")
                    task_group.start_soon(handle.call, "skillhub", "list_tree")
            return gateway.trace("req-deadline")

    trace = anyio.run(scenario)
    assert sorted((call.source_id, call.outcome) for call in trace.calls) == [
        ("codehub", "timeout"), ("codehub", "timeout"), ("skillhub", "timeout")]


def test_argument_validation_error_is_recorded_not_raised(world_build):
    async def scenario():
        service = _service(world_build)
        async with HubGateway(world_build, ["codehub"], service) as gateway:
            handle = gateway.handle("req-bad-arg", service.issue_caller_token(PRINCIPAL))
            payload = await handle.call("codehub", "search_code", {"query": {"nested": 1}})
            return payload, gateway.trace("req-bad-arg")

    payload, trace = anyio.run(scenario)
    assert payload["error"]["code"] == "invalid_argument"
    assert [(call.tool, call.outcome) for call in trace.calls] == [("search_code", "error")]


class BadArgumentSUT:
    async def retrieve(self, request, context):
        await context.gateway.call("codehub", "search_code", {"query": {"nested": 1}})
        return StubSUT().retrieve(request)


def test_runner_survives_malformed_tool_arguments(world_build, tmp_path):
    result = run(BadArgumentSUT(), RunConfig(
        cases_dir=ROOT / "gold" / "m0", out_dir=tmp_path / "bad-arg", seed=SEED, sut_name="bad-arg",
        world_build_dir=world_build, principal_aliases=load_principal_aliases(DEFAULT_M0_PRINCIPAL_ALIASES)))
    assert len(result.scores) == 3


def test_partial_startup_failure_closes_opened_sessions(world_build, monkeypatch):
    real_load = gateway_module.HubStore.load

    def failing_load(hub_dir):
        if Path(hub_dir).name == "dochub":
            raise RuntimeError("injected dochub load failure")
        return real_load(hub_dir)

    monkeypatch.setattr(gateway_module.HubStore, "load", staticmethod(failing_load))

    async def scenario():
        baseline = set(asyncio.all_tasks())
        gateway = HubGateway(world_build, ["codehub", "dochub", "skillhub"], _service(world_build))
        with pytest.raises(RuntimeError, match="injected dochub"):
            async with gateway:
                pass
        await asyncio.sleep(0)
        leftover = {task for task in asyncio.all_tasks() - baseline if not task.done()}
        return gateway._sessions, leftover

    sessions, leftover = anyio.run(scenario)
    assert sessions == {}
    assert leftover == set()
