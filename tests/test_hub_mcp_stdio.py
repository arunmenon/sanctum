"""Launch one hub as `python -m sanctum_hubs` over stdio and run one search (plan M2 task 2)."""
import os
import sys
from pathlib import Path

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from sanctum_hubs.client import call_hub_tool, tool_payload
from sanctum_hubs.tokens import TokenService
from sanctum_world.render import build

ROOT = Path(__file__).resolve().parents[1]
SECRET = "stdio-test-secret"


def test_codehub_over_stdio(tmp_path):
    build_dir = tmp_path / "world"
    build(ROOT / "world", 20260930, build_dir)
    tokens = TokenService(build_dir / "identity" / "principals.json", SECRET)
    hub_token = tokens.exchange(tokens.issue_caller_token("kestrel-payments"), "codehub")
    parameters = StdioServerParameters(
        command=sys.executable, args=["-m", "sanctum_hubs", "codehub", "--build", str(build_dir)],
        env={**os.environ, "PYTHONPATH": str(ROOT / "src"), "SANCTUM_LAB_TOKEN_SECRET": SECRET})

    async def scenario():
        async with stdio_client(parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await call_hub_tool(session, "search_code", {"query": "RetryConfig"},
                                             hub_token, request_id="stdio-1")
                payload = tool_payload(result)
                assert not result.isError and payload["results"]
                denied = tool_payload(await call_hub_tool(session, "list_repos", {}, None))
                assert denied["error"]["code"] == "denied_or_not_found"

    anyio.run(scenario)
