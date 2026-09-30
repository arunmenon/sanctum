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
an anomaly (`anomalies()`) that fails the run's integrity check. From M3 `sanctum_ref` runs
out of process (`process_sut.ProcessSUT`) and reaches hubs only through the MCP gateway proxy
(`proxy.GatewayProxy`), which stays in this process with the secrets.

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

import hashlib
import secrets
import uuid

import anyio
import yaml
from mcp.shared.memory import create_connected_server_and_client_session

from sanctum_eval.trace import ModelCall, ObservedCall, ObservedTrace
from sanctum_hubs.client import call_hub_tool, tool_payload
from sanctum_hubs.corpus import HubRow, HubStore
from sanctum_hubs.interfaces import (
    CALLER_AUDIENCE, AuthUnavailable, ErrorCode, FailureInjector, TokenRejected,
)
from sanctum_hubs.servers import build_hub_server
from sanctum_hubs.tokens import TokenService


class DuplicateRequestBinding(RuntimeError):
    """A request id already has an active invocation; credentials are never replaced."""


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


def _artifact_ids(payload: Any) -> set[str]:
    """Every `artifact_id` value anywhere in a hub response body."""
    found: set[str] = set()
    stack = [payload]
    while stack:
        value = stack.pop()
        if isinstance(value, dict):
            if isinstance(value.get("artifact_id"), str):
                found.add(value["artifact_id"])
            stack.extend(value.values())
        elif isinstance(value, list):
            stack.extend(value)
    return found


