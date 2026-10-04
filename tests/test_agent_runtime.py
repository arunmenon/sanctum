"""Real process/MCP/HTTP integration; the local model server is a test double."""
import hashlib
import json
from pathlib import Path
import shutil

import anyio
import pytest
import yaml

from sanctum_hubs.tokens import TokenService
from sanctum_run.agent_runtime import open_agent_runtime, validate_runtime
from sanctum_run.agent_mcp import AgentMCP
from sanctum_run.delivery import DeliveryBudget, EvidenceNormalizer
from sanctum_run.gateway import HubGateway
from tests.helpers.systemone_server import SystemOneTestServer
from tests.scenarios.conftest import scenario_world  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
HUBS = ['codehub', 'dochub', 'skillhub', 'memoryhub']


def runtime_fixture(root, world):
    (root/'registry').mkdir(parents=True)
    (root/'calibration').mkdir()
    for hub in HUBS:
        shutil.copy(ROOT/f'owners/manifests/{hub}.yaml', root/f'registry/{hub}.yaml')
    for source, target in [('configs/matrix.yaml', 'matrix.yaml'),
                           ('configs/system_one_providers.yaml', 'providers.yaml'),
                           ('configs/system_one_templates.yaml', 'templates.yaml'),
                           ('configs/d2_standin.yaml', 'descriptors.yaml')]:
        shutil.copy(ROOT/source, root/target)
    release = yaml.safe_load((ROOT/'owners/memory_seed/r1/release.yaml').read_text())
    records = [json.loads(line) for line in (world/'hubs/codehub/artifacts.jsonl').read_text().splitlines()]
    record = next(r for r in records if r['location'] == 'repo:payments/payment-auth' and r['version'] == 'R42')
    release['artifact_subject_bindings_required'] = True
    release['artifacts'] = [dict(source_id='codehub', artifact_id=record['artifact_id'],
        version=record['version'], content_hash=hashlib.sha256(record['text'].encode()).hexdigest(),
        visibility_groups=record['acl'], subjects=[dict(entity_id='svc:payments/payment-auth',
            status='accepted', provenance=dict(assertion_id='fixture-about', reviewed_by='fixture-owner',
                                               evidence=[dict(fixture=True)]))])]
    (root/'memory/r1').mkdir(parents=True)
    (root/'memory/r1/release.yaml').write_text(yaml.safe_dump(release))
    runtime = dict(schema_version=1, data_class='synthetic', config_id='C5', matrix='matrix.yaml',
        registry_directory='registry', calibration_directory='calibration', memory_release='memory/r1/release.yaml',
        providers='providers.yaml', descriptors='descriptors.yaml', templates='templates.yaml',
        system_one_broker=dict(provider='local-test', profile='relaxed',
                              max_calls_per_attempt=4, max_input_tokens_per_attempt=10000),
        files={str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in root.rglob('*.yaml')})
    return runtime, records


def test_pinned_runtime_refuses_changed_and_unpinned_policy(tmp_path, scenario_world):
    runtime, _ = runtime_fixture(tmp_path, scenario_world)
    assert validate_runtime(tmp_path, runtime, fixture=True)['arm']['memory_store'] == 'relations'
    with pytest.raises(ValueError, match='test System One'):
        validate_runtime(tmp_path, runtime)
    (tmp_path/'registry/extra.yaml').write_text('hub_id: unexpected')
    with pytest.raises(ValueError, match='unpinned policy'):
        validate_runtime(tmp_path, runtime, fixture=True)
    (tmp_path/'registry/extra.yaml').unlink()
    (tmp_path/'memory/r1/release.yaml').write_text('changed')
    with pytest.raises(ValueError, match='hash mismatch'):
        validate_runtime(tmp_path, runtime, fixture=True)


