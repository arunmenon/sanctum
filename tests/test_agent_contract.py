import json
import hashlib

import pytest
import yaml

from sanctum_run.agent_schedule import load_experiment
from tests.test_agent_schedule import setup


@pytest.mark.parametrize('failure', ['caller', 'adapter', 'paid', 'span', 'quote', 'boundary', 'planning'])
def test_invalid_execution_contracts_fail_before_dispatch(tmp_path, failure):
    path, config = setup(tmp_path)
    gold_path=path.parent/config['gold'];gold=json.loads(gold_path.read_text())
    if failure=='caller': config['caller']['principal']='unknown'
    elif failure=='adapter': config['agent']['adapter']='not-yet-implemented'
    elif failure=='paid': config['readiness']=dict(paid_budget_approved=True)
    elif failure=='span': gold['required_facts'][0]['evidence'][0].update(start=1,end=5)
    elif failure=='quote': gold['required_facts'][0]['evidence'][0]['quote']='invented behavior'
    elif failure=='boundary': gold['required_facts'][0].update(support_kind='boundary',boundary_record={})
    elif failure=='planning': gold['plan_checklist']=[dict(dimension='tests',mandatory_items=[])]
    path.write_text(yaml.safe_dump(config));gold_path.write_text(json.dumps(gold)+'\n')
    with pytest.raises(ValueError): load_experiment(path)
    assert not (path.parent/'attempts.json').exists()


@pytest.mark.parametrize('damage',['changed_proof','changed_executable'])
def test_paid_preflight_binds_actual_agent_isolation_evidence(tmp_path,monkeypatch,damage):
    path,config=setup(tmp_path);binary=tmp_path/'claude';binary.write_text('fixture executable')
    monkeypatch.setattr('sanctum_run.agent_contract.shutil.which',lambda name:str(binary))
    config['agent'].update(model='fixture-model',effort='low',verification={})
    config['limits']['total_inference_spend_usd']=1
    config['readiness']=dict(paid_budget_approved=True,agent_isolation_verified=True)
    ledger=path.parent/'spend.json';ledger.write_text('{}');config['spend']=dict(ledger=ledger.name)
    for name in ('isolation','round_limit'):
        proof=path.parent/f'{name}.json';proof.write_text(json.dumps(dict(passed=True,requested_models=['fixture-model'],
            cli_sha256=hashlib.sha256(binary.read_bytes()).hexdigest())))
        config['agent']['verification'][name]=dict(file=proof.name,expected_sha256=hashlib.sha256(proof.read_bytes()).hexdigest())
    path.write_text(yaml.safe_dump(config));load_experiment(path)
    if damage=='changed_proof':(path.parent/'isolation.json').write_text('{}')
    else:binary.write_text('changed executable')
    with pytest.raises(ValueError,match='proof hash mismatch|executable changed'):
        load_experiment(path)
