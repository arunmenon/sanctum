"""Harvest failure boundaries and reviewed ABOUT semantics, independent of paid inference."""
from copy import deepcopy
import json

import anyio
import pytest

from sanctum_ref.harvest import HarvestArtifact, InventoryPage, collect, propose, apply_semantic_results, apply_owner_declarations as _apply_owner_declarations, project_release as _project_release, review_bundle, sha, validate
from sanctum_ref.memory import Release, RelationStore, TableStore, authority_for


def apply_owner_declarations(candidate, declaration):
    return _apply_owner_declarations(candidate, declaration, owner_registry={
        'source_owners': {'hub': 'fixture-owner'}})


def project_release(candidate, release_id, review=None):
    # Fixture policy is separate from the review document under test.
    delegations = {'grants': [{'reviewer': review['reviewed_by'], 'source_id': 'hub',
                              'edge_types': ['ABOUT', 'DENOTES', 'SELECTS_FOR', 'MEMBER_OF',
                                             'AUTHORITATIVE_FOR', 'APPLIES_TO', 'PARENT']}]} if review else None
    return _project_release(candidate, release_id, review, delegations=delegations)


def artifact():
    text = 'Payment Authorization calls the fraud client.'
    return {'source_id':'hub','artifact_id':'a','native_ref':'file.py','version':'R42',
            'content_hash':sha(text),'title':'Authorization handler','text':text,
            'metadata':{'container':{'id':'repo.pay','name':'Payment repo'},
                        'harvest_selector':{'repo':'repo:pay'},'harvest_location':'repo:pay',
                        'services':[{'id':'svc.pay','name':'Payment Authorization','grounding':'observed'}],
                        'domains':[]},'visibility_groups':['readers'],'principal':None}


def bundle():
    return propose([{'source_id':'hub','snapshot_id':'s1','complete_for_access_context':True,
                     'capabilities':{},'artifacts':[artifact()]}])


def test_review_gates_about_without_turning_it_into_identity():
    candidate = bundle()
    assertion = next(a for a in candidate['assertions'] if a['type']=='ABOUT')
    projected = Release.model_validate(project_release(candidate,'test-release'))
    for backend in (RelationStore,TableStore):
        store = backend(projected)
        assert store.denotes(('payment','authorization')) == []
        assert store.subjects_for('hub','a','R42',artifact()['content_hash'],{'readers'},None)[0].entity_id is None
    review = {'snapshot_hash':sha(json.dumps(candidate,sort_keys=True)),'reviewed_by':'fixture-owner',
              'decisions':{assertion['id']:'accepted'}}
    projected = Release.model_validate(project_release(candidate,'test-release',review))
    for backend in (RelationStore,TableStore):
        store = backend(projected)
        assert store.subjects_for('hub','a','R42',artifact()['content_hash'],{'readers'},None)[0].entity_id == 'svc.pay'
        assert store.denotes(('payment','authorization')) == []
        assert store.subjects_for('hub','a','R42','stale-hash',{'readers'},None)[0].entity_id is None
        assert store.subjects_for('hub','a','R42',artifact()['content_hash'],{'outsiders'},None)[0].entity_id is None


def test_principal_scoping_and_snapshot_bound_review():
    candidate = bundle()
    candidate['sources'][0]['artifacts'][0]['principal'] = 'owner'
    about = next(a for a in candidate['assertions'] if a['type']=='ABOUT')
    review = {'snapshot_hash':sha(json.dumps(candidate,sort_keys=True)),'reviewed_by':'reviewer',
              'decisions':{about['id']:'accepted'}}
    release = Release.model_validate(project_release(candidate,'test',review))
    store = RelationStore(release)
    assert store.subjects_for('hub','a','R42',artifact()['content_hash'],{'readers'},'other')[0].entity_id is None
    assert store.subjects_for('hub','a','R42',artifact()['content_hash'],{'readers'},'owner')[0].entity_id == 'svc.pay'
    review['snapshot_hash']='incorrect'
    with pytest.raises(ValueError,match='snapshot hash'): project_release(candidate,'test',review)


def test_malformed_semantic_proposals_are_quarantined():
    candidate = bundle()
    invalid = {'source_id':'hub','artifact_id':'a','relation':'ABOUT','entity_id':'svc.pay',
               'field':'text','quote':'An invented quote','label':''}
    invalid_authority = {**invalid,'relation':'AUTHORITATIVE_FOR','quote':'fraud client'}
    apply_semantic_results(candidate,[{'proposals':[invalid,invalid_authority]}])
    assert len(candidate['rejected_proposals']) == 2
    assert all(a['status']=='proposed' for a in candidate['assertions'])
    corrupted = deepcopy(candidate)
    corrupted['assertions'][0]['evidence'][0]['start'] += 1
    with pytest.raises(ValueError,match='span mismatch'): validate(corrupted)


