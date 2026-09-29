"""FastMCP server per hub with the lab plan §6.1 tools (plan decisions 4 to 7).

Every tool call goes through `HubRuntime.call`: read the hub token and request id from the
MCP request `_meta`, authenticate (any failure is `denied_or_not_found`), draw the seeded
failure for `(request_id, hub, tool, call_index)`, sleep the drawn latency, fail or truncate
as drawn, then run the tool. Errors are returned as MCP error results whose text carries
`HubError.body()` as JSON (see `client.tool_payload`).

Search results: `{"results": [hit...], "total_matches": n, "partial": bool}`.
Lists: `{"items": [...], "partial": bool}`. Gets: `{"artifact": {...}}`.
"""

import inspect
import json
from collections import defaultdict
from typing import Any, Awaitable, Callable, Optional, Union

import anyio
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from .access import authenticate, readable
from .corpus import HubRow, HubStore
from .index import HubIndex, SearchFilters
from .interfaces import (
    META_HUB_TOKEN, META_REQUEST_ID, ErrorCode, FailureInjector, FailureOutcome, HubError,
    NoFailures, TokenClaims, TokenVerifier, denied_or_not_found,
)
from .versions import read_version, require_hub_version_reads, visible_versions

DEFAULT_TOP_K = 10
ToolBody = Callable[[TokenClaims], Union[Awaitable[dict[str, Any]], dict[str, Any]]]


def transport_meta(context: Context) -> dict[str, Any]:
    meta = context.request_context.meta
    if meta is None:
        return {}
    return dict(meta.model_extra or {})


class HubRuntime:
    """State shared by one hub's tools: store, index, verifier, failure knobs, call counters."""

    def __init__(self, store: HubStore, verifier: TokenVerifier,
                 failures: Optional[FailureInjector] = None):
        self.store = store
        self.index = HubIndex(store)
        self.verifier = verifier
        self.failures = failures or NoFailures()
        self._call_counts: dict[tuple[str, str], int] = defaultdict(int)

    @property
    def hub_id(self) -> str:
        return self.store.hub_id

    @property
    def principal_scoped(self) -> bool:
        return self.store.contract.principal_scoped

    def top_k(self, requested: Optional[int]) -> int:
        top_k = DEFAULT_TOP_K if requested is None else requested
        if not 1 <= top_k <= self.store.contract.max_results:
            raise HubError(ErrorCode.INVALID_ARGUMENT,
                           f"top_k must be between 1 and {self.store.contract.max_results}")
        return min(top_k, self.store.contract.max_results)

    def readable_row(self, artifact_id: str, claims: TokenClaims) -> bool:
        rows = self.store.versions_of(artifact_id)
        return bool(rows) and readable(rows[-1], claims, self.principal_scoped)

    def get_artifact(self, artifact_id: Optional[str], version: Optional[str],
                     claims: TokenClaims) -> dict[str, Any]:
        if not artifact_id or not self.readable_row(artifact_id, claims):
            raise denied_or_not_found()
        row = read_version(self.store, artifact_id, version)
        return {"artifact": artifact_view(row, visible_versions(self.store, artifact_id))}

    def first_readable(self, artifact_ids: list[str], claims: TokenClaims) -> Optional[str]:
        return next((artifact_id for artifact_id in artifact_ids if self.readable_row(artifact_id, claims)),
                    None)

    def search(self, query: str, claims: TokenClaims, filters: SearchFilters,
               top_k: Optional[int]) -> dict[str, Any]:
        hits, total = self.index.search(query, claims, filters, self.top_k(top_k))
        return {"results": [hit.to_dict() for hit in hits], "total_matches": total}

    def readable_current_rows(self, claims: TokenClaims) -> list[HubRow]:
        return [row for row in self.store.current_rows() if readable(row, claims, self.principal_scoped)]

    async def call(self, context: Context, tool: str, body: ToolBody) -> dict[str, Any]:
        meta = transport_meta(context)
        try:
            claims = authenticate(self.verifier, meta.get(META_HUB_TOKEN), self.hub_id)
            request_id = str(meta.get(META_REQUEST_ID) or "")
            call_index = self._call_counts[(request_id, tool)]
            self._call_counts[(request_id, tool)] += 1
            draw = self.failures.draw(request_id, self.hub_id, tool, call_index)
            if draw.latency_ms and self.failures.time_scale:
                await anyio.sleep(draw.latency_ms * self.failures.time_scale / 1000.0)
            if draw.outcome is FailureOutcome.TIMEOUT:
                raise HubError(ErrorCode.TIMEOUT)
            if draw.outcome is FailureOutcome.ERROR:
                raise HubError(ErrorCode.UPSTREAM_ERROR)
            result = body(claims)
            if inspect.isawaitable(result):
                result = await result
        except HubError as error:
            raise ToolError(json.dumps(error.body(), sort_keys=True)) from None
        return apply_partial(result, draw)


