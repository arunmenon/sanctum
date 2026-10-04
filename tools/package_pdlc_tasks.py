"""Save source-verified development tasks and private review evidence.

The review dispositions below are implementer judgments; they are deliberately
separate from independent acceptance and evaluation freeze.
"""
import hashlib
import json
import re
import shutil
from collections import Counter
from itertools import combinations
from pathlib import Path

import yaml

from regenerate_pdlc_tasks import BUILD, OUT, load_rows

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / 'build/agent-bundles/pdlc-development'
BOUNDARIES = {
    'payment-authorization-testing-v2': (
        r'pending.review|NotImplementedError|enable_pending_review',
        'Handler source establishes the existing enabled-path placeholder. Proposal and review handoffs do not settle a future review API/state/error contract; tests can cover current behavior and condition proposed outcomes on that contract.'),
    'identity-provisioning-testing-v2': (
        r'onboarding/status|fetch_provisioning_status',
        'Both recorded routes exist. Neither the browser note, status client nor design supplies an alias/canonical shared end-to-end contract; this is not a claim that either route is absent.'),
    'ledger-reconciliation-implementation-v2': (
        r'post_authorized_amount|LedgerWriter|reconcile_batch',
        'The protocol and fake-writer tests establish the draft seam. They supply no concrete production adapter implementing that seam; the separate HTTP event consumer is not evidence of such an adapter.'),
    'gateway-routing-behavior-v2': (
        r'choose_route|upstream_responds|available.*route|route.*available',
        'Selection and probe behavior are provided. No caller connects probe output to availability or in-progress dispatch; separate helper behavior remains answerable.'),
    'shared-engineering-testing-testing-v2': (
        r'fetch_snapshot|SnapshotUnavailable|snapshot.*endpoint|snapshot.*retry',
        'The scratch helper and timeout test use caller-supplied timeout and placeholder URL. There is no identified adopting-service integration establishing its real endpoint/deadline/retry contract.'),
    'shared-engineering-testing-uncertainty-v2': (
        r'X-Gateway-Route|gateway.routing|send_request',
        'The historical devbox note explicitly has not checked consumption. Gateway helpers/design supply no current consumer contract for this header; do not infer that no consumer exists.'),
}
LIVE_RATIONALE = ('The pinned manifest declares a synthetic development corpus. Its source snapshots, draft designs '
    'and historical operational discussions do not supply current real production deployment/tenant/telemetry, '
    'approved operational controls, production endpoint access or a production service contract. This is a bounded '
    'corpus limitation, not a universal absence claim; source-described behavior can still be explained conditionally.')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def main():
    raw = OUT / 'pdlc-tasks-v2-repaired-candidate.json'
    data = json.loads(raw.read_text())
    rows = load_rows()
    by_id = {r['artifact_id']: r for r in rows}
    manifest = json.loads((BUILD / 'manifest.json').read_text())
    assert len(rows) == manifest['total_artifacts'] == 120 and manifest['synthetic'] is True
    assert digest(BUILD / 'manifest.json') == data['corpus_manifest_sha256']
    for name, sha in manifest['files'].items():
        assert digest(BUILD / name) == sha, name
    boundaries, refs = [], 0
    gold, public = [], []
    for t in data['tasks']:
        task_boundaries = []
        for f in t['required_facts']:
            assert f['support_kind'] in ('evidence', 'boundary')
            if f['support_kind'] == 'evidence':
                assert f['evidence']
                for e in f['evidence']:
                    r = by_id[e['artifact_id']]
                    assert e['source_id'] == r['source_id'] and e['version'] == r['version']
                    assert r['text'][e['start']:e['end']] == e['quote']
                    assert hashlib.sha256(r['text'].encode()).hexdigest() == e['content_sha256']
                    refs += 1
            else:
                assert not f['evidence'] and t['scope'] != 'in_scope'
                pattern, rationale = BOUNDARIES.get(t['task_id'],
                    (r'production|deployed|capacity|rollout|screen_one|idempoten|duplicate', LIVE_RATIONALE))
                hits = [r['artifact_id'] for r in rows if re.search(pattern, r['text'], re.I)]
                check = dict(task_id=t['task_id'], fact_id=f['fact_id'],
                    searched_artifact_count=120, search_pattern=pattern, related_artifacts=hits,
                    disposition='bounded_unavailable_requested_contract_or_live_state', rationale=rationale,
                    corpus_manifest_sha256=data['corpus_manifest_sha256'],
                    scope='Only this pinned synthetic corpus; a search miss alone is not proof.',
                    reviewer='runtime_implementer_source_review', independent=False)
                task_boundaries.append(check)
                boundaries.append(check)
                f['boundary_verification_needed'] = False
                f['boundary_record'] = check
        assert t['answerability'] == {'in_scope':'complete','partial':'partial','out_of_scope':'unavailable'}[t['scope']]
        assert t['design_kind'] is None or t['design_kind'] in t['prompt']
        public.append({k:t[k] for k in ('task_id','family','prompt','caller_requirements','answer_format')})
        sources = sorted({e['source_id'] for f in t['required_facts'] for e in f['evidence']})
        gold.append(dict(task_id=t['task_id'], required_facts=t['required_facts'], plan_checklist=t['plan_checklist'],
            version_conflict_demand=t['version_conflict_demand'], matrix=dict(
                family=t['family'], domains=t['domains'], sources=sources, difficulty=t['difficulty'],
                answerability=t['answerability'], scope=t['scope'], design_kind=t['design_kind']),
            source_review=dict(reviewer='runtime_implementer_source_review', independent=False,
                result='verified_for_development', task_demand='Reviewed against its prompt/family and applicable checklist; multiple sound designs allowed.'),
            generation_source=t['generation_source']))
    family_counts = dict(Counter(t['family'] for t in data['tasks']))
    scope_counts = dict(Counter(t['scope'] for t in data['tasks']))
    assert len(public) == len({t['task_id'] for t in public}) == 30
    assert set(family_counts.values()) == {5}
    assert scope_counts == dict(in_scope=18, partial=6, out_of_scope=6)
    overlaps = []
    for a,b in combinations(gold,2):
        fa,fb = ({f['fact_id'] for f in t['required_facts']} for t in (a,b))
        common = sorted(fa & fb)
        if common:
            overlaps.append(dict(task_ids=[a['task_id'],b['task_id']], common_fact_ids=common,
                same_fact_set=fa==fb, disposition='Different requested work or scope; disclose shared substrate, not independent fact samples.'))
    # The identity explanation and impact tasks intentionally share interface facts,
    # but one resolves a mismatch and the other traces consequences of changing it.
    exact = [x for x in overlaps if x['same_fact_set']]
    for x in exact:
        assert set(x['task_ids']) == {'identity-provisioning-impact-v2','identity-provisioning-uncertainty-v2'}
        x['disposition'] = 'Reviewed exception: dependency-change impact versus adjudicating route ambiguity. Same facts, distinct reasoning demands; report overlap.'
    BUNDLE.mkdir(parents=True, exist_ok=True)
    shutil.copytree(BUILD / 'hubs', BUNDLE / 'corpus/hubs', dirs_exist_ok=True)
    shutil.copy2(BUILD / 'manifest.json', BUNDLE / 'corpus/manifest.json')
    (BUNDLE/'connections').mkdir(exist_ok=True)
    shutil.copy2(BUILD/'identity/principals.json', BUNDLE/'connections/principals.json')
    for relative, records in [('public/tasks.jsonl',public),('private/gold.jsonl',gold)]:
        p=BUNDLE/relative;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))
    instructions = ('Answer using authorized tool evidence. Explain supported parts and diagnose missing/conflicting evidence; '
        'conditional recommendations are allowed. Do not invent current production facts. Proposed designs may differ if they satisfy '
        'the requested constraints. Return JSON with schema_version=1, answer (full prose), claims [{claim_id,text,citations '
        '[{source_id,artifact_id,version,start,end,evidence_id}]}], uncertainties [strings], unmet_requirements [strings]. '
        'Citations must refer to evidence actually delivered in this session. Character coordinates use original artifact text. '
        'Do not infer approval or deployment from a draft or source snapshot.')
    (BUNDLE/'public/instructions.txt').write_text(instructions+'\n')
    write(BUNDLE/'private/rubric.json',dict(version=1,primary='supported_required_fact_coverage',
        equal_fact_weights=True, levels=dict(missing=0,partial=1,meets=2),
        completion='All required obligations and applicable checklist items met; no material unsupported claims; valid answer protocol.',
        design='Multiple coherent HLD/LLD proposals accepted; existing-system claims require evidence; recommendations assessed against task constraints.',
        human_adjudication_required=True,independent_acceptance=False))
    config=dict(schema_version=1,experiment_id='pdlc-pilot-0-development',mode='evidence_only',
        corpus=dict(manifest='corpus/manifest.json',expected_sha256=data['corpus_manifest_sha256']),
        tasks='public/tasks.jsonl',gold='private/gold.jsonl', instructions='public/instructions.txt',
        agent=dict(adapter='claude_code',model=None,effort=None),workspace=dict(kind='empty'),
        caller=dict(principal='pdlc-pilot-reader',principal_file='connections/principals.json',
            expected_sha256=digest(BUNDLE/'connections/principals.json')),
        arms=dict(direct=dict(tool_surface='direct_hubs'),sanctum=dict(tool_surface='sanctum_only',runtime_ready=False)),
        limits=dict(agent_rounds=8,cumulative_evidence_tokens=8000,tool_response_evidence_tokens=4000,
            task_deadline_seconds=120,total_inference_spend_usd=0),
        execution=dict(repetitions=3,random_seed=42,fresh_session_per_attempt=True),
        diversity=dict(family_counts=family_counts,scope_counts=scope_counts,
            required_domains=sorted({d for t in gold for d in t['matrix']['domains']}),
            required_sources=['codehub','dochub','memoryhub'],required_answerability=['complete','partial','unavailable'],
            reject_duplicate_fact_sets=True,duplicate_fact_set_exceptions=[x['task_ids'] for x in exact]),
        readiness=dict(task_source_verified=True,independent_acceptance=False,frozen=False,paid_budget_approved=False))
    (BUNDLE/'experiment.yaml').write_text(yaml.safe_dump(config,sort_keys=False))
    report=dict(status='source_verified_development_bundle_not_independently_accepted_or_frozen',
        task_count=30,source_artifacts_checked=120,citation_references_checked=refs,
        corpus_manifest_sha256=data['corpus_manifest_sha256'], repaired_candidate_sha256=digest(raw),
        family_counts=family_counts,scope_counts=scope_counts,
        design_counts=dict(Counter(t['design_kind'] for t in data['tasks'] if t['design_kind'])),
        semantic_review='Implementer read task demands, required statements and supporting code/design/version context; repaired unsupported and incomplete support.',
        boundary_checks=boundaries,fact_overlaps=overlaps,
        limitations=['Independent task/gold acceptance and human realism review remain pending.',
            'Difficulty labels are provisional; paired repetitions are not additional independent tasks.',
            'Shared tooling is cross-cutting; its sources lack domain bindings, so no binding was fabricated.',
            'Tasks share corpus facts; family diversity does not establish independent ecosystem generalization.'],
        repairs=data['repairs'],independent_acceptance=False,frozen=False)
    write(BUNDLE/'private/verification.json',report)
    print(json.dumps(dict(bundle=str(BUNDLE),tasks=30,reference_checks=refs,
                          boundary_checks=len(boundaries),independent_acceptance=False)))


if __name__ == '__main__':
    main()
