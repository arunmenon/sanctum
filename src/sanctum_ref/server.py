"""`sanctum.retrieve` over MCP stdio, and the client side of the runner's gateway proxy.

The caller token arrives in the request `_meta` (never as a request field). It is handed back
to the proxy on every hub call so the proxy can check it against the runner's binding; the SUT
cannot mint, exchange or verify tokens itself. The registry is loaded per request, so a
registry that disappears or goes invalid mid-run fails closed from the next request on.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from io import TextIOWrapper
from pathlib import Path
from typing import Any, Optional

import anyio
from mcp import ClientSession, types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from sanctum_contracts import RetrieveRequest

from .config import ArmConfig
from .pipeline import MemoryState, Retriever
from .registry import RegistryUnavailable, load_registry

RETRIEVE_TOOL = "sanctum.retrieve"
META_CALLER_TOKEN = "lab/caller_token"
META_REQUEST_ID = "lab/request_id"
CALLER_TOOL = "caller_access"
CAPABILITIES_TOOL = "hub_capabilities"
CHANGES_TOOL = "change_events"
SYSTEM_ONE_TOOL = "system_one.decide"


class ProxyPort:
    """`HubPort` over the gateway proxy session, bound to one request."""

    def __init__(self, session: ClientSession, request_id: str, caller_token: Optional[str]):
        self._session = session
        self._meta = {META_REQUEST_ID: request_id, META_CALLER_TOKEN: caller_token}
        self.reader: Optional[str] = None

    async def _call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        params = types.CallToolRequestParams.model_validate(
            {"name": name, "arguments": arguments, "_meta": self._meta})
        result = await self._session.send_request(
            types.ClientRequest(types.CallToolRequest(method="tools/call", params=params)), types.CallToolResult)
        if result.isError or result.structuredContent is None:
            return {"error": {"code": "upstream_error", "message": "proxy error"}}
        return dict(result.structuredContent)

    async def call(self, hub_id: str, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return await self._call(f"{hub_id}.{tool}", arguments)

    async def caller_groups(self) -> Optional[list[str]]:
        body = await self._call(CALLER_TOOL, {})
        reader = body.get("reader")
        self.reader = reader if isinstance(reader, str) else None     # opaque, per verified caller
        groups = body.get("groups")
        return list(groups) if isinstance(groups, list) and "error" not in body else None

    async def system_one_decide(self, payload: dict[str, Any]) -> dict[str, Any]:
        """One decision round through the runner's System One broker (it holds any key)."""
        body = await self._call(SYSTEM_ONE_TOOL, payload)
        if "error" in body and "provider" not in body:
            return {"provider": "unknown", "unavailable_reason": "not_configured"}
        return body

    async def change_events(self, after_seq: int) -> list[dict[str, Any]]:
        body = await self._call(CHANGES_TOOL, {"after_seq": after_seq})
        events = body.get("events")
        return list(events) if isinstance(events, list) else []

    async def capabilities(self) -> Optional[dict[str, Any]]:
        body = await self._call(CAPABILITIES_TOOL, {})
        hubs = body.get("hubs")
        return dict(hubs) if isinstance(hubs, dict) else None


def build_server(arm: ArmConfig, registry_dir: Path, proxy: ClientSession,
                 memory_seed: Optional[Path] = None, provider=None, memory_release: Optional[str] = None) -> Server:
    server: Server = Server("sanctum-ref")
    memory = MemoryState(memory_seed, memory_release)            # one per process: release cache, change cursor
    schema = RetrieveRequest.model_json_schema()

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [types.Tool(name=RETRIEVE_TOOL, description="Retrieve evidence (HLD v5.1 §12).",
                           inputSchema=schema)]

    @server.call_tool(validate_input=False)
    async def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name != RETRIEVE_TOOL:
            raise ValueError(f"unknown tool {name!r}")
        meta = server.request_context.meta
        extra = dict(meta.model_extra or {}) if meta is not None else {}
        request = RetrieveRequest.model_validate(arguments)
        try:
            retriever = Retriever(arm, load_registry(registry_dir), memory=memory, provider=provider)
        except RegistryUnavailable as error:
            retriever = Retriever(arm, None, str(error), memory=memory, provider=provider)
        port = ProxyPort(proxy, request.request_id, extra.get(META_CALLER_TOKEN))
        response, receipt = await retriever.retrieve(request, port)
        return {"response": response.model_dump(mode="json"), "receipt": receipt.model_dump(mode="json")}

    return server


def _text_file(descriptor: int, mode: str):
    return anyio.wrap_file(TextIOWrapper(os.fdopen(descriptor, mode + "b", buffering=0), encoding="utf-8",
                                         line_buffering=mode == "w", write_through=True))


@asynccontextmanager
async def proxy_session(read_descriptor: int, write_descriptor: int):
    async with stdio_server(stdin=_text_file(read_descriptor, "r"),
                            stdout=_text_file(write_descriptor, "w")) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            yield session


async def serve(arm: ArmConfig, registry_dir: Path, proxy_read_fd: int, proxy_write_fd: int,
                memory_seed: Optional[Path] = None, provider=None, memory_release: Optional[str] = None) -> None:
    async with proxy_session(proxy_read_fd, proxy_write_fd) as proxy:
        server = build_server(arm, registry_dir, proxy, memory_seed, provider, memory_release)
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
