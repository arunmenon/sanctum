"""Report a frozen run from saved results/scores; never dispatch or rerun agents."""
import argparse
import json
from pathlib import Path

from sanctum_run.agent_schedule import compare_scope_strata, file_hash, load_experiment, report_schedule
from sanctum_run.agent_session import write_atomic
from sanctum_run.bundle import _file
from sanctum_run.agent_score import _sha, judge_packet,score_answer


def report(config_path, run, scores_path=None, policy_path=None):
    policy=None
    if policy_path:
        from sanctum_run.quality_policy import load_policy,scoring_context
        policy=load_policy(policy_path)
    config, summary = load_experiment(config_path)
    root = config_path.resolve().parent
    schedule = json.loads((run/'schedule.json').read_text())
    expected = dict(config_sha256=file_hash(config_path), tasks_sha256=file_hash(_file(root,config['tasks'])),
        gold_sha256=file_hash(_file(root,config['gold'])), instructions_sha256=file_hash(_file(root,config['instructions'])),
        corpus_manifest_sha256=summary['manifest_sha256'])
    if schedule['basis'] != expected:
        raise ValueError('report bundle differs from frozen schedule')
    ledger = json.loads((run/'attempts.json').read_text()) if (run/'attempts.json').exists() else {}
    ledger = {key: dict(value) for key, value in ledger.items()}
    records = {}
    missing_results=[]
    for attempt in schedule['attempts']:
        path = run/'attempts'/attempt['attempt_id']/'result.json'
        if not path.exists():
            if attempt['attempt_id'] in ledger:
                missing_results.append(attempt['attempt_id'])
                ledger[attempt['attempt_id']]['comparison_invalid']=True
            continue
        record = json.loads(path.read_text())
        if record['attempt_id'] != attempt['attempt_id']:
            raise ValueError('result identity differs from scheduled attempt')
        if attempt['attempt_id'] not in ledger or ledger[attempt['attempt_id']]['state'] != record['status']:
            raise ValueError('result terminal state differs from attempt ledger')
        records[attempt['attempt_id']] = record
        if record.get('fixture') or ledger[attempt['attempt_id']].get('fixture'):
            ledger[attempt['attempt_id']]['comparison_invalid'] = True
    scores = json.loads(scores_path.read_text()) if scores_path else {}
    gold={r['task_id']:r for r in [json.loads(line) for line in _file(root,config['gold']).read_text().splitlines() if line.strip()]}
    scopes = {key:r['matrix']['scope'] for key,r in gold.items()}
    rows=[]
    for path in sorted((_file(root,config['corpus']['manifest']).parent/'hubs').glob('*/artifacts.jsonl')):
        rows.extend({**json.loads(line),'source_id':path.parent.name} for line in path.read_text().splitlines())
    valid_scores={};score_issues={}
    for item in schedule['attempts']:
        ident=item['attempt_id'];score=scores.get(ident);record=records.get(ident)
        if not score: continue
        if ledger.get(ident,{}).get('comparison_invalid'):
            score_issues[ident]='fixture_or_missing_result';continue
        answer_path=run/'attempts'/ident/'answer.json'
        if record is None or not answer_path.exists():
            score_issues[ident]='missing_result_or_answer';continue
        answer=answer_path.read_text();task_gold=gold[item['task_id']]
        context=scoring_context(policy,item['task_id']) if policy else None
        if context:
            from sanctum_run.agent_score import parse_answer
            normalized_path=answer_path.with_name('structured-answer.json')
            if normalized_path.exists() and json.loads(normalized_path.read_text())!=parse_answer(answer)[0]:
                score_issues[ident]='normalization_receipt_mismatch';continue
            review=None
            if score.get('adjudication_kind')!='protocol_failure':
                review_path=(run/score.get('review_file','')).resolve()
                if not review_path.is_relative_to(run.resolve()) or not review_path.is_file():
                    score_issues[ident]='missing_or_untrusted_review';continue
                review=json.loads(review_path.read_text())
            try: expected_score=score_answer(answer,task_gold,record,rows,review,context=context)
            except (ValueError,TypeError,KeyError):
                score_issues[ident]='invalid_saved_judgment';continue
            if any(score.get(key)!=value for key,value in expected_score.items()):
                score_issues[ident]='tampered_or_stale_score_derivation';continue
            valid_scores[ident]=score;continue
        if (score.get('task_id')!=item['task_id'] or score.get('attempt_sha256')!=_sha(record)
            or score.get('answer_sha256')!=_sha(answer) or score.get('gold_sha256')!=_sha(task_gold)
            or score.get('semantic_review_pending') is not False or not score.get('semantic_review_sha256')
            or score.get('judge_packet_sha256')!=judge_packet(answer,task_gold,record,rows)['packet_sha256']):
            score_issues[ident]='stale_or_unadjudicated_score';continue
        valid_scores[ident]=score
    arms = list(config['arms'])
    result = (compare_scope_strata(schedule, ledger, valid_scores, scopes, arms=arms,
              seed=config['execution']['random_seed']) if len(arms)==2 else report_schedule(schedule,ledger))
    planned = {a['attempt_id'] for a in schedule['attempts']}
    if set(scores)-planned:
        raise ValueError('score file contains unscheduled attempts')
    costs = dict(known_inference_cost_usd=0, unknown_cost_attempt_ids=list(missing_results), fixture_attempt_ids=[],missing_result_attempt_ids=missing_results)
    observations = []
    for attempt in schedule['attempts']:
        record = records.get(attempt['attempt_id'])
        if record is None: continue
        if record.get('fixture') or ledger[attempt['attempt_id']].get('fixture'):
            costs['fixture_attempt_ids'].append(attempt['attempt_id'])
        elif record.get('cost_usd') is None:
            costs['unknown_cost_attempt_ids'].append(attempt['attempt_id'])
        else:
            costs['known_inference_cost_usd'] += record['cost_usd']
        observations.append(dict(attempt_id=attempt['attempt_id'], arm=attempt['arm'],
            status=record['status'], fixture=record.get('fixture',False),
            controller_elapsed_ms=record.get('controller_elapsed_ms'),
            agent_rounds=record.get('agent_rounds'), mcp_calls=len(record.get('mcp_calls',[])),
            nested_model_calls=len(record.get('nested_model_calls',[])),
            usage=record.get('usage'), evidence_delivery=record.get('delivered_evidence',[])))
    costs['inference_cost_complete'] = not costs['unknown_cost_attempt_ids']
    if policy:
        dimensions={}
        for arm in arms:
            for scope in ('in_scope','partial','out_of_scope'):
                selected=[(i,valid_scores.get(i['attempt_id'])) for i in schedule['attempts'] if i['arm']==arm and scopes[i['task_id']]==scope]
                graded=[s for _,s in selected if s is not None]
                plan_values={}
                for s in graded:
                    for label in s.get('plan',[]):plan_values.setdefault(label['dimension'],[]).append(label['score'])
                dimensions[arm+':'+scope]=dict(planned=len(selected),graded=len(graded),protocol_failures=sum(s.get('adjudication_kind')=='protocol_failure' for s in graded),
                    material_unsupported_incidence=sum(any(c['severity']=='material' for c in s.get('unsupported_claims',[])) for s in graded),
                    provisional_completion=sum(s.get('provisional_task_complete',False) for s in graded),human_acceptance_pending=sum(s.get('human_acceptance_pending',True) for s in graded),
                    mean_citation_support=({k:sum(v)/len(v) for k,v in {'citation_support':[s['citation_support'] for s in graded if s.get('citation_support') is not None]}.items() if v}),
                    mean_plan_dimensions={k:sum(v)/len(v) for k,v in plan_values.items()},
                    evidence_budget_exhaustion=sum(any(d.get('budget_exhausted') for d in records[i['attempt_id']].get('delivered_evidence',[])) for i,_ in selected if i['attempt_id'] in records))
        result['quality_dimensions']=dimensions
        result['scoring_policy_sha256']=file_hash(policy_path)
        result['quality_claim']='exploratory machine judgments; no independent frozen gold or human completion acceptance'
    result.update(schema_version=1, schedule_sha256=file_hash(run/'schedule.json'),
        scores_sha256=file_hash(scores_path) if scores_path else None,
        score_binding_issues=score_issues,
        costs=costs, observations=observations,
        limitation='Fixture execution is operational evidence only. Semantic/human acceptance remains separately recorded.')
    write_atomic(run/'comparison-report.json',result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle',type=Path); parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--scores',type=Path)
    parser.add_argument('--quality-policy',type=Path)
    args=parser.parse_args()
    result=report(args.bundle,args.run,args.scores,args.quality_policy)
    print(json.dumps(dict(report=str(args.run/'comparison-report.json'),
        primary_comparison_ready=result['primary_comparison_ready'],costs=result['costs'])))
