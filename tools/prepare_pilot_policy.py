"""Author explicit synthetic lab policy; do not approve the ontology or activate it."""
import argparse
import hashlib
import json
from pathlib import Path

import yaml

from sanctum_ref.harvest import apply_owner_declarations, sha
from sanctum_ref.registry import load_registry

ROOT=Path(__file__).resolve().parents[1]
CURATOR='sanctum-pilot-lab-curator'


def write(path, document):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(document,indent=2,sort_keys=True)+'\n')


def prepare(candidate_path, hierarchy_path, out):
    bundle=json.loads(candidate_path.read_text())
    hierarchy=json.loads(hierarchy_path.read_text())
    nodes={n['id']:n for n in hierarchy['nodes']}
    entities={n['id'] for n in bundle['nodes'] if n['kind']=='Entity' and n['id']!='entity:unknown'}
    domains={n['id']:n for n in hierarchy['nodes'] if n['kind']=='domain' and n['id'] in entities}
    sources={s['source_id']:s for s in bundle['sources']}
    owner_registry=dict(schema_version=1,synthetic=True,scope='read-only synthetic Pilot-0 lab',
        author=CURATOR,authorization_basis='Owner active goal: autonomously prepare and wire synthetic lab memory.',
        source_owners={source:CURATOR for source in sources},
        note='Authored lab policy, not approval from enterprise source owners or permission to execute draft procedures.')
    memberships=[dict(entity_id=e,parent_id=nodes[e]['parent_id'],
        basis='explicit lab navigation declaration from pinned hierarchy',hierarchy_status=nodes[e]['status'])
        for e in sorted(entities) if e in nodes and nodes[e].get('kind')=='service'
        and nodes[e].get('parent_id') in domains]
    declarations=[]
    for source,snapshot in sources.items():
        observed_domains={d['id'] for a in snapshot['artifacts'] for d in a['metadata'].get('domains',[])}
        kind={'codehub':'implementation','dochub':'reference','skillhub':'procedure','memoryhub':'session_history'}[source]
        declaration=dict(source_id=source,owner=CURATOR,visibility_groups=['pdlc-pilot'],synthetic=True,
            scope='source-described evidence only; no deployment or document approval inferred',
            hierarchy_sha256=hashlib.sha256(hierarchy_path.read_bytes()).hexdigest(),
            memberships=memberships if source=='codehub' else [],
            authority=[dict(entity_id=d,fact_kind='implementation') for d in sorted(observed_domains)] if source=='codehub' else [],
            procedures=[dict(procedure_id='pilot-consult-'+source+'-'+d.replace('.','-'),version=1,
                trigger=dict(entity_member_of=d,fact_kind_needed=kind),
                action=dict(must_consult=source,selector={})) for d in sorted(observed_domains)])
        declarations.append(declaration)
        manifest=yaml.safe_load((ROOT/f'owners/manifests/{source}.yaml').read_text())
        manifest.update(owner=CURATOR,procedures=[],authority={'implementation':'authoritative'} if source=='codehub' else {},
            places=[dict(prefix=location,groups=['pdlc-pilot'],domain='any')
                for location in sorted({a['metadata'].get('harvest_location','') for a in snapshot['artifacts']})])
        if source=='memoryhub':
            manifest['places']=[dict(prefix='',groups=['pdlc-pilot'],domain='any')]
        manifest['versions'].update(releases=sorted({a['version'] for a in snapshot['artifacts']}),
            environment_refs={},branch_by_environment={})
        manifest['domains']={d: sorted({word.lower() for word in n['name'].replace('-',' ').split()} |
            {nodes[e]['name'].lower() for e in entities if e in nodes and nodes[e].get('parent_id')==d})
            for d,n in domains.items()}
        path=out/'registry'/f'{source}.yaml';path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(yaml.safe_dump(manifest,sort_keys=False))
    load_registry(out/'registry')
    document=dict(schema_version=1,synthetic=True,status='authored_lab_policy_pending_independent_review',
                  proposed_by=CURATOR,declarations=declarations)
    bundle=apply_owner_declarations(bundle,document,owner_registry=owner_registry)
    for assertion in bundle['assertions']: assertion['proposed_by']=CURATOR
    write(out/'owner-registry.json',owner_registry)
    write(out/'declarations.json',document)
    write(out/'candidate.json',bundle)
    write(out/'review-template.json',dict(snapshot_hash=sha(json.dumps(bundle,sort_keys=True)),reviewed_by=None,decisions={}))
    write(out/'summary.json',dict(status='proposed_not_active',assertions=len(bundle['assertions']),
        memberships=len(memberships),procedures=sum(len(d['procedures']) for d in declarations),
        source_owners='explicit synthetic lab curator role; not enterprise approval',
        snapshot_hash=sha(json.dumps(bundle,sort_keys=True))))
    print((out/'summary.json').read_text())


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',type=Path,required=True);parser.add_argument('--hierarchy',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    prepare(args.candidate,args.hierarchy,args.out)
