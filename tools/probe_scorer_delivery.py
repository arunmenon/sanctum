"""Verify scorer CLI on an actual delivered shipping passage, without inference."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')


def probe(connection_proof, out, arm="sanctum"):
    report = json.loads((connection_proof/'probe-report.json').read_text())
    attempt = next(a['result'] for a in report['attempts'] if a['bundle']=='shipping' and a['arm']==arm)
    unit = next(u for d in attempt['delivered_evidence'] for u in d['evidence'] if u.get('citable'))
    out.mkdir(parents=True)
    write(out/'attempt.json', attempt)
    answer = dict(schema_version=1, answer='Dispatch is permitted only when payment status equals paid.',
        claims=[dict(claim_id='dispatch', text='Only paid status permits dispatch.', citations=[{
            k:unit[k] for k in ('source_id','artifact_id','version','start','end','evidence_id')}])],
        uncertainties=[], unmet_requirements=[])
    review = dict(adjudicator='hand-authored-delivery-fixture', model='no-inference-fixture', version='1',
        full_prose_reviewed=True, facts=[dict(fact_id='shipping.paid', met=True, claim_ids=['dispatch'],
            reason='The delivered helper returns payment_status == paid.')],
        claims=[dict(claim_id='dispatch',claim_type='factual',supported=True,severity='none',
            citation_support=[True],reason='Exact helper behavior.')], additional_claims=[], contradictions=[],
        plan=[], uncertainties_met=True, caller_requirements_met=True)
    write(out/'answer.json',answer); write(out/'review.json',review)
    command=[sys.executable,str(ROOT/'tools/score_agent_answer.py'),
        str(connection_proof/'bundles/shipping/experiment.yaml'),'--task-id','shipping-eligibility',
        '--attempt',str(out/'attempt.json'),'--answer',str(out/'answer.json')]
    subprocess.run([*command,'--judge-packet','--out',str(out/'packet.json')],check=True)
    review['packet_sha256']=json.loads((out/'packet.json').read_text())['packet_sha256']
    write(out/'review.json',review)
    subprocess.run([*command,'--review',str(out/'review.json'),'--out',str(out/'positive.json')],check=True)
    changed=copy.deepcopy(answer); changed['claims'][0]['citations'][0]['version']='nonexistent'
    write(out/'answer.json',changed)
    subprocess.run([*command,'--judge-packet','--out',str(out/'wrong-version-packet.json')],check=True)
    negative_review={**review,'packet_sha256':json.loads((out/'wrong-version-packet.json').read_text())['packet_sha256']}
    write(out/'review.json',negative_review)
    subprocess.run([*command,'--review',str(out/'review.json'),'--out',str(out/'wrong-version.json')],check=True)
    write(out/'answer.json',answer)
    write(out/'review.json',review)
    positive=json.loads((out/'positive.json').read_text())
    negative=json.loads((out/'wrong-version.json').read_text())
    packet=json.loads((out/'packet.json').read_text())
    assert positive['supported_required_fact_coverage']==1 and positive['provisional_task_complete']
    assert not positive['task_complete'] and positive['human_acceptance_pending']
    assert negative['supported_required_fact_coverage']==0 and not negative['provisional_task_complete']
    assert 'sanctum_retrieve' not in json.dumps(packet) and '"arm"' not in json.dumps(packet)
    write(out/'verification.json',dict(passed=True,fixture_only=True,paid_inference=False,
        fixture_labels_independently_accepted=False,operational_task_completion=False,
        arm=arm, connection_proof_sha256=hashlib.sha256((connection_proof/'probe-report.json').read_bytes()).hexdigest()))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arm', choices=('direct','sanctum'), default='sanctum')
    parser.add_argument('--connection-proof',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists(): raise SystemExit('Choose a fresh output directory.')
    probe(args.connection_proof.resolve(),args.out.resolve(),args.arm)
