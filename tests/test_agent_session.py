import asyncio
import json
import os
import sys
from pathlib import Path

import pytest

from sanctum_run.agent_session import (AttemptLedger,AttemptAlreadyDispatched,NativeEvents,
    claude_command,isolated_environment,run_session,stop_process_group)
from sanctum_run.agent_mcp import AgentMCP
from sanctum_run.delivery import DeliveryBudget,EvidenceNormalizer
from sanctum_run.gateway import HubGateway
from sanctum_hubs.tokens import TokenService
from tests.scenarios.conftest import scenario_world  # noqa: F401


def test_ledger_stops_replay_and_unaccounted_transitions(tmp_path):
    ledger=AttemptLedger(tmp_path/'attempts.json')
    ledger.update('a','dispatched',model='fixture')
    with pytest.raises(AttemptAlreadyDispatched):
        ledger.update('a','dispatched')
    ledger.update('a','deadline_exceeded',cost_usd=None)
    with pytest.raises(AttemptAlreadyDispatched):
        ledger.update('a','dispatched')
    with pytest.raises(ValueError):
        ledger.update('b','completed')


def test_round_mapping_deduplicates_chunks_and_checks_tools():
    events=NativeEvents(1,['mcp__evidence__search'])
    events.observe({'type':'system','subtype':'init','tools':['mcp__evidence__search']})
    events.observe({'type':'assistant','message':{'id':'m1'}})
    events.observe({'type':'assistant','message':{'id':'m1'}})
    events.observe({'type':'user','message':{'content':[{'type':'tool_result'}]}})
    assert len(events.assistant_ids)==1 and events.violation is None
    events.observe({'type':'assistant','message':{'id':'m2'}})
    assert events.violation=='agent_round_budget_exceeded'
    other=NativeEvents(2,[])
    other.observe({'type':'system','subtype':'init','tools':['Bash']})
    assert other.violation=='tool_inventory_mismatch'


