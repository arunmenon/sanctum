"""Await the dispatched campaign, judge saved answers and compare historical cohorts.

Never dispatches or reruns an agent. Incomplete semantic judgments remain unknown.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from sanctum_run.agent_schedule import compare_scope_strata
from sanctum_run.agent_session import write_atomic
from tools.report_agent_run import report

ROOT=Path(__file__).resolve().parents[1]


def recommendations(run):
    counts=Counter()
    for p in (run/'attempts').glob('*/result.json'):
        result=json.loads(p.read_text())
        if result['arm']!='sanctum':continue
        for call in result['mcp_calls']:
            actual={c['source_id'] for c in call.get('backend_trace',{}).get('calls',[])}
            counts['hub_calls']+=len(call.get('backend_trace',{}).get('calls',[]))
            for d in call.get('router_receipt',{}).get('decisions',[]):
                v=d.get('value') or {}
                if not v.get('source'):continue
                counts['d2_decisions']+=1
                counts['shadow' if v.get('shadow') else 'active']+=1
                if v.get('call') is False:
                    counts['skip_recommendations']+=1
                    counts['skip_with_no_observed_hub_call' if v['source'] not in actual else 'guarded_or_other_call']+=1
    return dict(counts)


def finish(bundle,run,old_bundle,old_run,policy):
    deadline=time.monotonic()+7200
    while not (run/'campaign-result.json').exists():
        if time.monotonic()>deadline:raise SystemExit('Campaign wait timeout; no agent rerun or scoring dispatched')
        time.sleep(10)
    terminal=json.loads((run/'campaign-result.json').read_text())
    if not terminal['all_terminal']:raise SystemExit('Native campaign stopped; reconcile original dispatch records')
    quality=run/'quality-evaluation-01';quality.mkdir(exist_ok=False)
    # Unchanged judge fixture packets can reuse saved calibration judgments.
    old_quality=old_run/'quality-evaluation-07'
    shutil.copytree(old_quality/'cases',quality/'cases');shutil.copy2(old_quality/'calibration.json',quality/'calibration.json')
    shutil.copy2(policy,quality/'evaluation-policy.json')
    write_atomic(quality/'calibration-reuse.json',{'from':str(old_quality),'same_model':'claude-sonnet-5-5','same_operational_rubric':True,'agent_attempts_rerun':False})
    subprocess.run([sys.executable,str(ROOT/'tools/run_quality_evaluation.py'),str(bundle),'--run',str(run),'--policy',str(quality/'evaluation-policy.json'),'--out',str(quality)],check=True)
    # Both reports independently revalidate score derivations before the join.
    old_scores=old_quality/'scores.json';new_scores=quality/'scores.json'
    old_report=report(old_bundle,old_run,old_scores,policy);new_report=report(bundle,run,new_scores,quality/'evaluation-policy.json')
    if old_report['score_binding_issues'] or new_report['score_binding_issues']:raise SystemExit('Invalid score bindings; comparison not published')
    attempts=[];ledger={};scores={};scopes={}
    for label,folder,score_path in [('shadow',old_run,old_scores),('active',run,new_scores)]:
        schedule=json.loads((folder/'schedule.json').read_text());original_ledger=json.loads((folder/'attempts.json').read_text());graded=json.loads(score_path.read_text())
        for item in schedule['attempts']:
            if item['arm']!='sanctum':continue
            ident=item['attempt_id'];attempts.append({**item,'arm':label});ledger[ident]=original_ledger[ident]
            if ident in graded:scores[ident]=graded[ident]
    for line in (bundle.parent/'private/gold.jsonl').read_text().splitlines():
        g=json.loads(line);scopes[g['task_id']]=g['matrix']['scope']
    schedule={'attempts':attempts,'repetitions':3,'task_count':30}
    comparison=compare_scope_strata(schedule,ledger,scores,scopes,arms=['shadow','active'],seed=42)
    comparison.update(recommendations={'shadow':recommendations(old_run),'active':recommendations(run)},cohort_design='Historical shadow cohort vs fresh active cohort; timing/order confounded development ablation, not causal proof.',input_constraints='Same corpus/task/gold/instructions/agent model/effort/limits/memory/descriptors/template; active calibration is the intended runtime change.',human_and_independent_gold_acceptance_pending=True,source_reports={'shadow':str(old_run/'comparison-report.json'),'active':str(run/'comparison-report.json')})
    write_atomic(run/'active-vs-shadow-report.json',comparison)
    write_atomic(run/'ablation-complete.json',{'native_attempts':90,'quality_report':str(run/'active-vs-shadow-report.json'),'primary_comparison_ready':comparison['primary_comparison_ready'],'human_acceptance':False})
    print(json.dumps({'ablation_report':str(run/'active-vs-shadow-report.json'),'primary_comparison_ready':comparison['primary_comparison_ready']}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('bundle',type=Path);p.add_argument('--run',type=Path,required=True);p.add_argument('--old-bundle',type=Path,required=True);p.add_argument('--old-run',type=Path,required=True);p.add_argument('--policy',type=Path,required=True);a=p.parse_args();finish(a.bundle.resolve(),a.run.resolve(),a.old_bundle.resolve(),a.old_run.resolve(),a.policy.resolve())
