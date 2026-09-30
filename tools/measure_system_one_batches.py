"""Measure latency and usage against batch size for one System One provider (plan point 15).

Relaxed profile (60 s deadline), batch sizes 1, 2, 5, 10, 20 `noul` questions over one D2-like
state. Per size: one cold call (a fresh client, so a new connection) and two warm calls (same
client). Hard cap on HTTP calls, retries included. Measured once; the report says so. Keys come
from the environment or `.env` and are never written anywhere.

    PYTHONPATH=src python tools/measure_system_one_batches.py --provider typesafe-jev
"""
import argparse
import datetime
import json
import os
import statistics
from pathlib import Path

from sanctum_systemone import SystemOneClient, load_provider_specs

ROOT = Path(__file__).resolve().parents[1]
SIZES = (1, 2, 5, 10, 20)
WARM_REPEATS = 2
DEADLINE_S = 60.0
DESCRIPTORS = {
    "codehub": "Source code and configuration per service repository; implemented behavior",
    "skillhub": "Skills and runbooks per domain namespace; intended procedure",
    "dochub": "Team reference pages per space: overviews, policies, SLAs",
    "memoryhub": "The caller's own agent session notes",
}


def dotenv() -> dict[str, str]:
    path = ROOT / ".env"
    if not path.exists():
        return {}
    pairs = (line.split("=", 1) for line in path.read_text().splitlines() if "=" in line and not line.startswith("#"))
    return {key.strip(): value.strip().strip('"') for key, value in pairs}


def questions(size: int) -> dict:
    sources = list(DESCRIPTORS)
    return {f"d2:{sources[i % len(sources)]}-{i}": {
        "type": "noul",
        "instructions": f"Answer true if searching source {sources[i % len(sources)]} (copy {i}) is likely to "
                        "return evidence necessary to answer the query, judged from its description."}
        for i in range(size)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--max-calls", type=int, default=60)
    parser.add_argument("--out", type=Path, default=None)
    arguments = parser.parse_args()
    spec = load_provider_specs(ROOT / "configs" / "system_one_providers.yaml")[arguments.provider]
    environment = {**dotenv(), **os.environ}
    base_url = spec.resolved_base_url(environment) or "https://api.typesafe.ai"
    key = environment.get(spec.api_key_env) if spec.api_key_env else None
    model = spec.requested_model(environment)
    spec = spec.model_copy(update={"capabilities": spec.capabilities.model_copy(update={"max_questions_per_call": max(SIZES)})})
    state = {"query": "What retry limit does payment-auth apply on a gateway timeout?", "sources": DESCRIPTORS}
    rows, total_calls, usage_total = [], 0, {}
    for size in SIZES:
        client = None
        for run in ["cold"] + ["warm"] * WARM_REPEATS:
            if total_calls + 2 > arguments.max_calls:          # a call may retry once
                raise SystemExit(f"call cap {arguments.max_calls} reached")
            if run == "cold":
                if client is not None:
                    client.close()
                client = SystemOneClient(spec, base_url, model, api_key=key)
            outcome = client.decide(state, questions(size), DEADLINE_S, max_calls=1)
            total_calls += outcome.calls
            for name, value in (outcome.usage or {}).items():
                usage_total[name] = usage_total.get(name, 0) + value
            rows.append({"size": size, "run": run, "latency_ms": outcome.latency_ms, "calls": outcome.calls,
                         "model": outcome.model, "answered": len(outcome.answers),
                         "unavailable": outcome.unavailable_reason, "usage": outcome.usage})
            print(json.dumps(rows[-1]))
        client.close()
    out = arguments.out or ROOT / "docs" / "reports" / f"system-one-batches-{arguments.provider}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# System One batch measurement: {arguments.provider}", "",
             "> SYNTHETIC, NOT PRODUCTION EVIDENCE. **Measured once**, relaxed profile (60 s deadline), from a "
             "laptop against the provider endpoint, so network time dominates; not evidence about the fast path.",
             "", f"Date {datetime.date.today().isoformat()}. Requested model `{model}`. HTTP calls {total_calls} "
             f"(cap {arguments.max_calls}). Usage total {json.dumps(usage_total)}.", "",
             "| Questions | Run | Latency ms | Calls | Answered | Resolved model | Input tokens | Output tokens | Input tokens per question |",
             "|---|---|---|---|---|---|---|---|---|"]
    for row in rows:
        usage = row["usage"] or {}
        input_tokens = usage.get("input_tokens")
        per_question = f"{input_tokens / row['size']:.0f}" if isinstance(input_tokens, (int, float)) else "-"
        lines.append(f"| {row['size']} | {row['run']} | {row['latency_ms']} | {row['calls']} | {row['answered']}"
                     f"{'' if not row['unavailable'] else ' (' + row['unavailable'] + ')'} | {row['model'] or '-'} | "
                     f"{input_tokens if input_tokens is not None else '-'} | {usage.get('output_tokens', '-')} | {per_question} |")
    lines += ["", "| Questions | Warm latency ms (median of repeats) |", "|---|---|"]
    for size in SIZES:
        warm = [row["latency_ms"] for row in rows if row["size"] == size and row["run"] == "warm" and not row["unavailable"]]
        lines.append(f"| {size} | {statistics.median(warm) if warm else '-'} |")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out} ({total_calls} calls)")
