"""Shared hub fixtures: one rendered build per session, a token service over its principals,
and in-memory MCP sessions to any hub."""
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from sanctum_hubs.client import call_hub_tool, tool_payload
from sanctum_hubs.corpus import HubStore
from sanctum_hubs.servers import build_hub_server
from sanctum_hubs.tokens import TokenService
from sanctum_world.render import build

ROOT = Path(__file__).resolve().parents[2]
WORLD_DIR = ROOT / "world"
SEED = 20260930
TOKEN_SECRET = "hub-test-secret"


@pytest.fixture(scope="session")
def hub_build(tmp_path_factory) -> Path:
    out_dir = tmp_path_factory.mktemp("hub-build") / "world"
    build(WORLD_DIR, SEED, out_dir)
    return out_dir


@pytest.fixture
def token_service(hub_build) -> TokenService:
    return TokenService(hub_build / "identity" / "principals.json", TOKEN_SECRET)


class HubClient:
    """Calls one hub's tools as one principal over an in-memory MCP session."""

    def __init__(self, session, hub_id: str, hub_token):
        self.session = session
        self.hub_id = hub_id
        self.hub_token = hub_token

    async def call(self, tool: str, token=..., request_id=None, **arguments) -> dict:
        hub_token = self.hub_token if token is ... else token
        result = await call_hub_tool(self.session, tool, arguments, hub_token, request_id)
        return tool_payload(result)


@pytest.fixture
def open_hub(hub_build, token_service):
    """`async with open_hub(hub_id, principal, failures=None, store=None) as client`."""
    @asynccontextmanager
    async def _open(hub_id: str, principal=None, failures=None, store=None):
        store = store or HubStore.load(hub_build / "hubs" / hub_id)
        server = build_hub_server(store, token_service, failures)
        hub_token = None
        if principal is not None:
            hub_token = token_service.exchange(token_service.issue_caller_token(principal), hub_id)
        async with create_connected_server_and_client_session(server._mcp_server) as session:
            yield HubClient(session, hub_id, hub_token)
    return _open
