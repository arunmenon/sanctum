"""SUT protocol: `await sut.retrieve(request, context) -> (EvidenceResponse, Receipt)`.

`context` carries only the caller token (audience `sanctum`, minted by the runner for the
case's private principal) and a `GatewayHandle`. The principal itself never reaches the SUT.
"""
from __future__ import annotations

import json
from importlib import resources
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from sanctum_contracts import EvidenceResponse, Receipt, RetrieveRequest
from sanctum_stub.stub import StubSUT

from .gateway import GatewayHandle


@dataclass(frozen=True)
class SUTContext:
    caller_token: str
    gateway: GatewayHandle


@runtime_checkable
class SystemUnderTest(Protocol):
    async def retrieve(self, request: RetrieveRequest,
                       context: SUTContext) -> tuple[EvidenceResponse, Receipt]:
        ...


def load_call_plan(traces_dir: Path) -> dict[str, list[tuple[str, str]]]:
    """{request_id: [(hub_id, tool), ...]} from M0 fixture traces."""
    plan: dict[str, list[tuple[str, str]]] = {}
    for trace_path in sorted(Path(traces_dir).glob("*.json")):
        data = json.loads(trace_path.read_text(encoding="utf-8"))
        plan[data["request_id"]] = [(call["source_id"], call["tool"]) for call in data["calls"]]
    return plan


class MissingCannedResponse(LookupError):
    pass


class StubSUTAdapter:
    """Runs the unchanged `StubSUT` under the SUT protocol.

    The stub's canned responses were written against the M0 fixture traces, so the adapter
    replays that call plan through the gateway (query = the request's query). The trace the
    evaluator scores is still the gateway's observation, never the plan itself."""

    def __init__(self, call_plan: dict[str, list[tuple[str, str]]], stub: StubSUT | None = None):
        self._stub = stub or StubSUT()
        self._call_plan = call_plan

    def check_supported(self, requests: list[RetrieveRequest]) -> None:
        """Raise `MissingCannedResponse` before a run if any request has no canned response."""
        missing = [request.request_id for request in requests if not resources.files("sanctum_stub.responses").joinpath(f"{request.request_id}.json").is_file()]
        if missing:
            raise MissingCannedResponse(
                f"the stub has no canned responses for {', '.join(missing)}; it only answers gold/m0")

    async def retrieve(self, request: RetrieveRequest,
                       context: SUTContext) -> tuple[EvidenceResponse, Receipt]:
        for hub_id, tool in self._call_plan.get(request.request_id, []):
            await context.gateway.call(hub_id, tool, {"query": request.query})
        return self._stub.retrieve(request)
