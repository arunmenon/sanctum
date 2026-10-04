"""Pinned Sanctum process and runner-owned System One broker for agent bundles."""
from contextlib import asynccontextmanager
import hashlib
import json
from pathlib import Path

import yaml
from sanctum_run.agent_schedule import file_hash
from sanctum_run.bundle import _file
from sanctum_run.process_sut import ProcessSUT
from sanctum_run.system_one_broker import SystemOneBroker, load_provider, load_descriptors, load_secret
from sanctum_systemone import CampaignBudget


def validate_runtime(root: Path, runtime: dict, *, fixture=False):
    if runtime.get('schema_version') != 1 or runtime.get('data_class') != 'synthetic':
        raise ValueError('unsupported runtime schema or data class')
    pins = runtime.get('files')
    if not isinstance(pins, dict) or not pins:
        raise ValueError('runtime requires pinned files')
    files = {}
    for name, expected in pins.items():
        path = _file(root, name)
        if file_hash(path) != expected:
            raise ValueError('runtime file hash mismatch')
        files[name] = path

    def pinned(name):
        value = runtime[name]
        if value not in files:
            raise ValueError('runtime references an unpinned file')
        return files[value]

    matrix, providers, descriptors, templates = [pinned(n) for n in
        ('matrix', 'providers', 'descriptors', 'templates')]
    registry_dir = (root / runtime['registry_directory']).resolve()
    calibration_dir = (root / runtime['calibration_directory']).resolve()
    for directory in (registry_dir, calibration_dir):
        if not directory.is_relative_to(root.resolve()) or not directory.is_dir():
            raise ValueError('runtime directory missing or outside bundle')
    for path in [*registry_dir.glob('*.yaml'), *calibration_dir.glob('*.yaml')]:
        if path.resolve() not in files.values():
            raise ValueError('runtime directory contains unpinned policy')
    # The controller validates pins and protocol prerequisites. Detailed SUT
    # configuration types remain inside the isolated reference process.
    manifests = [yaml.safe_load(path.read_text()) for path in registry_dir.glob('*.yaml')]
    registry_hubs = [manifest['hub_id'] for manifest in manifests]
    if not registry_hubs or len(set(registry_hubs)) != len(registry_hubs):
        raise ValueError('runtime registry has missing or duplicate hubs')
    arm = yaml.safe_load(matrix.read_text())['arms'][runtime['config_id']]
    if arm.get('memory_store') not in ('relations', 'tables') or arm.get('decision_provider') != 'named':
        raise ValueError('runtime must enable memory and named System One')
    release_file = pinned('memory_release')
    release = yaml.safe_load(release_file.read_text())
    if (release.get('release_id') != release_file.parent.name
            or release.get('artifact_subject_bindings_required') is not True):
        raise ValueError('runtime requires an exact graph-backed memory release')
    if not any(b.get('status') == 'accepted' and b.get('entity_id')
               for a in release.get('artifacts', []) for b in a.get('subjects', [])):
        raise ValueError('runtime has no accepted artifact subjects')
    provider = runtime['system_one_broker']
    for name in ('max_calls_per_attempt', 'max_input_tokens_per_attempt'):
        if type(provider.get(name)) is not int or provider[name] <= 0:
            raise ValueError('positive System One attempt limit required')
    spec, profile = load_provider(provider['provider'], provider['profile'], providers)
    if fixture and provider['provider'] != 'local-test':
        raise ValueError('fixture runtime may use only the local test provider')
    if not fixture and provider['provider'] == 'local-test':
        raise ValueError('test System One provider cannot serve real agent runs')
    if not fixture and (not spec.capabilities.hosted and provider.get('verified_model') is None):
        raise ValueError('local System One model is not verified')
    if not fixture and not provider.get('verified_model'):
        raise ValueError('real System One resolved model is not verified')
    if not fixture:
        proof = json.loads(pinned('system_one_verification').read_text())
        if (proof.get('passed') is not True or proof.get('provider') != provider['provider']
                or proof.get('resolved_model') != provider['verified_model']
                or proof.get('provider_config_sha256') != file_hash(providers)):
            raise ValueError('System One verification does not match runtime')
        review = json.loads(pinned('memory_review').read_text())
        delegations = json.loads(pinned('memory_delegations').read_text())
        if release.get('review_binding', {}).get('snapshot_sha256') != review.get('snapshot_hash'):
            raise ValueError('memory review candidate snapshot mismatch')
        owner_binding = release.get('review_binding', {}).get('owner_registry_sha256')
        if owner_binding:
            owners = json.loads(pinned('memory_owner_registry').read_text())
            digest = hashlib.sha256(json.dumps(owners, sort_keys=True).encode()).hexdigest()
            if owner_binding != digest or any(owners.get('source_owners', {}).get(m['hub_id']) != m['owner'] for m in manifests):
                raise ValueError('memory source owner registry mismatch')
        elif release.get('authority_assertions') or release.get('procedures') or any(e.get('member_of') for e in release.get('entities', [])):
            raise ValueError('operational routing declarations require a pinned source owner registry')
        for key, document in [('review_sha256', review), ('delegations_sha256', delegations)]:
            digest = hashlib.sha256(json.dumps(document, sort_keys=True).encode()).hexdigest()
            if release.get('review_binding', {}).get(key) != digest:
                raise ValueError('memory review/delegation binding mismatch')
        for artifact in release.get('artifacts', []):
            for binding in artifact.get('subjects', []):
                if binding.get('status') != 'accepted' or not binding.get('entity_id'): continue
                provenance = binding['provenance']
                if (provenance.get('reviewed_by') != review.get('reviewed_by')
                        or review.get('decisions', {}).get(provenance.get('assertion_id')) != 'accepted'
                        or not any(g.get('reviewer') == review.get('reviewed_by')
                            and g.get('source_id') == artifact['source_id'] and 'ABOUT' in g.get('edge_types', [])
                            and (not g.get('entity_ids') or binding['entity_id'] in g['entity_ids'])
                            for g in delegations.get('grants', []))):
                    raise ValueError('accepted artifact subject lacks a scoped review')
        # Pin the resolved model. An environment alias such as latest must not
        # quietly select a different model after readiness verification.
        spec = spec.model_copy(update={'model': provider['verified_model'], 'model_env': None})
    return dict(matrix=matrix, providers=providers, descriptors=descriptors, templates=templates,
                registry=registry_dir, calibration=calibration_dir, release=release_file,
                arm=arm, spec=spec, profile=profile, provider=provider, registry_hubs=set(registry_hubs))


