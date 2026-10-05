"""Verify draft task evidence and flag overlap; never infer boundary acceptance."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def verify(bundle, results, development, out):
    rows = {(p.parent.name, r['artifact_id'], r['version']): r
            for p in (bundle / 'corpus/hubs').glob('*/artifacts.jsonl')
            for r in map(json.loads, p.read_text().splitlines())}
    historical = [json.loads(l) for l in (bundle / 'private/gold.jsonl').read_text().splitlines()]
    prior_refs = [e for t in historical for f in t['required_facts'] for e in f.get('evidence', [])]
    prior_refs += json.loads(development.read_text())['cases']
    tasks, findings = [], []
    for path in sorted(results.glob('rubric-fresh-tasks-*-01-openai-gpt-6-luna.result.json')):
        for task in json.loads(path.read_text())['tasks']:
            task['generation_source'] = {'model': 'gpt-6-luna', 'file': str(path),
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
            for fact in task['required_facts']:
                if fact['support_kind'] == 'boundary':
                    findings.append({'task_id': task['task_id'], 'fact_id': fact['fact_id'],
                                     'issue': 'whole_corpus_boundary_review_required'})
                    continue
                if not fact.get('evidence'):
                    raise ValueError('Positive fact lacks evidence')
                for evidence in fact['evidence']:
                    key = tuple(evidence[k] for k in ('source_id', 'artifact_id', 'version'))
                    text = rows[key]['text']; quote = evidence['quote']
                    if len(quote.strip()) < 12 or text.count(quote) != 1:
                        raise ValueError('Evidence quote must be sufficiently specific and unique')
                    evidence.update(start=text.index(quote), end=text.index(quote)+len(quote),
                                    content_sha256=hashlib.sha256(text.encode()).hexdigest())
                    overlap = [p for p in prior_refs if tuple(p[k] for k in ('source_id', 'artifact_id', 'version')) == key
                               and (p['quote'] in quote or quote in p['quote'])]
                    if overlap:
                        findings.append({'task_id': task['task_id'], 'fact_id': fact['fact_id'],
                                         'issue': 'prior_evidence_overlap_review_required'})
            tasks.append(task)
    if len(tasks) != 12 or len({t['task_id'] for t in tasks}) != 12:
        raise ValueError('Expected twelve distinct drafts')
    summary = {'status': 'source_verified_drafts_not_accepted', 'tasks': len(tasks),
               'families': dict(Counter(t['family'] for t in tasks)),
               'scopes': dict(Counter(t['scope'] for t in tasks)), 'findings': findings,
               'independent_acceptance': False, 'same_corpus': True}
    out.mkdir(parents=True, exist_ok=False)
    (out / 'tasks.json').write_text(json.dumps(tasks, indent=2) + '\n')
    (out / 'verification.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('bundle', type=Path)
    p.add_argument('--results', type=Path, required=True)
    p.add_argument('--development', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    verify(a.bundle, a.results, a.development, a.out)
