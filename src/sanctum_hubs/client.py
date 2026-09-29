"""Client helpers for calling hub tools with lab transport metadata.

`mcp` 1.12's `ClientSession.call_tool` cannot set request `_meta`, so `call_hub_tool` sends
the `tools/call` request itself with the hub token (and request id) in `_meta`.
`tool_payload` turns any result, success or error, into the JSON dict the hub produced.
"""
from __future__ import annotations

import json
from typing import Any, Optional

from mcp import ClientSession, types

from .interfaces import META_HUB_TOKEN, META_REQUEST_ID


async def call_hub_tool(session: ClientSession, tool: str, arguments: Optional[dict[str, Any]] = None,
                        hub_token: Optional[str] = None,
                        request_id: Optional[str] = None) -> types.CallToolResult:
    meta: dict[str, Any] = {}
    if hub_token is not None:
        meta[META_HUB_TOKEN] = hub_token
    if request_id is not None:
        meta[META_REQUEST_ID] = request_id
    params = types.CallToolRequestParams.model_validate(
        {"name": tool, "arguments": arguments or {}, "_meta": meta or None})
    request = types.ClientRequest(types.CallToolRequest(method="tools/call", params=params))
    return await session.send_request(request, types.CallToolResult)


def _parse_json_object(text: str) -> Optional[dict[str, Any]]:
    """The whole text as a JSON object, else the object after the first `{` (FastMCP prefixes
    tool errors with "Error executing tool ...: "). None when neither parses to a dict."""
    candidates = [text]
    start = text.find("{")
    if start > 0:
        candidates.append(text[start:])
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except ValueError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def tool_payload(result: types.CallToolResult) -> dict[str, Any]:
    """The hub's JSON body. Error results carry `{"error": {...}}` after FastMCP's prefix.

    Never raises on malformed text: an error result whose text is not a hub error body (for
    example a pydantic argument validation message) becomes `invalid_argument`, and a success
    result without a JSON object becomes `upstream_error`."""
    if not result.isError and result.structuredContent is not None:
        return dict(result.structuredContent)
    text = "".join(block.text for block in result.content if isinstance(block, types.TextContent))
    parsed = _parse_json_object(text)
    if result.isError:
        error = (parsed or {}).get("error")
        if isinstance(error, dict) and isinstance(error.get("code"), str):
            return {"error": error}
        return {"error": {"code": "invalid_argument", "message": "invalid argument"}}
    if parsed is None:
        return {"error": {"code": "upstream_error", "message": "hub error"}}
    return parsed