def apply_partial(result: dict[str, Any], draw) -> dict[str, Any]:
    result = dict(result)
    partial = False
    for key in ("results", "items"):
        if key in result:
            kept = draw.kept(len(result[key]))
            partial = partial or kept < len(result[key])
            result[key] = result[key][:kept]
    if "results" in result or "items" in result:
        result["partial"] = partial
    return result


def artifact_view(row: HubRow, versions: list[str]) -> dict[str, Any]:
    return {"artifact_id": row.artifact_id, "kind": row.kind, "title": row.title,
            "location": row.location, "path": row.path, "version": row.version,
            "environment": row.environment, "metadata": row.metadata, "text": row.text,
            "versions": versions}


def prefixed(value: Optional[str], prefix: str) -> Optional[str]:
    if value is None:
        return None
    return value if value.startswith(prefix) else prefix + value


def unsupported_filter(name: str, value: Optional[str]) -> None:
    if value is not None:
        raise HubError(ErrorCode.CAPABILITY_UNSUPPORTED, f"filter {name} is not supported")


# ---- per-hub tool registration ---------------------------------------------------------------
def _register_codehub(server: FastMCP, runtime: HubRuntime) -> None:
    @server.tool(description="Search code by keywords. Optional repo filter and ref (version).")
    async def search_code(context: Context, query: str, repo: Optional[str] = None,
                          ref: Optional[str] = None, top_k: Optional[int] = None) -> dict[str, Any]:
        filters = SearchFilters(location=prefixed(repo, "repo:"), version=ref)
        return await runtime.call(context, "search_code",
                                  lambda claims: runtime.search(query, claims, filters, top_k))

    @server.tool(description="Read a file by path, at the current version or at ref.")
    async def get_file(context: Context, path: str, ref: Optional[str] = None) -> dict[str, Any]:
        def body(claims: TokenClaims) -> dict[str, Any]:
            artifact_id = runtime.first_readable(runtime.store.ids_with_path(path), claims)
            return runtime.get_artifact(artifact_id, ref, claims)
        return await runtime.call(context, "get_file", body)

    @server.tool(description="List repositories you can read.")
    async def list_repos(context: Context) -> dict[str, Any]:
        def body(claims: TokenClaims) -> dict[str, Any]:
            return {"items": sorted({row.location for row in runtime.readable_current_rows(claims)
                                     if row.location})}
        return await runtime.call(context, "list_repos", body)


def _register_skillhub(server: FastMCP, runtime: HubRuntime) -> None:
    @server.tool(description="Search skills by keywords. Optional path_prefix filter.")
    async def search_skills(context: Context, query: str, path_prefix: Optional[str] = None,
                            top_k: Optional[int] = None) -> dict[str, Any]:
        filters = SearchFilters(path_prefix=path_prefix)
        return await runtime.call(context, "search_skills",
                                  lambda claims: runtime.search(query, claims, filters, top_k))

    @server.tool(description="Read a skill by path, at the current version or at version.")
    async def get_skill(context: Context, path: str, version: Optional[str] = None) -> dict[str, Any]:
        def body(claims: TokenClaims) -> dict[str, Any]:
            artifact_id = runtime.first_readable(runtime.store.ids_with_path(path), claims)
            return runtime.get_artifact(artifact_id, version, claims)
        return await runtime.call(context, "get_skill", body)

    @server.tool(description="List skill paths you can read, optionally under a prefix.")
    async def list_tree(context: Context, prefix: Optional[str] = None) -> dict[str, Any]:
        def body(claims: TokenClaims) -> dict[str, Any]:
            return {"items": sorted({row.path for row in runtime.readable_current_rows(claims)
                                     if row.path and row.path.startswith(prefix or "")})}
        return await runtime.call(context, "list_tree", body)