def test_semantic_proposals_do_not_silently_bind_to_another_version():
    first = artifact()
    second = {**deepcopy(first), 'version': 'R43'}
    candidate = propose([{'source_id': 'hub', 'snapshot_id': 's1',
                         'complete_for_access_context': True, 'capabilities': {},
                         'artifacts': [first, second]}])
    proposal = {'source_id': 'hub', 'artifact_id': 'a', 'relation': 'ABOUT',
                'entity_id': 'svc.pay', 'field': 'text', 'quote': 'fraud client'}
    apply_semantic_results(candidate, [{'proposals': [proposal]}])
    assert len(candidate['rejected_proposals']) == 1
    apply_semantic_results(candidate, [{'proposals': [{**proposal, 'version': 'R42',
                                                      'content_hash': first['content_hash']}]}])
    assert not candidate['rejected_proposals']
    semantic = [a for a in candidate['assertions'] if a['basis'] == 'llm_content_proposal']
    assert len(semantic) == 1
    assert semantic[0]['from'] == 'hub:a@R42'
    apply_semantic_results(candidate, [{'proposals': [{**proposal, 'version': 'R43',
                                                      'content_hash': 'stale'}]}])
    assert len(candidate['rejected_proposals']) == 1


def test_inventory_tracks_incomplete_snapshots_and_refuses_cursor_cycles():
    class Connector:
        source_id='hub'; capabilities={}
        async def inventory(self,cursor):
            return InventoryPage([{}],None,'snapshot',False)
        async def fetch(self,item): return HarvestArtifact.model_validate(artifact())
    result=anyio.run(collect,Connector())
    assert not result['complete_for_access_context'] and not result['deletion_inference_allowed']
    class Cycling(Connector):
        async def inventory(self,cursor): return InventoryPage([], 'repeat', 'snapshot',True)
    with pytest.raises(ValueError,match='cursor cycle'): anyio.run(collect,Cycling())
    class Changing(Connector):
        async def inventory(self,cursor):
            return InventoryPage([], 'next' if cursor is None else None, 'first' if cursor is None else 'changed',True)
    with pytest.raises(ValueError,match='changed during scan'): anyio.run(collect,Changing())


def test_same_scope_identity_conflict_rejected_after_review():
    candidate=bundle()
    name=next(a for a in candidate['assertions'] if a['type']=='DENOTES')
    candidate['nodes'].append({'id':'svc.other','kind':'Entity','type':'service','label':'Other'})
    second={**deepcopy(name),'id':'different','to':'svc.other'}
    candidate['assertions'].append(second)
    review={'snapshot_hash':sha(json.dumps(candidate,sort_keys=True)),'reviewed_by':'fixture',
            'decisions':{name['id']:'accepted',second['id']:'accepted'}}
    with pytest.raises(ValueError,match='Conflicting accepted identity'): project_release(candidate,'test',review)


def test_owner_policy_feed_is_explicit_reviewed_and_selector_checked():
    candidate=bundle()
    candidate['sources'][0]['capabilities']={'contract':{'filters':['repo']}}
    candidate['nodes'].append({'id':'domain.pay','kind':'Entity','type':'domain','label':'Payments'})
    declaration={'declarations':[{'owner':'fixture-owner','source_id':'hub','visibility_groups':['readers'],
        'memberships':[{'entity_id':'svc.pay','parent_id':'domain.pay'}],
        'authority':[{'entity_id':'domain.pay','fact_kind':'implementation'}],
        'procedures':[{'procedure_id':'ask-code','version':1,
                       'trigger':{'entity_member_of':'domain.pay','fact_kind_needed':'implementation'},
                       'action':{'must_consult':'hub','selector':{'repo':'repo:pay'}}}]}]}
    apply_owner_declarations(candidate,declaration)
    unreviewed=Release.model_validate(project_release(candidate,'test'))
    assert not RelationStore(unreviewed).member_of('svc.pay') and not unreviewed.procedures
    decisions={a['id']:'accepted' for a in candidate['assertions'] if a['type'] in ('MEMBER_OF','APPLIES_TO')}
    reviewed=Release.model_validate(project_release(candidate,'test',{
        'snapshot_hash':sha(json.dumps(candidate,sort_keys=True)),'reviewed_by':'fixture-reviewer','decisions':decisions}))
    assert RelationStore(reviewed).member_of('svc.pay') == ['domain.pay']
    assert reviewed.procedures[0].attested_by=='fixture-reviewer'
    assert reviewed.review_binding['snapshot_sha256'] == sha(json.dumps(candidate,sort_keys=True))
    bad=bundle();bad['sources'][0]['capabilities']={'contract':{'filters':['repo']}}
    declaration['declarations'][0]['procedures'][0]['action']['selector']['repo']='repo:missing'
    with pytest.raises(ValueError,match='does not match'): apply_owner_declarations(bad,declaration)


