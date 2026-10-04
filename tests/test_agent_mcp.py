import anyio

from mcp.shared.memory import create_connected_server_and_client_session

from sanctum_hubs.client import tool_payload
from sanctum_hubs.tokens import TokenService
from sanctum_run.agent_mcp import AgentMCP
from sanctum_run.delivery import DeliveryBudget,EvidenceNormalizer
from sanctum_run.gateway import HubGateway
from tests.scenarios.conftest import scenario_world  # noqa: F401


def test_direct_mcp_initializes_and_keeps_identity_trusted(scenario_world):
    async def exercise():
        tokens=TokenService(scenario_world/'identity/principals.json','agent-mcp-fixture')
        caller=tokens.issue_caller_token('kestrel-payments')
        async with HubGateway(scenario_world,['codehub'],tokens) as gateway:
            adapter=await AgentMCP(gateway,caller,'direct',EvidenceNormalizer([]),DeliveryBudget(8000,4000)).initialize()
            async with create_connected_server_and_client_session(adapter.server) as session:
                tools=await session.list_tools()
                names={t.name for t in tools.tools}
                assert 'codehub__list_repos' in names
                assert not any('system_one' in n or 'caller' in n or 'sanctum' in n for n in names)
                result=tool_payload(await session.call_tool('codehub__list_repos',{}))
                assert result['evidence']
                repos=str(result['evidence'])
                assert 'repo:payments/' in repos and 'repo:identity/' not in repos
                assert caller not in str(result) and 'agent-mcp-fixture' not in str(result)
                refused=await adapter.dispatch('system_one.decide',{})
                assert refused['error']['code']=='tool_not_allowed'
            assert adapter.calls[0]['backend_trace']['calls'][0]['audience_valid'] is True
            await adapter.close()
    anyio.run(exercise)


def test_sanctum_mcp_exposes_one_tool_and_rejects_forged_identity(scenario_world):
    class UnusedRuntime:
        async def retrieve(self,*args):
            raise AssertionError('invalid arguments must not reach router')
    async def exercise():
        tokens=TokenService(scenario_world/'identity/principals.json','agent-mcp-fixture')
        async with HubGateway(scenario_world,['codehub'],tokens) as gateway:
            adapter=await AgentMCP(gateway,tokens.issue_caller_token('kestrel-payments'),'sanctum',
                EvidenceNormalizer([]),DeliveryBudget(8000,4000),sut=UnusedRuntime()).initialize()
            async with create_connected_server_and_client_session(adapter.server) as session:
                assert [t.name for t in (await session.list_tools()).tools]==['sanctum_retrieve']
                result=await adapter.dispatch('sanctum_retrieve',{'query':'test','caller_token':'forged'})
                assert result['error']['code']=='invalid_argument'
            await adapter.close()
    anyio.run(exercise)
