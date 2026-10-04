"""Deterministic frozen attempt schedule, independent of repository/domain names."""
import hashlib
import json
import random
from statistics import mean
from pathlib import Path

import yaml

from sanctum_run.bundle import validate_bundle
from sanctum_run.agent_session import write_atomic
from sanctum_run.agent_contract import validate_contract


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_experiment(path:Path):
    summary=validate_bundle(path)
    root=path.resolve().parent
    config=yaml.safe_load(path.read_text())
    if config.get('mode')!='evidence_only' or config.get('workspace',{}).get('kind')!='empty':
        raise ValueError('only evidence-only empty-workspace mode is implemented')
    limits=config.get('limits',{})
    for key in ('agent_rounds','cumulative_evidence_tokens','tool_response_evidence_tokens','task_deadline_seconds'):
        if type(limits.get(key)) is not int or limits[key]<=0:
            raise ValueError('positive integer limit required: '+key)
    if limits['tool_response_evidence_tokens']>limits['cumulative_evidence_tokens']:
        raise ValueError('response evidence allowance exceeds session allowance')
    execution=config.get('execution',{})
    if type(execution.get('repetitions')) is not int or execution['repetitions']<=0 or execution.get('fresh_session_per_attempt') is not True:
        raise ValueError('fresh sessions and positive repetitions required')
    if type(execution.get('random_seed')) is not int:
        raise ValueError('integer schedule seed required')
    arms=config.get('arms')
    if not isinstance(arms,dict) or not arms:
        raise ValueError('explicit experiment arms required')
    if any(not isinstance(name,str) or not name or not isinstance(value,dict) or
           value.get('tool_surface') not in ('direct_hubs','sanctum_only') for name,value in arms.items()):
        raise ValueError('invalid arm declaration')
    validate_contract(root,config)
    return config,summary


def plan_schedule(path:Path,out:Path):
    config,summary=load_experiment(path)
    root=path.resolve().parent
    public_path=(root/config['tasks']).resolve()
    gold_path=(root/config['gold']).resolve()
    tasks=[json.loads(line) for line in public_path.read_text().splitlines() if line.strip()]
    basis=dict(config_sha256=file_hash(path),tasks_sha256=file_hash(public_path),gold_sha256=file_hash(gold_path),
               instructions_sha256=file_hash((root/config['instructions']).resolve()),
               corpus_manifest_sha256=summary['manifest_sha256'])
    basis_hash=hashlib.sha256(json.dumps(basis,sort_keys=True).encode()).hexdigest()
    rng=random.Random(config['execution']['random_seed'])
    attempts=[]
    for task in tasks:
        for repetition in range(config['execution']['repetitions']):
            arms=list(config['arms']);rng.shuffle(arms)
            for arm in arms:
                key=f'{basis_hash}:{task["task_id"]}:{repetition}:{arm}'
                attempts.append(dict(attempt_id=hashlib.sha256(key.encode()).hexdigest()[:32],
                    task_id=task['task_id'],repetition=repetition,arm=arm))
    schedule=dict(schema_version=1,basis=basis,attempts=attempts,task_count=len(tasks),
                  repetitions=config['execution']['repetitions'],seed=config['execution']['random_seed'])
    out.mkdir(parents=True,exist_ok=True)
    target=out/'schedule.json'
    if target.exists():
        if json.loads(target.read_text())!=schedule:
            raise ValueError('existing schedule differs; choose a new run directory')
    else:
        write_atomic(target,schedule)
    return schedule


def report_schedule(schedule:dict,ledger:dict):
    planned={a['attempt_id'] for a in schedule['attempts']}
    if set(ledger)-planned:
        raise ValueError('attempt ledger contains unscheduled dispatches')
    by_arm={}
    for item in schedule['attempts']:
        counts=by_arm.setdefault(item['arm'],dict(planned=0,undispatched=0,completed=0,failed=0,unresolved=0))
        counts['planned']+=1
        row=ledger.get(item['attempt_id'])
        if row is None:counts['undispatched']+=1
        elif row['state']=='dispatched':counts['unresolved']+=1
        elif row['state']=='completed':counts['completed']+=1
        else:counts['failed']+=1
    complete=all(not x['undispatched'] and not x['unresolved'] for x in by_arm.values())
    return dict(by_arm=by_arm,all_planned_attempts_terminal=complete,
                primary_comparison_ready=False,quality_estimate=None)


