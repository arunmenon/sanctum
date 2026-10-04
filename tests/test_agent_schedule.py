import copy
import hashlib
import json

import pytest
import yaml

from sanctum_run.agent_schedule import plan_schedule,report_schedule,compare_scores,compare_scope_strata
from tests.test_agent_bundle import make_bundle


def setup(tmp_path):
    path,config=make_bundle(tmp_path/'bundle')
    root=path.parent
    artifact=root/'hubs/codehub/artifacts.jsonl';artifact.parent.mkdir(parents=True)
    artifact.write_text(json.dumps(dict(artifact_id='a',version='v1',text='return paid'))+'\n')
    manifest=dict(files={'hubs/codehub/artifacts.jsonl':hashlib.sha256(artifact.read_bytes()).hexdigest()})
    (root/'manifest.json').write_text(json.dumps(manifest))
    config['corpus']['expected_sha256']=hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest()
    (root/'principals.json').write_text(json.dumps([dict(principal='reader',groups=['shipping'])]))
    (root/'instructions.txt').write_text('Use evidence only.')
    task=json.loads((root/'tasks.jsonl').read_text());task.update(answer_format='evidence_answer_v1',caller_requirements=[])
    (root/'tasks.jsonl').write_text(json.dumps(task)+'\n')
    gold=json.loads((root/'gold.jsonl').read_text());gold.update(plan_checklist=[])
    gold['matrix'].update(scope='in_scope',sources=['codehub'])
    gold['required_facts']=[dict(fact_id='f1',statement='Paid permits dispatch.',support_kind='evidence',
        evidence=[dict(source_id='codehub',artifact_id='a',version='v1',quote='return paid')])]
    (root/'gold.jsonl').write_text(json.dumps(gold)+'\n')
    config['diversity']['required_sources']=['codehub']
    config.update(mode='evidence_only',workspace=dict(kind='empty'),
        experiment_id='schedule-fixture', instructions='instructions.txt',agent=dict(adapter='claude_code',model=None,effort=None),
        caller=dict(principal='reader',principal_file='principals.json',expected_sha256=hashlib.sha256((root/'principals.json').read_bytes()).hexdigest()),
        limits=dict(agent_rounds=8,cumulative_evidence_tokens=8000,tool_response_evidence_tokens=4000,task_deadline_seconds=120,total_inference_spend_usd=0),
        execution=dict(repetitions=3,random_seed=42,fresh_session_per_attempt=True),
        arms=dict(a=dict(tool_surface='direct_hubs'),b=dict(tool_surface='sanctum_only')))
    path.write_text(yaml.safe_dump(config))
    return path,config


def test_schedule_is_repeatable_and_bound_to_config(tmp_path):
    path,config=setup(tmp_path)
    schedule=plan_schedule(path,tmp_path/'run')
    assert len(schedule['attempts'])==6 and len({a['attempt_id'] for a in schedule['attempts']})==6
    assert plan_schedule(path,tmp_path/'run')==schedule
    config['execution']['random_seed']=43;path.write_text(yaml.safe_dump(config))
    with pytest.raises(ValueError,match='existing schedule differs'):
        plan_schedule(path,tmp_path/'run')


def test_failures_and_missing_attempts_remain_in_denominators(tmp_path):
    path,_=setup(tmp_path);schedule=plan_schedule(path,tmp_path/'run')
    a=schedule['attempts'][0];b=schedule['attempts'][1]
    ledger={a['attempt_id']:dict(state='deadline_exceeded'),b['attempt_id']:dict(state='dispatched')}
    report=report_schedule(schedule,ledger)
    assert sum(x['planned'] for x in report['by_arm'].values())==6
    assert sum(x['failed'] for x in report['by_arm'].values())==1
    assert sum(x['unresolved'] for x in report['by_arm'].values())==1
    assert sum(x['undispatched'] for x in report['by_arm'].values())==4
    assert report['primary_comparison_ready'] is False


def test_paired_task_means_keep_failures_and_missing_judgments_explicit(tmp_path):
    path,_=setup(tmp_path);schedule=plan_schedule(path,tmp_path/'run')
    ledger={a['attempt_id']:dict(state='completed') for a in schedule['attempts']}
    scores={a['attempt_id']:dict(supported_required_fact_coverage=1 if a['arm']=='b' else .5) for a in schedule['attempts']}
    report=compare_scores(schedule,ledger,scores,arms=['a','b'],resamples=100)
    assert report['quality_estimate']['paired_difference']==.5
    assert report['quality_estimate']['task_count']==1
    bad=next(a for a in schedule['attempts'] if a['arm']=='b')
    ledger[bad['attempt_id']]['state']='deadline_exceeded'
    report=compare_scores(schedule,ledger,scores,arms=['a','b'],resamples=100)
    assert report['quality_estimate']['paired_difference']==pytest.approx(1/6)
    missing=next(a for a in schedule['attempts'] if a['arm']=='a')
    del scores[missing['attempt_id']]
    report=compare_scores(schedule,ledger,scores,arms=['a','b'],resamples=100)
    assert report['primary_comparison_ready'] is False and report['quality_estimate'] is None


def test_successful_refusals_cannot_hide_poor_supported_task_scores():
    attempts = [dict(attempt_id=task+arm, task_id=task, arm=arm, repetition=0)
                for task in ['supported', 'boundary'] for arm in ['direct', 'sanctum']]
    schedule = dict(attempts=attempts, repetitions=1, task_count=2)
    ledger = {a['attempt_id']: dict(state='completed') for a in attempts}
    scores = {a['attempt_id']: dict(supported_required_fact_coverage=(
        1 if a['task_id'] == 'boundary' else .25)) for a in attempts}
    report = compare_scope_strata(schedule, ledger, scores,
        {'supported': 'in_scope', 'boundary': 'out_of_scope'}, arms=['direct', 'sanctum'], resamples=100)
    assert report['scope_strata']['in_scope']['quality_estimate']['task_count'] == 1
    assert report['scope_strata']['out_of_scope']['quality_estimate']['task_count'] == 1
    assert report['scope_strata']['partial']['quality_estimate'] is None
    with pytest.raises(ValueError, match='scope mapping'):
        compare_scope_strata(schedule, ledger, scores, {'supported': 'in_scope'}, arms=['direct', 'sanctum'])
