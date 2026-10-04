import json

import pytest

from sanctum_run.agent_schedule import plan_schedule
from sanctum_run.agent_score import _sha,judge_packet
from tests.test_agent_schedule import setup
from tools.report_agent_run import report


def test_fixture_scores_cannot_establish_agent_quality_and_state_mismatch_fails(tmp_path):
    config,settings = setup(tmp_path)
    gold_path=config.parent/settings['gold']
    gold=[json.loads(line) for line in gold_path.read_text().splitlines()]
    for task in gold: task['matrix']['scope']='in_scope'
    gold_path.write_text(''.join(json.dumps(task)+'\n' for task in gold))
    run=tmp_path/'run'
    schedule=plan_schedule(config,run)
    ledger={}
    scores={}
    for item in schedule['attempts']:
        ident=item['attempt_id']
        folder=run/'attempts'/ident;folder.mkdir(parents=True)
        record=dict(attempt_id=ident,status='completed',fixture=True,cost_usd=12,
                    agent_rounds=2,mcp_calls=[],delivered_evidence=[])
        (folder/'result.json').write_text(json.dumps(record))
        ledger[ident]=dict(state='completed')
        scores[ident]=dict(supported_required_fact_coverage=1)
    (run/'attempts.json').write_text(json.dumps(ledger))
    score_path=tmp_path/'scores.json';score_path.write_text(json.dumps(scores))
    result=report(config,run,score_path)
    assert not result['primary_comparison_ready']
    assert result['quality_estimate'] is None
    assert result['costs']['known_inference_cost_usd']==0
    assert len(result['costs']['fixture_attempt_ids'])==6
    ident=schedule['attempts'][0]['attempt_id'];ledger[ident]['state']='deadline_exceeded'
    (run/'attempts.json').write_text(json.dumps(ledger))
    with pytest.raises(ValueError,match='terminal state'):
        report(config,run,score_path)


@pytest.mark.parametrize('damage',['stale_score','wrong_task','missing_result','missing_answer'])
def test_comparison_requires_current_result_answer_and_semantic_score(tmp_path,damage):
    config,settings=setup(tmp_path);run=tmp_path/'run'
    schedule=plan_schedule(config,run)
    gold={r['task_id']:r for r in [json.loads(l) for l in (config.parent/settings['gold']).read_text().splitlines()]}
    row=json.loads(((config.parent/settings['corpus']['manifest']).parent/'hubs/codehub/artifacts.jsonl').read_text().strip())
    rows=[{**row,'source_id':'codehub'}]
    answer=json.dumps(dict(schema_version=1,answer='Report binding fixture.',claims=[],uncertainties=[],unmet_requirements=[]))+'\n'
    ledger={};scores={}
    for item in schedule['attempts']:
        ident=item['attempt_id'];folder=run/'attempts'/ident;folder.mkdir(parents=True)
        record=dict(attempt_id=ident,task_id=item['task_id'],status='completed',fixture=False,cost_usd=0,
                    mcp_calls=[],delivered_evidence=[])
        (folder/'result.json').write_text(json.dumps(record));(folder/'answer.json').write_text(answer)
        ledger[ident]=dict(state='completed',fixture=False)
        task_gold=gold[item['task_id']]
        scores[ident]=dict(task_id=item['task_id'],supported_required_fact_coverage=1,attempt_sha256=_sha(record),
            answer_sha256=_sha(answer),gold_sha256=_sha(task_gold),semantic_review_pending=False,
            semantic_review_sha256='unit-test-only',judge_packet_sha256=judge_packet(answer,task_gold,record,rows)['packet_sha256'])
    (run/'attempts.json').write_text(json.dumps(ledger));score_path=tmp_path/'scores.json';score_path.write_text(json.dumps(scores))
    assert report(config,run,score_path)['primary_comparison_ready']
    ident=schedule['attempts'][0]['attempt_id'];folder=run/'attempts'/ident
    if damage=='stale_score':scores[ident]['answer_sha256']='old-answer'
    elif damage=='wrong_task':scores[ident]['task_id']='other-task'
    elif damage=='missing_result':(folder/'result.json').unlink()
    else:(folder/'answer.json').unlink()
    score_path.write_text(json.dumps(scores));result=report(config,run,score_path)
    assert not result['primary_comparison_ready'] and result['quality_estimate'] is None
    assert ident in result['score_binding_issues']
    if damage=='missing_result':
        assert ident in result['costs']['unknown_cost_attempt_ids']
        assert not result['costs']['inference_cost_complete']


def test_changed_public_instructions_require_a_new_frozen_schedule(tmp_path):
    config,settings=setup(tmp_path);run=tmp_path/'run';plan_schedule(config,run)
    instructions=config.parent/settings['instructions'];instructions.write_text('Changed experiment instructions.')
    with pytest.raises(ValueError,match='existing schedule differs'):
        plan_schedule(config,run)
    with pytest.raises(ValueError,match='differs from frozen schedule'):
        report(config,run)
