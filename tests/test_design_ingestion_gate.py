import hashlib
import json

import pytest

from tools import ingest_pdlc_corpus as builder


@pytest.mark.parametrize('change', ['text', 'status', 'review'])
def test_changed_design_cannot_be_published_after_review(tmp_path, monkeypatch, change):
    root = tmp_path
    authoring = root / 'build/pdlc-authoring'
    authoring.mkdir(parents=True)
    output = root / 'build/pdlc-pilot'
    doc = {'path': 'docs/a/hld.md', 'text': 'source-grounded draft', 'title': 'HLD',
           'version': 'draft-1', 'review_status': 'draft; review pending', 'module_key': None,
           'source_refs': ['source'], 'related_document_paths': [], 'kind': 'HLD'}
    source = json.dumps({'documents': [doc]}).encode()
    (authoring/'pdlc-designs-repaired-candidate.json').write_bytes(source)
    review = {'verdict': 'pass_for_readonly_draft', 'document_text_hashes': {
        doc['path']: hashlib.sha256(doc['text'].encode()).hexdigest()}}
    review_bytes = json.dumps(review).encode()
    (authoring/'pdlc-design-semantic-review.json').write_bytes(review_bytes)
    artifact = {**doc, 'document_kind': 'HLD'}
    record = {'status': 'source_semantic_review_passed', 'documents': 1,
              'review_sha256': hashlib.sha256(review_bytes).hexdigest(),
              'design_candidate_sha256': hashlib.sha256(source).hexdigest()}
    if change == 'text':
        artifact['text'] = 'unreviewed behavior'
    elif change == 'status':
        artifact['review_status'] = 'approved for production'
    else:
        (authoring/'pdlc-design-semantic-review.json').write_text('{}')
    candidate = authoring/'candidate.json'
    candidate.write_text(json.dumps({'status': 'audited_candidate_packaging_pending',
                                    'design_supplement': record, 'artifacts': [artifact]}))
    monkeypatch.setattr(builder, 'ROOT', root)
    monkeypatch.setattr(builder, 'DEFAULT_OUT', output)
    with pytest.raises(ValueError, match='Design'):
        builder.build(output, candidate)
    assert not output.exists()
