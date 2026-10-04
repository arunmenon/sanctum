"""Executable bundle contracts, beyond offline matrix/linkage validation."""
import hashlib
import json
import math
import shutil
from pathlib import Path

from sanctum_run.bundle import _file, _records


def text(value):
    return isinstance(value, str) and bool(value.strip())


def validate_contract(root: Path, config: dict):
    if not text(config.get('experiment_id')):
        raise ValueError('experiment identifier required')
    agent = config.get('agent', {})
    if agent.get('adapter') != 'claude_code':
        raise ValueError('only the Claude Code adapter is implemented')
    if agent.get('model') is not None and not text(agent['model']):
        raise ValueError('invalid agent model identifier')
    if agent.get('effort') not in (None, 'low', 'medium', 'high', 'xhigh', 'max'):
        raise ValueError('invalid agent effort')
    _file(root, config['instructions'])
    caller = config['caller']
    identity_file = _file(root, caller['principal_file'])
    if (not text(caller.get('principal')) or
            hashlib.sha256(identity_file.read_bytes()).hexdigest() != caller.get('expected_sha256')):
        raise ValueError('caller identity snapshot mismatch')
    identities = json.loads(identity_file.read_text())
    if (not isinstance(identities, list) or
            any(not isinstance(p, dict) or not text(p.get('principal')) or not isinstance(p.get('groups'), list)
                or any(not text(g) for g in p['groups']) for p in identities) or
            len({p['principal'] for p in identities}) != len(identities) or
            caller['principal'] not in {p['principal'] for p in identities}):
        raise ValueError('invalid caller principal registry')
    spend = config['limits'].get('total_inference_spend_usd')
    if type(spend) not in (float, int) or not math.isfinite(spend) or spend < 0:
        raise ValueError('finite nonnegative inference ceiling required')
    if 'agent_tool_calls' in config['limits'] and (type(config['limits']['agent_tool_calls']) is not int
                                                  or config['limits']['agent_tool_calls'] <= 0):
        raise ValueError('positive tool-call ceiling required')
    readiness = config.get('readiness', {})
    if not isinstance(readiness, dict) or any(type(value) is not bool for value in readiness.values()):
        raise ValueError('readiness fields must be explicit booleans')
    if readiness.get('frozen') and not readiness.get('independent_acceptance'):
        raise ValueError('evaluation freeze requires independent acceptance')
    if readiness.get('paid_budget_approved'):
        if spend <= 0 or not text(agent.get('model')) or agent.get('effort') is None:
            raise ValueError('paid dispatch needs explicit model, effort and positive ceiling')
        if readiness.get('agent_isolation_verified') is not True:
            raise ValueError('paid dispatch requires installed-agent isolation evidence')
        _file(root, config['spend']['ledger'])
        verification=agent.get('verification',{})
        reports=[]
        for kind in ('isolation','round_limit'):
            pin=verification.get(kind,{})
            if not text(pin.get('file')):
                raise ValueError('paid dispatch requires pinned installed-agent proof')
            proof=_file(root,pin['file'])
            if hashlib.sha256(proof.read_bytes()).hexdigest()!=pin.get('expected_sha256'):
                raise ValueError('installed-agent proof hash mismatch')
            record=json.loads(proof.read_text())
            if record.get('passed') is not True or config['agent']['model'] not in record.get('requested_models',[]):
                raise ValueError('installed-agent proof model/result mismatch')
            if record.get('authentication_mode','api')!=agent.get('authentication_mode','api'):
                raise ValueError('installed-agent proof authentication mode mismatch')
            reports.append(record)
        executable=shutil.which('claude')
        if not executable or any(r.get('cli_sha256')!=hashlib.sha256(Path(executable).read_bytes()).hexdigest() for r in reports):
            raise ValueError('installed Claude executable changed since isolation proof')
    for arm in config['arms'].values():
        if 'runtime_ready' in arm and type(arm['runtime_ready']) is not bool:
            raise ValueError('runtime readiness must be boolean')
        if arm.get('runtime_ready'):
            runtime_file = _file(root, arm['runtime_file'])
            if hashlib.sha256(runtime_file.read_bytes()).hexdigest() != arm.get('runtime_sha256'):
                raise ValueError('runtime hash mismatch')
    manifest = _file(root, config['corpus']['manifest'])
    rows = {}
    for path in sorted((manifest.parent/'hubs').glob('*/artifacts.jsonl')):
        for line in path.read_text().splitlines():
            row = json.loads(line)
            key = (path.parent.name, row['artifact_id'], row['version'])
            if key in rows or not isinstance(row.get('text'), str):
                raise ValueError('duplicate or malformed corpus record')
            rows[key] = row
    if not rows:
        raise ValueError('executable bundle requires corpus records')
    tasks, gold = _records(_file(root, config['tasks'])), _records(_file(root, config['gold']))
    for task_id, task in tasks.items():
        if (task.get('answer_format') != 'evidence_answer_v1' or
                not isinstance(task.get('caller_requirements'), list) or
                any(not text(v) for v in task['caller_requirements'])):
            raise ValueError('invalid public task contract')
        record = gold[task_id]
        if record['matrix'].get('scope') not in ('in_scope', 'partial', 'out_of_scope'):
            raise ValueError('executable task requires explicit scope')
        dimensions = set()
        if not isinstance(record.get('plan_checklist'), list):
            raise ValueError('task planning checklist required')
        for item in record['plan_checklist']:
            if (not isinstance(item, dict) or not text(item.get('dimension')) or item['dimension'] in dimensions
                    or not isinstance(item.get('mandatory_items'), list) or not item['mandatory_items']
                    or any(not text(v) for v in item['mandatory_items'])):
                raise ValueError('invalid or repeated planning dimension')
            dimensions.add(item['dimension'])
        for fact in record['required_facts']:
            if not text(fact.get('statement')) or fact.get('support_kind') not in ('evidence', 'boundary'):
                raise ValueError('required fact needs statement and support kind')
            if not isinstance(fact.get('evidence'), list):
                raise ValueError('fact evidence list required')
            if fact['support_kind'] == 'evidence' and not fact['evidence']:
                raise ValueError('positive fact needs pinned evidence')
            for ref in fact['evidence']:
                if not isinstance(ref, dict): raise ValueError('invalid gold reference')
                row = rows.get((ref.get('source_id'), ref.get('artifact_id'), ref.get('version')))
                quote = ref.get('quote')
                if row is None or not text(quote) or quote not in row['text']:
                    raise ValueError('gold reference not in pinned corpus')
                if 'start' in ref or 'end' in ref:
                    start, end = ref.get('start'), ref.get('end')
                    if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(row['text'])
                            or row['text'][start:end] != quote):
                        raise ValueError('gold reference span mismatch')
                elif row['text'].count(quote) != 1:
                    raise ValueError('ambiguous gold quote requires a span')
                if 'content_sha256' in ref and ref['content_sha256'] != hashlib.sha256(row['text'].encode()).hexdigest():
                    raise ValueError('gold reference content hash mismatch')
            if fact['support_kind'] == 'boundary':
                boundary = fact.get('boundary_record')
                if (not isinstance(boundary, dict) or boundary.get('task_id') != task_id
                        or boundary.get('fact_id') != fact['fact_id'] or not text(boundary.get('rationale'))
                        or boundary.get('corpus_manifest_sha256') != config['corpus']['expected_sha256']
                        or boundary.get('searched_artifact_count') != len(rows)):
                    raise ValueError('boundary obligation lacks a pinned corpus check')
