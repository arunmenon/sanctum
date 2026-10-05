"""Wait for the scheduled campaign, score saved answers, and report paired variants.

Does not rerun agent attempts or alter gold. Cached calibration packets must match
exactly before judgments are reused. Partial judging never produces a full winner.
"""
import argparse
import json
from pathlib import Path
import shutil
import statistics
import time
import yaml

from tools.run_quality_evaluation import evaluate
from sanctum_run.agent_schedule import compare_scope_strata
from sanctum_run.agent_session import write_atomic


def finish(bundle, run, calibration_cache):
    deadline = time.monotonic() + 7200
    terminal = run / 'campaign-result.json'
    while not terminal.exists():
        if time.monotonic() > deadline:
            raise TimeoutError('Campaign did not finish within two hours; preserve dispatch state')
        time.sleep(5)
    campaign = json.loads(terminal.read_text())
    if not campaign.get('all_terminal') or campaign.get('stop_reason'):
        raise ValueError('Campaign stopped; do not silently evaluate a selected subset')
    out = run / 'quality-evaluation-01'
    out.mkdir(exist_ok=False)
    # Recheck the existing fixture judgments under this scorer, with exact packet
    # equality enforced by judge(); this avoids redundant calibration inference.
    shutil.copytree(calibration_cache / 'cases', out / 'cases')
    write_atomic(out / 'calibration-reuse-receipt.json', {'source': str(calibration_cache),
        'method': 'exact packet equality plus fresh mechanical fixture regrading', 'new_fixture_model_calls': 0})
    policy = bundle.parent / 'private/evaluation-policy.json'
    evaluate(bundle, run, policy, out)
    config = yaml.safe_load(bundle.read_text())
    schedule = json.loads((run / 'schedule.json').read_text())
    ledger = json.loads((run / 'attempts.json').read_text())
    scores = json.loads((out / 'scores.json').read_text())
    gold = {g['task_id']: g for g in map(json.loads, (bundle.parent / config['gold']).read_text().splitlines())}
    scopes = {tid: g['matrix']['scope'] for tid, g in gold.items()}
    comparisons = {}
    for variant in ('system-one', 'memory', 'combined'):
        subset = {**schedule, 'attempts': [a for a in schedule['attempts'] if a['arm'] in ('baseline', variant)]}
        ids = {a['attempt_id'] for a in subset['attempts']}
        comparison = compare_scope_strata(subset, {k: v for k, v in ledger.items() if k in ids},
            {k: v for k, v in scores.items() if k in ids}, scopes, arms=['baseline', variant], seed=42)
        write_atomic(run / ('baseline-vs-' + variant + '.json'), comparison)
        comparisons[variant] = comparison
    summaries = {}
    for arm in config['arms']:
        for scope in ('in_scope', 'partial', 'out_of_scope'):
            selected = [scores[a['attempt_id']] for a in schedule['attempts'] if a['arm'] == arm
                        and scopes[a['task_id']] == scope and a['attempt_id'] in scores]
            summaries[arm + '/' + scope] = {'scored': len(selected),
                'coverage': statistics.mean(s['supported_required_fact_coverage'] for s in selected) if selected else None,
                'provisional_complete': sum(s['provisional_task_complete'] for s in selected),
                'answers_with_material_unsupported_claims': sum(any(c['severity'] == 'material'
                    for c in s.get('unsupported_claims', [])) for s in selected)}
    write_atomic(run / 'followup-summary.json', {'summaries': summaries,
        'all_answers_scored': len(scores) == len(schedule['attempts']),
        'comparisons': {k: {'ready': v['primary_comparison_ready'], 'estimate': v.get('quality_estimate')} for k, v in comparisons.items()},
        'limitations': ['12 same-corpus tasks, one attempt per variant',
                       'Codex technical task acceptance; independent human acceptance pending',
                       'Fresh questions have disclosed shared premises; not independent generalization',
                       'Same-model semantic judge; descriptive exploratory estimates']})
    print(json.dumps({'followup_complete': True, 'scored': len(scores), 'summary': str(run / 'followup-summary.json')}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('bundle', type=Path)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--calibration-cache', type=Path, required=True)
    a = p.parse_args()
    finish(a.bundle.resolve(), a.run.resolve(), a.calibration_cache.resolve())
