"""Run one frozen attempt; --fixture uses no inference and cannot establish quality."""
import argparse
import asyncio
import json
import os
import subprocess
import yaml
from pathlib import Path

from sanctum_run.agent_runner import run_attempt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle',type=Path);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--task-id',required=True);parser.add_argument('--arm',required=True)
    parser.add_argument('--repetition',type=int,default=0);parser.add_argument('--fixture',action='store_true')
    args=parser.parse_args()
    credentials={}
    config=yaml.safe_load(args.bundle.read_text())
    if not args.fixture and config.get('agent',{}).get('authentication_mode')=='subscription':
        # Read the existing first-party login solely to pass auth to Claude Code.
        cached=Path.home()/'.claude/.credentials.json'
        raw=cached.read_text() if cached.exists() else subprocess.run(
            ['security','find-generic-password','-s','Claude Code-credentials','-w'],capture_output=True,text=True,check=True).stdout
        token=json.loads(raw).get('claudeAiOauth',{}).get('accessToken')
        if not token: raise ValueError('Claude subscription login missing')
        credentials['CLAUDE_CODE_OAUTH_TOKEN']=token
    elif not args.fixture and os.environ.get('ANTHROPIC_API_KEY'):
        credentials['ANTHROPIC_API_KEY']=os.environ['ANTHROPIC_API_KEY']
    result=asyncio.run(run_attempt(args.bundle,args.out,task_id=args.task_id,arm=args.arm,
        repetition=args.repetition,fixture=args.fixture,credentials=credentials))
    print(json.dumps(dict(attempt_id=result['attempt_id'],status=result['status'],fixture=result['fixture'],
                         task_complete=False,result=str(args.out/'attempts'/result['attempt_id']/'result.json'))))


if __name__=='__main__':main()