def _register_dochub(server: FastMCP, runtime: HubRuntime) -> None:
    @server.tool(description="Search pages by keywords. Optional space filter.")
    async def search(context: Context, query: str, space: Optional[str] = None,
                     top_k: Optional[int] = None) -> dict[str, Any]:
        filters = SearchFilters(location=prefixed(space, "space:"))
        return await runtime.call(context, "search",
                                  lambda claims: runtime.search(query, claims, filters, top_k))

    @server.tool(description="Read a page by id; version only where the space keeps versions.")
    async def get_page(context: Context, page_id: str, version: Optional[str] = None) -> dict[str, Any]:
        return await runtime.call(context, "get_page",
                                  lambda claims: runtime.get_artifact(page_id, version, claims))

    @server.tool(description="List spaces you can read.")
    async def list_spaces(context: Context) -> dict[str, Any]:
        def body(claims: TokenClaims) -> dict[str, Any]:
            return {"items": sorted({row.location for row in runtime.readable_current_rows(claims)
                                     if row.location})}
        return await runtime.call(context, "list_spaces", body)


def _register_memoryhub(server: FastMCP, runtime: HubRuntime) -> None:
    @server.tool(description="Search your own session notes by keywords.")
    async def search_sessions(context: Context, query: str, top_k: Optional[int] = None) -> dict[str, Any]:
        return await runtime.call(context, "search_sessions",
                                  lambda claims: runtime.search(query, claims, SearchFilters(), top_k))

    @server.tool(description="Read one of your session notes by artifact id or session id.")
    async def get_session(context: Context, id: str, version: Optional[str] = None) -> dict[str, Any]:
        def body(claims: TokenClaims) -> dict[str, Any]:
            require_hub_version_reads(runtime.store, version)
            candidates = [id] if runtime.store.versions_of(id) else runtime.store.ids_with_session(id)
            return runtime.get_artifact(runtime.first_readable(candidates, claims), None, claims)
        return await runtime.call(context, "get_session", body)


def _register_incidenthub(server: FastMCP, runtime: HubRuntime) -> None:
    @server.tool(description="Search incident tickets by keywords. Optional queue filter.")
    async def search_incidents(context: Context, query: str, queue: Optional[str] = None,
                               service: Optional[str] = None, since: Optional[str] = None,
                               top_k: Optional[int] = None) -> dict[str, Any]:
        def body(claims: TokenClaims) -> dict[str, Any]:
            unsupported_filter("service", service)
            unsupported_filter("since", since)
            filters = SearchFilters(location=prefixed(queue, "queue:"))
            return runtime.search(query, claims, filters, top_k)
        return await runtime.call(context, "search_incidents", body)

    @server.tool(description="Read an incident ticket by id.")
    async def get_incident(context: Context, id: str, version: Optional[str] = None) -> dict[str, Any]:
        def body(claims: TokenClaims) -> dict[str, Any]:
            require_hub_version_reads(runtime.store, version)
            return runtime.get_artifact(id, None, claims)
        return await runtime.call(context, "get_incident", body)


REGISTRARS = {
    "codehub": _register_codehub,
    "skillhub": _register_skillhub,
    "dochub": _register_dochub,
    "memoryhub": _register_memoryhub,
    "incidenthub": _register_incidenthub,
}
HUB_TOOLS = {
    "codehub": ("search_code", "get_file", "list_repos"),
    "skillhub": ("search_skills", "get_skill", "list_tree"),
    "dochub": ("search", "get_page", "list_spaces"),
    "memoryhub": ("search_sessions", "get_session"),
    "incidenthub": ("search_incidents", "get_incident"),
}


def build_hub_server(store: HubStore, verifier: TokenVerifier,
                     failures: Optional[FailureInjector] = None) -> FastMCP:
    """An MCP server exposing exactly the hub's §6.1 tools over `store`."""
    runtime = HubRuntime(store, verifier, failures)
    server = FastMCP(name=store.hub_id)
    REGISTRARS[store.hub_id](server, runtime)
    server.hub_runtime = runtime   # lab introspection (tests, admin wiring); not an MCP surface
    return server
