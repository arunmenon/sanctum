"""Out-of-process SUT (discrepancy register 16, fixed at M3).

`ProcessSUT` launches a SUT as its own process (`python -m sanctum_ref ...`) and speaks MCP to
it over two pipe pairs:

- the SUT's stdin/stdout carry `sanctum.retrieve` (runner = client, SUT = server);
- two extra descriptors carry the gateway proxy (SUT = client, runner's `GatewayProxy` = server).

The child gets a scrubbed environment: no token secret, no admin secret, and only `src` on its
path. Its only route to hubs is the proxy, which forwards through `HubGateway`, so every hub
call is observed by the runner. The caller token travels in the `sanctum.retrieve` request
`_meta`, never as a request field; the SUT hands it back on each proxy call and the proxy
checks it against the runner's binding.
"""
from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from io import TextIOWrapper
from pathlib import Path
from typing import Any, AsyncIterator, Optional

import anyio
from mcp import ClientSession, types
from mcp.server.stdio import stdio_server

from sanctum_contracts import EvidenceResponse, Receipt, RetrieveRequest
from sanctum_hubs.interfaces import META_REQUEST_ID

from .gateway import HubGateway
from .proxy import META_CALLER_TOKEN, GatewayProxy
from .sut import SUTContext

ROOT = Path(__file__).resolve().parents[2]
RETRIEVE_TOOL = "sanctum.retrieve"
# Environment variables passed through to the child. Everything else (including
# SANCTUM_LAB_TOKEN_SECRET and the admin secret) is dropped.
PASSTHROUGH_ENVIRONMENT = ("PATH", "HOME", "TMPDIR", "LANG", "TIKTOKEN_CACHE_DIR", "SYSTEMROOT")
# Slack on top of the request deadline before the runner gives up on the process.
RETRIEVE_GRACE_SECONDS = 30.0


class SUTProcessError(RuntimeError):
    """The SUT process failed a call or returned something that is not a response."""


class SUTTimeout(SUTProcessError):
    """One request outlived its deadline plus grace. The runner records the case as failed and
    goes on; it never takes the whole run down (register row 24)."""


def child_environment() -> dict[str, str]:
    environment = {name: os.environ[name] for name in PASSTHROUGH_ENVIRONMENT if name in os.environ}
    environment["PYTHONPATH"] = str(ROOT / "src")
    return environment


def _text_file(descriptor: int, mode: str):
    return anyio.wrap_file(TextIOWrapper(os.fdopen(descriptor, mode + "b", buffering=0), encoding="utf-8",
                                         line_buffering=mode == "w", write_through=True))


@asynccontextmanager
async def _line_transport(read_descriptor: int, write_descriptor: int):
    """MCP message streams over two pipe descriptors (newline-delimited JSON-RPC)."""
    async with stdio_server(stdin=_text_file(read_descriptor, "r"),
                            stdout=_text_file(write_descriptor, "w")) as streams:
        yield streams


class ProcessSUT:
    """Use via the runner: `run_cases` enters `open(gateway, world_build_dir)` before the cases."""

    def __init__(self, arguments: list[str], module: str = "sanctum_ref"):
        # extra seconds per request for runner-side System One rounds (set by the runner from the
        # provider profile); a slow model round is not a hung SUT
        self.extra_timeout_seconds = 0.0
        self._command = [sys.executable, "-m", module, *arguments]
        self._proxy: Optional[GatewayProxy] = None
        self._session: Optional[ClientSession] = None

    @property
    def proxy(self) -> Optional[GatewayProxy]:
        return self._proxy

    @asynccontextmanager
    async def open(self, gateway: HubGateway, world_build_dir: Path) -> AsyncIterator["ProcessSUT"]:
        self._proxy = await GatewayProxy.create(gateway, world_build_dir)
        sut_stdin_read, sut_stdin_write = os.pipe()
        sut_stdout_read, sut_stdout_write = os.pipe()
        proxy_request_read, proxy_request_write = os.pipe()     # SUT -> proxy
        proxy_response_read, proxy_response_write = os.pipe()   # proxy -> SUT
        child_descriptors = (proxy_request_write, proxy_response_read)
        command = [*self._command, "--proxy-read-fd", str(proxy_response_read),
                   "--proxy-write-fd", str(proxy_request_write)]
        process = await anyio.open_process(command, stdin=sut_stdin_read, stdout=sut_stdout_write,
                                           stderr=None, pass_fds=child_descriptors,
                                           env=child_environment(), cwd=str(ROOT))
        for descriptor in (sut_stdin_read, sut_stdout_write, *child_descriptors):
            os.close(descriptor)
        proxy_server = self._proxy.server
        try:
            async with anyio.create_task_group() as task_group:
                async with _line_transport(proxy_request_read, proxy_response_write) as (proxy_read, proxy_write):
                    task_group.start_soon(proxy_server.run, proxy_read, proxy_write,
                                          proxy_server.create_initialization_options())
                    async with _line_transport(sut_stdout_read, sut_stdin_write) as (sut_read, sut_write):
                        async with ClientSession(sut_read, sut_write) as session:
                            await session.initialize()
                            self._session = session
                            try:
                                yield self
                            finally:
                                self._session = None
                                # Ending the child closes its pipe ends, so every reader here sees EOF.
                                await _stop(process)
                task_group.cancel_scope.cancel()
        finally:
            await _stop(process)
            await process.aclose()

    async def retrieve(self, request: RetrieveRequest,
                       context: SUTContext) -> tuple[EvidenceResponse, Receipt]:
        if self._session is None or self._proxy is None:
            raise SUTProcessError("ProcessSUT is not open")
        self._proxy.bind(request.request_id, context.caller_token, context.gateway, query=request.query)
        try:
            params = types.CallToolRequestParams.model_validate({
                "name": RETRIEVE_TOOL, "arguments": request.model_dump(mode="json"),
                "_meta": {META_CALLER_TOKEN: context.caller_token, META_REQUEST_ID: request.request_id}})
            limit = request.deadline_ms / 1000.0 + RETRIEVE_GRACE_SECONDS + self.extra_timeout_seconds
            try:
                with anyio.fail_after(limit):
                    result = await self._session.send_request(
                        types.ClientRequest(types.CallToolRequest(method="tools/call", params=params)),
                        types.CallToolResult)
            except TimeoutError:
                raise SUTTimeout(f"request {request.request_id} gave no result within {limit:.1f}s") from None
        finally:
            self._proxy.unbind(request.request_id, context.gateway)
        return parse_retrieve_result(result)

    def anomalies(self) -> list[dict[str, Any]]:
        return self._proxy.anomalies() if self._proxy else []


async def _stop(process) -> None:
    if process.returncode is None:
        process.terminate()
        with anyio.move_on_after(5):
            await process.wait()
    if process.returncode is None:
        process.kill()
        await process.wait()


def parse_retrieve_result(result: types.CallToolResult) -> tuple[EvidenceResponse, Receipt]:
    if result.isError or result.structuredContent is None:
        text = "".join(block.text for block in result.content if isinstance(block, types.TextContent))
        raise SUTProcessError(f"sanctum.retrieve failed: {text[:500]}")
    body = result.structuredContent
    return EvidenceResponse.model_validate(body["response"]), Receipt.model_validate(body["receipt"])


__all__ = ["ProcessSUT", "RETRIEVE_TOOL", "SUTProcessError", "child_environment", "parse_retrieve_result"]
