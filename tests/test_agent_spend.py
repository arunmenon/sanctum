import json

import pytest

from sanctum_run.spend import SpendLedger,SpendNotReady


def ledger(tmp_path):
    path=tmp_path/'spend.json'
    path.write_text(json.dumps(dict(approved=True,approval_ref='fixture-only-owner-record',
        pricing_basis='fixture, no provider inference',ceiling_usd=1,reservations={})))
    return SpendLedger(path)


def test_reservation_limits_inflight_and_duplicate_attempts(tmp_path):
    spend=ledger(tmp_path)
    spend.reserve('a',.6)
    with pytest.raises(SpendNotReady,match='insufficient'):
        spend.reserve('b',.5)
    with pytest.raises(SpendNotReady,match='already exists'):
        spend.reserve('a',.1)
    spend.reconcile('a',.1)
    spend.reserve('b',.5)


def test_unknown_cost_stops_until_real_receipt(tmp_path):
    spend=ledger(tmp_path);spend.reserve('a',.2);spend.reconcile('a',None)
    with pytest.raises(SpendNotReady,match='unknown usage'):
        spend.reserve('b',.1)
    assert json.loads(spend.path.read_text())['reservations']['a']['reserved_usd']=='0.2'
    spend.reconcile('a',.15);spend.reserve('b',.1)


def test_missing_approval_and_overrun_stop_dispatch(tmp_path):
    spend=SpendLedger(tmp_path/'absent.json')
    with pytest.raises(SpendNotReady,match='missing'):
        spend.reserve('a',.1)
    spend=ledger(tmp_path)
    content=json.loads(spend.path.read_text());content['approved']=False;spend.path.write_text(json.dumps(content))
    with pytest.raises(SpendNotReady,match='approval'):
        spend.reserve('a',.1)
    content['approved']=True;spend.path.write_text(json.dumps(content))
    spend.reserve('a',.1);spend.reconcile('a',.2)
    with pytest.raises(SpendNotReady,match='overrun'):
        spend.reserve('b',.1)


@pytest.mark.parametrize('value',[-1,float('nan'),float('inf'),True])
def test_invalid_exposure_is_never_reserved(tmp_path,value):
    with pytest.raises(SpendNotReady):
        ledger(tmp_path).reserve('a',value)