def test_real_runtime_binds_review_snapshot_and_registered_source_owners(tmp_path, scenario_world):
    runtime, _ = runtime_fixture(tmp_path, scenario_world)
    digest = lambda value: hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
    review = dict(snapshot_hash='fixture-candidate', reviewed_by='fixture-owner', decisions={'fixture-about':'accepted'})
    grants = dict(grants=[dict(reviewer='fixture-owner',source_id='codehub',edge_types=['ABOUT'])])
    owners = dict(source_owners={hub:yaml.safe_load((tmp_path/f'registry/{hub}.yaml').read_text())['owner'] for hub in HUBS})
    release_path=tmp_path/'memory/r1/release.yaml'
    release=yaml.safe_load(release_path.read_text())
    release['review_binding']=dict(snapshot_sha256='fixture-candidate',review_sha256=digest(review),
        delegations_sha256=digest(grants),owner_registry_sha256=digest(owners))
    release_path.write_text(yaml.safe_dump(release))
    runtime['system_one_broker'].update(provider='typesafe-jev',verified_model='jev-fixture')
    documents={'memory_review':review,'memory_delegations':grants,'memory_owner_registry':owners,
        'system_one_verification':dict(passed=True,provider='typesafe-jev',resolved_model='jev-fixture',
            provider_config_sha256=hashlib.sha256((tmp_path/'providers.yaml').read_bytes()).hexdigest())}
    for key, doc in documents.items():
        path=tmp_path/f'{key}.json';path.write_text(json.dumps(doc))
        runtime[key]=path.name
    runtime['files']={str(p.relative_to(tmp_path)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in tmp_path.rglob('*') if p.is_file()}
    assert validate_runtime(tmp_path,runtime)['provider']['verified_model']=='jev-fixture'
    # Re-pinning changed files cannot bypass the cross-document owner binding.
    owners['source_owners']['codehub']='unregistered-person'
    path=tmp_path/'memory_owner_registry.json';path.write_text(json.dumps(owners))
    runtime['files'][path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError,match='owner registry mismatch'):
        validate_runtime(tmp_path,runtime)


def test_sanctum_agent_mcp_runs_memory_and_broker_out_of_process(tmp_path, scenario_world, monkeypatch):
    runtime, records = runtime_fixture(tmp_path, scenario_world)
    with SystemOneTestServer() as server:
        monkeypatch.setenv('SANCTUM_SYSTEMONE_TEST_URL', server.base_url)
        async def exercise():
            tokens = TokenService(scenario_world/'identity/principals.json', 'runtime-test-only')
            async with HubGateway(scenario_world, HUBS, tokens) as gateway:
                async with open_agent_runtime(tmp_path, runtime, gateway, scenario_world,
                                              tmp_path/'observed', fixture=True) as sut:
                    adapter = await AgentMCP(gateway, tokens.issue_caller_token('kestrel-payments'),
                        'sanctum', EvidenceNormalizer([{**r, 'source_id': 'codehub'} for r in records]),
                        DeliveryBudget(8000, 4000), sut=sut).initialize()
                    result = await adapter.dispatch('sanctum_retrieve',
                        dict(query='What is the payment-auth retry limit in R42?', mode='explore'))
                    assert result.get('error') is None
                    trace = adapter.calls[0]
                    assert trace['router_receipt']['memory_release_id'] == 'r1'
                    assert trace['router_receipt']['decisions']
                    assert any(a['kind'] == 'subject_binding'
                               for a in trace['router_receipt']['activations'])
                    assert trace['backend_trace']['model_calls']
                    assert any(u.get('artifact_id') for u in result['evidence'])
                    assert adapter.inventory == ['sanctum_retrieve']
                    await adapter.close()
                assert gateway.system_one is None
        anyio.run(exercise)
        assert server.behavior.requests


@pytest.mark.parametrize('change', ['unshared', 'deleted'])
def test_stale_subject_snapshot_does_not_disclose_revoked_artifact(tmp_path, scenario_world, monkeypatch, change):
    world = tmp_path/'world'
    shutil.copytree(scenario_world, world)
    runtime, records = runtime_fixture(tmp_path/'runtime', world)
    release = yaml.safe_load((tmp_path/'runtime/memory/r1/release.yaml').read_text())
    bound_id = release['artifacts'][0]['artifact_id']
    altered = []
    for record in records:
        if record['artifact_id'] == bound_id:
            if change == 'deleted': continue
            record = {**record, 'acl': ['unrelated-group']}
        altered.append(record)
    (world/'hubs/codehub/artifacts.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in altered))
    with SystemOneTestServer() as server:
        monkeypatch.setenv('SANCTUM_SYSTEMONE_TEST_URL', server.base_url)
        async def exercise():
            tokens = TokenService(world/'identity/principals.json', 'revocation-fixture')
            async with HubGateway(world, HUBS, tokens) as gateway:
                async with open_agent_runtime(tmp_path/'runtime', runtime, gateway, world,
                                              tmp_path/'observed', fixture=True) as sut:
                    adapter = await AgentMCP(gateway, tokens.issue_caller_token('kestrel-payments'),
                        'sanctum', EvidenceNormalizer([{**r, 'source_id': 'codehub'} for r in records]),
                        DeliveryBudget(8000, 4000), sut=sut).initialize()
                    result = await adapter.dispatch('sanctum_retrieve',
                        dict(query='What is the payment-auth retry limit in R42?', mode='explore'))
                    assert result.get('error') is None
                    assert all(u.get('artifact_id') != bound_id for u in result['evidence'])
                    receipt = adapter.calls[0]['router_receipt']
                    assert not any(a['kind'] == 'subject_binding' for a in receipt['activations'])
                    await adapter.close()
        anyio.run(exercise)


def test_unconstrained_offers_four_hubs_even_for_release_query(tmp_path, scenario_world, monkeypatch):
    runtime, records = runtime_fixture(tmp_path, scenario_world)
    matrix_path=tmp_path/'matrix.yaml'
    matrix=yaml.safe_load(matrix_path.read_text());matrix['arms']['C5']['routing']='jev_unconstrained'
    matrix_path.write_text(yaml.safe_dump(matrix));runtime['files']['matrix.yaml']=hashlib.sha256(matrix_path.read_bytes()).hexdigest()
    with SystemOneTestServer() as server:
        monkeypatch.setenv('SANCTUM_SYSTEMONE_TEST_URL', server.base_url)
        async def exercise():
            tokens=TokenService(scenario_world/'identity/principals.json','runtime-test-only')
            async with HubGateway(scenario_world,HUBS,tokens) as gateway:
                async with open_agent_runtime(tmp_path,runtime,gateway,scenario_world,tmp_path/'observed',fixture=True) as sut:
                    adapter=await AgentMCP(gateway,tokens.issue_caller_token('kestrel-payments'),'sanctum',EvidenceNormalizer([{**r,'source_id':'codehub'} for r in records]),DeliveryBudget(8000,4000),sut=sut).initialize()
                    result=await adapter.dispatch('sanctum_retrieve',dict(query='What is the payment-auth retry limit in R42?',mode='explore'))
                    assert result.get('error') is None
                    trace=adapter.calls[0]
                    decisions=[d['value'] for d in trace['router_receipt']['decisions'] if (d.get('value') or {}).get('source')]
                    assert {d['source'] for d in decisions} == set(HUBS)
                    assert all(d['selection_policy']=='raw_argmax' and not d['shadow'] for d in decisions)
                    called={c['source_id'] for c in trace['backend_trace']['calls']}
                    assert called == {d['source'] for d in decisions if d['call']}
                    await adapter.close()
        anyio.run(exercise)
