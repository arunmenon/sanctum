"""An exhausted review retry must not grade a failure or strand other answers."""
import json
import sys
from pathlib import Path

import yaml
import pytest

from tools import run_quality_evaluation as driver


@pytest.mark.parametrize('saved_retry', [False, True])
def test_exhausted_judge_retry_preserves_unknown_and_finishes_other_attempt(monkeypatch, tmp_path, saved_retry):
    bundle = tmp_path / 'bundle'
    bundle.mkdir()
    (bundle / 'corpus').mkdir()
    (bundle / 'corpus' / 'manifest.json').write_text('{}')
    (bundle / 'gold.jsonl').write_text(json.dumps({'task_id': 't1'}) + '\n')
    config = bundle / 'experiment.yaml'
    config.write_text(yaml.safe_dump({'corpus': {'manifest': 'corpus/manifest.json'}, 'gold': 'gold.jsonl'}))
    policy = bundle / 'policy.json'
    policy.write_text('{}')
    cli = tmp_path / 'claude'
    cli.write_text('fixture binary')
    run = tmp_path / 'run'
    run.mkdir()
    attempts = [{'attempt_id': name, 'task_id': 't1'} for name in ('bad', 'good')]
    (run / 'schedule.json').write_text(json.dumps({'attempts': attempts}))
    for item in attempts:
        folder = run / 'attempts' / item['attempt_id']
        folder.mkdir(parents=True)
        (folder / 'result.json').write_text('{}')
        (folder / 'answer.json').write_text(item['attempt_id'])
    out = run / 'quality'
    out.mkdir()
    (out / 'calibration.json').write_text('{"passed":true}')
    if saved_retry:
        prior=out/'judgments'/'good'
        (prior/'schema-retry-01').mkdir(parents=True)
        (prior/'review.json').write_text('{}')
        (prior/'schema-retry-receipt.json').write_text('{"max_retries":1}')
        (prior/'schema-retry-01'/'review.json').write_text('{"valid":true}')
    monkeypatch.setattr(driver, 'CLI', cli)
    monkeypatch.setattr(driver, 'sys', sys, raising=False)
    monkeypatch.setattr(driver, 'load_policy', lambda p: {'judge': {'invalid_schema_retries': 1}})
    monkeypatch.setattr(driver, 'scoring_context', lambda *args: {})
    monkeypatch.setattr(driver, 'judge_packet', lambda answer, *args: {'answer': answer})
    monkeypatch.setattr(driver, 'parse_answer', lambda answer: ({}, []))
    calls = []
    def judge(packet, folder, policy, format_feedback=None):
        calls.append((packet['answer'], format_feedback is not None))
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'review.json').write_text('{}')
        return {}
    def score(answer, *args, **kwargs):
        if answer == 'bad':
            raise ValueError('semantic labels missing')
        if saved_retry and not args[3].get('valid'):
            raise ValueError('semantic labels missing')
        return {'adjudication_kind': 'semantic', 'supported_required_fact_coverage': 1}
    reports = []
    monkeypatch.setattr(driver, 'judge', judge)
    monkeypatch.setattr(driver, 'score_answer', score)
    monkeypatch.setattr(driver.subprocess, 'run', lambda *args, **kwargs: reports.append(args[0]))
    driver.evaluate(config, run, policy, out)
    scores = json.loads((out / 'scores.json').read_text())
    failures = json.loads((out / 'judge-failures.json').read_text())
    complete = json.loads((out / 'complete.json').read_text())
    assert set(scores) == {'good'}
    assert failures['bad']['quality_score'] is None
    assert failures['bad']['agent_rerun'] is False
    assert [c for c in calls if c[0] == 'bad'] == [('bad', False), ('bad', True)]
    assert complete['scored'] == 1 and complete['judge_failures'] == 1
    assert complete['all_attempts_scored'] is False
    assert len(reports) == 1
    if saved_retry:
        assert not [c for c in calls if c[0]=='good']
        assert scores['good']['review_file'].endswith('schema-retry-01/review.json')
