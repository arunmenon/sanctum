"""Apply recorded source-grounded repairs without overwriting model receipts.

This produces a private development candidate, never accepted/frozen gold.
"""
import copy
import hashlib
import json
from pathlib import Path
from regenerate_pdlc_tasks import load_rows, OUT, BUILD


def main():
    source = OUT / 'pdlc-tasks-v2-candidate.json'
    data = copy.deepcopy(json.loads(source.read_text()))
    rows = {r['artifact_id']: r for r in load_rows()}
    tasks = {t['task_id']: t for t in data['tasks']}
    changes = []

    def task(name):
        return tasks[name + '-v2']

    def fact(t, fid):
        return next(f for f in t['required_facts'] if f['fact_id'] == fid)

    def evidence(aid, quote=None):
        r = rows['artifact-' + aid]
        q = r['text'] if quote is None else quote
        assert q in r['text'], (aid, q)
        return dict(source_id=r['source_id'], artifact_id=r['artifact_id'], version=r['version'],
                    quote=q, start=r['text'].index(q), end=r['text'].index(q) + len(q),
                    content_sha256=hashlib.sha256(r['text'].encode()).hexdigest())

    def positive(fid, statement, aid):
        return dict(fact_id=fid, statement=statement, support_kind='evidence',
                    evidence=[evidence(aid)], boundary_verification_needed=False)

    def record(t, reason):
        changes.append(dict(task_id=t['task_id'], reason=reason))

    # Correct three literal errors by selecting actual source spans, not fuzzy matching.
    t = task('gateway-routing-uncertainty')
    f = fact(t, 'gateway.selector.order_test_evidence')
    f['evidence'] = [evidence('bec341318b30faa78eb9')]
    record(t, 'Remove an invented design quotation; actual tests establish behavior, not policy approval.')
    t = task('fraud-batch-client-uncertainty')
    fact(t, 'fraud_timeout_proposal.disposition_and_status')['evidence'] = [evidence('9454b9bb25a6d0a55bcb')]
    fact(t, 'fraud_timeout_historical_budget_not_current_deadline')['evidence'] = [evidence('e3f2ecc39654765718f2')]
    record(t, 'Replace misquoted proposal/history with actual complete source evidence.')

    handler = 'af43e17a8af944b34668'
    statement = ('R42 source configures an 800 ms fraud transport timeout, not a whole-request deadline; '
                 'on fraud timeout the disabled flag returns FAILED/GENERIC_DEPENDENCY_ERROR, '
                 'while the enabled flag raises NotImplementedError. This source does not prove a live deployment.')
    t = task('ledger-reconciliation-uncertainty')
    t['answerability'] = 'complete'
    f = fact(t, 'payments.current_handler_timeout_behavior')
    f.clear()
    f.update(positive('r42.timeout.source_behavior', statement, handler))
    t['prompt'] = ('Reconcile the R41 fraud wait target, the R42 request contract and handler source, '
                   'and the pending-review proposal. Explain the source-described timeout setting and '
                   'response paths, what the proposal changes, and what those dispositions mean for ledger posting. '
                   'Keep transport timeout, whole-request deadline, proposal, and deployment claims distinct.')
    t['plan_checklist'] = [dict(dimension='uncertainty', mandatory_items=[
        'Resolve the historical target against the R42 handler source and contract without confusing timeout with end-to-end deadline.',
        'Distinguish implemented source paths from the proposed review behavior and live deployment claims.'])]
    record(t, 'Resolve false missing-handler obligation using cross-repository R42 code; remains an in-scope evidence reconciliation.')
    t = task('fraud-batch-client-uncertainty')
    t['prompt'] = ('Assess the fraud-timeout pending-review proposal and the historical 500 ms figure against '
                   'the R42 handler source. Explain whether the retry/duplicate-ledger claim is established, '
                   'and determine whether the review behavior is enabled for tenants in current production.')
    t['required_facts'].append(positive('r42.timeout.source_behavior', statement, handler))
    f = fact(t, 'fraud_timeout_current_implementation_status')
    f['statement'] = ('Current production deployment, tenant enrollment and flag values are unavailable in this '
                      'synthetic snapshot; explain the source-described behavior separately and request current '
                      'deployment/flag evidence before claiming production enablement.')
    record(t, 'Separate known handler implementation from genuinely unavailable production enablement; retain partial scope.')

    t = task('payment-authorization-impact')
    fact(t, 'r42.handler.fraud_client_call')['evidence'] = [evidence(handler)]
    fact(t, 'fraud_client.http_contract')['evidence'] = [evidence('55979f9d4f411fa48913')]
    record(t, 'Supply context, constant and header construction supporting all components of compound facts.')
    for name, fid, aid in [
        ('payment-authorization-behavior', 'r42.timeout.disabled_response', handler),
        ('payment-authorization-testing', 'r42.timeout.regression_baseline', '2b6034bb9a3a5f2fffe3'),
        ('payment-authorization-testing', 'r42.retry.same_call_arguments', '637995f6113db1f1fc83'),
        ('identity-provisioning-implementation', 'provisioning.status_client_error_flow', 'fde0f248cddc804189cc'),
        ('gateway-routing-behavior', 'gateway.probe.failure_result', '37c1a177a8333d6f1c44'),
        ('gateway-routing-rollout', 'gateway.selector.release_state', '709d0287607696231f8d'),
        ('fraud-batch-client-implementation', 'fraud_batch_client.timeout_baseline', '1221c1cd9e996eb2ada2')]:
        t = task(name)
        fact(t, fid)['evidence'] = [evidence(aid)]
        record(t, 'Include complete local control/context supporting every component of the required obligation.')
    t = task('fraud-batch-client-impact')
    fact(t, 'fraud_batch_client.row_outcome_and_revisit_boundary')['evidence'] = [
        evidence('1221c1cd9e996eb2ada2'), evidence('d7446df202df29c6624d')]
    record(t, 'Attach both writer-revisit comment and operator-view label to compound outcome obligation.')

    t = task('identity-provisioning-implementation')
    f = fact(t, 'invites.partial_indexes')
    f.clear()
    f.update(positive('provisioning.write_ownership',
        'The status client is read-only; provisioning writes belong to the worker. Proposed interface evolution must respect or explicitly revise that boundary.',
        'fde0f248cddc804189cc'))
    record(t, 'Replace unrelated invite-index obligation with status-client write ownership relevant to the requested LLD.')
    t = task('identity-provisioning-uncertainty')
    for f in t['required_facts']:
        f['statement'] = f['statement'].replace('landed Python client', 'versioned Python client source')
    for c in t['plan_checklist']:
        c['mandatory_items'] = [s.replace('landed Python-client', 'versioned Python-client') for s in c['mandatory_items']]
    record(t, 'Avoid implying deployed or committed status from versioned synthetic code.')
    t = task('gateway-routing-behavior')
    t['prompt'] = ('Explain how the gateway selector chooses a route and how the upstream probe handles request failures. '
                   'Then describe the documented caller flow, if established, linking probe results to the selector availability '
                   'input and requests already in progress. Distinguish each helper’s behavior from caller integration.')
    record(t, 'Clarify that the unavailable part is caller integration, not the fully supplied helper behavior.')
    t = task('shared-engineering-testing-testing')
    t['prompt'] = ('Prepare tests with observable outcomes for the scratch snapshot-fetch helper and its adoption by a service. '
                   'Cover the helper’s timeout behavior and specify service-level assertions using the actual adopting service’s '
                   'maintained deadline, retry and endpoint contract, distinguishing confirmed expectations from proposed ones.')
    record(t, 'Make the partial demand an actual adopting-service contract rather than an unconstrained hypothetical design.')

    # Distinct release decisions, rather than repeating payment flag/canary plans.
    t = task('ledger-reconciliation-rollout')
    t['prompt'] = ('Propose gated release and recovery steps for the draft ledger batch reconciler once its writer adapter '
                   'contract is agreed. Cover posting eligibility, validation before enabling writes, stopping on writer failures, '
                   'and safe handling of already-processed rows before resuming. Keep any proposed retry or deduplication control '
                   'distinct from what the draft currently guarantees.')
    t['required_facts'] = [positive('ledger.batch.draft_contract',
        'The unreleased batch sketch is separate from synchronous payments; adapter names/fields are placeholders requiring verification.',
        '2ffdf808316fcad5452b'), positive('ledger.batch.posting_and_error_flow',
        'The draft posts only approval_status="approved" events, increments its count after each writer call, and supplies no exception handler, retry loop or deduplication control.',
        '2ffdf808316fcad5452b')]
    t['plan_checklist'] = [dict(dimension='validation', mandatory_items=[
        'Gate write enablement on adapter agreement and controlled approved/non-approved/error cases.']),
        dict(dimension='rollout_recovery', mandatory_items=[
        'Define staged write enablement and observable stop conditions.',
        'Explain how to stop writes and reconcile processed/uncertain rows before resumption without asserting existing idempotency or safe replay.'])]
    t['version_conflict_demand'] = 'Keep unreleased batch draft distinct from the separate versioned synchronous consumer and any proposed recovery controls.'
    record(t, 'Replace repeated payment-canary work with ledger-specific batch-write recovery and uncertain-row handling.')
    t = task('fraud-batch-client-rollout')
    t['prompt'] = ('Plan release and recovery for a proposed timeout-input validation change in the offline fraud batch client. '
                   'Cover caller compatibility, controlled adoption by remaining-budget callers, observation of scored/deferred rows, '
                   'and recovery if validation rejects previously accepted caller inputs. Do not assume an approved numeric range '
                   'or a new retry policy.')
    t['required_facts'] = [positive('fraud_batch_client.timeout_baseline',
        'Version 2.4.0 forwards the caller timeout without input validation; request Timeout returns an identifiable deferred row with request_timeout reason.',
        '1221c1cd9e996eb2ada2'), positive('fraud_batch_client.runner_budget_and_retry_ownership',
        'Runner budget differs from HTTP defaults, newer callers pass remaining_seconds, and there is no client-owned retry loop; needs_followup is an operator label.',
        'd7446df202df29c6624d'), positive('fraud_batch_client.timeout_test_seam',
        'Mock tests establish timeout forwarding, deferred subject-key preservation and successful response payload preservation.',
        '38cc62e96a5ba40f744a')]
    t['plan_checklist'] = [dict(dimension='validation', mandatory_items=[
        'Gate release on proposed validation-policy approval and old/new caller compatibility tests.']),
        dict(dimension='rollout_recovery', mandatory_items=[
        'Describe controlled caller adoption and observable rejection/deferred-row signals without invented approved thresholds.',
        'Explain reverting validation and inspecting affected rows while preserving caller-owned budget and retry decisions.'])]
    t['version_conflict_demand'] = 'Separate 2.4.0 client source, 2.3.1 maintenance guidance and proposed input validation.'
    record(t, 'Replace repeated payment flag rollout with offline-client compatibility and validation recovery.')

    for t in data['tasks']:
        if t['scope'] == 'out_of_scope':
            t['plan_checklist'] = [dict(dimension='uncertainty', mandatory_items=[
                'Identify which requested current production or external-contract conclusions lack evidence in the pinned corpus.',
                'Avoid an unsupported factual determination; specify the authoritative evidence or access needed to proceed.',
                'Where useful, distinguish source-supported context or conditional recommendations from the unavailable requested conclusion.'])]
            record(t, 'Score appropriate boundary recognition and evidence requests, not impossible access to live facts.')
        for f in t['required_facts']:
            for e in f['evidence']:
                r = rows[e['artifact_id']]
                assert e['source_id'] == r['source_id'] and e['version'] == r['version']
                assert e['quote'] in r['text'], (t['task_id'], f['fact_id'])
                e.update(start=r['text'].index(e['quote']), end=r['text'].index(e['quote']) + len(e['quote']),
                         content_sha256=hashlib.sha256(r['text'].encode()).hexdigest())
    data.update(status='source_repairs_applied_not_accepted', mechanical_findings=[],
                semantic_source_review_pending=True, boundary_absence_checks_pending=True,
                repairs=changes, raw_candidate_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                independent_acceptance=False)
    target = OUT / 'pdlc-tasks-v2-repaired-candidate.json'
    target.write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps(dict(tasks=len(data['tasks']), repairs=len(changes), candidate=str(target),
                         independent_acceptance=False)))


if __name__ == '__main__':
    main()
