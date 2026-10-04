"""Package audited synthetic sources for the existing hub loader, separately from base world."""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from sanctum_hubs.corpus import HubRow, HubStore
from sanctum_world.render import hub_capabilities, load_hub_config
from sanctum_world.schema import load_world

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / 'build' / 'pdlc-pilot'
HUBS = ('codehub', 'dochub', 'skillhub', 'memoryhub')
PRINCIPAL = 'pdlc-pilot-reader'
GROUP = 'pdlc-pilot'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def build(out=DEFAULT_OUT, candidate_path=None):
    out = Path(out).resolve()
    if out != DEFAULT_OUT.resolve():
        raise ValueError('This pilot builder writes only build/pdlc-pilot, never the base world')
    candidate_path = Path(candidate_path or ROOT / 'build/pdlc-authoring/pdlc-audited-candidate.json').resolve()
    if candidate_path.parent != (ROOT/'build/pdlc-authoring').resolve():
        raise ValueError('Candidate must come from the private pilot authoring directory')
    candidate = json.loads(candidate_path.read_text())
    if candidate['status'] != 'audited_candidate_packaging_pending':
        raise ValueError('Expected audited candidate')
    if candidate.get('supplement',{}).get('status') not in (None,'source_semantic_review_passed'):
        raise ValueError('Supplement source review remains pending')
    if candidate.get('design_supplement',{}).get('status') not in (None,'source_semantic_review_passed'):
        raise ValueError('Design supplement source review remains pending')
    if candidate.get('design_supplement'):
        record = candidate['design_supplement']
        authoring = ROOT/'build/pdlc-authoring'
        review_bytes = (authoring/'pdlc-design-semantic-review.json').read_bytes()
        review = json.loads(review_bytes)
        if digest(review_bytes) != record['review_sha256'] or review['verdict'] != 'pass_for_readonly_draft':
            raise ValueError('Design review record changed or failed')
        design_bytes = (authoring/'pdlc-designs-repaired-candidate.json').read_bytes()
        if digest(design_bytes) != record['design_candidate_sha256']:
            raise ValueError('Design source changed after review')
        reviewed_docs = {d['path']: d for d in json.loads(design_bytes)['documents']}
        designs = [a for a in candidate['artifacts'] if a.get('document_kind')]
        if len(designs) != record['documents'] or len(designs) != len(review['document_text_hashes']):
            raise ValueError('Design coverage changed after review')
        for design in designs:
            if digest(design['text'].encode()) != review['document_text_hashes'].get(design['path']):
                raise ValueError('Design text changed after review')
            approved = reviewed_docs[design['path']]
            for field in ('title', 'version', 'review_status', 'module_key', 'source_refs', 'related_document_paths'):
                if design.get(field) != approved.get(field):
                    raise ValueError('Design metadata changed after review')
            if design['document_kind'] != approved['kind']:
                raise ValueError('Design kind changed after review')
    hierarchy = candidate['hierarchy']
    nodes = {n['id']: n for n in hierarchy['nodes']}
    mappings = {m['artifact_id']: m for m in hierarchy['mappings']}
    caps = hub_capabilities(load_world(ROOT/'world/world.yaml'), load_hub_config())
    rows = {hub: [] for hub in HUBS}
    provenance = []
    public_ids = set()
    for artifact in candidate['artifacts']:
        mapping = mappings[artifact['artifact_id']]
        hub = mapping['hub']
        if hub not in HUBS:
            raise ValueError('Pilot excludes IncidentHub')
        container = nodes[mapping['container_id']]
        location_node = container
        if hub == 'dochub':
            while location_node['kind'] != 'document_space':
                location_node = nodes[location_node['parent_id']]
        location = ('repo:' if hub == 'codehub' else 'space:' if hub == 'dochub' else 'collection:') + location_node['id'].split('.', 1)[1]
        path = mapping['logical_path']
        version = str(artifact.get('version') or 'unversioned-draft')
        text = artifact['text']
        source_text = text
        fenced = list(re.finditer(r'^```[^\n]*\n(.*?)^```\s*$', text, re.M | re.S))
        packaging = 'source_preserved'
        # A single fenced code source may be unwrapped. Multiple excerpts retain boundaries.
        if hub == 'codehub' and len(fenced) == 1 and not (text[:fenced[0].start()].strip() or text[fenced[0].end():].strip()):
            text = fenced[0].group(1)
            packaging = 'single_code_fence_unwrapped'
        elif hub == 'codehub' and fenced:
            packaging = 'markdown_snippet_boundaries_preserved'
        identity = json.dumps([hub, location, path, version, artifact['title'], text], ensure_ascii=False).encode()
        public_id = 'artifact-' + digest(identity)[:20]
        if public_id in public_ids:
            raise ValueError('Duplicate public artifact identity')
        public_ids.add(public_id)
        def links(ids):
            return [{'id': i, 'name': nodes[i]['name'], 'grounding': nodes[i]['status']} for i in ids]
        ownership = [{'team': nodes[o['team_id']]['name'], 'role': o['role'], 'grounding': o['status']}
                     for o in hierarchy['container_ownership'] if o['container_id'] == container['id']]
        metadata = {
            'revision': 1, 'synthetic': True,
            'review_status': artifact.get('review_status', 'unspecified'),
            'chronology': artifact.get('chronology', ''),
            'container': {'id': container['id'], 'name': container['name'], 'grounding': container['status']},
            'domains': links(mapping['domain_ids']), 'services': links(mapping['service_ids']),
            'related_repositories': links(mapping['related_repo_ids']),
            'container_responsibilities': ownership,
            'packaging': packaging,
            'execution_status': 'source_excerpt_not_complete_executable_package',
            'source_content_sha256': digest(source_text.encode()),
            'published_content_sha256': digest(text.encode()),
            'citation': {'start': 0, 'end': len(text), 'unit': 'unicode_codepoints'},
        }
        if hub == 'skillhub':
            metadata['namespace'] = container['id'].split('.', 1)[1]
        if hub == 'dochub':
            metadata['space'] = location
        if hub == 'memoryhub':
            metadata['principal'] = PRINCIPAL
            metadata['session'] = artifact.get('session') or path
        if artifact.get('source_refs'):
            metadata['related_source_refs'] = artifact['source_refs']
        if artifact.get('document_kind'):
            metadata['document_kind'] = artifact['document_kind']
            metadata['module_key'] = artifact.get('module_key')
            metadata['related_document_paths'] = artifact.get('related_document_paths', [])
            metadata['design_status'] = 'synthetic_draft_unapproved'
        row = HubRow(acl=[GROUP], artifact_id=public_id, environment=None,
                     kind={'codehub': 'code', 'dochub': 'document', 'skillhub': 'procedure', 'memoryhub': 'session'}[hub],
                     location=location, path=path, title=artifact['title'], version=version,
                     metadata=metadata, text=text).model_dump(mode='json')
        serialized = json.dumps(row, ensure_ascii=False)
        if re.search(r'pdlc\.\d{3}|sk-proj-|AIza[\w-]{20,}|introduced_claims|gold_constraints', serialized):
            raise ValueError(f'Private identifier or credential-like content in {public_id}')
        rows[hub].append(row)
        provenance.append({'private_artifact_id': artifact['artifact_id'], 'public_artifact_id': public_id,
                           'hub': hub, 'raw_source': mapping['source'], 'logical_path': path,
                           'source_content_sha256': digest(source_text.encode()),
                           'published_content_sha256': digest(text.encode()), 'packaging': packaging})
    if len(public_ids) != candidate.get('supplement',{}).get('expected_artifacts',96) or len(mappings)!=len(public_ids):
        raise ValueError('Expected complete distinct artifact/mapping coverage')
    if (out/'manifest.json').exists():
        old=(out/'manifest.json').read_bytes()
        history=out/'private/history'/('manifest-'+digest(old)[:20]+'.json')
        history.parent.mkdir(parents=True,exist_ok=True)
        history.write_bytes(old)
    for hub in HUBS:
        folder = out / 'hubs' / hub
        folder.mkdir(parents=True, exist_ok=True)
        (folder/'artifacts.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False, sort_keys=True)+'\n' for r in sorted(rows[hub], key=lambda r: r['artifact_id'])))
        caps[hub]['place_version_reads'] = {}  # Custom pilot places use the existing hub-wide contract.
        dump(folder/'capabilities.json', caps[hub])
        assert len(HubStore.load(folder).rows()) == len(rows[hub])
    dump(out/'identity/principals.json', [{'principal': PRINCIPAL, 'groups': [GROUP]}])
    dump(out/'private/provenance.json', provenance)
    dump(out/'private/gold-constraints.json', candidate['gold_constraints'])
    dump(out/'private/acceptance.json', {'status': 'loaded_development_candidate_not_frozen',
        'pending': ['human_realism_review', 'base_world_conflict_reconciliation', 'independent_task_gold'],
        'acl_policy': 'Explicit shared pilot group; memory owned by pilot-reader. Synthetic organizational teams confer no permissions.',
        'source_policy': 'Separate generated corpus, not merged base facts; existing loader/capabilities reused. No world-derived gold established.'})
    files = {str(p.relative_to(out)): digest(p.read_bytes()) for p in sorted((out/'hubs').rglob('*')) if p.is_file()}
    manifest = {'status': 'loaded_development_candidate_not_frozen', 'synthetic': True,
                'candidate_sha256': digest(candidate_path.read_bytes()), 'files': files,
                'counts': {h: {'artifacts': len(rows[h]), 'rows': len(rows[h])} for h in HUBS},
                'total_artifacts': len(public_ids), 'held_back_hubs': ['incidenthub'],
                'packaging_counts': dict(Counter(r['metadata']['packaging'] for rs in rows.values() for r in rs))}
    dump(out/'manifest.json', manifest)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    parser.add_argument('--candidate',type=Path)
    args=parser.parse_args()
    print(json.dumps(build(args.out,args.candidate), indent=2))
