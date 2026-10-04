import hashlib

import anyio
import pytest

from sanctum_eval.budget import serialized_evidence_tokens
from sanctum_run.delivery import DeliveryBudget,DeliveryClosed,EvidenceNormalizer


@pytest.fixture
def anyio_backend():
    return 'asyncio'


def test_direct_and_sanctum_displayed_passage_agree():
    text='A timeout returns deferred. A successful response returns scored.'
    normalizer=EvidenceNormalizer([dict(source_id='shipping',artifact_id='a',version='v1',text=text)])
    direct=normalizer.normalize('shipping',{'artifact':dict(artifact_id='a',version='v1',text=text)})[0]
    sanctum=normalizer.normalize(None,{'evidence':[dict(source_id='shipping',artifact_id='a',source_version='v1',text=text,span=dict(start=0,end=len(text)))]})[0]
    for key in ('text','start','end','content_sha256','citable'):
        assert direct[key]==sanctum[key]
    assert direct['content_sha256']==hashlib.sha256(text.encode()).hexdigest()


def test_discontinuous_excerpt_does_not_invent_full_span():
    normalizer=EvidenceNormalizer([dict(source_id='s',artifact_id='a',version='v',text='First. Hidden middle. Last.')])
    units=normalizer.normalize('s',{'results':[dict(artifact_id='a',version='v',snippet='First. ... Last.')]})
    assert [(u['start'],u['end']) for u in units]==[(0,6),(22,27)]
    ambiguous=normalizer.normalize('s',{'artifact':dict(artifact_id='a',version='wrong',text='First.')})[0]
    assert ambiguous['citable'] is False and 'start' not in ambiguous


@pytest.mark.anyio
async def test_router_id_does_not_compete_with_public_delivery_id():
    normalizer=EvidenceNormalizer([dict(source_id='s',artifact_id='a',version='v',text='one')])
    units=normalizer.normalize(None,dict(evidence=[dict(source_id='s',artifact_id='a',
        source_version='v',text='one',span=dict(start=0,end=3),evidence_id='ev-5')]))
    budget=DeliveryBudget(1000,1000)
    delivered=await budget.deliver(await budget.issue(),units)
    assert delivered['evidence'][0]['evidence_id']=='call-0-unit-0'
    assert 'evidence_id' not in delivered['evidence'][0]['metadata']


@pytest.mark.anyio
async def test_parallel_results_deliver_in_invocation_order_and_repeats_count():
    budget=DeliveryBudget(300,300)
    a,b=await budget.issue(),await budget.issue()
    unit=dict(kind='passage',text='x '*80)
    finished=[]
    async def second():
        finished.append(('second',await budget.deliver(b,[unit])))
    async with anyio.create_task_group() as group:
        group.start_soon(second)
        await anyio.sleep(0)
        first=await budget.deliver(a,[unit])
    assert [r['sequence'] for r in budget.records]==[0,1]
    assert budget.used==sum(r['evidence_tokens'] for r in budget.records)
    assert first['evidence'] and finished[0][1]['evidence']


@pytest.mark.anyio
async def test_whole_units_and_metadata_cannot_bypass_budget():
    budget=DeliveryBudget(70,70)
    units=[dict(kind='metadata',metadata={'current_policy':'secret '*500}),dict(kind='passage',text='short')]
    result=await budget.deliver(await budget.issue(),units)
    assert result['omitted_unit_indices']==[0]
    assert result['evidence'][0]['text']=='short'
    assert result['evidence_tokens']==serialized_evidence_tokens(result['evidence'])
    with pytest.raises(ValueError):
        await budget.deliver(0,[])


@pytest.mark.anyio
async def test_close_releases_waiting_delivery():
    budget=DeliveryBudget(100,100)
    await budget.issue();b=await budget.issue()
    stopped=anyio.Event()
    async def waiting():
        with pytest.raises(DeliveryClosed):
            await budget.deliver(b,[])
        stopped.set()
    async with anyio.create_task_group() as group:
        group.start_soon(waiting)
        await anyio.sleep(0)
        await budget.close()
    assert stopped.is_set()
