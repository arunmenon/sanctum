"""Paired development retrieval probes: measure source decisions and exact target recall.

This does not run Claude or score answer quality. The cases are development data,
and missing an exact target does not exclude alternate supporting evidence.
"""
import argparse
import asyncio
import json
from pathlib import Path
import secrets

from sanctum_hubs.tokens import TokenService
from sanctum_run.agent_runtime import open_agent_runtime
from sanctum_run.agent_schedule import load_experiment
from sanctum_run.agent_mcp import AgentMCP
from sanctum_run.delivery import DeliveryBudget, EvidenceNormalizer
from sanctum_run.gateway import HubGateway
from sanctum_run.agent_session import write_atomic


def target_delivered(response, case):
    return any(u.get('citable') is True and
               all(u.get(k) == case[k] for k in ('source_id', 'artifact_id', 'version')) and
               case['quote'] in u.get('text', '') for u in response.get('evidence', []))


async def probe(variants, cases, out):
    out.mkdir(parents=True, exist_ok=False)
    summaries = {}
    for name, variant in variants.items():
        bundle = Path(variant['bundle']).resolve()
        config, _ = load_experiment(bundle)
        root = bundle.parent
        runtime = json.loads((root / config['arms']['sanctum']['runtime_file']).read_text())
        corpus = root / 'corpus'
        rows = [{**json.loads(l), 'source_id': p.parent.name}
                for p in (corpus / 'hubs').glob('*/artifacts.jsonl') for l in p.read_text().splitlines()]
        hubs = sorted({r['source_id'] for r in rows})
        tokens = TokenService(root / 'connections/principals.json', secrets.token_hex(32))
        checks = []
        async with HubGateway(corpus, hubs, tokens) as gateway:
            for index, case in enumerate(cases):
                folder = out / name / f'case-{index:03d}'
                folder.mkdir(parents=True)
                async with open_agent_runtime(root, runtime, gateway, corpus, folder) as sut:
                    adapter = await AgentMCP(gateway, tokens.issue_caller_token(config['caller']['principal']),
                        'sanctum', EvidenceNormalizer(rows), DeliveryBudget(8000, 4000),
                        sut=sut, deadline_seconds=90, max_calls=1).initialize()
                    response = await adapter.dispatch('sanctum_retrieve', {'query': case['query'], 'mode': 'explore'})
                    traces = adapter.calls
                    await adapter.close()
                decisions = [d for t in traces for d in t.get('router_receipt', {}).get('decisions', [])
                             if (d.get('value') or {}).get('source')]
                called = {c['source_id'] for t in traces for c in t.get('backend_trace', {}).get('calls', [])}
                check = {'case_id': case['case_id'], 'target_source': case['source_id'],
                         'target_source_called': case['source_id'] in called,
                         'exact_target_quote_delivered': target_delivered(response, case),
                         'called_sources': sorted(called), 'decisions': decisions,
                         'all_four_considered': {d['value']['source'] for d in decisions} == set(hubs),
                         'non_shadow': all(d['value'].get('shadow') is False for d in decisions)}
                if not check['all_four_considered'] or not check['non_shadow']:
                    raise ValueError('Probe failed unconstrained routing activation contract')
                checks.append(check)
                write_atomic(folder / 'evidence.json', {'case': case, 'response': response, 'traces': traces, 'check': check})
                print(json.dumps({'variant': name, 'completed': index + 1, 'total': len(cases),
                                  'target_source_called': check['target_source_called'],
                                  'exact_target_quote_delivered': check['exact_target_quote_delivered']}), flush=True)
        summaries[name] = {'cases': len(checks), 'target_source_called': sum(c['target_source_called'] for c in checks),
                           'exact_target_quote_delivered': sum(c['exact_target_quote_delivered'] for c in checks),
                           'checks': checks}
        write_atomic(out / 'progress.json', summaries)
    write_atomic(out / 'complete.json', {'scope': 'development retrieval probes, not answer quality',
                                       'claude_calls': 0, 'variants': summaries})


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--variants', type=Path, required=True)
    p.add_argument('--cases', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    asyncio.run(probe(json.loads(a.variants.read_text()), json.loads(a.cases.read_text())['cases'], a.out))
