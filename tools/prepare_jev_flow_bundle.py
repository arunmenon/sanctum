"""Prepare a paired D2/D4/D6 development comparison without changing its source bundle."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

import yaml

from sanctum_run.agent_runtime import validate_runtime
from sanctum_run.agent_schedule import load_experiment
from sanctum_run.bundle import validate_bundle


def prepare(base: Path, out: Path, *, isolation_proof: Path, round_limit_proof: Path):
    base, out = base.resolve(), out.resolve()
    validate_bundle(base)
    config = yaml.safe_load(base.read_text())
    source = base.resolve().parent
    baseline = config['arms']['baseline']
    if baseline['tool_surface'] != 'sanctum_only':
        raise ValueError('source baseline must use Sanctum')
    runtime = json.loads((source / baseline['runtime_file']).read_text())
    checked = validate_runtime(source, runtime)
    if checked['arm'].get('routing') != 'jev_unconstrained':
        raise ValueError('preserve the existing unconstrained D2 baseline')
    if runtime.get('round3', {}).get('mode', 'none') != 'none':
        raise ValueError('source baseline already enables Round 3')
    shutil.copytree(source, out)  # Refuses to replace an existing bundle.
    arms = {}
    for name, mode in [('baseline', 'none'), ('relevance', 'd4'), ('conflicts', 'd6'), ('all-decisions', 'both')]:
        variant = json.loads(json.dumps(runtime))
        variant['round3'] = {'mode': mode, 'policy': 'raw',
            'templates': {'d4': 'd4-noul-v1', 'd6': 'd6-noul-v1'}}
        validate_runtime(out, variant)
        path = out / 'connections' / f'jev-flow-{name}.json'
        path.write_text(json.dumps(variant, indent=2, sort_keys=True) + '\n')
        arms[name] = dict(tool_surface='sanctum_only', runtime_ready=True,
            runtime_file=str(path.relative_to(out)), runtime_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    for kind, proof in [('isolation', isolation_proof), ('round_limit', round_limit_proof)]:
        destination = out/'connections'/f'jev-flow-{kind}-proof.json'
        shutil.copyfile(proof, destination)
        config['agent']['verification'][kind] = {'file': str(destination.relative_to(out)),
            'expected_sha256': hashlib.sha256(destination.read_bytes()).hexdigest()}
    config['experiment_id'] = out.name
    config['arms'] = arms
    config['execution']['repetitions'] = 1
    config['readiness']['frozen'] = False
    config['readiness']['independent_acceptance'] = False
    manifest = out / 'experiment.yaml'
    manifest.write_text(yaml.safe_dump(config, sort_keys=False))
    load_experiment(manifest)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('base', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--isolation-proof', type=Path, required=True)
    parser.add_argument('--round-limit-proof', type=Path, required=True)
    args = parser.parse_args()
    print(prepare(args.base, args.out, isolation_proof=args.isolation_proof, round_limit_proof=args.round_limit_proof))
