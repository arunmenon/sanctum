"""Version mechanical scores using original hash-bound judgments; no inference or agent replay."""
import argparse
import json
from pathlib import Path
import statistics

import yaml
from sanctum_run.agent_score import SCORER_VERSION, score_answer
from sanctum_run.agent_schedule import compare_scope_strata, file_hash
from sanctum_run.agent_session import write_atomic
from sanctum_run.quality_policy import load_policy, scoring_context
from tools.report_agent_run import report


def rescore(spec_path, out):
    spec=json.loads(spec_path.read_text());out.mkdir(parents=True,exist_ok=False)
    policy_path=Path(spec['policy']).resolve();policy=load_policy(policy_path)
    cohorts={}; summaries={}; changes=[]; pins={'policy':file_hash(policy_path),'scorer':file_hash(Path(__file__).resolve().parents[1]/'src/sanctum_run/agent_score.py')}
    for name, entry in spec['cohorts'].items():
        bundle=Path(entry['bundle']).resolve();run=Path(entry['run']).resolve();prior=Path(entry['scores']).resolve()
        config=yaml.safe_load(bundle.read_text());root=bundle.parent
        gold={g['task_id']:g for g in map(json.loads,(root/config['gold']).read_text().splitlines())}
        rows=[{**json.loads(line),'source_id':p.parent.name} for p in sorted(((root/config['corpus']['manifest']).parent/'hubs').glob('*/artifacts.jsonl')) for line in p.read_text().splitlines()]
        saved=json.loads(prior.read_text());schedule=json.loads((run/'schedule.json').read_text());ledger=json.loads((run/'attempts.json').read_text());graded={}
        pins[name]={'bundle':file_hash(bundle),'original_scores':file_hash(prior),'schedule':file_hash(run/'schedule.json')}
        for ident, old in saved.items():
            folder=run/'attempts'/ident;attempt=json.loads((folder/'result.json').read_text());raw=(folder/'answer.json').read_text()
            review_path=(run/old['review_file']).resolve() if old.get('review_file') else None
            if review_path and not review_path.is_relative_to(run):raise ValueError('review outside original run')
            review=json.loads(review_path.read_text()) if review_path else None
            if old['adjudication_kind']=='semantic' and review is None:raise ValueError('missing original semantic judgment')
            new=score_answer(raw,gold[old['task_id']],attempt,rows,review,context=scoring_context(policy,old['task_id']))
            for key in ['answer_sha256','attempt_sha256','gold_sha256','semantic_review_sha256','judge_packet_sha256']:
                if new.get(key)!=old.get(key):raise ValueError('original evidence binding differs: '+key)
            if review_path:new['review_file']=str(review_path.relative_to(run))
            graded[ident]=new
            if new.get('fact_credit')!=old.get('fact_credit') or new['provisional_task_complete']!=old['provisional_task_complete']:
                changes.append({'cohort':name,'attempt_id':ident,'task_id':old['task_id'],'old_coverage':old['supported_required_fact_coverage'],'new_coverage':new['supported_required_fact_coverage'],'old_provisional_completion':old['provisional_task_complete'],'new_provisional_completion':new['provisional_task_complete'],'changed_facts':{k:{'old':old.get('fact_credit',{}).get(k),'new':v} for k,v in new.get('fact_credit',{}).items() if v!=old.get('fact_credit',{}).get(k)}})
        folder=out/name;folder.mkdir();write_atomic(folder/'scores.json',graded)
        validated=report(bundle,run,folder/'scores.json',policy_path,output_path=folder/'report.json')
        if validated['score_binding_issues']:raise ValueError('rescored report validation failed')
        cohorts[name]=(schedule,ledger,graded,gold)
        dimensions={}
        for arm in config['arms']:
            ids={i['attempt_id'] for i in schedule['attempts'] if i['arm']==arm}
            for scope in ['in_scope','partial','out_of_scope']:
                values=[v for ident,v in graded.items() if ident in ids and gold[v['task_id']]['matrix']['scope']==scope]
                dimensions[arm+':'+scope]={'graded':len(values),'mean_fact_coverage':statistics.mean(v['supported_required_fact_coverage'] for v in values),'provisional_completion':sum(v['provisional_task_complete'] for v in values)}
        summaries[name]=dimensions
    comparisons={}
    for pair in spec['comparisons']:
        attempts=[];ledger={};scores={};scopes={}
        for name,arm,label in pair['arms']:
            sched,logs,graded,gold=cohorts[name]
            for item in sched['attempts']:
                if item['arm']!=arm:continue
                ident=item['attempt_id'];attempts.append({**item,'arm':label})
                if ident in logs:ledger[ident]=logs[ident]
                if ident in graded:scores[ident]=graded[ident]
            scopes.update({k:g['matrix']['scope'] for k,g in gold.items()})
        comparison=compare_scope_strata({'attempts':attempts,'repetitions':3,'task_count':30},ledger,scores,scopes,arms=[v[2] for v in pair['arms']],seed=42)
        comparison.update(scoring_version=SCORER_VERSION,original_judgments_reused=True,historical_cohort_confounding=True,human_acceptance_pending=True)
        write_atomic(out/(pair['name']+'.json'),comparison);comparisons[pair['name']]=comparison
    summary={'scoring_version':SCORER_VERSION,'inference_calls':0,'agent_reruns':0,'original_artifacts_modified':False,'pins':pins,'cohorts':summaries,'changed_attempts':len(changes),'comparisons':{k:{'ready':v['primary_comparison_ready'],'estimate':v['quality_estimate']} for k,v in comparisons.items()}}
    write_atomic(out/'changes.json',changes);write_atomic(out/'complete.json',summary)
    print(json.dumps(summary),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('spec',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();rescore(a.spec.resolve(),a.out.resolve())
