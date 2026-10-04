"""Require non-shadow Jev decisions and observed optional-source pruning."""
import argparse
import asyncio
import json
from pathlib import Path
import secrets

from sanctum_hubs.tokens import TokenService
from sanctum_run.agent_runtime import open_agent_runtime
from sanctum_run.agent_schedule import load_experiment
from sanctum_run.agent_mcp import AgentMCP
from sanctum_run.delivery import DeliveryBudget,EvidenceNormalizer
from sanctum_run.gateway import HubGateway
from sanctum_run.agent_session import write_atomic


async def probe(bundle,out,cases):
    config,_=load_experiment(bundle);root=bundle.parent;runtime=json.loads((root/config['arms']['sanctum']['runtime_file']).read_text());corpus=root/'corpus'
    rows=[{**json.loads(l),'source_id':p.parent.name} for p in (corpus/'hubs').glob('*/artifacts.jsonl') for l in p.read_text().splitlines()];hubs=sorted({r['source_id'] for r in rows});tokens=TokenService(root/'connections/principals.json',secrets.token_hex(32));checks=[]
    async with HubGateway(corpus,hubs,tokens) as gateway:
        for index,case in enumerate(cases):
            folder=out/f'case-{index:03d}';folder.mkdir()
            async with open_agent_runtime(root,runtime,gateway,corpus,folder) as sut:
                adapter=await AgentMCP(gateway,tokens.issue_caller_token(config['caller']['principal']),'sanctum',EvidenceNormalizer(rows),DeliveryBudget(8000,4000),sut=sut,deadline_seconds=90,max_calls=1).initialize()
                response=await adapter.dispatch('sanctum_retrieve',{'query':case['query'],'mode':'explore'});traces=adapter.calls;await adapter.close()
            decisions=[d for t in traces for d in t.get('router_receipt',{}).get('decisions',[]) if (d.get('value') or {}).get('source')]
            applied=[d for d in decisions if d.get('value',{}).get('shadow') is False and d['value'].get('call') is False]
            called={c['source_id'] for t in traces for c in t.get('backend_trace',{}).get('calls',[])}
            sources={d['value']['source'] for d in applied};actual_skips=sources-called
            check={'query':case['query'],'non_shadow_decisions':sum(d['value'].get('shadow') is False for d in decisions),'applied_optional_skips':sorted(actual_skips),'called_sources':sorted(called)};checks.append(check)
            write_atomic(folder/'evidence.json',{'response':response,'traces':traces,'check':check});print(json.dumps(check),flush=True)
            if actual_skips:break
    passed=any(c['applied_optional_skips'] for c in checks) and all(c['non_shadow_decisions']>0 for c in checks)
    write_atomic(out/'proof.json',{'passed':passed,'checks':checks,'paid_claude_calls':0,'calibration_matching':any(c['non_shadow_decisions'] for c in checks),'scope':'development-only routing activation; not answer quality or held-out safety'})
    if not passed:raise SystemExit('No observed Jev-applied skip: do not dispatch native ablation.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('bundle',type=Path);p.add_argument('--cases',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False);asyncio.run(probe(a.bundle.resolve(),a.out.resolve(),json.loads(a.cases.read_text())['cases']))
