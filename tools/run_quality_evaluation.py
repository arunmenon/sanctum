"""Calibrate and judge saved answers only; no agent reruns or human sign-off."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import uuid

from sanctum_run.agent_score import _sha,judge_packet,score_answer,parse_answer
from sanctum_run.agent_session import isolated_environment,claude_command,write_atomic
from sanctum_run.quality_policy import load_policy,scoring_context

CLI=Path('/Users/arunmenon/.local/share/claude/versions/2.1.288')


def subscription_token():
    path=Path.home()/'.claude/.credentials.json'
    raw=path.read_text() if path.exists() else subprocess.run(['security','find-generic-password','-s','Claude Code-credentials','-w'],capture_output=True,text=True,check=True).stdout
    token=json.loads(raw).get('claudeAiOauth',{}).get('accessToken')
    if not token:raise ValueError('subscription login missing')
    return token


def json_reply(raw):
    value=raw.strip()
    if value.startswith('```json\n') and value.endswith('\n```'):value=value[8:-4]
    return json.loads(value)


def judge(packet,out,policy,format_feedback=None):
    out.mkdir(parents=True,exist_ok=True)
    if (out/'packet.json').exists() and json.loads((out/'packet.json').read_text())!=packet:
        raise ValueError('saved judge packet changed; choose a new evaluation')
    write_atomic(out/'packet.json',packet)
    if (out/'native-result.json').exists():
        native=json.loads((out/'native-result.json').read_text())
        returncode=0
    else:
        token=subscription_token()
        with tempfile.TemporaryDirectory(prefix='sanctum-judge-',dir='/tmp') as folder:
            base=Path(folder);home=base/'home';home.mkdir();(home/'claude-config').mkdir();(home/'tmp').mkdir()
            workspace=base/'workspace';workspace.mkdir();mcp=base/'mcp.json';mcp.write_text('{"mcpServers":{}}')
            env=isolated_environment(home,{'CLAUDE_CODE_OAUTH_TOKEN':token})
            command=claude_command(str(CLI),policy['judge']['model'],policy['judge']['effort'],str(uuid.uuid4()),mcp,2,0.5,authentication_mode='subscription')
            command[command.index('--output-format')+1]='json'
            judge_input=packet if format_feedback is None else {"packet":packet,"format_feedback":format_feedback,"instruction":"Return a complete review for the original packet. Correct the schema violation; do not change grades to achieve any target. packet_sha256 must remain the original packet digest. Every additional_claims entry requires severity: none, minor, or material. Preserve substantive findings unless the original packet warrants a correction."}
            process=subprocess.run(command,input=json.dumps(judge_input),text=True,capture_output=True,env=env,cwd=workspace,timeout=120)
        native=json.loads(process.stdout.replace(token,'[REDACTED]'))
        returncode=process.returncode
        # Preserve visible text and terminal metadata, excluding native thinking.
        if isinstance(native,list):
            for event in native:
                message=event.get('message',{})
                if isinstance(message.get('content'),list):message['content']=[x for x in message['content'] if x.get('type')!='thinking']
        write_atomic(out/'native-result.json',native)
        (out/'stderr.log').write_text(process.stderr.replace(token,'[REDACTED]'))
    if isinstance(native,list):native=next((v for v in reversed(native) if v.get('type')=='result'),{})
    if returncode or native.get('is_error'):raise ValueError('judge provider failure: '+str(native.get('result',''))[:300])
    if policy['judge']['model'] not in native.get('modelUsage',{}):raise ValueError('native judge model not verified')
    reply=native.get('structured_output') or json_reply(native.get('result',''))
    if reply.get('model')!=policy['judge']['model']:
        write_atomic(out/'invalid-review.json',reply)
        if format_feedback is not None or policy['judge'].get('invalid_schema_retries',0)!=1:
            raise ValueError('judge reported wrong model')
        write_atomic(out/'schema-retry-receipt.json',{'reason':'missing or wrong top-level model label','max_retries':1,'native_model_verified':True,'agent_rerun':False})
        reply=judge(packet,out/'schema-retry-model-01',policy,format_feedback={'validation_error':'Required top-level model must be '+policy['judge']['model']+' and adjudicator must be a string; do not nest the model under adjudicator.','previous_review':reply})
    write_atomic(out/'review.json',reply)
    return reply


def calibration(policy,out):
    from tests.test_agent_score import fixture,CASES
    from tests.test_quality_scoring import contextual
    cases=[]
    for case in CASES:
        a,g,t,rows,expected,context=contextual(case)
        context['task']['prompt']='Explain the source-supported screening-timeout disposition, identify live-deployment limits where requested, and give grounded rollout guidance when the task checklist asks for it.'
        context['rubric']=policy['rubric']
        cases.append((case['name'],a,g,t,rows,context,case['expected_coverage'],case['expected_provisional_complete']))
    for kind,complete in [('HLD',True),('HLD',False),('LLD',True),('LLD',False)]:
        a,g,t,rows,expected,context=contextual()
        g['plan_checklist']=[{'dimension':'design','mandatory_items':['Define component responsibility.','Describe timeout error flow and observable tests.']}]
        if kind=='HLD':
            a['answer']+=' Proposed HLD: a thin screening adapter owns transport, and the row runner owns scheduling.'
        else:
            g['plan_checklist']=[{'dimension':'design','mandatory_items':['Define proposed input/output interface and compatibility.','Describe timeout error flow and observable tests.']}]
            a['answer']+=' Proposed LLD: add a wrapper screen(payload: Mapping[str, JSONValue], remaining_budget: BudgetSeconds) returning a proposed tagged Outcome: Deferred(reason=transport_timeout) or Scored(value=OpaqueScreeningResult). The payload is forwarded unchanged and the successful result is deliberately opaque rather than assuming unsupported business fields. Existing callers keep their old entry point, signature and response shape; only opt-in callers use the wrapper, with a compatibility adapter translating the existing successful result into Scored. Before adoption, compatibility tests compare old-entry results before and after adding the wrapper, with old callers never receiving the new tagged shape. The wrapper owns transport errors and the caller owns scheduling.'
        if complete:a['answer']+=' Proposed timeout flow: the adapter catches a transport timeout and returns deferred; the row runner records the pending row for a later scheduled pass without an immediate retry. Tests inject a timeout, assert deferred from the adapter and pending at the row runner, and verify the successful screening path retains its prior outcome. These are proposed integration and tests, not claims that the existing caller already implements them.'
        context['task']['prompt']='Propose an '+kind+' with component responsibilities, timeout error flow and observable tests.';context['rubric']=policy['rubric']
        cases.append(('alternative-'+kind if complete else 'incomplete-'+kind,a,g,t,rows,context,1,complete))
    results=[]
    for name,a,g,t,rows,context,coverage,completion in cases:
        packet=judge_packet(a,g,t,rows,context)
        try:
            review=judge(packet,out/'cases'/name,policy)
            score=score_answer(a,g,t,rows,review,context=context)
            agreed=score['supported_required_fact_coverage']==coverage and score['provisional_task_complete']==completion
            row={'case':name,'passed':agreed,'expected_coverage':coverage,'actual_coverage':score['supported_required_fact_coverage'],'expected_provisional':completion,'actual_provisional':score['provisional_task_complete']}
            write_atomic(out/'cases'/name/'score.json',score)
        except (ValueError,subprocess.TimeoutExpired) as error:row={'case':name,'passed':False,'error':str(error)}
        results.append(row);write_atomic(out/'calibration-progress.json',{'cases':results,'passed':all(x['passed'] for x in results),'complete':False});print(json.dumps(row),flush=True)
    result={'cases':results,'passed':all(x['passed'] for x in results),'complete':True,'same_model_bias':True,'human_spot_check_completed':False}
    write_atomic(out/'calibration.json',result)
    return result['passed']


def evaluate(bundle,run,policy_path,out):
    import yaml
    policy=load_policy(policy_path);config=yaml.safe_load(bundle.read_text());root=bundle.resolve().parent
    rows=[]
    for file in sorted((root/config['corpus']['manifest']).parent.glob('hubs/*/artifacts.jsonl')):
        rows.extend({**json.loads(l),'source_id':file.parent.name} for l in file.read_text().splitlines())
    gold={v['task_id']:v for v in [json.loads(l) for l in (root/config['gold']).read_text().splitlines()]}
    schedule=json.loads((run/'schedule.json').read_text());out.mkdir(parents=True,exist_ok=True)
    binding={'policy_sha256':hashlib.sha256(policy_path.read_bytes()).hexdigest(),'scorer_sha256':hashlib.sha256(Path('src/sanctum_run/agent_score.py').read_bytes()).hexdigest(),'judge_cli_sha256':hashlib.sha256(CLI.read_bytes()).hexdigest(),'run_schedule_sha256':hashlib.sha256((run/'schedule.json').read_bytes()).hexdigest(),'evaluator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'fixtures_sha256':hashlib.sha256(Path('tests/fixtures/agent-score-cases.json').read_bytes()).hexdigest()}
    ordered=copy.deepcopy(schedule['attempts']);random.Random(183).shuffle(ordered)
    plan={'basis':binding,'attempts':ordered,'judge':policy['judge'],'protocol_failures_retained':True,'frozen_evaluation':False}
    if (out/'schedule.json').exists() and json.loads((out/'schedule.json').read_text())!=plan:raise ValueError('quality schedule changed')
    write_atomic(out/'schedule.json',plan)
    if not (out/'calibration.json').exists():
        if not calibration(policy,out):raise SystemExit('Calibration disagreements: inspect saved cases; bulk judging not dispatched.')
    elif not json.loads((out/'calibration.json').read_text())['passed']:raise SystemExit('Calibration gate remains closed')
    scores={}
    failures=json.loads((out/'judge-failures.json').read_text()) if (out/'judge-failures.json').exists() else {}
    if (out/'scores.json').exists():scores=json.loads((out/'scores.json').read_text())
    for item in ordered:
        ident=item['attempt_id']
        if ident in scores or ident in failures:continue
        folder=run/'attempts'/ident;attempt=json.loads((folder/'result.json').read_text());answer=(folder/'answer.json').read_text();g=gold[item['task_id']];context=scoring_context(policy,item['task_id'])
        packet=judge_packet(answer,g,attempt,rows,context);_,errors=parse_answer(answer)
        if errors:
            score=score_answer(answer,g,attempt,rows,context=context)
        else:
            judgment=out/'judgments'/ident
            try:
                if (judgment/'review.json').exists():review=json.loads((judgment/'review.json').read_text())
                else:review=judge(packet,judgment,policy)
                try:
                    score=score_answer(answer,g,attempt,rows,review,context=context)
                except ValueError as schema_error:
                    if policy['judge'].get('invalid_schema_retries',0)!=1:raise
                    initial=review
                    prior_retry=(judgment/'schema-retry-receipt.json').exists()
                    judgment=judgment/'schema-retry-01'
                    feedback={'validation_error':str(schema_error),'previous_review':initial}
                    if prior_retry:
                        # Resume the one already-recorded retry; never issue a second.
                        if not (judgment/'review.json').exists():raise schema_error
                        review=json.loads((judgment/'review.json').read_text())
                    else:
                        write_atomic(judgment.parent/'schema-retry-receipt.json',{'reason':str(schema_error),'max_retries':1,'agent_rerun':False})
                        review=judge(packet,judgment,policy,format_feedback=feedback)
                    score=score_answer(answer,g,attempt,rows,review,context=context)
            except (ValueError,subprocess.TimeoutExpired) as error:
                failures[ident]={'reason':str(error),'quality_score':None,'agent_rerun':False,'review_directory':str(judgment.relative_to(run))}
                write_atomic(out/'judge-failures.json',failures)
                print(json.dumps({'judge_failure':ident,'reason':str(error),'quality_score':None}),flush=True)
                continue
            score['review_file']=str((judgment/'review.json').relative_to(run))
        scores[ident]=score;write_atomic(out/'scores.json',scores)
        write_atomic(out/'progress.json',{'planned':len(ordered),'scored':len(scores),'semantic_judgments':sum(s['adjudication_kind']=='semantic' for s in scores.values()),'protocol_failures':sum(s['adjudication_kind']=='protocol_failure' for s in scores.values()),'human_acceptance_pending':True,'judge_failures':len(failures),'judging_terminal':len(scores)+len(failures)})
        print(json.dumps({'scored':len(scores),'planned':len(ordered)}),flush=True)
    env=dict(os.environ);env['PATH']=str(run/'pinned-cli')+os.pathsep+env.get('PATH','')
    subprocess.run([sys.executable,str(Path(__file__).with_name('report_agent_run.py')),str(bundle),'--run',str(run),'--scores',str(out/'scores.json'),'--quality-policy',str(policy_path)],check=True,env=env)
    write_atomic(out/'complete.json',{'scored':len(scores),'judge_failures':len(failures),'all_attempts_scored':len(scores)==len(ordered),'report':str(run/'comparison-report.json'),'human_completion_accepted':False,'frozen_evaluation':False})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('bundle',type=Path);p.add_argument('--run',type=Path,required=True);p.add_argument('--policy',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();evaluate(args.bundle.resolve(),args.run.resolve(),args.policy.resolve(),args.out.resolve())
