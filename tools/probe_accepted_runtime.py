"""Bounded real System One smoke on accepted synthetic memory; no Claude calls."""
import argparse
import json
from pathlib import Path
import secrets

import anyio

from sanctum_hubs.tokens import TokenService
from sanctum_run.agent_runtime import open_agent_runtime
from sanctum_run.agent_schedule import load_experiment
from sanctum_run.agent_mcp import AgentMCP
from sanctum_run.delivery import DeliveryBudget, EvidenceNormalizer
from sanctum_run.gateway import HubGateway
from sanctum_run.bundle import _file


async def probe(bundle_path, out, queries):
    config,_=load_experiment(bundle_path);root=bundle_path.resolve().parent
    runtime=json.loads(_file(root,config['arms']['sanctum']['runtime_file']).read_text())
    corpus=_file(root,config['corpus']['manifest']).parent
    rows=[{**json.loads(line),'source_id':p.parent.name} for p in sorted((corpus/'hubs').glob('*/artifacts.jsonl'))
        for line in p.read_text().splitlines()]
    tokens=TokenService(_file(root,config['caller']['principal_file']),secrets.token_hex(32))
    async with HubGateway(corpus,sorted({r['source_id'] for r in rows}),tokens) as gateway:
        async with open_agent_runtime(root,runtime,gateway,corpus,out,fixture=False) as sut:
            adapter=await AgentMCP(gateway,tokens.issue_caller_token(config['caller']['principal']),'sanctum',
                EvidenceNormalizer(rows),DeliveryBudget(8000,4000),sut=sut,deadline_seconds=90,max_calls=len(queries)).initialize()
            responses=[await adapter.dispatch('sanctum_retrieve',dict(query=query,mode='explore')) for query in queries]
            traces=adapter.calls
            await adapter.close()
    activations=[a for trace in traces for a in trace.get('router_receipt',{}).get('activations',[])]
    calls=[c for trace in traces for c in trace.get('backend_trace',{}).get('model_calls',[])]
    receipts=[trace.get('router_receipt',{}) for trace in traces]
    passed=bool(any(r.get('chosen') for receipt in receipts for r in receipt.get('resolutions',[])) and
        any(a['kind']=='procedure' for a in activations) and any(a['kind']=='subject_binding' for a in activations) and calls and
        all(c.get('model')==runtime['system_one_broker']['verified_model'] and c.get('outcome')=='ok' for c in calls)
        and any(u.get('citable') for response in responses for u in response.get('evidence',[])))
    result=dict(passed=passed,authorization='D-JEV: synthetic lab System One only',paid_claude_calls=0,
        quality_comparison_valid=False,bundle=str(bundle_path),queries=queries,responses=responses,traces=traces,
        scope='Scoped accepted development memory; unreviewed mappings remain inactive. This is not agent-quality evidence.')
    (out/'probe-report.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(passed=passed,memory_release=receipts[0].get('memory_release_id'),
        subject_bindings=sum(a['kind']=='subject_binding' for a in activations),model_calls=len(calls),
        resolved_models=sorted({c.get('model') for c in calls if c.get('model')}),report=str(out/'probe-report.json'))))
    if not passed:raise SystemExit('Accepted runtime proof incomplete; inspect saved response and trace.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle',type=Path);parser.add_argument('--out',required=True,type=Path)
    parser.add_argument('--query',action='append',help='Repeat to check complementary routing cases within one broker budget.')
    args=parser.parse_args()
    if args.out.exists():raise SystemExit('Choose a fresh output directory.')
    args.out.mkdir(parents=True)
    anyio.run(probe,args.bundle,args.out,args.query or [
        'Explain payment-auth implementation when fraud times out.', 'payment-auth fraud outcomes'])