def compare_scores(schedule,ledger,scores,*,arms,seed=42,resamples=10000):
    """Average repetitions within tasks, then bootstrap paired task clusters."""
    if len(arms)!=2 or len(set(arms))!=2 or resamples<=0:
        raise ValueError('two distinct comparison arms and positive resamples required')
    operational=report_schedule(schedule,ledger)
    groups={}
    for item in schedule['attempts']:
        if item['arm'] not in arms:
            continue
        group=groups.setdefault(item['task_id'],{arm:[] for arm in arms})
        record=ledger.get(item['attempt_id'])
        value=None
        if record and record['state']!='dispatched' and not record.get('comparison_invalid'):
            if record['state']!='completed':
                value=0.0  # dispatched outcome failures remain in the primary denominator
            else:
                value=scores.get(item['attempt_id'],{}).get('supported_required_fact_coverage')
                if value is not None and (type(value) not in (float,int) or not 0<=value<=1):
                    raise ValueError('invalid coverage score')
        group[item['arm']].append(value)
    complete_tasks={tid:values for tid,values in groups.items()
        if all(len(values[a])==schedule['repetitions'] and all(v is not None for v in values[a]) for a in arms)}
    deltas=[mean(values[arms[1]])-mean(values[arms[0]]) for values in complete_tasks.values()]
    estimate=None
    if deltas:
        rng=random.Random(seed)
        draws=sorted(mean(rng.choices(deltas,k=len(deltas))) for _ in range(resamples))
        estimate=dict(task_count=len(deltas),paired_difference=mean(deltas),
            descriptive_95_percent_interval=[draws[int(.025*(resamples-1))],draws[int(.975*(resamples-1))]],
            resamples=resamples,seed=seed,unit='task cluster, averaged repetitions',
            interpretation='Directional pilot; not a production-adoption claim.')
    ready=len(complete_tasks)==len(groups) and bool(groups) and operational['all_planned_attempts_terminal']
    return dict(**{k:v for k,v in operational.items() if k not in ('primary_comparison_ready','quality_estimate')},
        primary_comparison_ready=ready,quality_estimate=estimate if ready else None,
        exploratory_complete_task_estimate=None if ready else estimate,
        incomplete_task_ids=sorted(set(groups)-set(complete_tasks)),comparison_arms=arms)


def compare_scope_strata(schedule, ledger, scores, task_scopes, *, arms, seed=42, resamples=10000):
    """Keep supported, partial and boundary performance visible separately."""
    task_ids = {a['task_id'] for a in schedule['attempts']}
    if set(task_scopes) != task_ids or any(scope not in ('in_scope', 'partial', 'out_of_scope')
                                        for scope in task_scopes.values()):
        raise ValueError('exact task scope mapping required')
    report = compare_scores(schedule, ledger, scores, arms=arms, seed=seed, resamples=resamples)
    strata = {}
    for scope in ('in_scope', 'partial', 'out_of_scope'):
        attempts = [a for a in schedule['attempts'] if task_scopes[a['task_id']] == scope]
        if not attempts:
            strata[scope] = dict(task_count=0, quality_estimate=None, primary_comparison_ready=False)
            continue
        ids = {a['attempt_id'] for a in attempts}
        subset = {**schedule, 'attempts': attempts,
                  'task_count': len({a['task_id'] for a in attempts})}
        strata[scope] = compare_scores(subset, {k: v for k, v in ledger.items() if k in ids},
            {k: v for k, v in scores.items() if k in ids}, arms=arms, seed=seed, resamples=resamples)
    report['scope_strata'] = strata
    report['interpretation'] = 'Inspect each scope stratum; successful boundary handling cannot establish supported-task quality.'
    return report
