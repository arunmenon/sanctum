"""Durable approved-budget reservations; unknown usage stops further dispatch."""
import fcntl
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sanctum_run.agent_session import write_atomic


class SpendNotReady(ValueError):
    pass


def amount(value):
    if isinstance(value,bool):
        raise SpendNotReady('invalid spend amount')
    try:
        parsed=Decimal(str(value))
    except InvalidOperation:
        raise SpendNotReady('invalid spend amount') from None
    if not parsed.is_finite() or parsed<0:
        raise SpendNotReady('invalid spend amount')
    return parsed


class SpendLedger:
    def __init__(self,path:Path):
        self.path=path

    def _locked(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        lock=self.path.with_suffix('.lock').open('a')
        fcntl.flock(lock,fcntl.LOCK_EX)
        return lock

    def reserve(self,attempt_id,max_exposure):
        exposure=amount(max_exposure)
        if exposure<=0:
            raise SpendNotReady('positive bounded exposure required')
        with self._locked():
            if not self.path.is_file():
                raise SpendNotReady('approved spend ledger missing')
            ledger=json.loads(self.path.read_text())
            if ledger.get('approved') is not True or not ledger.get('approval_ref') or not ledger.get('pricing_basis'):
                raise SpendNotReady('budget or pricing approval missing')
            reservations=ledger.setdefault('reservations',{})
            if attempt_id in reservations:
                raise SpendNotReady('reservation already exists; do not replay')
            if any(r['state']=='unknown_usage' for r in reservations.values()):
                raise SpendNotReady('unknown usage requires reconciliation')
            if ledger.get('overrun'):
                raise SpendNotReady('observed cost overrun requires reconciliation')
            committed=sum((amount(r['actual_usd'] if r['state']=='reconciled' else r['reserved_usd'])
                           for r in reservations.values()),Decimal(0))
            if committed+exposure>amount(ledger['ceiling_usd']):
                raise SpendNotReady('insufficient unreserved approved budget')
            reservations[attempt_id]=dict(state='reserved',reserved_usd=str(exposure),actual_usd=None)
            write_atomic(self.path,ledger)

    def reconcile(self,attempt_id,actual):
        parsed=None if actual is None else amount(actual)
        with self._locked():
            ledger=json.loads(self.path.read_text())
            reservation=ledger['reservations'][attempt_id]
            if reservation['state'] not in ('reserved','unknown_usage'):
                raise SpendNotReady('receipt already reconciled')
            reservation['state']='unknown_usage' if parsed is None else 'reconciled'
            reservation['actual_usd']=None if parsed is None else str(parsed)
            if parsed is not None and parsed>amount(reservation['reserved_usd']):
                ledger['overrun']=True
            write_atomic(self.path,ledger)
