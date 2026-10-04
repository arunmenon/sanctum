"""Source-neutral ontology harvesting: snapshots, grounded proposals, review projection.

Search is not inventory. Connectors must explicitly report pagination, completeness,
snapshot consistency and visibility; incomplete snapshots never imply deletion.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Optional, Protocol

from pydantic import BaseModel, ConfigDict, Field


def sha(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class HarvestArtifact(BaseModel):
    model_config = ConfigDict(extra='forbid')
    source_id: str
    artifact_id: str
    native_ref: str
    version: str
    content_hash: str
    title: str
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    visibility_groups: list[str]
    principal: Optional[str] = None


@dataclass(frozen=True)
class InventoryPage:
    items: list[dict[str, Any]]
    next_cursor: Optional[str]
    snapshot_id: str
    complete: bool


class HarvestConnector(Protocol):
    source_id: str
    capabilities: dict[str, Any]
    async def inventory(self, cursor: Optional[str]) -> InventoryPage: ...
    async def fetch(self, item: dict[str, Any]) -> HarvestArtifact: ...


async def collect(connector: HarvestConnector, max_pages: int = 1000) -> dict:
    artifacts, seen, cursors = [], set(), set()
    cursor, snapshot, complete = None, None, False
    for _ in range(max_pages):
        page = await connector.inventory(cursor)
        if not page.snapshot_id or (snapshot and snapshot != page.snapshot_id):
            raise ValueError('Inventory changed during scan; retry a fresh snapshot')
        snapshot = page.snapshot_id
        for item in page.items:
            artifact = await connector.fetch(item)
            if artifact.source_id != connector.source_id or sha(artifact.text) != artifact.content_hash:
                raise ValueError('Fetched source/hash mismatch')
            key = (artifact.artifact_id, artifact.version)
            if key in seen:
                raise ValueError('Duplicate artifact/version in inventory')
            seen.add(key)
            artifacts.append(artifact.model_dump())
        if page.next_cursor is None:
            complete = page.complete
            break
        if page.next_cursor in cursors:
            raise ValueError('Inventory cursor cycle')
        cursors.add(page.next_cursor)
        cursor = page.next_cursor
    else:
        raise ValueError('Inventory page limit exceeded')
    return {'source_id': connector.source_id, 'snapshot_id': snapshot,
            'complete_for_access_context': complete, 'capabilities': connector.capabilities,
            'artifacts': artifacts, 'deletion_inference_allowed': False}


class EvidenceRef(BaseModel):
    model_config = ConfigDict(extra='forbid')
    source_id: str
    artifact_id: str
    version: str
    content_hash: str
    field: str
    start: int
    end: int
    quote: str


def evidence(artifact: dict, field: str, quote: str) -> dict:
    if field not in ('text', 'title', 'metadata'):
        raise ValueError('Unsupported evidence field')
    value = json.dumps(artifact['metadata'], sort_keys=True, ensure_ascii=False) if field == 'metadata' else artifact[field]
    if not quote.strip() or quote not in value:
        raise ValueError('Proposed evidence is not an exact source substring')
    start = value.index(quote)
    return EvidenceRef(source_id=artifact['source_id'], artifact_id=artifact['artifact_id'],
                       version=artifact['version'], content_hash=artifact['content_hash'],
                       field=field, start=start, end=start+len(quote), quote=quote).model_dump()


ENDPOINTS = {'DENOTES': ('Term', 'Entity'), 'SELECTS_FOR': ('Term', 'Entity'),
             'PARENT': ('Term', 'Term'), 'MEMBER_OF': ('Entity', 'Entity'),
             'ABOUT': ('Artifact', 'Entity'), 'COVERS': ('Source', 'Entity'),
             'AUTHORITATIVE_FOR': ('Source', 'Entity'), 'APPLIES_TO': ('Procedure', 'Entity')}


def validate(bundle: dict) -> None:
    nodes = {n['id']: n for n in bundle['nodes']}
    if len(nodes) != len(bundle['nodes']):
        raise ValueError('Duplicate ontology node')
    artifacts = {(a['source_id'], a['artifact_id'], a['version']): a
                 for s in bundle['sources'] for a in s['artifacts']}
    artifacts.update({(a['source_id'], a['artifact_id'], a['version']): a for a in bundle.get('declaration_records',[])})
    ids = set()
    accepted_names = {}
    for assertion in bundle['assertions']:
        if assertion['id'] in ids:
            raise ValueError('Duplicate assertion')
        ids.add(assertion['id'])
        kinds = ENDPOINTS.get(assertion['type'])
        if not kinds or any(nodes.get(assertion[k], {}).get('kind') != kind for k,kind in zip(('from','to'), kinds)):
            raise ValueError('Invalid ontology edge endpoints')
        if assertion['status'] not in ('proposed', 'accepted', 'rejected'):
            raise ValueError('Invalid assertion review state')
        if assertion['status'] == 'accepted' and not assertion.get('reviewed_by'):
            raise ValueError('Accepted assertion requires recorded reviewer')
        for ref in assertion['evidence']:
            artifact = artifacts.get((ref['source_id'], ref['artifact_id'], ref['version']))
            if not artifact or artifact['content_hash'] != ref['content_hash']:
                raise ValueError('Unknown or stale evidence')
            regenerated = evidence(artifact, ref['field'], ref['quote'])
            if regenerated != ref:
                raise ValueError('Evidence span mismatch')
        if not assertion['evidence']:
            raise ValueError('Assertion requires source provenance')
        if assertion['type'] == 'DENOTES' and assertion['status'] == 'accepted':
            term = nodes[assertion['from']]
            key = (term['source_id'], term['namespace'], term['label'].casefold())
            if key in accepted_names and accepted_names[key] != assertion['to']:
                raise ValueError('Conflicting accepted identity in one scope')
            accepted_names[key] = assertion['to']
    parents = {}
    for edge in bundle['assertions']:
        if edge['type'] == 'PARENT' and edge['status'] != 'rejected':
            parents.setdefault(edge['from'], []).append(edge['to'])
    def visit(node, stack):
        if node in stack:
            raise ValueError('Native structure cycle')
        for parent in parents.get(node, []):
            visit(parent, stack | {node})
    for node in parents:
        visit(node, set())


def propose(snapshots: list[dict]) -> dict:
    """Structural source proposals only; semantic extraction is a separately grounded stage."""
    nodes, assertions, artifacts = {}, [], []
    def node(record):
        prior = nodes.get(record['id'])
        if prior and prior != record:
            raise ValueError(f'Conflicting canonical node: {record["id"]}')
        nodes[record['id']] = record
    def edge(kind, origin, target, ref, **attrs):
        payload = {'type': kind, 'from': origin, 'to': target, 'evidence': [ref], **attrs}
        assertions.append({'id': 'assertion-'+sha(json.dumps(payload, sort_keys=True))[:24],
                           'status': 'proposed', 'reviewed_by': None, **payload})
    node({'id': 'entity:unknown', 'kind': 'Entity', 'type': 'other', 'label': 'Unknown subject'})
    for snapshot in snapshots:
        source = snapshot['source_id']
        node({'id': 'source:'+source, 'kind': 'Source', 'label': source,
              'capabilities': snapshot['capabilities'], 'snapshot_id': snapshot['snapshot_id'],
              'coverage': {'declared': 'unknown', 'measured': 'unknown',
                           'inventory_count': len(snapshot['artifacts']),
                           'complete_for_access_context': snapshot['complete_for_access_context']}})
        for artifact in snapshot['artifacts']:
            aid = source+':'+artifact['artifact_id']+'@'+artifact['version']
            node({'id': aid, 'kind': 'Artifact', 'source_id': source, 'artifact_id': artifact['artifact_id'],
                  'version': artifact['version'], 'content_hash': artifact['content_hash']})
            artifacts.append(artifact)
            metadata = artifact['metadata']
            container = metadata.get('container')
            namespace = container['id'] if container else source
            if container:
                selector = metadata.get('harvest_selector', {})
                tid = 'place:'+source+':'+container['id']+':'+sha(json.dumps(selector, sort_keys=True))[:12]
                node({'id': tid, 'kind': 'Term', 'source_id': source, 'namespace': namespace,
                      'label': container['name'], 'native_id': metadata.get('harvest_location', container['id']),
                      'term_kind': 'place', 'selector': selector})
                place_term_id = tid
                location = metadata.get('harvest_location')
                if location and source == 'dochub' and container['id'].startswith('collection.'):
                    parent_id = 'native-place:'+source+':'+location
                    node({'id': parent_id, 'kind': 'Term', 'source_id': source, 'namespace': source,
                          'label': location, 'native_id': location, 'term_kind': 'place',
                          'selector': {'space': location}})
                    edge('PARENT', tid, parent_id, evidence(artifact, 'metadata', json.dumps(location)),
                         basis='source_space_and_collection_structure')
            subjects = metadata.get('services', []) + metadata.get('domains', [])
            for subject in subjects:
                eid = subject['id']
                node({'id': eid, 'kind': 'Entity', 'type': 'service' if eid.startswith('svc.') else 'domain',
                      'label': subject['name']})
                ref = evidence(artifact, 'metadata', json.dumps(subject, sort_keys=True, ensure_ascii=False))
                tid = 'name:'+source+':'+namespace+':'+eid
                node({'id': tid, 'kind': 'Term', 'source_id': source, 'namespace': namespace,
                      'label': subject['name'], 'native_id': eid, 'term_kind': 'name'})
                # Structured subject metadata supplies proposed ABOUT, never proof of identity or coverage.
                edge('ABOUT', aid, eid, ref, basis='source_subject_metadata')
                edge('DENOTES', tid, eid, ref, basis='source_subject_metadata_requires_review')
                if container and metadata.get('harvest_selector'):
                    edge('SELECTS_FOR', place_term_id, eid, ref,
                         basis='observed_location_subject_association_requires_review')
            if not subjects:
                edge('ABOUT', aid, 'entity:unknown', evidence(artifact, 'title', artifact['title']), basis='no_attributed_subject')
    # Stable dedup across multiple records, while retaining all distinct support assertions.
    assertions = list({a['id']: a for a in assertions}.values())
    bundle = {'schema_version': 1, 'status': 'candidate_not_active', 'nodes': list(nodes.values()),
              'assertions': assertions, 'sources': snapshots, 'observations': [],
              'authority': [], 'procedures': [], 'unknown_coverage': [s['source_id'] for s in snapshots]}
    validate(bundle)
    return bundle


def apply_semantic_results(bundle: dict, results: list[dict]) -> dict:
    """LLMs can propose ABOUT and native names, never approve identity or authority."""
    nodes = {n['id']: n for n in bundle['nodes']}
    artifacts = {}
    for snapshot in bundle['sources']:
        for artifact in snapshot['artifacts']:
            artifacts.setdefault((artifact['source_id'], artifact['artifact_id']), []).append(artifact)
    rejected = []
    for result in results:
        for proposal in result.get('proposals', []):
            try:
                matches = artifacts[(proposal['source_id'], proposal['artifact_id'])]
                if proposal.get('version') is not None:
                    matches = [a for a in matches if a['version'] == proposal['version']]
                if proposal.get('content_hash') is not None:
                    matches = [a for a in matches if a['content_hash'] == proposal['content_hash']]
                # Legacy receipts omit version. They are safe only when the input
                # identifies exactly one record; never pick an arbitrary version.
                if len(matches) != 1:
                    raise ValueError('Semantic proposal requires an unambiguous artifact version and hash')
                artifact = matches[0]
                target = proposal['entity_id']
                if nodes.get(target, {}).get('kind') != 'Entity' or target == 'entity:unknown':
                    raise ValueError('Unknown semantic entity')
                ref = evidence(artifact, proposal['field'], proposal['quote'])
                if proposal['relation'] == 'ABOUT':
                    origin = artifact['source_id']+':'+artifact['artifact_id']+'@'+artifact['version']
                elif proposal['relation'] == 'DENOTES':
                    label = proposal['label']
                    if not label.strip() or label.casefold() not in proposal['quote'].casefold():
                        raise ValueError('Native name not present in quoted evidence')
                    namespace = artifact['metadata'].get('container', {}).get('id', artifact['source_id'])
                    origin = 'name:'+artifact['source_id']+':'+namespace+':'+sha(label)[:16]
                    nodes[origin] = {'id': origin, 'kind': 'Term', 'source_id': artifact['source_id'],
                                     'namespace': namespace, 'label': label, 'native_id': origin, 'term_kind': 'name'}
                else:
                    raise ValueError('LLM relation not permitted')
                payload = {'type': proposal['relation'], 'from': origin, 'to': target,
                           'evidence': [ref], 'basis': 'llm_content_proposal'}
                assertion = {'id': 'assertion-'+sha(json.dumps(payload, sort_keys=True))[:24],
                             'status': 'proposed', 'reviewed_by': None, **payload}
                if assertion['id'] not in {a['id'] for a in bundle['assertions']}:
                    bundle['assertions'].append(assertion)
            except (ValueError, KeyError, TypeError) as error:
                rejected.append({'proposal': proposal, 'reason': str(error)})
    bundle['nodes'] = list(nodes.values())
    bundle['rejected_proposals'] = rejected
    validate(bundle)
    return bundle


def apply_owner_declarations(bundle: dict, document: dict, *, owner_registry: Optional[dict] = None) -> dict:
    """Owner inputs are proposed, provenance-backed policy; still require explicit review."""
    from .memory import MemoryProcedure
    nodes = {n['id']: n for n in bundle['nodes']}
    for declaration in document.get('declarations', []):
        if not declaration.get('owner') or declaration['source_id'] not in {s['source_id'] for s in bundle['sources']}:
            raise ValueError('Declaration requires owner and harvested source')
        if (owner_registry or {}).get('source_owners', {}).get(declaration['source_id']) != declaration['owner']:
            raise ValueError('Declaration owner is not registered for source')
        text = json.dumps(declaration, sort_keys=True, ensure_ascii=False)
        record = HarvestArtifact(source_id='owner-manifest', artifact_id='declaration-'+sha(text)[:20],
            native_ref='owner declaration',version='1',content_hash=sha(text),title='Owner declaration',
            text=text,metadata={},visibility_groups=declaration.get('visibility_groups',[])).model_dump()
        bundle.setdefault('declaration_records',[]).append(record)
        ref = evidence(record,'text',text)
        def add(kind, origin, target, **attributes):
            payload={'type':kind,'from':origin,'to':target,'evidence':[ref],
                     'basis':'explicit_owner_declaration_requires_review',**attributes}
            bundle['assertions'].append({'id':'assertion-'+sha(json.dumps(payload,sort_keys=True))[:24],
                                         'status':'proposed','reviewed_by':None,**payload})
        for membership in declaration.get('memberships',[]):
            add('MEMBER_OF',membership['entity_id'],membership['parent_id'])
        for authority in declaration.get('authority',[]):
            if authority['fact_kind'] not in ('implementation','procedure','observed','reference','session','session_history'):
                raise ValueError('Unknown authority fact kind')
            add('AUTHORITATIVE_FOR','source:'+declaration['source_id'],authority['entity_id'],fact_kind=authority['fact_kind'])
        for procedure in declaration.get('procedures',[]):
            policy={**procedure,'status':'proposed','owner':declaration['owner'],'attested_by':'unreviewed'}
            MemoryProcedure.model_validate(policy)
            if policy['action']['must_consult'] not in {s['source_id'] for s in bundle['sources']}:
                raise ValueError('Procedure references an unharvested source')
            source=next(s for s in bundle['sources'] if s['source_id']==policy['action']['must_consult'])
            for key,value in policy['action'].get('selector',{}).items():
                if key not in source['capabilities'].get('contract',{}).get('filters',[]) and key!='path_prefix':
                    raise ValueError('Procedure selector unsupported')
                if not any(a['metadata'].get('harvest_selector',{}).get(key)==value for a in source['artifacts']):
                    raise ValueError('Procedure selector does not match harvested structure')
            pid='procedure:'+policy['procedure_id']
            if pid in nodes: raise ValueError('Duplicate procedure declaration')
            nodes[pid]={'id':pid,'kind':'Procedure','policy':policy}
            add('APPLIES_TO',pid,policy['trigger']['entity_member_of'])
    bundle['nodes']=list(nodes.values())
    bundle['owner_declarations']=document
    bundle['owner_registry_binding']=sha(json.dumps(owner_registry,sort_keys=True))
    validate(bundle)
    return bundle


def review_bundle(bundle: dict, review: Optional[dict] = None, *, delegations: Optional[dict] = None) -> dict:
    """Bind explicit reviewer decisions to exactly one candidate snapshot."""
    from copy import deepcopy
    bundle = deepcopy(bundle)
    if review:
        if review.get('snapshot_hash') != sha(json.dumps(bundle, sort_keys=True)) or not review.get('reviewed_by'):
            raise ValueError('Review must name reviewer and exact candidate snapshot hash')
        decisions = review.get('decisions', {})
        known = {a['id'] for a in bundle['assertions']}
        if set(decisions) - known:
            raise ValueError('Review names unknown assertions')
        # Delegations are a separately trusted policy input, never a grant
        # embedded in the review being evaluated.
        grants = (delegations or {}).get('grants', [])
        nodes = {node['id']: node for node in bundle['nodes']}
        for assertion in bundle['assertions']:
            if assertion['id'] in decisions:
                if decisions[assertion['id']] not in ('accepted', 'rejected'):
                    raise ValueError('Invalid review decision')
                if decisions[assertion['id']] == 'accepted' and assertion.get('proposed_by') == review['reviewed_by']:
                    raise ValueError('Proposer cannot approve its own assertion')
                origin = nodes[assertion['from']]
                source = origin.get('source_id')
                if origin['kind'] == 'Source':
                    source = origin['id'].removeprefix('source:')
                if source is None:
                    # Membership and procedure declarations carry their source
                    # in the exact quoted owner declaration record.
                    records = {r['artifact_id']: r for r in bundle.get('declaration_records', [])}
                    for ref in assertion['evidence']:
                        record = records.get(ref['artifact_id'])
                        if record:
                            source = json.loads(record['text'])['source_id']
                            break
                if not any(g.get('reviewer') == review['reviewed_by']
                           and g.get('source_id') == source
                           and assertion['type'] in g.get('edge_types', [])
                           and (not g.get('entity_ids') or assertion['to'] in g['entity_ids'])
                           for g in grants):
                    raise ValueError('Reviewer lacks a scoped delegation for assertion')
                assertion['status'] = decisions[assertion['id']]
                assertion['reviewed_by'] = review['reviewed_by']
    validate(bundle)
    return bundle


def project_release(bundle: dict, release_id: str, review: Optional[dict] = None, *, delegations: Optional[dict] = None) -> dict:
    """Explicit decisions only. No ACTIVE switch; names absent from review stay proposed."""
    snapshot_hash = sha(json.dumps(bundle, sort_keys=True))
    bundle = review_bundle(bundle,review,delegations=delegations)
    nodes = {n['id']: n for n in bundle['nodes']}
    entities = [{'id': n['id'], 'ref': 'ment-'+sha(n['id'])[:12], 'type': n['type'],
                 'label': n['label'], 'member_of': []} for n in bundle['nodes'] if n['kind'] == 'Entity']
    terms, places = [], []
    for a in bundle['assertions']:
        if a['type'] not in ('DENOTES', 'SELECTS_FOR', 'MEMBER_OF'):
            continue
        if a['type'] == 'MEMBER_OF':
            if a['status'] == 'accepted':
                next(e for e in entities if e['id'] == a['from'])['member_of'].append(a['to'])
            continue
        term = nodes[a['from']]
        common = {'source': term['source_id'], 'status': a['status'], 'version': 1,
                  'reviewed_by': a['reviewed_by'] or 'unreviewed'}
        if a['type'] == 'DENOTES':
            terms.append({**common, 'namespace': term['namespace'], 'native_id': term['native_id'],
                          'label': term['label'], 'kind': 'name', 'denotes': a['to']})
        else:
            for key, value in term['selector'].items():
                places.append({**common, 'filter': key, 'value': value, 'place': term['native_id'], 'selects_for': a['to']})
    artifact_records = []
    for snapshot in bundle['sources']:
        for artifact in snapshot['artifacts']:
            aid = artifact['source_id']+':'+artifact['artifact_id']+'@'+artifact['version']
            bindings = [{'entity_id': None if a['to']=='entity:unknown' else a['to'], 'status': a['status'],
                         'provenance': {'assertion_id': a['id'], 'release_id': release_id,
                                        'reviewed_by': a['reviewed_by'], 'evidence': a['evidence']}}
                        for a in bundle['assertions'] if a['type']=='ABOUT' and a['from']==aid]
            artifact_records.append({k: artifact[k] for k in ('source_id','artifact_id','version','content_hash','visibility_groups','principal')})
            artifact_records[-1]['subjects'] = bindings
    # Multiple supporting artifacts must not multiply one native identity/filter assertion.
    def compact(records, fields):
        selected={}
        priority={'rejected':0,'proposed':1,'accepted':2}
        for record in records:
            key=tuple(record[f] for f in fields)
            if key not in selected or priority[record['status']]>priority[selected[key]['status']]:
                selected[key]=record
        return list(selected.values())
    terms=compact(terms,('source','namespace','native_id','label','denotes'))
    places=compact(places,('source','filter','value','place','selects_for'))
    descriptors = {}
    for snapshot in bundle['sources']:
        records = snapshot['artifacts']
        native_locations = sorted({a['metadata'].get('harvest_location','') for a in records})
        kinds = sorted({a['metadata'].get('harvest_artifact_kind','unspecified') for a in records})
        descriptors[snapshot['source_id']] = {'text':
            f"Observed {len(records)} readable source records; artifact types {', '.join(kinds)}; "
            f"{len(native_locations)} native locations. Semantic coverage and freshness beyond this snapshot unknown. "
            "Versions and source review statuses retained; storage does not establish deployment or authority.",
            'pinned': release_id}
    procedures=[]
    for assertion in bundle['assertions']:
        if assertion['type']=='APPLIES_TO' and assertion['status']=='accepted':
            policy={**nodes[assertion['from']]['policy'],'status':'accepted','attested_by':assertion['reviewed_by']}
            procedures.append(policy)
    return {'release_id': release_id, 'schema_version': 1, 'status': 'candidate',
            'artifact_subject_bindings_required': True,
            'note': 'Harvested candidates; only explicit reviewed assertions can operate. No activation performed.',
            'entities': entities, 'terms': terms, 'places': places, 'contexts': [], 'procedures': procedures,
            'relations': [{'from': a['from'], 'type': 'PARENT', 'to': a['to'], 'status': a['status']}
                          for a in bundle['assertions'] if a['type'] == 'PARENT'],
            'artifacts': artifact_records,
            'authority_assertions': [a for a in bundle['assertions']
                                     if a['type'] == 'AUTHORITATIVE_FOR' and a['status'] == 'accepted'],
            'review_binding': {'snapshot_sha256': snapshot_hash,
                               'review_sha256': sha(json.dumps(review, sort_keys=True)),
                               'delegations_sha256': sha(json.dumps(delegations, sort_keys=True)),
                               **({'owner_registry_sha256': bundle['owner_registry_binding']}
                                  if bundle.get('owner_registry_binding') else {})},
            'descriptors': descriptors}
