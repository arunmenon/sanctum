"""Jev owns selection, including empty selections, independently of rule authority."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import anyio
import pytest

from sanctum_contracts import RetrieveRequest
from sanctum_ref.config import load_arm
from sanctum_ref.pipeline import Retriever
from sanctum_ref.routing import SourcePlan
from sanctum_ref.providers.http_systemone import SystemOneHttpAdapter
from sanctum_ref.providers.interface import d2_request
from sanctum_systemone import CallOutcome

ROOT = Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('selected', [set(), {'dochub'}, {'codehub', 'memoryhub'}, {'codehub','dochub','skillhub','memoryhub'}])
def test_selection_is_not_overridden(selected):
    arm = replace(load_arm(ROOT/'configs/matrix.yaml', 'C5'), routing='jev_unconstrained')
    class Provider:
        async def decide_batch(self, requests, port, deadline_ms, *, raw_selection):
            assert raw_selection
            assert {r.candidate_ids[0] for r in requests} == {'codehub','dochub','skillhub','memoryhub'}
            return [SimpleNamespace(status=SimpleNamespace(value='answered'), value={'call':r.candidate_ids[0] in selected}) for r in requests]
    plans = [SourcePlan(h, None, True, 'called', [], required=False) for h in ['codehub','dochub','skillhub','memoryhub']]
    retriever = Retriever(arm, None, provider=Provider())
    async def run():
        await retriever._judge_usefulness(RetrieveRequest(request_id='test',query='q',mode='explore',budget_tokens=4000,deadline_ms=3000), plans, None)
    anyio.run(run)
    assert {p.hub_id for p in plans if p.call} == selected


def test_raw_provider_ignores_missing_calibration():
    # Exercise the actual HTTP adapter decision policy, using a recorded-shape transport double.
    from sanctum_ref.providers.templates import TemplateRegistry, DEFAULT_TEMPLATES
    adapter = object.__new__(SystemOneHttpAdapter)
    adapter.name='test'; adapter._max_calls=1
    adapter.template=lambda kind: TemplateRegistry(DEFAULT_TEMPLATES).resolve(kind)
    adapter._calibration=lambda model: None
    class Transport:
        async def send(self, port, payload, deadline_ms):
            return CallOutcome(provider='test',model='test-model',answers={'d2:dochub':{'noul':0.2},'d2:memoryhub':{'noul':0.8}},calls=1)
    adapter._transport=Transport()
    async def run():
        return await adapter.decide_batch([d2_request(h,'q',3000) for h in ['dochub','memoryhub']],None,3000,raw_selection=True)
    results=anyio.run(run)
    assert [r.value['call'] for r in results] == [False,True]
    assert all(r.value['shadow'] is False and r.calibration is None for r in results)
