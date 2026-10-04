"""Exercise generic agent connections on two bundles using local fixtures only.

Fixture acceptance is deliberately separate from operational ontology review.
This does not approve the pilot candidate or measure agent answer quality.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

import anyio
import yaml

from sanctum_ref.harvest import project_release, sha
from sanctum_run.agent_runner import run_attempt
from tests.helpers.systemone_server import SystemOneTestServer

ROOT = Path(__file__).resolve().parents[1]


def write(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=True)+'\n')


def prepare(source, target, *, pdlc):
    shutil.copytree(source, target)
    config = yaml.safe_load((target/'experiment.yaml').read_text())
    config['experiment_id'] += '-local-connection-fixture'
    config['execution']['repetitions'] = 1
    runtime = target/'connections/runtime'
    (runtime/'calibration').mkdir(parents=True)
    (runtime/'registry').mkdir()
    for name, destination in [('matrix', 'matrix'), ('system_one_providers', 'providers'),
                              ('system_one_templates', 'templates')]:
        shutil.copy(ROOT/f'configs/{name}.yaml', runtime/f'{destination}.yaml')
    release_id = 'local-connection-fixture'
    if pdlc:
        candidate = json.loads((ROOT/'build/pdlc-memory/policy-candidate/candidate.json').read_text())
        reviewer = 'local-fixture-acceptance-only'
        review = dict(snapshot_hash=sha(json.dumps(candidate, sort_keys=True)), reviewed_by=reviewer,
                      decisions={a['id']: 'accepted' for a in candidate['assertions']})
        grants = dict(grants=[dict(reviewer=reviewer, source_id=s['source_id'],
            edge_types=sorted({a['type'] for a in candidate['assertions']})) for s in candidate['sources']])
        release = project_release(candidate, release_id, review, delegations=grants)
        for p in (ROOT/'build/pdlc-memory/policy-candidate/registry').glob('*.yaml'):
            shutil.copy(p, runtime/'registry'/p.name)
    else:
        row = json.loads((target/'corpus/hubs/codehub/artifacts.jsonl').read_text().strip())
        entity = 'svc.shipping-dispatch'
        release = dict(release_id=release_id, schema_version=1,
            artifact_subject_bindings_required=True, status='fixture',
            entities=[dict(id=entity, ref='shipping-dispatch', type='service',
                           label='Shipping Dispatch', member_of=[])],
            terms=[dict(source='codehub', namespace='code', native_id='shipping-dispatch',
                label='shipping dispatch', kind='name', denotes=entity, status='accepted',
                version=1, reviewed_by='local-fixture-acceptance-only')],
            places=[dict(source='codehub', filter='repo', value=row['location'],
                place=row['location'], selects_for=entity, status='accepted', version=1,
                reviewed_by='local-fixture-acceptance-only')],
            contexts=[], procedures=[], relations=[], authority_assertions=[],
            artifacts=[dict(source_id='codehub', artifact_id=row['artifact_id'], version=row['version'],
                content_hash=sha(row['text']), visibility_groups=row['acl'], principal=None,
                subjects=[dict(entity_id=entity, status='accepted', provenance=dict(
                    assertion_id='shipping-fixture-about', reviewed_by='local-fixture-acceptance-only',
                    evidence=[dict(fixture=True)]))])],
            descriptors={'codehub': dict(text='Versioned shipping dispatch helper source code.', pinned=release_id)})
        manifest = yaml.safe_load((ROOT/'owners/manifests/codehub.yaml').read_text())
        manifest.update(owner='local-fixture-only', domains={'shipping': ['shipping', 'dispatch']},
            places=[dict(prefix='repo:shipping/', groups=row['acl'], domain='shipping')])
        manifest['versions'].update(releases=['v1'], environment_refs={}, branch_by_environment={})
        (runtime/'registry/codehub.yaml').write_text(yaml.safe_dump(manifest))
    release['note'] = 'LOCAL FIXTURE ONLY: not operational acceptance or independent review.'
    release_path = runtime/'memory'/release_id/'release.yaml'
    release_path.parent.mkdir(parents=True)
    release_path.write_text(yaml.safe_dump(release, sort_keys=False))
    (runtime/'descriptors.yaml').write_text(yaml.safe_dump(dict(
        descriptors={k: v['text'] for k, v in release['descriptors'].items()})))
    relative = lambda p: str(p.relative_to(target))
    runtime_config = dict(schema_version=1, data_class='synthetic', config_id='C5',
        matrix=relative(runtime/'matrix.yaml'), providers=relative(runtime/'providers.yaml'),
        descriptors=relative(runtime/'descriptors.yaml'), templates=relative(runtime/'templates.yaml'),
        registry_directory=relative(runtime/'registry'), calibration_directory=relative(runtime/'calibration'),
        memory_release=relative(release_path), system_one_broker=dict(provider='local-test', profile='relaxed',
            max_calls_per_attempt=12, max_input_tokens_per_attempt=50000),
        files={relative(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in runtime.rglob('*.yaml')})
    runtime_path = target/'connections/runtime.json'
    write(runtime_path, runtime_config)
    config['arms']['sanctum'] = dict(tool_surface='sanctum_only', runtime_ready=True,
        runtime_file=relative(runtime_path), runtime_sha256=hashlib.sha256(runtime_path.read_bytes()).hexdigest())
    (target/'experiment.yaml').write_text(yaml.safe_dump(config, sort_keys=False))
    return config


async def probe(out):
    results = []
    with SystemOneTestServer() as server:
        previous = os.environ.get('SANCTUM_SYSTEMONE_TEST_URL')
        os.environ['SANCTUM_SYSTEMONE_TEST_URL'] = server.base_url
        try:
            for name, source in [('pdlc', 'pdlc-development'), ('shipping', 'shipping-fixture')]:
                bundle = out/'bundles'/name
                prepare(ROOT/'build/agent-bundles'/source, bundle, pdlc=name=='pdlc')
                tasks = [json.loads(line) for line in (bundle/'public/tasks.jsonl').read_text().splitlines()]
                task = next(t for t in tasks if t['task_id'] == 'gateway-routing-uncertainty-v2') if name == 'pdlc' else tasks[0]
                for arm in ('direct', 'sanctum'):
                    result = await run_attempt(bundle/'experiment.yaml', out/'runs'/name,
                        task_id=task['task_id'], arm=arm, fixture=True)
                    delivered = [u for record in result['delivered_evidence'] for u in record['evidence']]
                    activations = [a for call in result['mcp_calls']
                        for a in call.get('router_receipt', {}).get('activations', [])]
                    citable = [u for u in delivered if u.get('citable')]
                    results.append(dict(bundle=name, arm=arm, result=result,
                        citable_units=len(citable), full_file_reads=sum(c['tool'].endswith('__get_file') for c in result['mcp_calls']),
                        subject_bindings=sum(a['kind']=='subject_binding' for a in activations)))
        finally:
            if previous is None: os.environ.pop('SANCTUM_SYSTEMONE_TEST_URL', None)
            else: os.environ['SANCTUM_SYSTEMONE_TEST_URL'] = previous
        write(out/'probe-report.json', dict(fixture_only=True, operational_acceptance=False,
            quality_comparison_valid=False, system_one_http_calls=len(server.behavior.requests), attempts=results))
    passed = all(r['result']['status']=='completed' and r['citable_units'] and
        (r['full_file_reads'] if r['arm']=='direct' else r['subject_bindings']) for r in results)
    print(json.dumps(dict(report=str(out/'probe-report.json'), passed=bool(passed), attempts=len(results),
                         statuses=[r['result'].get('status') for r in results])))
    if not passed: raise SystemExit('Connection fixture did not establish fetched, bound evidence in both Sanctum bundles.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists(): raise SystemExit('Choose a fresh output directory; proofs are not overwritten.')
    anyio.run(probe, args.out.resolve())
