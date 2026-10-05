"""Prepare isolated development variants; preserve historical bundles and runtime pins."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import yaml


def prepare(base, descriptors, memory, out):
    out.mkdir(parents=True, exist_ok=False)
    variants = {}
    for name, rich, places in [('baseline', False, False), ('system-one', True, False),
                                ('memory', False, True), ('combined', True, True)]:
        target = out / name
        shutil.copytree(base, target)
        runtime_path = target / 'connections/runtime.json'
        runtime = json.loads(runtime_path.read_text())
        if rich:
            shutil.copyfile(descriptors, target / runtime['descriptors'])
        if places:
            destination = target / 'connections/memory' / memory.name
            shutil.copytree(memory, destination)
            for key, filename in [('memory_release', 'release.yaml'), ('memory_review', 'review.json'),
                                  ('memory_delegations', 'delegations.json'),
                                  ('memory_owner_registry', 'owner-registry.json')]:
                runtime[key] = str((destination / filename).relative_to(target))
                runtime['files'][runtime[key]] = hashlib.sha256((destination / filename).read_bytes()).hexdigest()
        runtime['files'][runtime['descriptors']] = hashlib.sha256((target / runtime['descriptors']).read_bytes()).hexdigest()
        runtime_path.write_text(json.dumps(runtime, indent=2, sort_keys=True) + '\n')
        manifest_path = target / 'experiment.yaml'
        manifest = yaml.safe_load(manifest_path.read_text())
        manifest['experiment_id'] = 'rubric-development-' + name
        # Each arm remains unconstrained C5; only the declared variables change.
        manifest['arms']['sanctum']['runtime_sha256'] = hashlib.sha256(runtime_path.read_bytes()).hexdigest()
        manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False))
        variants[name] = {'bundle': str(manifest_path), 'rich_descriptors': rich,
                          'reviewed_place_memory': places, 'historical_tasks_for_probes_only': True}
    (out / 'variants.json').write_text(json.dumps(variants, indent=2) + '\n')
    return variants


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('base', type=Path)
    p.add_argument('--descriptors', type=Path, required=True)
    p.add_argument('--memory', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(prepare(a.base, a.descriptors, a.memory, a.out)))
