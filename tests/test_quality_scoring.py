import copy
import json
import pytest
from sanctum_run.agent_score import judge_packet,score_answer
from tests.test_agent_score import fixture,CASES


def contextual(case=None):
    answer,gold,attempt,rows,review=fixture(case or CASES[0])
    context={'version':'quality-scoring-v2','task':{'prompt':'Explain the screening timeout and its limits.','caller_requirements':[]},
        'rubric':{'levels':{'0':'absent','1':'partial','2':'all mandatory items'}},'topic_vocabulary':{},'boundary_sources':{}}
    for f in review['facts']:f['investigation_relevant']=True
    for p in review['plan']:p['items']=[{'item':i,'met':False,'reason':'Required ground not established.'} for d in gold['plan_checklist'] for i in d['mandatory_items'] if d['dimension']==p['dimension']]
    for c in review['additional_claims']:c.update(claim_type='factual',supporting_evidence_ids=[])
    review['packet_sha256']=judge_packet(answer,gold,attempt,rows,context)['packet_sha256']
    return answer,gold,attempt,rows,review,context


def test_fenced_input_preserves_raw_binding_and_malformed_is_bound_zero():
    a,g,t,rows,r,c=contextual();raw='```json\n'+json.dumps(a)+'\n```'
    r['packet_sha256']=judge_packet(raw,g,t,rows,c)['packet_sha256']
    assert score_answer(raw,g,t,rows,r,context=c)['supported_required_fact_coverage']==1
    score=score_answer('```json\n{"bad":\n```',g,t,rows,context=c)
    assert score['adjudication_kind']=='protocol_failure' and score['supported_required_fact_coverage']==0
    assert score['semantic_review_pending'] is False and score['judge_packet_sha256']


@pytest.mark.parametrize('damage',['reason','relevance','item','nested'])
def test_strict_judge_labels_fail_closed(damage):
    a,g,t,rows,r,c=contextual(next(x for x in CASES if 'plan_score' in x))
    if damage=='reason':r['facts'][0].pop('reason')
    if damage=='relevance':r['facts'][0].pop('investigation_relevant')
    if damage=='item':r['plan'][0]['items']=[]
    if damage=='nested':r['facts'][0]=None
    with pytest.raises(ValueError):score_answer(a,g,t,rows,r,context=c)


def test_boundary_overlay_and_same_source_irrelevance():
    a,g,t,rows,r,c=contextual(next(x for x in CASES if x['name']=='justified_partial'))
    g['required_facts'][1]['boundary_record'].pop('required_sources');g['matrix']={'sources':[]}
    c['boundary_sources']={'live.deployment':['code']}
    r['packet_sha256']=judge_packet(a,g,t,rows,c)['packet_sha256']
    assert score_answer(a,g,t,rows,r,context=c)['fact_credit']['live.deployment']==1
    r['facts'][1]['investigation_relevant']=False
    assert score_answer(a,g,t,rows,r,context=c)['fact_credit']['live.deployment']==0


def test_context_evidence_and_task_binding_blinded():
    a,g,t,rows,r,c=contextual();t['arm']='sanctum';t['model']='secret-agent-model'
    packet=judge_packet(a,g,t,rows,c)
    assert packet['packet']['task']==c['task'] and len(packet['packet']['delivered_evidence'])==4
    assert 'call-0-unit' not in json.dumps(packet) and 'secret-agent-model' not in json.dumps(packet)
    changed=copy.deepcopy(c);changed['task']['prompt']='Different required work'
    assert judge_packet(a,g,t,rows,changed)['packet_sha256']!=packet['packet_sha256']


def test_supported_but_unmapped_factual_extra_prevents_completion():
    a,g,t,rows,r,c=contextual();r['additional_claims']=[{'text':'Retries always succeed.','claim_type':'factual','supported':True,'severity':'none','reason':'Unsupported mapping omitted.','supporting_evidence_ids':[]}]
    score=score_answer(a,g,t,rows,r,context=c)
    assert not score['provisional_task_complete'] and score['unsupported_claims'][0]['severity']=='material'


def test_report_recomputes_protocol_zero_and_rejects_numeric_tampering(tmp_path):
    from pathlib import Path
    from tests.test_agent_schedule import setup
    from sanctum_run.agent_schedule import plan_schedule
    from tools.report_agent_run import report
    from sanctum_run.quality_policy import scoring_context
    config,settings=setup(tmp_path)
    run=tmp_path/'run';schedule=plan_schedule(config,run)
    gold_rows=[json.loads(l) for l in (config.parent/settings['gold']).read_text().splitlines()]
    gold={g['task_id']:g for g in gold_rows}
    policy={'version':'quality-scoring-v2','frozen_evaluation':False,'tasks':{key:{'prompt':'Explain the source','caller_requirements':[]} for key in gold},'rubric':{},'boundary_sources':{},'topic_vocabulary':{}}
    policy_path=tmp_path/'policy.json';policy_path.write_text(json.dumps(policy))
    rows=[]
    for path in (config.parent/settings['corpus']['manifest']).parent.glob('hubs/*/artifacts.jsonl'):
        rows.extend({**json.loads(l),'source_id':path.parent.name} for l in path.read_text().splitlines())
    scores={};ledger={}
    for item in schedule['attempts']:
        key=item['attempt_id'];folder=run/'attempts'/key;folder.mkdir(parents=True)
        record={'attempt_id':key,'status':'completed','fixture':False,'cost_usd':0,'mcp_calls':[],'delivered_evidence':[]}
        (folder/'result.json').write_text(json.dumps(record));(folder/'answer.json').write_text('Malformed JSON')
        ledger[key]={'state':'completed'}
        scores[key]=score_answer('Malformed JSON',gold[item['task_id']],record,rows,context=scoring_context(policy,item['task_id']))
    (run/'attempts.json').write_text(json.dumps(ledger));p=tmp_path/'scores.json';p.write_text(json.dumps(scores))
    valid=report(config,run,p,policy_path)
    assert not valid['score_binding_issues'] and valid['primary_comparison_ready']
    first=next(iter(scores));scores[first]['supported_required_fact_coverage']=1;p.write_text(json.dumps(scores))
    changed=report(config,run,p,policy_path)
    assert changed['score_binding_issues'][first]=='tampered_or_stale_score_derivation'
    assert not changed['primary_comparison_ready']


def test_mandatory_item_identity_allows_quotes_but_not_changed_words():
    a,g,t,rows,r,c=contextual(next(x for x in CASES if 'plan_score' in x))
    g['plan_checklist'][0]['mandatory_items']=["Explain the caller’s recovery path."]
    r['plan'][0]['items']=[{'item':"Explain the caller's recovery path.",'met':False,'reason':'Recovery is missing.'}]
    r['packet_sha256']=judge_packet(a,g,t,rows,c)['packet_sha256']
    score_answer(a,g,t,rows,r,context=c)
    r['plan'][0]['items'][0]['item']="Explain a different recovery path."
    with pytest.raises(ValueError,match='match rubric'):score_answer(a,g,t,rows,r,context=c)
