"""Describe saved rubric outcomes and evidence access signals without causal guesses."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import statistics

from sanctum_run.agent_session import write_atomic


def analyze(spec_path,score_root,out):
    spec=json.loads(spec_path.read_text());out.mkdir(parents=True,exist_ok=False);summaries={};gaps=[];supported=[]
    for name,entry in spec['cohorts'].items():
        import yaml
        bundle=Path(entry['bundle']);run=Path(entry['run']);config=yaml.safe_load(bundle.read_text());root=bundle.parent
        gold={g['task_id']:g for g in map(json.loads,(root/config['gold']).read_text().splitlines())};schedule=json.loads((run/'schedule.json').read_text())
        scores=json.loads((score_root/name/'scores.json').read_text());scheduled={a['attempt_id']:a for a in schedule['attempts']};groups=defaultdict(list)
        for ident,s in scores.items():
            g=gold[s['task_id']];item=scheduled[ident];matrix=g['matrix'];arm=item['arm'];groups[(arm,matrix['family'],matrix['scope'],matrix.get('design_kind'))].append(s)
            if name!='unconstrained' or s.get('adjudication_kind')!='semantic':continue
            result=json.loads((run/'attempts'/ident/'result.json').read_text());review=json.loads((run/s['review_file']).read_text());reviews={f['fact_id']:f for f in review['facts']}
            calls=[c for m in result['mcp_calls'] for c in m.get('backend_trace',{}).get('calls',[])];called={c['source_id'] for c in calls}
            evidence=[u for d in result['delivered_evidence'] for u in d['evidence']];delivered={(u['source_id'],u['artifact_id'],u['version']) for u in evidence if all(k in u for k in ['source_id','artifact_id','version'])}
            for fact in g['required_facts']:
                if s['fact_credit'][fact['fact_id']]:continue
                targets={(e['source_id'],e['artifact_id'],e['version']) for e in fact.get('evidence',[])};sources={t[0] for t in targets}
                if fact.get('support_kind')=='boundary':signal='boundary_diagnosis_or_credit_gap'
                elif targets & delivered:signal='gold_target_delivered_but_uncredited'
                elif sources and not sources & called:signal='gold_source_not_called'
                else:signal='gold_target_not_delivered_fetch_or_packing_unknown'
                gaps.append({'cohort':name,'attempt_id':ident,'repetition':item['repetition'],'task_id':s['task_id'],'matrix':matrix,'dimension':'required_fact','fact_id':fact['fact_id'],'statement':fact['statement'],'signal':signal,'judge':reviews[fact['fact_id']],'gold_targets':[list(t) for t in sorted(targets)],'called_sources':sorted(called),'delivered_gold_targets':[list(t) for t in sorted(targets&delivered)],'queries':[c.get('public_arguments') for c in result['mcp_calls']],'decisions':[d for c in result['mcp_calls'] for d in c.get('router_receipt',{}).get('decisions',[])],'delivery_limited':s['evidence_delivery_limited'],'review_file':str(run/s['review_file'])})
            for p in s['plan']:
                for row in p['items']:
                    if not row['met']:gaps.append({'cohort':name,'attempt_id':ident,'task_id':s['task_id'],'matrix':matrix,'dimension':p['dimension'],'item':row['item'],'judge_reason':row['reason'],'signal':'plan_item_gap'})
            for c in s['unsupported_claims']:
                if c['severity']=='material':gaps.append({'cohort':name,'attempt_id':ident,'task_id':s['task_id'],'matrix':matrix,'dimension':'unsupported_claim','claim':c,'signal':'material_unsupported_claim'})
            if s['provisional_task_complete']:supported.append({'attempt_id':ident,'task_id':s['task_id'],'matrix':matrix,'review_file':str(run/s['review_file'])})
        summaries[name]=[{'arm':arm,'family':family,'scope':scope,'design_kind':design,'graded':len(values),'task_count':len({v['task_id'] for v in values}),'mean_fact_coverage':statistics.mean(v['supported_required_fact_coverage'] for v in values),'provisional_completion':sum(v['provisional_task_complete'] for v in values)} for (arm,family,scope,design),values in sorted(groups.items(),key=lambda x:str(x[0]))]
    write_atomic(out/'task-family-breakdown.json',summaries);write_atomic(out/'gap-ledger.json',gaps);write_atomic(out/'positive-cases.json',supported)
    summary={'signals':dict(Counter(g['signal'] for g in gaps)),'gap_records':len(gaps),'unique_tasks_with_gaps':len({g['task_id'] for g in gaps}),'provisional_positive_attempts':len(supported),'limitations':['Missing exact gold targets can have alternative support; not proof of a retrieval failure.','Original traces do not expose the complete prepacking candidate set; fetch versus omission is unresolved.','Same-model judgments and development corpus; human acceptance pending.'],'inference_calls':0}
    write_atomic(out/'complete.json',summary);print(json.dumps(summary))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('spec',type=Path);p.add_argument('--scores',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();analyze(a.spec.resolve(),a.scores.resolve(),a.out.resolve())
