"""Execute the frozen development schedule once, preserving every terminal outcome."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from sanctum_run.agent_schedule import plan_schedule
from sanctum_run.agent_session import write_atomic


def campaign(bundle, out):
    schedule=plan_schedule(bundle,out)
    ledger_path=out/'attempts.json'
    started=time.time()
    stop_reason=None
    for item in schedule['attempts']:
        ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else {}
        if item['attempt_id'] in ledger:
            if ledger[item['attempt_id']]['state']=='dispatched':
                stop_reason='unknown live dispatch requires reconciliation';break
            continue
        log=out/'dispatch-logs';log.mkdir(exist_ok=True)
        command=[sys.executable,str(Path(__file__).with_name('run_agent_attempt.py')),str(bundle),
            '--out',str(out),'--task-id',item['task_id'],'--arm',item['arm'],'--repetition',str(item['repetition'])]
        with (log/(item['attempt_id']+'.log')).open('w') as stream:
            completed=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
        if completed.returncode:
            stop_reason='dispatch process failed; inspect '+str(log/(item['attempt_id']+'.log'));break
        result_path=out/'attempts'/item['attempt_id']/'result.json'
        result=json.loads(result_path.read_text())
        raw=(result.get('native_result') or {}).get('result','')
        if isinstance(raw,str):
            text=raw.strip()
            if text.startswith('```json') and text.endswith('```'):text=text[7:-3].strip()
            try:
                answer=json.loads(text)
                if isinstance(answer,dict):write_atomic(result_path.parent/'structured-answer.json',answer)
            except ValueError:pass
        ledger=json.loads(ledger_path.read_text())
        counts=dict(Counter(row['state'] for row in ledger.values()))
        progress=dict(planned=len(schedule['attempts']),terminal=len(ledger),outcomes=counts,
            elapsed_seconds=round(time.time()-started),last_attempt=item,latest_status=result['status'],
            quality_scoring_pending=True,frozen_evaluation=False)
        write_atomic(out/'campaign-progress.json',progress)
        print(json.dumps(progress),flush=True)
        error_text=json.dumps(result.get('native_result') or {}).lower()
        if result.get('cost_reconciliation_pending'):
            stop_reason='unknown usage reconciliation required';break
        if any(term in error_text for term in ('rate_limit_error','usage limit','not logged in','authentication_error')):
            stop_reason='provider authentication/usage limit; preserve failure and stop dispatch';break
    ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else {}
    result=dict(planned=len(schedule['attempts']),terminal=len(ledger),
        all_terminal=len(ledger)==len(schedule['attempts']) and all(v['state']!='dispatched' for v in ledger.values()),
        outcomes=dict(Counter(v['state'] for v in ledger.values())),stop_reason=stop_reason,
        elapsed_seconds=round(time.time()-started),schedule_sha256=hashlib.sha256((out/'schedule.json').read_bytes()).hexdigest(),
        quality_scoring_pending=True,frozen_evaluation=False)
    write_atomic(out/'campaign-result.json',result);print(json.dumps(result),flush=True)
    if not result['all_terminal']:raise SystemExit(1)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle',type=Path);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();campaign(args.bundle.resolve(),args.out.resolve())
