"""Common evidence normalization and ordered atomic delivery for both arms.

Only displayed text is credited as delivered. FTS excerpts can be discontinuous;
ambiguous excerpt coordinates remain explicitly uncitable until a full read.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

import anyio

from sanctum_eval.budget import serialized_evidence_tokens


class DeliveryClosed(RuntimeError):
    pass


class EvidenceNormalizer:
    def __init__(self, rows: list[dict]):
        self.rows = {(r['source_id'], r['artifact_id'], r['version']): r for r in rows}

    def _passage(self, source: str, record: dict) -> list[dict]:
        aid = record.get('artifact_id')
        version = record.get('version', record.get('source_version'))
        row = self.rows.get((source, aid, version))
        text = record.get('text', record.get('snippet'))
        if not isinstance(text, str):
            return [dict(kind='metadata', source_id=source, metadata=record, citable=False)]
        metadata = {k:v for k,v in record.items() if k not in ('text','snippet','exact_token_count','tokenizer_id','evidence_id')}
        # The delivery controller assigns the sole public citation ID. Original
        # router IDs remain in private receipts, not a competing citation field.
        # Preserve all source-described metadata; do not promote it into authority.
        if 'span' in record:
            fragments = [text]
        elif 'snippet' in record:
            fragments = [f for f in text.split(' ... ') if f]
        else:
            fragments = [text]
        units = []
        for fragment in fragments:
            start = None
            if row is not None:
                if 'span' in record:
                    s,e = record['span']['start'],record['span']['end']
                    if row['text'][s:e] == fragment:
                        start = s
                elif row['text'].count(fragment) == 1 or row['text'] == fragment:
                    start = row['text'].find(fragment)
            unit = dict(kind='passage',source_id=source,artifact_id=aid,version=version,
                        text=fragment,metadata=metadata,citable=start is not None)
            if start is not None:
                unit.update(start=start,end=start+len(fragment),
                    content_sha256=hashlib.sha256(row['text'].encode()).hexdigest())
            units.append(unit)
        return units

    def normalize(self, source: str | None, payload: dict) -> list[dict]:
        if source is None:  # Sanctum response
            units = []
            for record in payload.get('evidence', []):
                units.extend(self._passage(record['source_id'], record))
            context = {k:v for k,v in payload.items() if k != 'evidence'}
        else:
            if 'artifact' in payload:
                units = self._passage(source,payload['artifact'])
                context = {k:v for k,v in payload.items() if k != 'artifact'}
            elif 'results' in payload:
                units = [u for record in payload['results'] for u in self._passage(source,record)]
                context = {k:v for k,v in payload.items() if k != 'results'}
            else:
                units = []
                context = payload
        # Even source-bearing lists, counts, routing summaries and errors are
        # charged; an operational error can be represented by the adapter instead.
        if context:
            units.append(dict(kind='metadata',source_id=source,metadata=context,citable=False))
        return units


class DeliveryBudget:
    def __init__(self, cumulative: int, per_response: int, tokenizer: str = 'cl100k_base'):
        if not 0 < per_response <= cumulative:
            raise ValueError('invalid evidence limits')
        self.cumulative,self.per_response,self.tokenizer = cumulative,per_response,tokenizer
        self.used = 0
        self.records: list[dict] = []
        self._issued = self._next = 0
        self._condition = anyio.Condition()
        self._closed = False

    async def issue(self) -> int:
        async with self._condition:
            if self._closed:
                raise DeliveryClosed('session closed')
            number=self._issued
            self._issued+=1
            return number

    @property
    def remaining(self):
        return max(0,self.cumulative-self.used)

    async def deliver(self, sequence: int, units: list[dict], *, error: str | None = None) -> dict:
        async with self._condition:
            if not 0 <= sequence < self._issued:
                raise ValueError('unissued call sequence')
            while sequence > self._next and not self._closed:
                await self._condition.wait()
            if self._closed:
                raise DeliveryClosed('session closed')
            if sequence != self._next:
                raise ValueError('call sequence already delivered')
            chosen,omitted = [],[]
            allowance=min(self.remaining,self.per_response)
            for index,unit in enumerate(units):
                candidate={**unit,'evidence_id':f'call-{sequence}-unit-{index}'}
                if serialized_evidence_tokens(chosen+[candidate],self.tokenizer) <= allowance:
                    chosen.append(candidate)
                else:
                    omitted.append(index)
            cost=serialized_evidence_tokens(chosen,self.tokenizer) if chosen else 0
            self.used+=cost
            result=dict(evidence=chosen,evidence_tokens=cost,cumulative_evidence_tokens=self.used,
                        omitted_unit_indices=omitted,budget_exhausted=bool(omitted) or self.remaining==0)
            if error:
                result['error']={'code':error}
            self.records.append(dict(sequence=sequence,**result))
            self._next+=1
            self._condition.notify_all()
            return result

    async def close(self):
        async with self._condition:
            self._closed=True
            self._condition.notify_all()
