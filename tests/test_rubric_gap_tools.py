import json
from pathlib import Path
import pytest
import yaml

from tests.test_memory_harvest import bundle
from sanctum_ref.harvest import sha
from tools.prepare_reviewed_place_memory import prepare
from tools.validate_routing_descriptors import validate
from tools.probe_rubric_variants import target_delivered


def test_probe_credit_requires_citable_bound_target_not_metadata_or_alternate_artifact():
    case=dict(source_id='codehub',artifact_id='client',version='v1',quote='actual timeout conversion')
    unit={**case,'text':case['quote'],'citable':True}
    assert target_delivered({'evidence':[unit]},case)
    assert not target_delivered({'evidence':[{**unit,'artifact_id':'other'}]},case)
    assert not target_delivered({'evidence':[{**unit,'text':'unrelated','metadata':{'quote':case['quote']}}]},case)
    assert not target_delivered({'evidence':[{**unit,'citable':False}]},case)


@pytest.mark.parametrize('native_filter,accepted',[('repo',1),('space',0)])
def test_place_review_uses_real_native_filter_and_snapshot(tmp_path,native_filter,accepted):
    candidate=bundle();path=tmp_path/'candidate.json';path.write_text(json.dumps(candidate))
    base=tmp_path/'base';base.mkdir();review={'snapshot_hash':sha(json.dumps(candidate,sort_keys=True)),'reviewed_by':'fixture-owner','decisions':{}}
    (base/'review.json').write_text(json.dumps(review));(base/'delegations.json').write_text(json.dumps({'grants':[{'reviewer':'fixture-owner','source_id':'hub','edge_types':['ABOUT']}]}));(base/'owner-registry.json').write_text('{}')
    registry=tmp_path/'registry';registry.mkdir();(registry/'hub.yaml').write_text(yaml.safe_dump({'hub_id':'hub','search':{'place_filter':native_filter}}))
    prepare(path,base,registry,tmp_path/'out')
    summary=json.loads((tmp_path/'out/complete.json').read_text());assert summary['accepted']==accepted
    assert summary['bundle_activated'] is False
    review['snapshot_hash']='different';(base/'review.json').write_text(json.dumps(review))
    with pytest.raises(ValueError,match='originally reviewed snapshot'):prepare(path,base,registry,tmp_path/'stale')


@pytest.mark.parametrize('quote,valid',[('source client handles timeouts',True),('invented production guarantee',False)])
def test_descriptor_provenance_refuses_invented_quote(tmp_path,quote,valid):
    corpus=tmp_path/'corpus';hub=corpus/'hubs/hub';hub.mkdir(parents=True)
    (hub/'artifacts.jsonl').write_text(json.dumps({'artifact_id':'a','version':'v1','text':'The source client handles timeouts in this snapshot.'})+'\n')
    results=tmp_path/'results';results.mkdir();(results/'rubric-descriptor-hub-01-openai-gpt-6-luna.result.json').write_text(json.dumps({'source_id':'hub','descriptor':'A source snapshot, with unknown live deployment.','coverage':[{'label':str(i),'evidence':[{'artifact_id':'a','version':'v1','quote':quote}]} for i in range(3)]}))
    if valid:
        validate(corpus,results,tmp_path/'out');assert (tmp_path/'out/grounding-audit.json').exists()
    else:
        with pytest.raises(ValueError,match='exact source bytes'):validate(corpus,results,tmp_path/'out')
