"""Build a private audited candidate without altering raw authoring responses."""
import ast
import hashlib
import json
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import MagicMock

from map_pdlc_hierarchy import OUT, EVIDENCE_FIELDS, check_catalog, check_evidence, dump, sources


def main():
    rows = sources()
    indexed = {r['artifact_id']: r for r in rows}
    hierarchy = json.loads((OUT / 'pdlc-hierarchy.json').read_text())
    original = deepcopy(rows)
    replacements = {}

    def replace(artifact_id, before, after):
        text = indexed[artifact_id]['text']
        if text.count(before) != 1:
            raise ValueError(f'Expected one repair target: {artifact_id}: {before}')
        indexed[artifact_id]['text'] = text.replace(before, after)
        replacements.setdefault(artifact_id, []).append((before, after))

    replace('pdlc.001', 'from typing import Dict, Any', 'from typing import Dict, Any, Protocol')
    replace('pdlc.001', 'class R41AuthHandler:', '''class LegacyFraudResult(Protocol):
    is_approved: bool
    score: float

class LegacyFraudClient(Protocol):
    def check_risk_legacy(self, request: AuthRequest, context: Dict[str, Any]) -> LegacyFraudResult:
        ...

class R41AuthHandler:''')
    replace('pdlc.001', 'fraud_client: FraudServiceClient', 'fraud_client: LegacyFraudClient')
    replace('pdlc.005', 'import R41AuthHandler', 'import R41AuthHandler, LegacyFraudClient')
    replace('pdlc.005', 'mock_fraud = MagicMock(spec=FraudServiceClient)\n    mock_fraud.check_risk_legacy',
            'mock_fraud = MagicMock(spec=LegacyFraudClient)\n    mock_fraud.check_risk_legacy')
    replace('pdlc.002', '# R42 sets an explicit 800ms fraud response deadline',
            '# R42 configures an 800ms transport timeout')
    replace('pdlc.002', 'fraud deadline exceeded', 'fraud transport timeout')
    replace('pdlc.003', 'Raised when downstream fraud evaluation exceeds the allotted deadline.',
            'Raised when the fraud HTTP client reports a transport timeout.')
    replace('pdlc.005', '800ms deadline exceeded', 'transport timeout')
    replace('pdlc.036', '`aud` value in the decoded header', '`aud` value in the decoded payload')
    replace('pdlc.002', '# Not implemented in release code; canary duration and prod capacity still unverified.',
            '# TODO: implement the flagged path.')
    replace('pdlc.008', '# Not enabled in current release. Canary rollout schedules and payment timeout deadlines\n# are controlled by the payments squad and remain unknown to this service.',
            '# Not enabled in current release.')
    replace('pdlc.008', "# Interface concern vs defect check:\n    # If the payment service introduces 'PENDING_REVIEW' or any unexpected status,\n    # it is treated as an unhandled interface status variation, not an internal ledger defect.",
            '# Pending review is not postable.')

    for mapping in hierarchy['mappings']:
        aid = mapping['artifact_id']
        if aid in ('pdlc.043', 'pdlc.044', 'pdlc.045', 'pdlc.046'):
            mapping['service_ids'] = [s for s in mapping['service_ids'] if s not in ('svc.payment-auth', 'svc.identity-auth')]
            mapping['reason'] = 'Gateway-routing navigation is inferred; generic payment/identity labels establish subject domains, not canonical authorization service identities.'
            mapping['unresolved'].append('Canonical service bindings for generic payment/identity route keys are unknown.')
        if aid == 'pdlc.036':
            mapping['service_ids'] = []
            mapping['reason'] = 'Platform document navigation is inferred; a gateway dashboard does not identify the canonical gateway-edge service.'
            mapping['unresolved'].append('Specific gateway service identity is unknown.')
        if aid == 'pdlc.090':
            mapping['logical_path'] = 'payments/fraud-timeout/sessions/2024-10-23-trace-fields.md'
        if aid == 'pdlc.085':
            mapping['logical_path'] = 'payments/fraud-timeout/handoffs/support-handoff-fields.md'
    hierarchy['unresolved'] = [
        'Auth route keys and identity naming relationships remain unresolved in the supplied full source; do not infer canonical aliases.'
        if 'full contents are not supplied here' in s else s for s in hierarchy['unresolved']]

    # Recheck all quotation spans against corrected content, including metadata evidence.
    def recheck(obj):
        if isinstance(obj, dict):
            if 'evidence' in obj and 'status' in obj and 'reason' in obj:
                for e in obj['evidence']:
                    for before, after in replacements.get(e['artifact_id'], []):
                        e['quote'] = e['quote'].replace(before, after)
                check_evidence(obj, indexed, allow_anchor=obj.get('reason') == 'existing_world_anchor')
            for value in obj.values():
                recheck(value)
        elif isinstance(obj, list):
            for value in obj:
                recheck(value)
    recheck(hierarchy)
    check_catalog(hierarchy, indexed)

    # Exercise the repaired historical interface and timeout branch with dependency stubs.
    tree = ast.parse(indexed['pdlc.001']['text'])
    tree.body = [n for n in tree.body if not isinstance(n, ast.ImportFrom) or not n.level]
    class TimeoutErrorFixture(Exception):
        pass
    namespace = {'FraudServiceClient': object, 'FraudServiceTimeout': TimeoutErrorFixture,
                 'AuthRequest': object, 'AuthResponse': SimpleNamespace,
                 'ErrorCode': SimpleNamespace(GENERIC_DEPENDENCY_ERROR='DEPENDENCY', INTERNAL_ERROR='INTERNAL')}
    exec(compile(tree, '<audited-r41>', 'exec'), namespace)
    client = MagicMock(spec=namespace['LegacyFraudClient'])
    client.check_risk_legacy.side_effect = TimeoutErrorFixture('fixture timeout')
    response = namespace['R41AuthHandler'](client).handle_authorization(
        SimpleNamespace(auth_id='fixture-auth', idempotency_key='fixture-key'), 'fixture-tenant', 'fixture-subject')
    assert response.status == 'FAILED' and response.error_code == 'DEPENDENCY'
    client.check_risk_legacy.assert_called_once()
    for aid in ('pdlc.001', 'pdlc.002', 'pdlc.003', 'pdlc.005', 'pdlc.008'):
        ast.parse(indexed[aid]['text'])
    assert len(rows) == len(hierarchy['mappings']) == 96
    assert len({r['artifact_id'] for r in rows}) == 96
    for mapping in hierarchy['mappings']:
        mapping['source']['audited_content_sha256'] = hashlib.sha256(indexed[mapping['artifact_id']]['text'].encode()).hexdigest()
    for source in original:
        assert hashlib.sha256((OUT/source['source_file']).read_bytes()).hexdigest() == source['source_sha256']

    dispositions = {
        'SA-01': 'repair: declare historical client/result protocols and bind the R41 mock to them; transport implementation and shared model dependencies remain unavailable',
        'SA-02': 'repair: gold is configured 800 ms transport timeout, not an end-to-end deadline; stale 500 ms design retained',
        'SA-03': 'retain explicit gap: schema-to-wire adapter, authentication/validation ownership and payments-engine alias unknown; exclude agreement/rejection guarantees from gold',
        'SA-04': 'retain explicit gap: producer/status transformation and deduplication unknown; no end-to-end exactly-once gold',
        'SA-05': 'repair: remove unsupported canonical service links and stale source-availability rationale; retain broad domains and unresolved aliases',
        'SA-06': 'repair: neutral session-derived logical path; all private IDs remain audit-only and require public citation IDs at hydration',
        'SA-07': 'retain sketches: preserve fence/snippet boundaries and dependencies; no full executable repository claim; enforce at packaging',
        'SA-08': 'repair: JWT audience is decoded payload claim; retain stale dashboard guidance',
        'SA-09': 'repair local code comments: remove unrelated capacity and evaluator-oriented defect coaching; retain locally relevant uncertainty elsewhere; human realism assessment pending',
    }
    hierarchy['status'] = 'audited_candidate_packaging_pending'
    hierarchy['ingestion']['state'] = 'not_loaded'
    candidate = {'status': 'audited_candidate_packaging_pending', 'artifacts': rows, 'hierarchy': hierarchy,
                 'dispositions': dispositions,
                 'gold_constraints': ['configured_timeout_not_total_deadline', 'identity_binding_unknown',
                                      'event_producer_unknown', 'deduplication_unknown', 'dependencies_incomplete'],
                 'verification': {'raw_sources_unchanged': True, 'quotation_spans_rechecked': True,
                                  'navigation_rechecked': True, 'r41_timeout_branch_with_stubs': True,
                                  'complete_package_execution': False},
                 'content_changes': {aid: [{'before': a, 'after': b} for a,b in changes] for aid,changes in replacements.items()}}
    dump(OUT/'pdlc-audited-candidate.json', candidate)
    print(json.dumps({'artifacts': len(rows), 'corrected_artifacts': len(replacements),
                      'dispositions': len(dispositions), 'status': candidate['status']}))


if __name__ == '__main__':
    main()
