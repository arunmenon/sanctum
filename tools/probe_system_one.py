"""One bounded synthetic System One call under D-JEV; no Claude inference."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from sanctum_run.system_one_broker import DEFAULT_PROVIDERS, load_secret
from sanctum_systemone import SystemOneClient, load_provider_specs

ROOT = Path(__file__).resolve().parents[1]


def probe(out):
    if out.exists():
        raise ValueError('probe output already exists; do not overwrite evidence')
    environment = {}
    if (ROOT/'.env').exists():
        for line in (ROOT/'.env').read_text().splitlines():
            if line.strip().startswith('#') or '=' not in line: continue
            name, value = line.split('=', 1)
            environment[name.strip()] = value.strip().strip('"').strip("'")
    environment.update(os.environ)
    spec = load_provider_specs(DEFAULT_PROVIDERS)['typesafe-jev']
    url = spec.resolved_base_url(environment)
    if not url: raise ValueError('System One base URL is not configured')
    client = SystemOneClient(spec, url, spec.requested_model(environment), api_key=load_secret(spec.api_key_env))
    state = {'query': 'Which source describes implemented retry behavior?',
             'sources': {'codehub': 'Synthetic code and configuration for payment authorization.'}}
    questions = {'d2:codehub': {'type': 'noul',
        'instructions': 'Answer true if codehub is likely to contain evidence needed for the query in state.'}}
    try:
        outcome = client.decide(state, questions, deadline_s=10, max_calls=1)
    finally:
        client.close()
    report = dict(time_utc=datetime.now(timezone.utc).isoformat(), provider='typesafe-jev',
        authorization='D-JEV: synthetic lab state only', data_class='synthetic',
        provider_config_sha256=hashlib.sha256(DEFAULT_PROVIDERS.read_bytes()).hexdigest(),
        requested_model=spec.requested_model(environment), resolved_model=outcome.model,
        calls=outcome.calls, max_calls=1, deadline_seconds=10, usage=outcome.usage,
        latency_ms=outcome.latency_ms, unavailable_reason=outcome.unavailable_reason,
        answered_ids=sorted(outcome.answers),
        passed=bool(outcome.model and 'd2:codehub' in outcome.answers and outcome.calls == 1),
        limitation='Connectivity/model identity probe only; not an agent benchmark or calibration proof.')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    probe(args.out)
