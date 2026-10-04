"""Verify the packaged pilot through actual stdio MCP hubs; no model inference."""
import hashlib
import json
import os
import secrets
import sys
from pathlib import Path

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from sanctum_hubs.client import call_hub_tool, tool_payload
from sanctum_hubs.corpus import HubStore, CorpusPathRefused
from sanctum_hubs.index import HubIndex, SearchFilters
from sanctum_hubs.interfaces import TokenClaims
from sanctum_hubs.tokens import TokenService

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT/'build/pdlc-pilot'


async def verify():
    secret = secrets.token_hex(32)
    tokens = TokenService(BUILD/'identity/principals.json', secret)
    caller = tokens.issue_caller_token('pdlc-pilot-reader')
    report = {'status': 'mcp_retrieval_verified_development_candidate', 'hubs': {}, 'model_calls': 0}
    manifest = json.loads((BUILD/'manifest.json').read_text())
    for relative, expected in manifest['files'].items():
        assert hashlib.sha256((BUILD/relative).read_bytes()).hexdigest() == expected
    for hub in ('codehub', 'dochub', 'skillhub', 'memoryhub'):
        store = HubStore.load(BUILD/'hubs'/hub)
        token = tokens.exchange(caller, hub)
        search_tool = {'codehub': 'search_code', 'dochub': 'search', 'skillhub': 'search_skills', 'memoryhub': 'search_sessions'}[hub]
        parameters = StdioServerParameters(command=sys.executable,
            args=['-m', 'sanctum_hubs', hub, '--build', str(BUILD)],
            env={**os.environ, 'PYTHONPATH': str(ROOT/'src'), 'SANCTUM_LAB_TOKEN_SECRET': secret})
        async with stdio_client(parameters) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                read_count = 0
                for row in store.rows():
                    if hub == 'codehub':
                        tool, args = 'get_file', {'path': row.path, 'ref': row.version}
                    elif hub == 'dochub':
                        tool, args = 'get_page', {'page_id': row.artifact_id, 'version': row.version}
                    elif hub == 'skillhub':
                        tool, args = 'get_skill', {'path': row.path, 'version': row.version}
                    else:
                        tool, args = 'get_session', {'id': row.artifact_id}
                    result = await call_hub_tool(session, tool, args, token, request_id=f'ingest-read-{hub}-{read_count}')
                    assert not result.isError, tool_payload(result)
                    payload = tool_payload(result)['artifact']
                    assert payload['artifact_id'] == row.artifact_id and payload['version'] == row.version
                    assert payload['text'] == row.text and payload['metadata'] == row.metadata
                    span = payload['metadata']['citation']
                    assert payload['text'][span['start']:span['end']] == row.text
                    read_count += 1
                sample = store.rows()[0]
                search_args = {'query': sample.title, 'top_k': 25}
                if hub == 'codehub':
                    search_args['repo'] = sample.location
                if hub == 'dochub':
                    search_args['space'] = sample.location
                result = await call_hub_tool(session, search_tool, search_args, token, request_id=f'ingest-search-{hub}')
                payload = tool_payload(result)
                assert not result.isError and any(r['artifact_id'] == sample.artifact_id for r in payload['results'])
                denied = tool_payload(await call_hub_tool(session, search_tool, {'query': sample.title}, None))
                assert denied['error']['code'] == 'denied_or_not_found'
                if hub == 'codehub':
                    listed = tool_payload(await call_hub_tool(session, 'list_repos', {}, token))['items']
                    assert len(listed) == 6
                # Independent visibility probes use the same index/access implementation.
                index = HubIndex(store)
                claims = TokenClaims('unrelated-user', ('unrelated-group',), hub, 9999999999, 'probe')
                assert index.search(sample.title, claims, SearchFilters(), 25)[1] == 0
                if hub == 'memoryhub':
                    claims = TokenClaims('unrelated-user', ('pdlc-pilot',), hub, 9999999999, 'probe')
                    assert index.search(sample.title, claims, SearchFilters(), 25)[1] == 0
                report['hubs'][hub] = {'reads_verified': read_count, 'search_verified': True,
                    'missing_token_denied': True, 'unrelated_group_hidden': True,
                    'principal_scope_verified': hub == 'memoryhub'}
    # The loader rejects the private side even if files are deliberately made hub-shaped there.
    forbidden = BUILD/'private/hubs/codehub'
    try:
        HubStore.load(forbidden)
    except CorpusPathRefused:
        report['private_loader_boundary_verified'] = True
    else:
        raise AssertionError('Private loader path accepted')
    report['total_reads_verified'] = sum(h['reads_verified'] for h in report['hubs'].values())
    report['manifest_hashes_verified'] = True
    report['frozen'] = False
    (BUILD/'private/ingestion-verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    anyio.run(verify)
