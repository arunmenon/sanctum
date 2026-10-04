"""Execute declared schedule items through the shared gateway/controller."""
import json
import secrets
import sys
from contextlib import AsyncExitStack
from pathlib import Path

from sanctum_hubs.tokens import TokenService
from sanctum_run.agent_mcp import AgentMCP
from sanctum_run.agent_schedule import file_hash,load_experiment,plan_schedule,report_schedule
from sanctum_run.agent_session import AttemptLedger,run_session,write_atomic
from sanctum_run.bundle import _file
from sanctum_run.delivery import DeliveryBudget,EvidenceNormalizer
from sanctum_run.gateway import HubGateway
from sanctum_run.spend import SpendLedger
from sanctum_run.agent_runtime import open_agent_runtime


async def run_attempt(config_path:Path,out:Path,*,task_id:str,arm:str, repetition=0,fixture=False,credentials=None):
    config,summary=load_experiment(config_path)
    root=config_path.resolve().parent
    schedule=plan_schedule(config_path,out)
    selected=next((a for a in schedule['attempts'] if a['task_id']==task_id and a['arm']==arm and a['repetition']==repetition),None)
    if not selected:
        raise ValueError('attempt is not in the frozen schedule')
    agent=config.get('agent',{})
    expected_auth=agent.get('authentication_mode','api')
    actual_auth='subscription' if (credentials or {}).get('CLAUDE_CODE_OAUTH_TOKEN') else 'api'
    if not fixture and actual_auth!=expected_auth:
        raise ValueError('Claude authentication does not match the declared billing mode')
    limits=config['limits'];arm_config=config['arms'][arm]
    surface=arm_config['tool_surface']
    if not fixture:
        if config.get('readiness',{}).get('paid_budget_approved') is not True:
            raise ValueError('paid Claude budget gate is closed')
        if config.get('readiness',{}).get('agent_isolation_verified') is not True:
            raise ValueError('installed Claude isolation/round probes are not verified')
    if surface=='sanctum_only' and arm_config.get('runtime_ready') is not True:
        raise ValueError('Sanctum memory/System One runtime is not verified; no fallback is allowed')
    corpus=_file(root,config['corpus']['manifest']).parent
    identity=config['caller']
    principal_file=_file(root,identity['principal_file'])
    if file_hash(principal_file)!=identity['expected_sha256']:
        raise ValueError('caller identity snapshot hash mismatch')
    rows=[]
    for p in sorted((corpus/'hubs').glob('*/artifacts.jsonl')):
        for line in p.read_text().splitlines():
            r=json.loads(line);r['source_id']=p.parent.name;rows.append(r)
    hub_ids=sorted({r['source_id'] for r in rows})
    tokens=TokenService(principal_file,secrets.token_hex(32))
    caller=tokens.issue_caller_token(identity['principal'])
    ledger=AttemptLedger(out/'attempts.json')
    task=next(json.loads(line) for line in _file(root,config['tasks']).read_text().splitlines() if json.loads(line)['task_id']==task_id)
    instructions=_file(root,config['instructions']).read_text()
    prompt=instructions+'\n\nTask:\n'+task['prompt']+'\nCaller requirements:\n'+json.dumps(task.get('caller_requirements',[]))
    async with AsyncExitStack() as stack:
        gateway=await stack.enter_async_context(HubGateway(corpus,hub_ids,tokens,
            call_timeout_seconds=limits['task_deadline_seconds']))
        sut=None
        if surface=='sanctum_only':
            runtime_file=_file(root,arm_config['runtime_file'])
            if file_hash(runtime_file)!=arm_config['runtime_sha256']:
                raise ValueError('runtime connection changed after verification')
            runtime=json.loads(runtime_file.read_text())
            sut=await stack.enter_async_context(open_agent_runtime(root,runtime,gateway,corpus,
                out/'attempts'/selected['attempt_id'],fixture=fixture))
        budget=DeliveryBudget(limits['cumulative_evidence_tokens'],limits['tool_response_evidence_tokens'])
        adapter=await AgentMCP(gateway,caller,'direct' if surface=='direct_hubs' else 'sanctum',
            EvidenceNormalizer(rows),budget,sut=sut,deadline_seconds=limits['task_deadline_seconds'],
            max_calls=limits.get('agent_tool_calls',32)).initialize()
        fixture_command=None
        if fixture:
            fixture_command=[sys.executable,str(Path(__file__).with_name('fixture_agent.py')),'--mcp-config','{mcp_config}']
        spend=None if fixture else SpendLedger(_file(root,config['spend']['ledger']))
        result=await run_session(adapter,attempt_id=selected['attempt_id'],ledger=ledger,
            out=out/'attempts'/selected['attempt_id'],prompt=prompt,model=agent.get('model'),effort=agent.get('effort','low'),
            deadline_seconds=limits['task_deadline_seconds'],max_rounds=limits['agent_rounds'],
            approved_spend_usd=0 if fixture else limits['total_inference_spend_usd'],credentials=credentials,
            fixture_command=fixture_command,spend_ledger=spend,
            max_exposure_usd=None if fixture else config['spend']['max_exposure_usd'],
            exposure_verified=False if fixture else config['spend'].get('exposure_verified',False),
            model_prices=None if fixture else config['spend'].get('model_prices'))
    result.update(task_id=task_id,arm=arm,repetition=repetition,schedule_sha256=file_hash(out/'schedule.json'))
    target=out/'attempts'/selected['attempt_id']/'result.json';write_atomic(target,result)
    if result.get('native_result'):
        (target.parent/'answer.json').write_text(result['native_result'].get('result','')+'\n')
    terminal=json.loads((out/'attempts.json').read_text())
    write_atomic(out/'operational-report.json',report_schedule(schedule,terminal))
    return result
