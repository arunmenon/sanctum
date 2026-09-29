"""The only path from a SUT to the hubs.

`HubGateway` owns in-memory MCP sessions to the released hubs, exchanges the caller's token
for a hub-scoped token on the SUT's behalf, calls the tool with `call_hub_tool`, and records
one `ObservedCall` per attempt, including denied, failed and timed-out ones. The SUT gets a
`GatewayHandle`, which exposes `hub_ids` and `call` and nothing else (no store, no token
service, no secret).

Request binding: `handle(request_id, caller_token)` binds the runner-issued caller token (and
its principal) to the request; `GatewayHandle.call` takes no token. Every exchanged hub token
must name the bound principal, or the call is recorded `denied` with `audience_valid` false.

In-process SUTs are trusted code (discrepancy register): Python cannot stop a SUT from
walking object graphs to the token service. The gateway therefore watches the token service
while a SUT call is in flight, and any issuance or exchange it did not make itself is kept as
an anomaly (`anomalies()`) that fails the run's integrity check. From M3 the SUT runs out of
process and reaches hubs only through an MCP gateway proxy that holds the secrets.

Outcome mapping:
- token exchange refused or token service unavailable: `denied`, no hub call is made (fail
  closed), `audience_valid` false.
- hub `denied_or_not_found`: `denied`; hub `timeout` or the gateway deadline: `timeout`;
  any other hub error or an unknown hub: `error`.
"""
from __future__ import annotations

from contextlib import AsyncExitStack, contextmanager
from enum import StrEnum
from pathlib import Path
from typing import Any, Optional

import anyio
import yaml
from mcp.shared.memory import create_connected_server_and_client_session

from sanctum_eval.trace import ObservedCall, ObservedTrace
from sanctum_hubs.client import call_hub_tool, tool_payload
from sanctum_hubs.corpus import HubStore
from sanctum_hubs.interfaces import (
    CALLER_AUDIENCE, AuthUnavailable, ErrorCode, FailureInjector, TokenRejected,
)
from sanctum_hubs.servers import build_hub_server
from sanctum_hubs.tokens import TokenService


class TokenMode(StrEnum):
    """How the gateway presents credentials. Only `exchange` is a correct gateway; the others
    exist so tests can show that hubs reject missing tokens and caller-token passthrough."""
    EXCHANGE = "exchange"
    PASSTHROUGH = "passthrough"
    NONE = "none"


def released_hub_ids(hubs_config_path: Path, include_held_back: bool = False) -> list[str]:
    hubs = (yaml.safe_load(Path(hubs_config_path).read_text(encoding="utf-8")) or {})["hubs"]
    return sorted(hub_id for hub_id, hub in hubs.items()
                  if include_held_back or not hub.get("held_back", False))


def _outcome_from_payload(payload: dict[str, Any]) -> str:
    code = (payload.get("error") or {}).get("code")
    if code == ErrorCode.DENIED_OR_NOT_FOUND:
        return "denied"
    if code == ErrorCode.TIMEOUT:
        return "timeout"
    return "error"


