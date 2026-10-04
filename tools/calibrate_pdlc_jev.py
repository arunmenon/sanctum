"""Development-only D2 calibration with counterfactual source-removal labels.

Does not modify an existing experiment or run Claude. Writes raw outcomes and
counterfactual evidence before fitting; a zero-skip fit is not activation proof.
"""
import argparse
import asyncio
import hashlib
import json
import math
import os
from pathlib import Path
import random
import secrets
import shutil
import uuid

import yaml
from sanctum_contracts import RetrieveRequest
from sanctum_hubs.tokens import TokenService
from sanctum_ref.providers import d2_request
from sanctum_ref.providers.http_systemone import d2_questions, Calibration
from sanctum_run.gateway import HubGateway
from sanctum_run.process_sut import ProcessSUT
from sanctum_run.sut import SUTContext
from sanctum_run.system_one_broker import load_provider, load_descriptors, state_sources, descriptor_release
from sanctum_systemone import CampaignBudget, SystemOneClient, set_campaign_budget
from tools.fit_system_one import logit, platt, choose_skip_band, brier, ece
from tools.measure_system_one_batches import dotenv

ROOT=Path(__file__).resolve().parents[1]


def write(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')


def cases_for(bundle,out):
    gold=[json.loads(l) for l in (bundle/'private/gold.jsonl').read_text().splitlines()]
    used={(r['source_id'],r['artifact_id']) for g in gold for f in g['required_facts'] for r in f.get('evidence',[])}
    rows={(p.parent.name,r['artifact_id'],r['version']):r for p in (bundle/'corpus/hubs').glob('*/artifacts.jsonl') for r in map(json.loads,p.read_text().splitlines())}
    cases=[];seen=set();quarantined=[]
    for hub in ['codehub','dochub','memoryhub','skillhub']:
        path=ROOT/f'build/pdlc-authoring/jev-calibration-{hub}-openai-gpt-6-luna.result.json'
        draft=json.loads(path.read_text())
        for c in draft['cases']:
            key=(c['source_id'],c['artifact_id'],c['version']);quote=c['quote']
            if key not in rows or (key[0],key[1]) in used:raise ValueError('development artifact overlaps evaluation gold or is missing')
            if not isinstance(quote,str) or len(quote)<40 or rows[key]['text'].count(quote)!=1:
                quarantined.append({'case_id':c['case_id'],'reason':'quote_not_unique_exact_source_text'});continue
            if key in seen or not isinstance(c['query'],str) or not c['query'].strip():raise ValueError('duplicate or invalid development case')
            seen.add(key);c['case_id']='dev-'+hashlib.sha256(json.dumps(key).encode()).hexdigest()[:16];cases.append(c)
    write(out/'quarantined-drafts.json',quarantined)
    write(out/'development-cases.json',{'cases':cases,'artifact_disjoint_from_evaluation_gold':True,'author_model':'gpt-6-luna','label_method':'C1-fair evidence recall change on hub removal'})
    return cases


async def labels_for(bundle,out,cases):
    runtime=json.loads((bundle/'connections/runtime.json').read_text());corpus=bundle/'corpus';hubs=['codehub','dochub','memoryhub','skillhub'];scores={}
    for removed in [None,*hubs]:
        name=removed or 'full';target=out/'counterfactual'/name/'results.json'
        if target.exists():scores[name]=json.loads(target.read_text());continue
        registry=out/'counterfactual'/name/'registry';shutil.copytree(bundle/runtime['registry_directory'],registry)
        if removed:(registry/f'{removed}.yaml').unlink()
        tokens=TokenService(bundle/'connections/principals.json',secrets.token_hex(32));token=tokens.issue_caller_token('pdlc-pilot-reader');values={}
        async with HubGateway(corpus,hubs,tokens) as gateway:
            sut=ProcessSUT(['--config','C1-fair','--matrix',str(bundle/runtime['matrix']),'--registry',str(registry),'--decision-provider','rules'])
            async with sut.open(gateway,corpus):
                for index,c in enumerate(cases):
                    request=RetrieveRequest(request_id=uuid.uuid4().hex,query=c['query'],mode='explore',budget_tokens=8000,deadline_ms=30000)
                    handle=gateway.handle(request.request_id,token)
                    response,receipt=await sut.retrieve(request,SUTContext(token,handle))
                    got=any(u.source_id==c['source_id'] and u.artifact_id==c['artifact_id'] and u.source_version==c['version'] and c['quote'] in u.text for u in response.evidence)
                    values[c['case_id']]=int(got)
                    write(target.parent/f'{index:03d}.json',{'response':response.model_dump(mode='json'),'receipt':receipt.model_dump(mode='json'),'target_recalled':got})
        write(target,values);scores[name]=values
        print(json.dumps({'counterfactual':name,'cases':len(values),'recalled':sum(values.values())}),flush=True)
    labels={(c['case_id'],hub):int(scores['full'][c['case_id']]>scores[hub][c['case_id']]) for c in cases for hub in hubs}
    write(out/'source-labels.json',[{'case_id':k[0],'source_id':k[1],'useful':v} for k,v in labels.items()])
    return labels


def collect_fit(bundle,out,cases,labels):
    runtime=json.loads((bundle/'connections/runtime.json').read_text());spec,_=load_provider('typesafe-jev','relaxed',bundle/runtime['providers']);spec=spec.model_copy(update={'model':'jev-1.13.0','model_env':None})
    env={**dotenv(),**os.environ};sources=state_sources(load_descriptors(bundle/runtime['descriptors']),['codehub','dochub','memoryhub','skillhub'])
    set_campaign_budget(CampaignBudget(80,200000));client=SystemOneClient(spec,spec.resolved_base_url(env) or 'https://api.typesafe.ai',spec.requested_model(env),api_key=env.get(spec.api_key_env) if spec.api_key_env else None)
    raw={};models=set();failed=[]
    for index,c in enumerate(cases):
        path=out/'raw'/f'{index:03d}.json'
        if path.exists():record=json.loads(path.read_text())
        else:
            outcome=client.decide({'query':c['query'],'sources':sources},d2_questions([d2_request(h,c['query'],60000) for h in sources]),60,max_calls=2)
            record={'case_id':c['case_id'],'model':outcome.model,'answers':outcome.answers,'calls':outcome.calls,'usage':outcome.usage,'unavailable_reason':str(outcome.unavailable_reason) if outcome.unavailable_reason else None};write(path,record)
        if record['case_id']!=c['case_id']:raise ValueError('cached development call mismatch')
        if record['unavailable_reason']:failed.append(c['case_id']);continue
        models.add(record['model'])
        for hub in sources:
            if 'd2:'+hub in record['answers']:raw[c['case_id'],hub]=record['answers']['d2:'+hub]['noul']
        print(json.dumps({'development_scores_collected':index+1,'total':len(cases)}),flush=True)
    if models!={'jev-1.13.0'}:raise ValueError('calibration resolved model mismatch')
    keys=sorted(set(raw)&set(labels));groups=sorted({k[0] for k in keys});random.Random(183).shuffle(groups);held=[];unscaled=[]
    if len(groups)<20 or sum(labels[k] for k in keys)<8:raise ValueError('insufficient development recall-positive labels; do not activate')
    for i in range(5):
        test=set(groups[i::5]);train=[(logit(raw[k]),labels[k]) for k in keys if k[0] not in test];a,b=platt(train)
        held.extend((1/(1+math.exp(-(a*logit(raw[k])+b))),labels[k]) for k in keys if k[0] in test)
        unscaled.extend((raw[k],labels[k]) for k in keys if k[0] in test)
    band=choose_skip_band(held,.05);a,b=platt([(logit(raw[k]),labels[k]) for k in keys]);binding={'provider':'typesafe-jev','model':'jev-1.13.0','template':'d2-noul-v1','descriptor_release':descriptor_release(sources),'decoding':'provider default'}
    document={'binding':binding,'platt':{'a':a,'b':b},'bands':{'use':.7,'skip':band},'provenance':{'fitted_on':'pdlc-development-artifact-disjoint','cases':len(groups),'points':len(keys),'positives':sum(labels[k] for k in keys),'folds':5,'harm_tolerance':.05,'failed_cases':failed,'held_out':{'brier_calibrated':brier(held),'ece_calibrated':ece(held),'brier_raw':brier(unscaled),'skipped_at_band':sum(p<band for p,y in held),'harmful_skips_at_band':sum(y for p,y in held if p<band)},'label':'C1-fair exact evidence recall drop when removing a source; limited retrieval-target calibration'}}
    path=out/'typesafe-jev@jev-1.13.0.yaml';path.write_text(yaml.safe_dump(document,sort_keys=False));Calibration(path)
    write(out/'fit-summary.json',{'calibration':str(path),'skip_band':band,'matching_binding':True,'activation_proven':False,'provenance':document['provenance']});print(json.dumps({'calibration_written':str(path),'skip_band':band,'activation_proven':False}),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('bundle',type=Path);p.add_argument('--out',type=Path,required=True);args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    bundle=args.bundle.resolve();bundle=bundle.parent if bundle.is_file() else bundle
    cases=cases_for(bundle,args.out.resolve());labels=asyncio.run(labels_for(bundle,args.out.resolve(),cases));collect_fit(bundle,args.out.resolve(),cases,labels)

if __name__=='__main__':main()
