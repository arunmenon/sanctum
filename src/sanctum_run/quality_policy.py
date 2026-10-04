"""Frozen post-run exploratory scoring context; never changes agent inputs."""
import json
from pathlib import Path


def scoring_context(policy,task_id):
    return dict(version=policy['version'],task=policy['tasks'][task_id],rubric=policy['rubric'],
        boundary_sources=policy['boundary_sources'].get(task_id,{}),topic_vocabulary=policy['topic_vocabulary'])


def load_policy(path):
    value=json.loads(Path(path).read_text())
    if value.get('version')!='quality-scoring-v2' or value.get('frozen_evaluation') is not False:
        raise ValueError('only exploratory quality policy v2 is implemented')
    return value
