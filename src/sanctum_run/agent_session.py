"""Headless agent process, fresh isolation and durable attempt state.

This module does not select task answers or agent search steps. Its local MCP
listener holds the trusted gateway; the CLI's relay gets no corpus or token.
"""
from __future__ import annotations

import asyncio
import fcntl
import hashlib
import json
import math
import os
import signal
import sys
import tempfile
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

class AttemptAlreadyDispatched(RuntimeError):
    pass


def write_atomic(path: Path, value):
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
    os.replace(temporary,path)


class AttemptLedger:
    """One atomic row per frozen schedule item; unknown attempts never replay."""
    def __init__(self,path:Path):
        self.path=path
        path.parent.mkdir(parents=True,exist_ok=True)

    def update(self,attempt_id,state,**fields):
        with self.path.with_suffix('.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            rows=json.loads(self.path.read_text()) if self.path.exists() else {}
            old=rows.get(attempt_id)
            if state=='dispatched' and old is not None:
                raise AttemptAlreadyDispatched('attempt already dispatched; reconcile before replacing')
            if state!='dispatched' and (old is None or old['state']!='dispatched'):
                raise ValueError('terminal transition requires one live dispatch')
            rows[attempt_id]={**(old or {}),**fields,'state':state,'updated_at':time.time()}
            write_atomic(self.path,rows)


class NativeEvents:
    """Count complete assistant message IDs, not text chunks or tool results."""
    def __init__(self,max_rounds,allowed_tools):
        self.max_rounds=max_rounds
        self.allowed=set(allowed_tools)
        self.assistant_ids=set()
        self.inventory=None
        self.result=None
        self.violation=None

    def observe(self,event):
        kind=event.get('type')
        if kind=='system' and event.get('subtype')=='init':
            self.inventory=event.get('tools')
            if not isinstance(self.inventory,list) or set(self.inventory)!=self.allowed:
                self.violation='tool_inventory_mismatch'
        elif kind=='assistant':
            message=event.get('message',{})
            mid=message.get('id')
            if not isinstance(mid,str) or not mid:
                self.violation='unaccountable_agent_round'
            else:
                self.assistant_ids.add(mid)
                if len(self.assistant_ids)>self.max_rounds:
                    self.violation='agent_round_budget_exceeded'
        elif kind=='result':
            self.result=event


class SocketLines:
    def __init__(self,reader,writer):
        self.reader,self.writer=reader,writer
    def __aiter__(self):
        return self
    async def __anext__(self):
        line=await self.reader.readline()
        if not line:
            raise StopAsyncIteration
        return line.decode()
    async def write(self,text):
        self.writer.write(text.encode())
    async def flush(self):
        await self.writer.drain()


@asynccontextmanager
async def local_mcp(adapter,path):
    from mcp.server.stdio import stdio_server
    connections=set()
    used=False
    async def connected(reader,writer):
        nonlocal used
        # One native relay connection per fresh attempt; a second is refused.
        if used:
            writer.close();await writer.wait_closed();return
        used=True
        current=asyncio.current_task();connections.add(current)
        try:
            lines=SocketLines(reader,writer)
            async with stdio_server(stdin=lines,stdout=lines) as streams:
                await adapter.server.run(*streams,adapter.server.create_initialization_options())
        finally:
            connections.discard(current)
            writer.close()
            await writer.wait_closed()
    server=await asyncio.start_unix_server(connected,str(path))
    os.chmod(path,0o600)
    try:
        yield
    finally:
        server.close();await server.wait_closed()
        await adapter.close()
        for task in tuple(connections):
            task.cancel()
        await asyncio.gather(*tuple(connections),return_exceptions=True)


def isolated_environment(home:Path,credentials:dict):
    allowed={'PATH','LANG','SSL_CERT_FILE','SSL_CERT_DIR','TIKTOKEN_CACHE_DIR'}
    environment={k:v for k,v in os.environ.items() if k in allowed}
    environment.update(HOME=str(home),CLAUDE_CONFIG_DIR=str(home/'claude-config'),TMPDIR=str(home/'tmp'),
                       CLAUDE_CODE_DISABLE_AUTO_MEMORY='1',CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC='1',DISABLE_AUTOUPDATER='1')
    # API auth uses --bare. Subscription auth is explicitly passed to the non-bare
    # launcher; inherited keychain/profile credentials are never copied into HOME.
    if set(credentials)-{'ANTHROPIC_API_KEY','ANTHROPIC_BASE_URL','CLAUDE_CODE_OAUTH_TOKEN'}:
        raise ValueError('unsupported explicit auth environment')
    if any(not isinstance(v,str) or not v for v in credentials.values()):
        raise ValueError('invalid explicit auth environment')
    if credentials.get('CLAUDE_CODE_OAUTH_TOKEN') and any(k.startswith('ANTHROPIC_') for k in credentials):
        raise ValueError('subscription authentication cannot be mixed with API credentials')
    environment.update(credentials)
    return environment


def claude_command(cli,model,effort,session_id,config,max_rounds,max_spend,*,allowed_tools=(),authentication_mode='api'):
    if not model or effort not in ('low','medium','high','xhigh','max') or max_spend<=0:
        raise ValueError('model, effort and approved positive cap required')
    if authentication_mode not in ('api','subscription'):
        raise ValueError('unsupported Claude authentication mode')
    command = [cli,'--print','--verbose','--output-format','stream-json','--bare','--restricted',
        '--disable-slash-commands','--setting-sources','','--strict-mcp-config','--mcp-config',str(config),
        '--tools','','--permission-mode','dontAsk','--permission-prompts','none','--no-chrome',
        '--no-session-persistence','--session-id',session_id,'--model',model,'--effort',effort,
        '--max-turns',str(max_rounds),'--max-budget-usd',str(max_spend)]
    if authentication_mode=='subscription':
        command.remove('--bare')
        command += ['--settings', '{"disableAllHooks":true}']
    if allowed_tools:
        if any(not name.startswith('mcp__evidence__') or ',' in name for name in allowed_tools):
            raise ValueError('only explicit evidence MCP tools may be allowed')
        command += ['--allowedTools', ','.join(allowed_tools)]
    return command


async def stop_process_group(process,grace=1.0):
    """Kill owned descendants even when their parent exited before cleanup."""
    try:
        os.killpg(process.pid,signal.SIGTERM)
    except ProcessLookupError:
        return True
    end=time.monotonic()+grace
    while time.monotonic()<end:
        try:
            os.killpg(process.pid,0)
        except ProcessLookupError:
            await process.wait();return True
        await asyncio.sleep(0.02)
    try:
        os.killpg(process.pid,signal.SIGKILL)
    except ProcessLookupError:
        pass
    await process.wait()
    # A descendant zombie may await OS reaping; group disappearance is checked
    # separately rather than misreported as confirmed termination.
    try:
        os.killpg(process.pid,0)
    except ProcessLookupError:
        return True
    return False


def nested_usage_cost(calls, model_prices):
    """List-price estimate only; retries/missing usage stay unknown."""
    total=0.0
    for call in calls:
        # An explicit broker refusal before any HTTP request has zero provider usage.
        if (type(call.get('calls')) is int and call['calls']==0 and
                call.get('outcome')=='unavailable' and call.get('reason')=='over_budget' and
                call.get('usage') is None and call.get('elapsed_ms')==0):
            continue
        rates=(model_prices or {}).get(call.get('model'), {})
        usage=call.get('usage') or {}
        if call.get('outcome')!='ok' or call.get('calls')!=1:
            return None
        for key in ('input_tokens','output_tokens'):
            if type(usage.get(key)) is not int or usage[key]<0:
                return None
        for key in ('input_usd_per_million','output_usd_per_million'):
            rate=rates.get(key)
            if type(rate) not in (int,float) or not math.isfinite(rate) or rate<0:
                return None
        total+=(usage['input_tokens']*rates['input_usd_per_million']+
                usage['output_tokens']*rates['output_usd_per_million'])/1_000_000
    return total


async def run_session(adapter,*,attempt_id,ledger:AttemptLedger,out:Path,prompt:str,
                      cli='claude',model=None,effort='low',deadline_seconds=120,max_rounds=8,
                      approved_spend_usd=0,credentials=None,fixture_command=None,
                      spend_ledger=None,max_exposure_usd=None,exposure_verified=False,model_prices=None):
    authentication_mode='subscription' if (credentials or {}).get('CLAUDE_CODE_OAUTH_TOKEN') else 'api'
    controller_started=time.monotonic()
    if deadline_seconds<=0 or max_rounds<=0:
        raise ValueError('positive session bounds required')
    if out.exists() and any(out.iterdir()):
        raise ValueError('attempt output directory is not empty')
    isolated_environment(Path('/unused-validation-path'),credentials or {})
    if fixture_command is None and approved_spend_usd<=0:
        raise ValueError('paid Claude dispatch budget is not approved')
    if fixture_command is not None and approved_spend_usd:
        raise ValueError('fixture execution cannot carry paid authorization')
    if fixture_command is None:
        # Validate settings before reserving money or recording a dispatch.
        claude_command(cli,model,effort,'unused',Path('/unused'),max_rounds,approved_spend_usd,authentication_mode=authentication_mode)
        if spend_ledger is None or not exposure_verified or max_exposure_usd is None:
            raise ValueError('verified provider/agent/nested exposure and spend reservation required')
        if max_exposure_usd<approved_spend_usd:
            raise ValueError('reservation cannot be below the agent API ceiling')
        spend_ledger.reserve(attempt_id,max_exposure_usd)
    out.mkdir(parents=True,exist_ok=True)
    session_id=str(uuid.uuid4())
    prompt_hash=hashlib.sha256(prompt.encode()).hexdigest()
    ledger.update(attempt_id,'dispatched',session_id=session_id,prompt_sha256=prompt_hash,
                  model=model,effort=effort,fixture=fixture_command is not None)
    process=None
    monitor=NativeEvents(max_rounds,['mcp__evidence__'+t for t in adapter.inventory])
    status='launch_failure';events=[];cleanup=False
    with tempfile.TemporaryDirectory(prefix='sanctum-agent-',dir='/tmp') as temp:
        root=Path(temp);workspace=root/'workspace';home=root/'home'
        workspace.mkdir();home.mkdir();(home/'tmp').mkdir();(home/'claude-config').mkdir()
        socket=root/'evidence.sock';config=root/'mcp.json'
        bridge=Path(__file__).with_name('agent_bridge.py')
        config.write_text(json.dumps({'mcpServers':{'evidence':{'command':sys.executable,
            'args':[str(bridge),'--socket',str(socket)]}}}))
        command=fixture_command or claude_command(cli,model,effort,session_id,config,max_rounds,approved_spend_usd,
            allowed_tools=['mcp__evidence__'+tool for tool in adapter.inventory],authentication_mode=authentication_mode)
        if fixture_command:
            command=[arg.replace('{mcp_config}',str(config)).replace('{session_id}',session_id) for arg in command]
        environment=isolated_environment(home,credentials or {})
        try:
            async with local_mcp(adapter,socket):
                process=await asyncio.create_subprocess_exec(*command,cwd=workspace,env=environment,
                    stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE,
                    start_new_session=True,limit=1024*1024)
                process.stdin.write(prompt.encode());await process.stdin.drain();process.stdin.close()
                async def stderr_reader():
                    # Preserve bounded stderr privately with credentials redacted.
                    chunks=[];kept=0
                    while chunk:=await process.stderr.read(65536):
                        if kept<1024*1024:
                            chunks.append(chunk[:1024*1024-kept]);kept+=len(chunks[-1])
                    text=b''.join(chunks).decode(errors='replace')
                    for value in (credentials or {}).values():
                        if value:
                            text=text.replace(value,'[REDACTED]')
                    (out/'stderr.txt').write_text(text)
                stderr_task=asyncio.create_task(stderr_reader())
                try:
                    async with asyncio.timeout(deadline_seconds):
                        with (out/'events.jsonl').open('w') as stream:
                            while line:=await process.stdout.readline():
                                text=line.decode(errors='replace')
                                for value in (credentials or {}).values():
                                    if value:
                                        text=text.replace(value,'[REDACTED]')
                                try:
                                    event=json.loads(text)
                                    if not isinstance(event,dict):
                                        raise ValueError()
                                except ValueError:
                                    status='protocol_violation';break
                                stream.write(json.dumps(event)+'\n');stream.flush()
                                events.append(event);monitor.observe(event)
                                if monitor.violation:
                                    status='protocol_violation';break
                            else:
                                await process.wait()
                                status='completed' if process.returncode==0 and monitor.result else 'infrastructure_failure'
                                if monitor.result and monitor.result.get('subtype') == 'error_max_turns':
                                    status='agent_round_budget_exhausted'
                                elif monitor.result and monitor.result.get('is_error'):
                                    status='agent_failure'
                except TimeoutError:
                    status='deadline_exceeded'
                finally:
                    cleanup=await stop_process_group(process)
                    await stderr_task
                if monitor.inventory is None:
                    status='protocol_violation' if status=='completed' else status
                if status=='completed' and not adapter.calls:
                    status='protocol_violation'
        except asyncio.CancelledError:
            status='cancelled'
            raise
        except Exception:
            status='infrastructure_failure' if process else 'launch_failure'
        finally:
            if process and process.returncode is None:
                cleanup=await stop_process_group(process)
            result=dict(attempt_id=attempt_id,session_id=session_id,status=status,
                controller_elapsed_ms=int((time.monotonic()-controller_started)*1000),
                prompt_sha256=prompt_hash,model=model,effort=effort,fixture=fixture_command is not None,
                authentication_mode=authentication_mode,agent_rounds=len(monitor.assistant_ids),effective_tools=monitor.inventory,
                protocol_issue=monitor.violation,process_group_termination_verified=cleanup,
                native_result=monitor.result,usage=(monitor.result or {}).get('usage'),
                cost_usd=(monitor.result or {}).get('total_cost_usd'),
                mcp_calls=sorted(adapter.calls,key=lambda c:c['sequence']),delivered_evidence=adapter.budget.records)
            nested=[call for c in adapter.calls for call in c['backend_trace'].get('model_calls',[])]
            # Broker receipts currently expose usage but no dollar amount. Never
            # reconcile a combined agent+System One reservation using agent cost alone.
            result['agent_cost_usd']=result['cost_usd']
            result['agent_cost_basis']='subscription SDK estimate, not incremental invoice' if authentication_mode=='subscription' else 'API SDK estimate'
            result['nested_model_calls']=nested
            if nested:
                nested_cost=nested_usage_cost(nested,model_prices)
                result['nested_cost_usd']=nested_cost
                result['cost_usd']=None if nested_cost is None or result['agent_cost_usd'] is None else result['agent_cost_usd']+nested_cost
                result['combined_cost_basis']='agent SDK plus nested rate-card estimate; not an invoice'
                if result['cost_usd'] is None:
                    result['cost_reconciliation_pending']='nested provider pricing/usage reconciliation required'
            if not cleanup and process:
                result['status']='infrastructure_failure'
                result['cleanup_issue']='process_group_termination_unverified'
            write_atomic(out/'result.json',result)
            ledger.update(attempt_id,result['status'],result_path=str(out/'result.json'),
                          cost_usd=result['cost_usd'],termination_verified=cleanup)
            if fixture_command is None:
                spend_ledger.reconcile(attempt_id,result['cost_usd'])
    return result
