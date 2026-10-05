"""Create a synthetic pilot memory variant with grounded native place mappings reviewed.

Inherited accepted assertions retain an explicit reference to their original review.
New decisions are scoped to SELECTS_FOR; this is Codex technical curation, not an
independent human or Astra review, and does not activate any bundle.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import yaml

from sanctum_ref.harvest import project_release,sha,validate
from sanctum_ref.memory import Release


def prepare(candidate,base_dir,registry,out):
    out.mkdir(parents=True,exist_ok=False);bundle=json.loads(candidate.read_text());validate(bundle)
    prior=json.loads((base_dir/'review.json').read_text());delegations=json.loads((base_dir/'delegations.json').read_text())
    if prior['snapshot_hash']!=sha(json.dumps(bundle,sort_keys=True)):raise ValueError('candidate not the originally reviewed snapshot')
    nodes={n['id']:n for n in bundle['nodes']};artifacts={(a['source_id'],a['artifact_id'],a['version']):a for s in bundle['sources'] for a in s['artifacts']}
    manifests={m['hub_id']:m for p in registry.glob('*.yaml') if (m:=yaml.safe_load(p.read_text()))}
    reviewer='codex-rubric-gap-audit';decisions=dict(prior['decisions']);audit=[]
    for a in bundle['assertions']:
        if a['type']!='SELECTS_FOR':continue
        term=nodes[a['from']];source=term['source_id'];selector=term.get('selector',{})
        allowed=manifests[source]['search'].get('place_filter')
        accepted=bool(selector) and set(selector)=={allowed}
        supporting=[]
        for e in a['evidence']:
            row=artifacts[(e['source_id'],e['artifact_id'],e['version'])];meta=row['metadata']
            subjects={x['id'] for x in meta.get('services',[])+meta.get('domains',[])}
            if source==row['source_id'] and a['to'] in subjects and selector==meta.get('harvest_selector'):
                supporting.append(e)
        accepted=accepted and bool(supporting)
        decisions[a['id']]='accepted' if accepted else 'rejected'
        audit.append({'assertion_id':a['id'],'source':source,'selector':selector,'subject':a['to'],'accepted':accepted,'support':supporting,'reason':'native search filter and observed selector/subject association match' if accepted else 'native filter or subject association not established'})
    grants=[]
    for g in delegations['grants']:
        if g['reviewer']==prior['reviewed_by']:grants.append({**g,'reviewer':reviewer})
    for source in manifests:grants.append({'reviewer':reviewer,'source_id':source,'edge_types':['SELECTS_FOR']})
    new_delegations={**delegations,'grants':grants,'scope_note':'User-authorized synthetic pilot technical curation; inherited assertions checked against the unchanged reviewed candidate, new permissions cover SELECTS_FOR only.'}
    review={'snapshot_hash':prior['snapshot_hash'],'reviewed_by':reviewer,'decisions':decisions,'inherited_review_sha256':sha(json.dumps(prior,sort_keys=True)),'new_decision_scope':'SELECTS_FOR only; other accepted decisions inherited from prior review','independent_human_acceptance':False}
    rid='pilot-place-reviewed-'+sha(json.dumps(review,sort_keys=True))[:12];release=project_release(bundle,rid,review,delegations=new_delegations);Release.model_validate(release)
    folder=out/rid;folder.mkdir();(folder/'release.yaml').write_text(yaml.safe_dump(release,sort_keys=False));(folder/'review.json').write_text(json.dumps(review,indent=2)+'\n');(folder/'delegations.json').write_text(json.dumps(new_delegations,indent=2)+'\n');(folder/'owner-registry.json').write_bytes((base_dir/'owner-registry.json').read_bytes())
    (out/'place-review.json').write_text(json.dumps(audit,indent=2)+'\n')
    summary={'release_id':rid,'reviewed_assertions':len(audit),'accepted':sum(x['accepted'] for x in audit),'rejected':sum(not x['accepted'] for x in audit),'operational_places':sum(p['status']=='accepted' for p in release['places']),'review_kind':'Codex technical review with inherited prior decisions','bundle_activated':False}
    (out/'complete.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);p.add_argument('--base-memory',type=Path,required=True);p.add_argument('--registry',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();prepare(a.candidate,a.base_memory,a.registry,a.out)