class HubGateway:
    """Use as `async with HubGateway(...) as gateway`; then `gateway.handle()` for a SUT."""

    def __init__(self, world_build_dir: Path, hub_ids: list[str], token_service: TokenService,
                 failures: Optional[FailureInjector] = None, token_mode: TokenMode = TokenMode.EXCHANGE,
                 call_timeout_seconds: Optional[float] = None):
        self._world_build_dir = Path(world_build_dir)
        self._hub_ids = sorted(hub_ids)
        self._token_service = token_service
        self._failures = failures
        self._token_mode = TokenMode(token_mode)
        self._call_timeout_seconds = call_timeout_seconds
        self._sessions: dict[str, Any] = {}
        self._calls_by_request: dict[str, list[ObservedCall]] = {}
        self._exit_stack: Optional[AsyncExitStack] = None
        self._bindings: dict[str, tuple[Optional[str], Optional[str]]] = {}
        self._anomalies: list[dict[str, Any]] = []
        self._active_request_id: Optional[str] = None
        self._gateway_exchanging = False
        self._watch_token_service()

    # ---- token service watch -----------------------------------------------------------------
    def _watch_token_service(self) -> None:
        """Wrap the service's minting methods on this instance so that any issuance or exchange
        during a SUT call that the gateway did not make itself is recorded as an anomaly."""
        service = self._token_service
        original_issue = service.issue_caller_token
        original_exchange = service.exchange

        def watched_issue(principal: str) -> str:
            if self._active_request_id is not None:
                self._anomaly("caller_token_issued_during_sut_call", principal=principal)
            return original_issue(principal)

        def watched_exchange(caller_token: Optional[str], audience: str) -> str:
            if self._active_request_id is not None and not self._gateway_exchanging:
                self._anomaly("token_exchanged_outside_gateway", audience=audience)
            return original_exchange(caller_token, audience)

        service.issue_caller_token = watched_issue
        service.exchange = watched_exchange

    def _anomaly(self, kind: str, **details: Any) -> None:
        self._anomalies.append({"request_id": self._active_request_id, "kind": kind, **details})

    def anomalies(self, request_id: Optional[str] = None) -> list[dict[str, Any]]:
        return [dict(entry) for entry in self._anomalies
                if request_id is None or entry["request_id"] == request_id]

    @contextmanager
    def sut_call(self, request_id: str):
        """Mark the window in which a SUT runs for `request_id`."""
        self._active_request_id = request_id
        try:
            yield
        finally:
            self._active_request_id = None

    async def __aenter__(self) -> "HubGateway":
        self._exit_stack = AsyncExitStack()
        await self._exit_stack.__aenter__()
        try:
            for hub_id in self._hub_ids:
                store = HubStore.load(self._world_build_dir / "hubs" / hub_id)
                server = build_hub_server(store, self._token_service, self._failures)
                self._sessions[hub_id] = await self._exit_stack.enter_async_context(
                    create_connected_server_and_client_session(server._mcp_server))
        except BaseException:
            # a later hub failed to start: close the sessions already opened, then re-raise
            self._sessions.clear()
            await self._exit_stack.aclose()
            raise
        return self

    async def __aexit__(self, *exc_info) -> None:
        self._sessions.clear()
        await self._exit_stack.__aexit__(*exc_info)

    @property
    def hub_ids(self) -> list[str]:
        return list(self._hub_ids)

    def trace(self, request_id: str) -> ObservedTrace:
        return ObservedTrace(request_id=request_id, calls=list(self._calls_by_request.get(request_id, [])))

    def _record(self, request_id: str, hub_id: str, tool: str, outcome: str, audience_valid: bool) -> None:
        self._calls_by_request.setdefault(request_id, []).append(
            ObservedCall(source_id=hub_id, tool=tool, outcome=outcome, audience_valid=audience_valid))

    def _hub_token(self, caller_token: Optional[str], hub_id: str) -> Optional[str]:
        """Raises `TokenRejected` or `AuthUnavailable` when exchange is refused."""
        if self._token_mode is TokenMode.NONE:
            return None
        if self._token_mode is TokenMode.PASSTHROUGH:
            return caller_token
        self._gateway_exchanging = True
        try:
            return self._token_service.exchange(caller_token, hub_id)
        finally:
            self._gateway_exchanging = False

    def _principal_of(self, token: Optional[str], audience: str) -> Optional[str]:
        try:
            return self._token_service.verify(token, audience).sub
        except TokenRejected:
            return None

    def bind(self, request_id: str, caller_token: Optional[str]) -> None:
        self._bindings[request_id] = (caller_token, self._principal_of(caller_token, CALLER_AUDIENCE))

    def _audience_valid(self, hub_token: Optional[str]) -> bool:
        """Only an exchanged token is scoped to the hub; a passthrough token has `aud == sanctum`."""
        return self._token_mode is TokenMode.EXCHANGE and bool(hub_token)

    def _denied(self, request_id: str, hub_id: str, tool: str) -> dict[str, Any]:
        self._record(request_id, hub_id, tool, "denied", False)
        return {"error": {"code": ErrorCode.DENIED_OR_NOT_FOUND.value, "message": "not found or access denied"}}

    async def call(self, request_id: str, hub_id: str, tool: str,
                   arguments: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Call one hub tool for one request as its bound principal; returns the hub's JSON body
        (or an error body). A request with no binding is denied."""
        session = self._sessions.get(hub_id)
        if session is None:
            self._record(request_id, hub_id, tool, "error", False)
            return {"error": {"code": ErrorCode.UPSTREAM_ERROR.value, "message": "unknown hub"}}
        caller_token, bound_principal = self._bindings.get(request_id, (None, None))
        try:
            hub_token = self._hub_token(caller_token, hub_id)
        except (TokenRejected, AuthUnavailable):
            return self._denied(request_id, hub_id, tool)
        if (self._token_mode is TokenMode.EXCHANGE
                and (bound_principal is None or self._principal_of(hub_token, hub_id) != bound_principal)):
            self._anomaly("principal_mismatch", hub=hub_id)
            return self._denied(request_id, hub_id, tool)
        audience_valid = self._audience_valid(hub_token)
        # Every attempt that reaches the hub is recorded exactly once, in `finally`, including
        # when the SUT's own deadline cancels it (recorded as `timeout`, then re-raised).
        outcome = "timeout"
        try:
            with anyio.fail_after(self._call_timeout_seconds):
                result = await call_hub_tool(session, tool, arguments, hub_token, request_id)
            payload = tool_payload(result)
            outcome = _outcome_from_payload(payload) if result.isError or "error" in payload else "ok"
            return payload
        except TimeoutError:
            outcome = "timeout"
            return {"error": {"code": ErrorCode.TIMEOUT.value, "message": "hub timed out"}}
        except anyio.get_cancelled_exc_class():
            outcome = "timeout"
            raise
        except Exception:
            outcome = "error"
            return {"error": {"code": ErrorCode.UPSTREAM_ERROR.value, "message": "hub error"}}
        finally:
            self._record(request_id, hub_id, tool, outcome, audience_valid)

    def handle(self, request_id: str, caller_token: Optional[str]) -> "GatewayHandle":
        """Bind `caller_token` to `request_id` and return the SUT's handle for it."""
        self.bind(request_id, caller_token)
        return GatewayHandle(self, request_id)


class GatewayHandle:
    """What a SUT holds: hub ids and a call method bound to one request. The gateway itself is
    kept in a name-mangled slot so the SUT's public surface carries no hub internals. This is
    not a security boundary against hostile in-process code; see the module docstring."""
    __slots__ = ("__gateway", "__request_id")

    def __init__(self, gateway: HubGateway, request_id: str):
        self.__gateway = gateway
        self.__request_id = request_id

    @property
    def hub_ids(self) -> list[str]:
        return self.__gateway.hub_ids

    async def call(self, hub_id: str, tool: str, arguments: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        return await self.__gateway.call(self.__request_id, hub_id, tool, arguments)


__all__ = ["GatewayHandle", "HubGateway", "TokenMode", "released_hub_ids"]