def test_repeated_support_does_not_create_duplicate_name_candidates():
    first=artifact();second=deepcopy(first);second['artifact_id']='b'
    candidate=propose([{'source_id':'hub','snapshot_id':'s1','complete_for_access_context':True,
                        'capabilities':{},'artifacts':[first,second]}])
    decisions={a['id']:'accepted' for a in candidate['assertions'] if a['type']=='DENOTES'}
    release=Release.model_validate(project_release(candidate,'test',{
        'snapshot_hash':sha(json.dumps(candidate,sort_keys=True)),'reviewed_by':'fixture','decisions':decisions}))
    for backend in (RelationStore,TableStore):
        assert len(backend(release).denotes(('payment','authorization')))==1


def test_review_cannot_grant_itself_authority_or_cross_source_scope():
    candidate = bundle()
    assertion = next(a for a in candidate['assertions'] if a['type'] == 'ABOUT')
    review = {'snapshot_hash': sha(json.dumps(candidate, sort_keys=True)),
              'reviewed_by': 'reviewer', 'decisions': {assertion['id']: 'accepted'},
              'grants': [{'reviewer': 'reviewer', 'source_id': 'hub', 'edge_types': ['ABOUT']}]}
    with pytest.raises(ValueError, match='scoped delegation'):
        review_bundle(candidate, review)
    for source, edges, entities in [('other', ['ABOUT'], []), ('hub', ['DENOTES'], []),
                                    ('hub', ['ABOUT'], ['svc.other'])]:
        policy = {'grants': [{'reviewer': 'reviewer', 'source_id': source,
                             'edge_types': edges, 'entity_ids': entities}]}
        with pytest.raises(ValueError, match='scoped delegation'):
            review_bundle(candidate, review, delegations=policy)
    reviewed = review_bundle(candidate, review, delegations={'grants': [
        {'reviewer': 'reviewer', 'source_id': 'hub', 'edge_types': ['ABOUT'], 'entity_ids': ['svc.pay']}]})
    assert next(a for a in reviewed['assertions'] if a['id'] == assertion['id'])['status'] == 'accepted'


def test_authority_is_carried_in_the_exact_reviewed_release():
    candidate = bundle()
    candidate['nodes'].append({'id': 'domain.pay', 'kind': 'Entity', 'type': 'domain', 'label': 'Payments'})
    apply_owner_declarations(candidate, {'declarations': [
        {'owner': 'fixture-owner', 'source_id': 'hub', 'visibility_groups': ['readers'],
         'authority': [{'entity_id': 'domain.pay', 'fact_kind': 'implementation'}]}]})
    assertion = next(a for a in candidate['assertions'] if a['type'] == 'AUTHORITATIVE_FOR')
    review = {'snapshot_hash': sha(json.dumps(candidate, sort_keys=True)), 'reviewed_by': 'fixture',
              'decisions': {assertion['id']: 'accepted'}}
    release = Release.model_validate(project_release(candidate, 'test', review))
    assert release.authority_assertions == [{**assertion, 'status': 'accepted', 'reviewed_by': 'fixture'}]
    assert release.review_binding['review_sha256'] == sha(json.dumps(review, sort_keys=True))
    assert authority_for(release,'hub',frozenset({'domain.pay'}),{'implementation'})
    assert authority_for(release,'other',frozenset({'domain.pay'}),{'implementation'}) is None
    assert authority_for(release,'hub',frozenset(),{'implementation'}) is None
    assert authority_for(release,'hub',frozenset({'domain.pay'}),{'procedure'}) is None


def test_owner_declaration_cannot_spoof_a_known_source_owner():
    candidate = bundle()
    declaration = {'declarations': [{'source_id': 'hub', 'owner': 'untrusted', 'memberships': []}]}
    with pytest.raises(ValueError, match='not registered'):
        _apply_owner_declarations(candidate, declaration, owner_registry={'source_owners': {'hub': 'fixture-owner'}})


def test_scoped_proposer_still_cannot_approve_its_own_assertion():
    candidate=bundle()
    assertion=next(a for a in candidate['assertions'] if a['type']=='ABOUT')
    assertion['proposed_by']='fixture'
    review=dict(snapshot_hash=sha(json.dumps(candidate,sort_keys=True)),reviewed_by='fixture',
                decisions={assertion['id']:'accepted'})
    with pytest.raises(ValueError,match='own assertion'):
        project_release(candidate,'test',review)