def test_isolation_drops_inherited_credentials_and_customization(tmp_path,monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','must-not-inherit')
    monkeypatch.setenv('ANTHROPIC_API_KEY','must-not-inherit')
    monkeypatch.setenv('CLAUDE_CONFIG_DIR','/inherited')
    env=isolated_environment(tmp_path,{'ANTHROPIC_API_KEY':'explicit'})
    assert 'must-not-inherit' not in env.values()
    assert env['ANTHROPIC_API_KEY']=='explicit'
    assert env['CLAUDE_CONFIG_DIR']==str(tmp_path/'claude-config')
    command=claude_command('claude','explicit-model','low','id',tmp_path/'mcp',8,1)
    assert '--bare' in command and '--restricted' in command and '--disable-slash-commands' in command
    assert command[command.index('--tools')+1]==''
    allowed = claude_command('claude','explicit-model','low','id',tmp_path/'mcp',8,1,
                             allowed_tools=['mcp__evidence__sanctum_retrieve'])
    assert allowed[allowed.index('--allowedTools')+1]=='mcp__evidence__sanctum_retrieve'
    with pytest.raises(ValueError, match='evidence MCP'):
        claude_command('claude','explicit-model','low','id',tmp_path/'mcp',8,1,allowed_tools=['Bash'])


FIXTURE_AGENT='''
import asyncio,json,sys,os
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
def emit(value): print(json.dumps(value),flush=True)
async def main():
 config=json.load(open(sys.argv[1]))['mcpServers']['evidence']
 assert '/projects/' not in os.getcwd()
 assert not os.path.exists(os.path.join(os.environ['HOME'],'CLAUDE.md'))
 async with stdio_client(StdioServerParameters(command=config['command'],args=config['args'])) as streams:
  async with ClientSession(*streams) as session:
   await session.initialize()
   names=[t.name for t in (await session.list_tools()).tools]
   emit({'type':'system','subtype':'init','tools':['mcp__evidence__'+n for n in names]})
   emit({'type':'assistant','message':{'id':'m1','content':[{'type':'tool_use','id':'t1','name':names[0],'input':{}}]}})
   await session.call_tool('codehub__list_repos',{})
   emit({'type':'assistant','message':{'id':'m2','content':[{'type':'text','text':'Fixture answer'}]}})
   emit({'type':'result','subtype':'success','result':'Fixture answer','usage':{'input_tokens':1,'output_tokens':1},'total_cost_usd':0})
asyncio.run(main())
'''


def test_fixture_agent_exercises_real_mcp_and_durable_session(scenario_world,tmp_path):
    script=tmp_path/'fixture_agent.py';script.write_text(FIXTURE_AGENT)
    async def exercise():
        tokens=TokenService(scenario_world/'identity/principals.json','session-fixture')
        async with HubGateway(scenario_world,['codehub'],tokens) as gateway:
            adapter=await AgentMCP(gateway,tokens.issue_caller_token('kestrel-payments'),'direct',
                EvidenceNormalizer([]),DeliveryBudget(8000,4000)).initialize()
            result=await run_session(adapter,attempt_id='fixture-1',ledger=AttemptLedger(tmp_path/'ledger.json'),
                out=tmp_path/'run',prompt='Investigate without answer hints',
                fixture_command=[sys.executable,str(script),'{mcp_config}'],deadline_seconds=10)
            assert result['status']=='completed',result
            assert result['fixture'] is True and result['agent_rounds']==2
            assert result['process_group_termination_verified'] is True
            assert result['mcp_calls'][0]['backend_trace']['calls'][0]['audience_valid'] is True
            assert (tmp_path/'run/events.jsonl').is_file()
            assert json.loads((tmp_path/'ledger.json').read_text())['fixture-1']['state']=='completed'
    asyncio.run(exercise())


def test_deadline_and_paid_gate_without_inference(scenario_world,tmp_path):
    async def exercise():
        tokens=TokenService(scenario_world/'identity/principals.json','session-fixture')
        async with HubGateway(scenario_world,['codehub'],tokens) as gateway:
            adapter=await AgentMCP(gateway,tokens.issue_caller_token('kestrel-payments'),'direct',
                EvidenceNormalizer([]),DeliveryBudget(8000,4000)).initialize()
            with pytest.raises(ValueError,match='budget'):
                await run_session(adapter,attempt_id='paid-blocked',ledger=AttemptLedger(tmp_path/'ledger.json'),
                    out=tmp_path/'paid',prompt='never dispatched')
            assert not (tmp_path/'ledger.json').exists()
            result=await run_session(adapter,attempt_id='slow',ledger=AttemptLedger(tmp_path/'ledger.json'),
                out=tmp_path/'slow',prompt='fixture',deadline_seconds=.1,
                fixture_command=[sys.executable,'-c','import time;time.sleep(60)'])
            assert result['status']=='deadline_exceeded',result
            assert result['cost_usd'] is None
            assert result['process_group_termination_verified'] is True
    asyncio.run(exercise())


def test_cleanup_includes_owned_child(tmp_path):
    async def exercise():
        code='''import subprocess,signal,time,sys
child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])
def stop(*args):
 child.terminate();child.wait();sys.exit(0)
signal.signal(signal.SIGTERM,stop)
print(child.pid,flush=True)
time.sleep(60)
'''
        process=await asyncio.create_subprocess_exec(sys.executable,'-c',code,stdout=asyncio.subprocess.PIPE,start_new_session=True)
        child=int(await process.stdout.readline())
        assert await stop_process_group(process)
        with pytest.raises(ProcessLookupError):
            os.kill(child,0)
    asyncio.run(exercise())


def test_subscription_launcher_keeps_isolation_without_api_fallback(tmp_path, monkeypatch):
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'inherited-api-must-not-be-used')
    env = isolated_environment(tmp_path, {'CLAUDE_CODE_OAUTH_TOKEN': 'explicit-test-token'})
    assert env['CLAUDE_CODE_OAUTH_TOKEN'] == 'explicit-test-token'
    assert 'ANTHROPIC_API_KEY' not in env
    assert env['CLAUDE_CONFIG_DIR'] == str(tmp_path/'claude-config')
    with pytest.raises(ValueError, match='cannot be mixed'):
        isolated_environment(tmp_path, {'CLAUDE_CODE_OAUTH_TOKEN': 'test', 'ANTHROPIC_API_KEY': 'api'})
    command = claude_command('claude', 'claude-sonnet-5-5', 'low', 'id', tmp_path/'mcp', 8, 2,
        authentication_mode='subscription', allowed_tools=['mcp__evidence__sanctum_retrieve'])
    assert '--bare' not in command
    assert json.loads(command[command.index('--settings')+1])['disableAllHooks'] is True
    assert command[command.index('--setting-sources')+1] == ''
    assert '--strict-mcp-config' in command and '--disable-slash-commands' in command
    assert command[command.index('--tools')+1] == ''


def test_nested_cost_estimates_only_complete_single_request_usage():
    from sanctum_run.agent_session import nested_usage_cost
    prices={'jev-1.13.0':{'input_usd_per_million':0.042,'output_usd_per_million':0}}
    call={'model':'jev-1.13.0','outcome':'ok','calls':1,'usage':{'input_tokens':1000,'output_tokens':24}}
    assert nested_usage_cost([call],prices)==pytest.approx(0.000042)
    assert nested_usage_cost([call],{}) is None
    assert nested_usage_cost([{**call,'calls':2}],prices) is None
    assert nested_usage_cost([{**call,'usage':{'input_tokens':1000}}],prices) is None
    assert nested_usage_cost([{**call,'outcome':'timeout'}],prices) is None


def test_nested_predispatch_budget_refusal_has_zero_provider_cost():
    from sanctum_run.agent_session import nested_usage_cost
    refused={'calls':0,'outcome':'unavailable','reason':'over_budget','usage':None,'elapsed_ms':0,'model':None}
    assert nested_usage_cost([refused],{}) == 0
    assert nested_usage_cost([{**refused,'calls':1}],{}) is None
    assert nested_usage_cost([{**refused,'elapsed_ms':1}],{}) is None