class HubGateway:
    """Use as `async with HubGateway(...) as gateway`; then `gateway.handle()` for a SUT."""

    def __init__(self, world_build_dir: Path, hub_ids: list[str], token_service: TokenService,
                 failures: Optional[FailureInjector] = None, token_mode: TokenMode = TokenMode.EXCHANGE,
                 call_timeout_seconds: Optional[float] = None, change_feed_path: Optional[Path] = None):
        self._world_build_dir = Path(world_build_dir)
        self._hub_ids = sorted(hub_ids)
        self._token_service = token_service
        self._failures = failures
        self._token_mode = TokenMode(token_mode)
        self._call_timeout_seconds = call_timeout_seconds
        self._sessions: dict[str, Any] = {}
        self._stores: dict[str, HubStore] = {}
        self.change_feed_path = Path(change_feed_path) if change_feed_path else None
        self._calls_by_request: dict[str, list[ObservedCall]] = {}
        self._model_calls_by_request: dict[str, list[ModelCall]] = {}
        # (hub, artifact id) pairs each request's own hub calls returned (for System One Round 3 reads)
        self._fetched_by_request: dict[str, set[tuple[str, str]]] = {}
        self.system_one = None      # runner-side SystemOneBroker, when the run configures a provider
        self._exit_stack: Optional[AsyncExitStack] = None
        # invocation id -> (request id, caller token, principal): fixed when the handle is made
        self._invocations: dict[str, tuple[str, Optional[str], Optional[str]]] = {}
        self._active_requests: dict[str, str] = {}   # request id -> its one active invocation
        self._reader_salt = secrets.token_hex(16)     # opaque reader ids are stable within this gateway
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

    def _anomaly(self, kind: str, request_id: Optional[str] = None, **details: Any) -> None:
        self._anomalies.append({"request_id": request_id or self._active_request_id, "kind": kind, **details})

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
                self._stores[hub_id] = store
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
        return ObservedTrace(request_id=request_id, calls=list(self._calls_by_request.get(request_id, [])),
                             model_calls=list(self._model_calls_by_request.get(request_id, [])))

    def record_model_call(self, request_id: str, call: ModelCall) -> None:
        """A broker-made System One call, observed apart from source calls."""
        self._model_calls_by_request.setdefault(request_id, []).append(call)

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

    def _open_invocation(self, request_id: str, caller_token: Optional[str]) -> str:
        if request_id in self._active_requests:
            self._anomaly("duplicate_request_binding", request_id=request_id)
            raise DuplicateRequestBinding(f"request {request_id!r} already has an active binding")
        invocation_id = uuid.uuid4().hex
        self._invocations[invocation_id] = (request_id, caller_token, self._principal_of(caller_token, CALLER_AUDIENCE))
        self._active_requests[request_id] = invocation_id
        return invocation_id

    def bind(self, request_id: str, caller_token: Optional[str]) -> None:
        """Legacy entry point: binds only a request id with no active invocation. Rebinding an
        active request never changes its credentials; it is refused and kept as an anomaly."""
        if request_id in self._active_requests:
            self._anomaly("duplicate_request_binding", request_id=request_id)
            return
        self._open_invocation(request_id, caller_token)

    def release(self, handle: "GatewayHandle") -> None:
        """End exactly this handle's invocation; a later call through it is denied."""
        invocation_id = handle._GatewayHandle__invocation_id
        request_id, _token, _principal = self._invocations.pop(invocation_id, (None, None, None))
        if request_id is not None and self._active_requests.get(request_id) == invocation_id:
            del self._active_requests[request_id]

    def _credentials(self, invocation_id: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        return self._invocations.get(invocation_id, (None, None, None))

    def _audience_valid(self, hub_token: Optional[str]) -> bool:
        """Only an exchanged token is scoped to the hub; a passthrough token has `aud == sanctum`."""
        return self._token_mode is TokenMode.EXCHANGE and bool(hub_token)

    async def list_hub_tools(self, hub_id: str) -> list[Any]:
        """The hub's MCP tool definitions (for the gateway proxy's tool list)."""
        return list((await self._sessions[hub_id].list_tools()).tools)

    def caller_groups(self, handle: "GatewayHandle") -> Optional[list[str]]:
        """The verified access groups of the handle's caller token (never the principal), or None
        when the token is invalid, the handle is released, or the token service is down."""
        _request_id, caller_token, _principal = self._credentials(handle._GatewayHandle__invocation_id)
        if not getattr(self._token_service, "available", True):
            return None
        try:
            return list(self._token_service.verify(caller_token, CALLER_AUDIENCE).groups)
        except TokenRejected:
            return None

    def reader_ref(self, handle: "GatewayHandle") -> Optional[str]:
        """A stable opaque id for the handle's verified caller (partitions per-reader state such
        as change-feed cursors); never the principal, and meaningless outside this gateway."""
        _request_id, caller_token, _principal = self._credentials(handle._GatewayHandle__invocation_id)
        try:
            subject = self._token_service.verify(caller_token, CALLER_AUDIENCE).sub
        except TokenRejected:
            return None
        return "reader-" + hashlib.sha256(f"{self._reader_salt}:{subject}".encode()).hexdigest()[:16]

    def read_for_request(self, handle: "GatewayHandle", source_id: str, artifact_id: str,
                         version: str) -> Optional[HubRow]:
        """The artifact version, for the runner's System One broker only, when the handle's verified
        caller may read it and this request's own hub calls returned it; else None."""
        request_id, caller_token, principal = self._credentials(handle._GatewayHandle__invocation_id)
        store = self._stores.get(source_id)
        if request_id is None or store is None or (source_id, artifact_id) not in self._fetched_by_request.get(request_id, set()):
            return None
        try:
            groups = set(self._token_service.verify(caller_token, CALLER_AUDIENCE).groups)
        except TokenRejected:
            return None
        row = store.at_version(artifact_id, version)
        if row is None or not set(row.acl) & groups:
            return None
        if row.owner is not None and row.owner != principal:
            return None                                  # session memory is personal
        return row

    @property
    def stores(self) -> dict[str, HubStore]:
        """Lab side only (admin API wiring in tests and scenario scripts); never reaches a SUT."""
        return dict(self._stores)

    def change_events(self, handle: "GatewayHandle", after_seq: int = 0) -> Optional[list[dict[str, Any]]]:
        """The handle's caller's per-reader change feed view (`ChangeFeed.events_for`), or None
        when the caller cannot be verified. Empty when the run has no feed."""
        _request_id, caller_token, _principal = self._credentials(handle._GatewayHandle__invocation_id)
        try:
            claims = self._token_service.verify(caller_token, CALLER_AUDIENCE)
        except TokenRejected:
            return None
        if self.change_feed_path is None:
            return []
        from sanctum_hubs.change_feed import ChangeFeed
        return [{"reader_seq": event.reader_seq, "hub": event.hub, "kind": str(event.kind), "subject": event.subject}
                for event in ChangeFeed(self.change_feed_path).events_for(claims, after_seq=after_seq)]

    def record_refused(self, request_id: str, hub_id: str, tool: str) -> None:
        """A call the proxy refused before it reached the gateway (binding mismatch)."""
        self._record(request_id, hub_id, tool, "denied", False)

    def _denied(self, request_id: str, hub_id: str, tool: str) -> dict[str, Any]:
        self._record(request_id, hub_id, tool, "denied", False)
        return {"error": {"code": ErrorCode.DENIED_OR_NOT_FOUND.value, "message": "not found or access denied"}}

    async def call(self, invocation_id: str, request_id: str, hub_id: str, tool: str,
                   arguments: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Call one hub tool for one invocation as its bound principal; returns the hub's JSON
        body (or an error body). A released or unknown invocation is denied and is an anomaly."""
        if invocation_id not in self._invocations:
            self._anomaly("call_on_inactive_binding", request_id=request_id, hub=hub_id)
            return self._denied(request_id, hub_id, tool)
        session = self._sessions.get(hub_id)
        if session is None:
            self._record(request_id, hub_id, tool, "error", False)
            return {"error": {"code": ErrorCode.UPSTREAM_ERROR.value, "message": "unknown hub"}}
        _request_id, caller_token, bound_principal = self._credentials(invocation_id)
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
            if outcome == "ok":
                self._fetched_by_request.setdefault(request_id, set()).update(
                    (hub_id, artifact_id) for artifact_id in _artifact_ids(payload))
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
        return GatewayHandle(self, self._open_invocation(request_id, caller_token), request_id)


class GatewayHandle:
    """What a SUT holds: hub ids and a call method bound to one request. The gateway itself is
    kept in a name-mangled slot so the SUT's public surface carries no hub internals. This is
    not a security boundary against hostile in-process code; see the module docstring."""
    __slots__ = ("__gateway", "__invocation_id", "__request_id")

    def __init__(self, gateway: HubGateway, invocation_id: str, request_id: str):
        self.__gateway = gateway
        self.__invocation_id = invocation_id
        self.__request_id = request_id

    @property
    def hub_ids(self) -> list[str]:
        return self.__gateway.hub_ids

    async def call(self, hub_id: str, tool: str, arguments: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        return await self.__gateway.call(self.__invocation_id, self.__request_id, hub_id, tool, arguments)


__all__ = ["DuplicateRequestBinding", "GatewayHandle", "HubGateway", "TokenMode", "released_hub_ids"]
