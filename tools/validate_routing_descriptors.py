"""Validate grounded source descriptor candidates; no activation or inference."""
import argparse
import hashlib
import json
from pathlib import Path
import yaml


def validate(corpus,results,out):
    out.mkdir(parents=True,exist_ok=False);descriptors={};audit=[]
    for folder in sorted((corpus/'hubs').iterdir()):
        if not (folder/'artifacts.jsonl').exists():continue
        source=folder.name;rows={(r['artifact_id'],r['version']):r for r in map(json.loads,(folder/'artifacts.jsonl').read_text().splitlines())}
        result_path=results/f'rubric-descriptor-{source}-01-openai-gpt-6-luna.result.json';p=json.loads(result_path.read_text())
        if p['source_id']!=source or not isinstance(p['descriptor'],str) or not 3<=len(p['coverage'])<=8 or len(p['descriptor'].split())>180:raise ValueError('descriptor envelope invalid')
        for claim in p['coverage']:
            if not claim['evidence']:raise ValueError('coverage without evidence')
            for e in claim['evidence']:
                row=rows[(e['artifact_id'],e['version'])];quote=e['quote']
                if not isinstance(quote,str) or len(quote)<12 or quote not in row['text']:raise ValueError('descriptor quote not in exact source bytes: '+source)
                audit.append({'source':source,'coverage':claim['label'],'artifact_id':e['artifact_id'],'version':e['version'],'quote':quote,'start':row['text'].index(quote),'end':row['text'].index(quote)+len(quote),'content_sha256':hashlib.sha256(row['text'].encode()).hexdigest(),'result_sha256':hashlib.sha256(result_path.read_bytes()).hexdigest()})
        descriptors[source]=p['descriptor']
    (out/'descriptors.yaml').write_text(yaml.safe_dump({'descriptors':descriptors},sort_keys=True));(out/'grounding-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps({'sources':len(descriptors),'grounded_quote_refs':len(audit),'active':False,'semantic_review':'candidate needs descriptor-claim review; quote validity alone is not entailment'}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('corpus',type=Path);p.add_argument('--results',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();validate(a.corpus,a.results,a.out)
