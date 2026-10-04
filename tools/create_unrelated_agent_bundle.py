"""Create a tiny shipping ecosystem fixture for runner-independence checks."""
import argparse
import hashlib
import json
from pathlib import Path

import yaml

ROOT=Path(__file__).resolve().parents[1]


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();root=args.out
    text='def can_dispatch(payment_status):\n    return payment_status == "paid"\n'
    row=dict(artifact_id='shipping-dispatch-v1',version='v1',environment=None,kind='code',
        location='repo:shipping/dispatch',path='src/dispatch.py',title='Shipping dispatch eligibility',text=text,
        acl=['shipping-engineering'],metadata={})
    file=root/'corpus/hubs/codehub/artifacts.jsonl';file.parent.mkdir(parents=True,exist_ok=True)
    file.write_text(json.dumps(row)+'\n')
    # Reuse the source-type contract, never PDLC content or expected answers.
    caps=ROOT/'build/pdlc-pilot/hubs/codehub/capabilities.json'
    contract=json.loads(caps.read_text());contract['place_version_reads']={'repo:shipping/dispatch':True}
    write(file.parent/'capabilities.json',contract)
    files={str(p.relative_to(root/'corpus')):hashlib.sha256(p.read_bytes()).hexdigest() for p in file.parent.iterdir()}
    write(root/'corpus/manifest.json',dict(synthetic=True,total_artifacts=1,files=files,status='fixture'))
    write(root/'connections/principals.json',[dict(principal='shipping-reader',groups=['shipping-engineering'])])
    task=dict(task_id='shipping-eligibility',family='behavior',prompt='Explain when the versioned shipping dispatch helper permits dispatch.',
              caller_requirements=[],answer_format='evidence_answer_v1')
    gold=dict(task_id=task['task_id'],required_facts=[dict(fact_id='shipping.paid',statement='Only paid status permits dispatch.',support_kind='evidence',
        evidence=[dict(source_id='codehub',artifact_id=row['artifact_id'],version='v1',quote=text)])],plan_checklist=[],
        matrix=dict(domains=['shipping'],sources=['codehub'],difficulty='simple',scope='in_scope',answerability='complete'))
    for name,value in [('public/tasks.jsonl',task),('private/gold.jsonl',gold)]:
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value)+'\n')
    (root/'public/instructions.txt').write_text('Use authorized MCP evidence; return the evidence_answer_v1 JSON envelope. State supported facts, uncertainty and unmet requirements.\n')
    config=dict(schema_version=1,experiment_id='shipping-independence-fixture',mode='evidence_only',
        corpus=dict(manifest='corpus/manifest.json',expected_sha256=hashlib.sha256((root/'corpus/manifest.json').read_bytes()).hexdigest()),
        caller=dict(principal='shipping-reader',principal_file='connections/principals.json',
            expected_sha256=hashlib.sha256((root/'connections/principals.json').read_bytes()).hexdigest()),
        tasks='public/tasks.jsonl',gold='private/gold.jsonl',instructions='public/instructions.txt',
        agent=dict(adapter='claude_code',model=None,effort=None),workspace=dict(kind='empty'),
        arms=dict(direct=dict(tool_surface='direct_hubs')),
        limits=dict(agent_rounds=8,cumulative_evidence_tokens=8000,tool_response_evidence_tokens=4000,task_deadline_seconds=120,total_inference_spend_usd=0),
        execution=dict(repetitions=1,random_seed=42,fresh_session_per_attempt=True),
        diversity=dict(family_counts={'behavior':1},scope_counts={'in_scope':1},required_domains=['shipping'],required_sources=['codehub'],reject_duplicate_fact_sets=True),
        readiness=dict(paid_budget_approved=False,frozen=False))
    (root/'experiment.yaml').write_text(yaml.safe_dump(config,sort_keys=False))
    print(json.dumps(dict(bundle=str(root/'experiment.yaml'),domain='shipping',paid_inference=False)))


if __name__=='__main__':main()
