"""Validate and summarize a four-setup Jev development campaign."""
import argparse
import json
from pathlib import Path
from statistics import mean

import yaml

from report_agent_run import report
from sanctum_run.agent_schedule import compare_scope_strata
from sanctum_run.agent_session import write_atomic


def summarize(bundle: Path, run: Path, scores_path: Path, policy: Path):
    checked = report(bundle, run, scores_path, policy)
    if checked['score_binding_issues']:
        raise ValueError('score binding issues remain')
    config = yaml.safe_load(bundle.read_text())
    schedule = json.loads((run/'schedule.json').read_text())
    ledger = json.loads((run/'attempts.json').read_text())
    scores = json.loads(scores_path.read_text())
    gold = {r['task_id']: r for r in (json.loads(line) for line in
            (bundle.parent/config['gold']).read_text().splitlines())}
    scopes = {key: value['matrix']['scope'] for key,value in gold.items()}
    if len(scores) != len(schedule['attempts']):
        raise ValueError('not all answers scored; keep missing judgments explicit')
    summaries = {}
    for arm in config['arms']:
        selected = [a for a in schedule['attempts'] if a['arm'] == arm]
        by_scope = {}
        for scope in ('in_scope','partial','out_of_scope'):
            values = [scores[a['attempt_id']]['supported_required_fact_coverage']
                      for a in selected if scopes[a['task_id']] == scope]
            by_scope[scope] = mean(values) if values else None
        selected_scores = [scores[a['attempt_id']] for a in selected]
        summary = dict(attempts=len(selected),coverage=by_scope,
            overall_coverage=mean(s['supported_required_fact_coverage'] for s in selected_scores),
            provisional_complete=sum(s['provisional_task_complete'] for s in selected_scores),
            material_unsupported_answers=sum(any(c['severity']=='material' for c in s.get('unsupported_claims',[])) for s in selected_scores),
            supported_plan_scores=checked['quality_dimensions'][arm+':in_scope']['mean_plan_dimensions'],
            supported_citation_support=checked['quality_dimensions'][arm+':in_scope']['mean_citation_support'],
            decisions={},provider_rounds={})
        for a in selected:
            record=json.loads((run/'attempts'/a['attempt_id']/'result.json').read_text())
            for call in record.get('nested_model_calls',[]):
                counts=summary['provider_rounds'].setdefault(call['round'],
                    dict(decisions=0,http_calls=0,unavailable=0,invalid_questions=0))
                counts['decisions']+=1
                counts['http_calls']+=call.get('calls',0)
                counts['unavailable']+=call.get('outcome')!='ok'
                counts['invalid_questions']+=len(call.get('invalid_ids',[]))
            for call in record.get('mcp_calls',[]):
                for d in call.get('router_receipt',{}).get('decisions',[]):
                    value=d.get('value') or {}
                    if value.get('application_policy') != 'raw':continue
                    kind=d['target'].split(':',1)[0]
                    counts=summary['decisions'].setdefault(kind,dict(answered=0,positive=0,shadow=0))
                    counts['answered']+=1
                    counts['positive']+=d.get('disposition')=='use'
                    counts['shadow']+=value.get('shadow') is True
        summaries[arm]=summary
    for arm in config['arms']:
        if arm=='baseline':continue
        paired=compare_scope_strata(schedule,ledger,scores,scopes,arms=['baseline',arm])
        if not paired['primary_comparison_ready']:raise ValueError('paired comparison incomplete')
        write_atomic(run/f'baseline-vs-{arm}.json',paired)
    result=dict(setups=summaries,all_answers_scored=True,agent_reruns=False,
                independent_acceptance=False,frozen_evaluation=False,
                limitation='Same development questions, one attempt per setup, machine judging; no promotion or causal production claim.')
    write_atomic(run/'jev-flow-summary.json',result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle',type=Path)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--scores',type=Path,required=True)
    parser.add_argument('--policy',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(summarize(args.bundle.resolve(),args.run.resolve(),args.scores.resolve(),args.policy.resolve())))
