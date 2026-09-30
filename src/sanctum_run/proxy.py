"""Gateway proxy: the only MCP surface an out-of-process SUT can reach (discrepancy register 16).

The proxy runs in the runner's process and serves MCP over a pipe pair handed to the SUT
process. It exposes every released hub tool as `<hub>.<tool>` (with the hub's own input
schema) plus `hub_capabilities`, `change_events` (the caller's per-reader invalidation feed) and `caller_access` (the verified groups of the bound caller token, the
broker's "who is asking" stage; never the principal), and forwards each call through `HubGateway`, which holds the
token service and its secret. The SUT therefore never sees a secret or a hub token, and every
forwarded call is recorded by the gateway as an `ObservedCall`.

Binding: before each case the runner calls `bind(request_id, caller_token, handle)`. A tool
call is forwarded only if its `_meta` carries that request id and caller token; any other call
(no binding, a stale request id, another token) is refused with the uniform denied body,
recorded as a `denied` observation for the bound request when there is one, and kept as an
anomaly. `hub_capabilities` is not a hub call and is not recorded.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from mcp import types
from mcp.server.lowlevel import Server

from sanctum_hubs.interfaces import META_REQUEST_ID, ErrorCode

from .gateway import DuplicateRequestBinding, GatewayHandle, HubGateway
from .system_one_broker import DECIDE_TOOL

META_CALLER_TOKEN = "lab/caller_token"
CAPABILITIES_TOOL = "hub_capabilities"
CALLER_TOOL = "caller_access"
CHANGES_TOOL = "change_events"
TOOL_SEPARATOR = "."


def _denied_body() -> dict[str, Any]:
    return {"error": {"code": ErrorCode.DENIED_OR_NOT_FOUND.value, "message": "not found or access denied"}}


class GatewayProxy:
    """Build with `await GatewayProxy.create(gateway, world_build_dir)`; serve `proxy.server`."""

    def __init__(self, gateway: HubGateway, capabilities: dict[str, Any],
                 tools: list[types.Tool]):
        self._gateway = gateway
        self._capabilities = capabilities
        self._tools = tools
        self._tool_targets = {tool.name: tuple(tool.name.split(TOOL_SEPARATOR, 1)) for tool in tools}
        # request_id -> (caller_token, handle); several requests may be in flight at once (M8)
        self._bindings: dict[str, tuple[str, GatewayHandle]] = {}
        self._queries: dict[str, str] = {}
        self._anomalies: list[dict[str, Any]] = []
        self.server = self._build_server()

    @classmethod
    async def create(cls, gateway: HubGateway, world_build_dir: Path) -> "GatewayProxy":
        capabilities = {
            hub_id: json.loads((Path(world_build_dir) / "hubs" / hub_id / "capabilities.json")
                               .read_text(encoding="utf-8"))
            for hub_id in gateway.hub_ids
        }
        tools: list[types.Tool] = []
        for hub_id in gateway.hub_ids:
            for tool in await gateway.list_hub_tools(hub_id):
                tools.append(types.Tool(name=f"{hub_id}{TOOL_SEPARATOR}{tool.name}",
                                        description=tool.description, inputSchema=tool.inputSchema))
        tools.append(types.Tool(name=CALLER_TOOL, description="Verified access groups of the bound caller.",
                                inputSchema={"type": "object", "properties": {}}))
        tools.append(types.Tool(name=CHANGES_TOOL, description="The bound caller's change feed after a cursor.",
                                inputSchema={"type": "object", "properties": {"after_seq": {"type": "integer"}}}))
        tools.append(types.Tool(
            name=DECIDE_TOOL, description="Ask the run's System One provider (runner-side broker).",
            inputSchema={"type": "object", "required": ["questions"], "properties": {
                "round": {"type": "string"},
                "items": {"type": "object"},
                "questions": {"type": "object", "additionalProperties": {"type": "object", "required": ["type"], "properties": {
                    "type": {"enum": ["noul", "choice", "score"]}, "instructions": {"type": "string"},
                    "criteria": {"type": ["array", "object"]}}}}}}))
        tools.append(types.Tool(name=CAPABILITIES_TOOL, description="Released hubs and their capabilities.",
                                inputSchema={"type": "object", "properties": {}}))
        return cls(gateway, capabilities, tools)

    # ---- binding ------------------------------------------------------------------------------
    def bind(self, request_id: str, caller_token: str, handle: GatewayHandle, query: Optional[str] = None) -> None:
        """Bind one request id to one gateway invocation. The handle must be for that request id,
        and an active binding is never replaced (duplicate ids are refused, with an anomaly)."""
        if handle._GatewayHandle__request_id != request_id:
            self._anomalies.append({"request_id": request_id, "kind": "binding_request_mismatch"})
            raise DuplicateRequestBinding("handle is for another request id")
        if request_id in self._bindings:
            self._anomalies.append({"request_id": request_id, "kind": "duplicate_request_binding"})
            raise DuplicateRequestBinding(f"request {request_id!r} is already bound")
        self._bindings[request_id] = (caller_token, handle)
        self._queries[request_id] = query or ""     # the trusted request text, for the System One broker

    def unbind(self, request_id: str, handle: Optional[GatewayHandle] = None) -> None:
        """Drop this request's binding only if it is still the given handle's (invocation-specific)."""
        binding = self._bindings.get(request_id)
        if binding is not None and (handle is None or binding[1] is handle):
            del self._bindings[request_id]
            self._queries.pop(request_id, None)

    def anomalies(self) -> list[dict[str, Any]]:
        return [dict(entry) for entry in self._anomalies]

    # ---- MCP surface --------------------------------------------------------------------------
    def _build_server(self) -> Server:
        server: Server = Server("sanctum-lab-gateway-proxy")

        @server.list_tools()
        async def list_tools() -> list[types.Tool]:
            return list(self._tools)

        @server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
            meta = server.request_context.meta
            extra = dict(meta.model_extra or {}) if meta is not None else {}
            return await self.dispatch(name, arguments, extra.get(META_REQUEST_ID), extra.get(META_CALLER_TOKEN))

        return server

    async def dispatch(self, name: str, arguments: dict[str, Any], request_id: Optional[str],
                       caller_token: Optional[str]) -> dict[str, Any]:
        if name == CAPABILITIES_TOOL:
            return {"hubs": self._capabilities}
        binding = self._bindings.get(request_id) if request_id is not None else None
        bound = binding is not None and binding[0] == caller_token
        if name == CALLER_TOOL:
            groups = self._gateway.caller_groups(binding[1]) if bound else None
            if groups is None:
                return {"error": {"code": "auth_unavailable_or_denied", "message": "caller not verified"}}
            return {"groups": groups, "reader": self._gateway.reader_ref(binding[1])}
        if name == CHANGES_TOOL:
            events = self._gateway.change_events(binding[1], int(arguments.get("after_seq") or 0)) if bound else None
            if events is None:
                return {"error": {"code": "auth_unavailable_or_denied", "message": "caller not verified"}}
            return {"events": events}
        if name == DECIDE_TOOL:
            broker = self._gateway.system_one
            if not bound:
                self._anomalies.append({"request_id": request_id if binding is not None else None,
                                        "kind": "proxy_call_outside_binding", "hub": "system_one", "tool": "decide"})
                return _denied_body()
            if broker is None:
                return {"error": {"code": "decision_layer_unavailable", "message": "no System One provider in this run"}}
            return await broker.decide(self._gateway, request_id, self._queries.get(request_id, ""), arguments,
                                       handle=binding[1])
        target = self._tool_targets.get(name)
        if target is None:
            return {"error": {"code": ErrorCode.INVALID_ARGUMENT.value, "message": "invalid argument: unknown tool"}}
        hub_id, tool = target
        if not bound:
            # Attribute the refusal to the request it claims when that one is bound (forged token),
            # else to the only request in flight, else to the claimed id itself; always an anomaly.
            if binding is not None:
                refused_for = request_id
            elif len(self._bindings) == 1:
                refused_for = next(iter(self._bindings))
            else:
                refused_for = request_id or "unbound"
            self._anomalies.append({"request_id": refused_for if self._bindings else None,
                                    "kind": "proxy_call_outside_binding", "hub": hub_id, "tool": tool})
            if self._bindings:
                self._gateway.record_refused(refused_for, hub_id, tool)
            return _denied_body()
        return await binding[1].call(hub_id, tool, arguments)


__all__ = ["CALLER_TOOL", "CAPABILITIES_TOOL", "GatewayProxy", "META_CALLER_TOKEN", "TOOL_SEPARATOR"]
