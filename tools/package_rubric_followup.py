"""Package technically reviewed fresh tasks with four randomized experimental arms."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import yaml


def package(variants, curated, policy_path, out):
    review = json.loads((curated / 'review.json').read_text())
    if review.get('status') != 'accepted_for_development' or review.get('independent') is not False:
        raise ValueError('Explicit technical acceptance required; do not infer human acceptance')
    tasks = json.loads((curated / 'tasks.json').read_text())
    for task in tasks:
        for fact in task['required_facts']:
            if fact['support_kind'] == 'boundary' and (fact.get('boundary_verification_needed') or not fact.get('boundary_record')):
                raise ValueError('Unverified boundary cannot enter a run bundle')
    roots = {name: Path(v['bundle']).resolve().parent for name, v in json.loads(variants.read_text()).items()}
    shutil.copytree(roots['baseline'], out)
    config = yaml.safe_load((out / 'experiment.yaml').read_text())
    config['experiment_id'] = 'pdlc-rubric-followup-01'
    config['execution']['repetitions'] = 1
    config['arms'] = {}
    for name, root in roots.items():
        destination = out / 'variants' / name / 'connections'
        shutil.copytree(root / 'connections', destination)
        runtime = json.loads((destination / 'runtime.json').read_text())
        prefix = f'variants/{name}/'
        for key in ('matrix', 'providers', 'descriptors', 'templates', 'registry_directory',
                    'calibration_directory', 'memory_release', 'memory_review', 'memory_delegations',
                    'memory_owner_registry', 'system_one_verification'):
            runtime[key] = prefix + runtime[key]
        runtime['files'] = {prefix + k: v for k, v in runtime['files'].items()}
        (destination / 'runtime.json').write_text(json.dumps(runtime, indent=2, sort_keys=True) + '\n')
        relative = str((destination / 'runtime.json').relative_to(out))
        config['arms'][name] = {'tool_surface': 'sanctum_only', 'runtime_ready': True, 'runtime_file': relative,
            'runtime_sha256': hashlib.sha256((destination / 'runtime.json').read_bytes()).hexdigest()}
    public, gold = [], []
    for t in tasks:
        public.append({k: t[k] for k in ('task_id', 'family', 'prompt', 'caller_requirements', 'answer_format')})
        sources = sorted({e['source_id'] for f in t['required_facts'] for e in f.get('evidence', [])})
        gold.append({'task_id': t['task_id'], 'required_facts': t['required_facts'],
            'plan_checklist': t['plan_checklist'], 'version_conflict_demand': t.get('version_conflict_demand', False),
            'matrix': {'family': t['family'], 'domains': t['domains'], 'sources': sources,
                'difficulty': t['difficulty'], 'answerability': t['answerability'], 'scope': t['scope'],
                'design_kind': t['design_kind']}, 'source_review': review,
            'generation_source': t['generation_source']})
    for path, records in [('public/tasks.jsonl', public), ('private/gold.jsonl', gold)]:
        (out / path).write_text(''.join(json.dumps(r) + '\n' for r in records))
    config['diversity'] = {'family_counts': dict(Counter(t['family'] for t in tasks)),
        'scope_counts': dict(Counter(t['scope'] for t in tasks)), 'required_domains': [],
        'required_sources': [], 'required_answerability': ['complete', 'partial', 'unavailable'],
        'reject_duplicate_fact_sets': True, 'duplicate_fact_set_exceptions': []}
    (out / 'experiment.yaml').write_text(yaml.safe_dump(config, sort_keys=False))
    ledger = {'approval_ref': 'User: continue rubric improvement plan autonomously, 5 October 2026; Claude subscription authorized',
        'approved': True, 'billing_mode': 'subscription', 'ceiling_usd': 144,
        'pricing_basis': {'agent': 'SDK estimate guardrail only; Claude Max subscription, not Anthropic API billing',
            'nested_rate_card_bound_usd': 1.008, 'nested': '48 attempts x 500000 input tokens x $0.042/M'},
        'reservations': {}}
    (out / 'private/campaign-ledger.json').write_text(json.dumps(ledger, indent=2) + '\n')
    policy = json.loads(policy_path.read_text())
    policy['tasks'] = {t['task_id']: t for t in public}
    policy['boundary_sources'] = {t['task_id']: {f['fact_id']: ['codehub', 'dochub', 'memoryhub', 'skillhub']
        for f in t['required_facts'] if f['support_kind'] == 'boundary'} for t in tasks}
    policy['boundary_source_method'] = 'Any successful relevant hub investigation may support a boundary; no fixed hub obligation. Claim support and scoped corpus absence remain required.'
    policy['review_ref'] = str(curated / 'review.json')
    policy['post_run_repairs'] = False
    (out / 'private/evaluation-policy.json').write_text(json.dumps(policy, indent=2) + '\n')
    (out / 'private/task-curation-review.json').write_text(json.dumps(review, indent=2) + '\n')
    print(json.dumps({'tasks': len(tasks), 'arms': list(roots), 'attempts': len(tasks)*4,
                      'frozen_evaluation': False, 'independent_acceptance': False}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--variants', type=Path, required=True)
    p.add_argument('--curated', type=Path, required=True)
    p.add_argument('--policy', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    package(a.variants, a.curated, a.policy, a.out.resolve())