@asynccontextmanager
async def open_agent_runtime(root: Path, runtime: dict, gateway, corpus: Path, out: Path, *, fixture=False):
    checked = validate_runtime(root, runtime, fixture=fixture)
    if checked['registry_hubs'] != set(gateway.hub_ids):
        raise ValueError('runtime registry and released hubs differ')
    provider = checked['provider']
    gateway.system_one = SystemOneBroker(spec=checked['spec'], profile=checked['profile'],
        data_class='synthetic', allowed_sources=list(gateway.hub_ids),
        descriptors=load_descriptors(checked['descriptors']), store_dir=out/'system_one',
        secret=load_secret(checked['spec'].api_key_env), campaign_budget=CampaignBudget(
            provider['max_calls_per_attempt'], provider['max_input_tokens_per_attempt']))
    if checked['spec'].base_url_env:
        configured_url = load_secret(checked['spec'].base_url_env)
        if configured_url:
            gateway.system_one.environment[checked['spec'].base_url_env] = configured_url
    arguments = ['--config', runtime['config_id'], '--matrix', str(checked['matrix']),
        '--registry', str(checked['registry']), '--memory-seed', str(checked['release'].parent.parent),
        '--memory-release', checked['release'].parent.name, '--decision-provider', provider['provider'],
        '--system-one-providers', str(checked['providers']), '--system-one-templates', str(checked['templates']),
        '--calibration-dir', str(checked['calibration'])]
    sut = ProcessSUT(arguments)
    sut.extra_timeout_seconds = checked['profile'].deadline_ms / 1000
    try:
        async with sut.open(gateway, corpus):
            yield sut
    finally:
        gateway.system_one = None
