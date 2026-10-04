"""Generate synthetic author packets with Gemini or OpenAI; retain private audit outputs.

One process with bounded jittered retries. Provider-specific reservations cover
32,000 input bytes and the configured output-token limit at pinned prices.
Reservations remain charged against the local cap, even on unknown outcomes.
This ledger accounts for this script only, not unrelated account usage or taxes.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import random
import re
import time
from pathlib import Path
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MODEL = "gemini-3.5-flash"
PRICES = {"input_per_million_usd": 1.50, "output_per_million_usd": 9.00,
          "source": "https://ai.google.dev/gemini-api/docs/pricing",
          "checked": "2026-10-03"}
PACKETS = {"payment-developer": 6, "cross-domain-developers": 2,
           "designer-and-reviewer": 11, "investigation-participants": 5}


def key_from_local_config(provider="gemini"):
    variable = "OPENAI_API_KEY" if provider == "openai" else "GEMINI_API_KEY"
    key = None
    local = ROOT / ".env"
    if local.exists():
        for line in local.read_text().splitlines():
            if line.startswith(variable + "="):
                key = line.split("=", 1)[1].strip().strip("\"'")
    if not key:
        key = os.environ.get(variable)
    if not key:
        raise ValueError(f"Configure {variable} locally; never put it in a prompt")
    return key


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", choices=tuple(PACKETS) + ("all",), default="all")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--include-surrounding", action="store_true")
    parser.add_argument("--retry-rejected", action="store_true", help="resume a previously rejected HTTP 429/503 packet")
    parser.add_argument("--provider", choices=("gemini", "openai"), default="gemini")
    parser.add_argument("--model", choices=(MODEL, "gemini-3.8-flash", "gpt-6-luna"))
    parser.add_argument("--max-retries", type=int, choices=range(0, 4), default=3, help="bounded transient retries per packet (default: 3)")
    parser.add_argument("--job-file", type=Path, help="JSON jobs with name and prompt; saves structured results using the same provider and budget ledger")
    parser.add_argument("--max-output-tokens", type=int, choices=(16384, 32768), default=16384)
    args = parser.parse_args()
    provider = args.provider
    model = args.model or ("gpt-6-luna" if provider == "openai" else "gemini-3.8-flash")
    if (provider == "openai") != (model == "gpt-6-luna"):
        parser.error("Model does not belong to selected provider")
    input_price, output_price = (0.10, 0.50) if provider == "openai" else ((0.75, 3.75) if model == "gemini-3.8-flash" else (1.5, 9.0))
    reservation = (0.04 if args.max_output_tokens == 32768 else 0.02) if provider == "openai" else 1.0
    price_source = "https://developers.openai.com/api/docs/models/gpt-6-luna" if provider == "openai" else PRICES["source"]
    packets = dict(PACKETS) if args.packet == "all" else {args.packet: PACKETS[args.packet]}
    if args.include_surrounding:
        if args.packet != "all":
            parser.error("--include-surrounding requires --packet all")
        packets.update({p.stem: 6 for p in sorted((ROOT / "tools" / "pdlc-authoring").glob("surrounding-*.md"))})
    jobs = {}
    if args.job_file:
        if args.include_surrounding or args.packet != "all":
            parser.error("--job-file cannot be combined with artifact packet selection")
        records = json.loads(args.job_file.read_text())["jobs"]
        for job in records:
            if not isinstance(job.get("prompt"), str) or not re.fullmatch(r"[a-z0-9-]+", job.get("name", "")):
                parser.error("Job names must be safe identifiers and prompts must be strings")
            if job["name"] in jobs:
                parser.error("Duplicate job name")
            jobs[job["name"]] = job
        packets = {name: 0 for name in jobs}
    out = ROOT / "build" / "pdlc-authoring"
    out.mkdir(parents=True, exist_ok=True)
    ledger_path = out / "ledger.json"
    lock = out / ".generation-lock"
    # Exclusive lock prevents simultaneous processes spending against stale ledgers.
    with lock.open("x"):
        pass
    try:
        ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {
            "cap_usd": 20.0, "reserved_usd": 0.0, "prices": PRICES, "calls": []}
        if ledger["prices"] != PRICES:
            raise ValueError("Price record changed; reconcile existing ledger first")
        key = None if args.dry_run else key_from_local_config(provider)
        for name, expected in packets.items():
            call_name = name if model == MODEL else name + ("-openai-gpt-6-luna" if provider == "openai" else "-3.8-flash")
            prompt = jobs[name]["prompt"] if jobs else (ROOT / "tools" / "pdlc-authoring" / f"{name}.md").read_text()
            if not jobs and model != MODEL:
                prompt += "\nReturn exactly the requested artifact count. Add audit claims separately from artifact text. Write like working engineers, not like instruction writers: no CRITICAL BOUNDARY sections or statements about what the author was told not to know. Use realistic uneven detail, concrete local identifiers and chronology. Do not introduce unassigned behavior such as approving payments on timeout. Keep proposed behavior out of released code; a disabled flag can exist without an implementation. Return version labels matching the stated releases where applicable. For HTTP code, handle the actual library timeout exception. Mark added assumptions explicitly.\n"
            if len(prompt.encode()) > 32000:
                raise ValueError("Prompt exceeds reserved input bound")
            digest = hashlib.sha256(prompt.encode()).hexdigest()
            compatible = [c for c in ledger["calls"] if
                (c.get("base_packet") == name or c["packet"] in (name, name + "-3.8-flash"))
                and c["status"] == "complete" and c.get("prompt_sha256") == digest]
            if compatible:
                print(f"{name}: already generated ({compatible[-1]['model']})", flush=True)
                continue
            prior = [c for c in ledger["calls"] if c["packet"] == call_name]
            if prior:
                if prior[-1]["status"] == "complete" and prior[-1]["prompt_sha256"] == digest:
                    print(f"{name}: already generated", flush=True)
                    continue
                if not (args.retry_rejected and (prior[-1].get("http_status") in (429, 503) or prior[-1].get("resume_authorized_after_credential_fix"))):
                    raise ValueError(f"{name}: reconcile prior call before retrying")
            committed = sum(c.get("estimated_usd", c["reserved_usd"]) if c["status"] == "complete" else c["reserved_usd"] for c in ledger["calls"])
            if committed + reservation > min(20.0, ledger["cap_usd"]):
                raise ValueError("Preparation reservation cap reached")
            if args.dry_run:
                print(f"{name}: valid prompt, {expected} artifacts, ${reservation:.2f} reservation", flush=True)
                continue
            (out / f"{call_name}.prompt.md").write_text(prompt)
            body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {"responseMimeType": "application/json",
                                         "maxOutputTokens": args.max_output_tokens}}
            if provider == "openai":
                body = {"model": model, "input": prompt, "store": False,
                        "reasoning": {"effort": "medium"}, "max_output_tokens": args.max_output_tokens,
                        "text": {"format": {"type": "json_object"}}}
                url = "https://api.openai.com/v1/responses"
                headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}
            else:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
                headers = {"x-goog-api-key": key, "Content-Type": "application/json"}
            schema = jobs[name].get("schema") if jobs else None
            if schema:
                if provider == "openai":
                    body["text"]["format"] = {"type": "json_schema", "name": "structured_job", "strict": True, "schema": schema}
                else:
                    body["generationConfig"]["responseJsonSchema"] = schema
            request = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
            call = None
            try:
                for attempt in range(args.max_retries + 1):
                    committed = sum(c.get("estimated_usd", c["reserved_usd"]) if c["status"] == "complete" else c["reserved_usd"] for c in ledger["calls"])
                    if committed + reservation > min(20.0, ledger["cap_usd"]):
                        raise ValueError("Preparation reservation cap reached before retry")
                    call = {"packet": call_name, "model": model, "prompt_sha256": digest,
                            "input_price": input_price, "output_price": output_price,
                            "started": datetime.now(timezone.utc).isoformat(),
                            "reserved_usd": reservation, "status": "reserved", "attempt_in_run": attempt + 1,
                            "provider": provider, "base_packet": name, "price_source": price_source, "price_checked": "2026-10-03", "max_output_tokens": args.max_output_tokens}
                    ledger["calls"].append(call)
                    ledger["reserved_usd"] += reservation
                    ledger_path.write_text(json.dumps(ledger, indent=2))
                    print(f"{name}: generating (attempt {attempt + 1}/{args.max_retries + 1})", flush=True)
                    try:
                        with urllib.request.urlopen(request, timeout=120) as response:
                            raw = response.read()
                        break
                    except urllib.error.HTTPError as error:
                        if error.code not in (429, 503) or attempt == args.max_retries:
                            raise
                        call["status"] = "needs_reconciliation"
                        call["http_status"] = error.code
                        try:
                            detail = json.loads(error.read()).get("error", {})
                            call["error"] = {k: str(detail.get(k, "")).replace(key, "[redacted]") for k in ("status", "code", "message")}

                        except (ValueError, OSError):
                            pass
                        if call.get("error", {}).get("code") == "insufficient_quota":
                            print("Provider quota exhausted; no retries.", flush=True)
                            raise
                        ceiling = min(60.0, 30.0 * 2 ** attempt)
                        delay = random.uniform(ceiling / 2, ceiling)
                        retry_after = error.headers.get("Retry-After")
                        if retry_after:
                            try:
                                server_delay = float(retry_after)
                                if server_delay > 60:
                                    raise ValueError("Server Retry-After exceeds bounded retry window")
                                delay = max(delay, server_delay)
                            except ValueError:
                                # A long or nonnumeric server delay is a stop, not an early retry.
                                raise ValueError("Retry-After requires a later resume")
                        call["retry_delay_seconds"] = round(delay, 2)
                        ledger_path.write_text(json.dumps(ledger, indent=2))
                        print(f"{name}: HTTP {error.code}; exponential backoff with jitter, waiting {delay:.1f}s", flush=True)
                        time.sleep(delay)
                (out / f"{call_name}.response.json").write_bytes(raw)
                data = json.loads(raw)
                if provider == "openai":
                    usage = data.get("usage", {})
                    call["usage"] = {"promptTokenCount": usage.get("input_tokens", 0),
                                     "candidatesTokenCount": usage.get("output_tokens", 0)}
                    call["provider_usage"] = usage
                    call["resolved_model"] = data.get("model", model)
                    if data.get("status") != "completed":
                        raise ValueError("Output did not finish normally; raw response retained")
                    content = "".join(part.get("text", "") for item in data.get("output", [])
                                      if item.get("type") == "message" for part in item.get("content", [])
                                      if part.get("type") == "output_text")
                else:
                    call["usage"] = data.get("usageMetadata", {})
                    call["resolved_model"] = data.get("modelVersion", model)
                    candidate = data["candidates"][0]
                    if candidate.get("finishReason") != "STOP":
                        raise ValueError("Output did not finish normally; raw response retained")
                    content = "".join(p.get("text", "") for p in candidate["content"]["parts"]
                                      if not p.get("thought"))
                result = json.loads(content)
                if not isinstance(result, dict):
                    raise ValueError("Structured result must be an object")
                if not jobs:
                    if len(result.get("artifacts", [])) != expected:
                        raise ValueError("Artifact count mismatch; raw response retained")
                    for artifact in result["artifacts"]:
                        if not artifact.get("title") or not isinstance(artifact.get("text"), str):
                            raise ValueError("Artifact missing native text or title")
                result_suffix = "result" if jobs else "artifacts"
                (out / f"{call_name}.{result_suffix}.json").write_text(json.dumps(result, indent=2))
                call["status"] = "complete"
                call["response_sha256"] = hashlib.sha256(raw).hexdigest()
                usage = call["usage"]
                call["estimated_usd"] = (usage.get("promptTokenCount", 0) * input_price
                    + (usage.get("candidatesTokenCount", 0) + usage.get("thoughtsTokenCount", 0)) * output_price) / 1e6
                print(f"{name}: structured result saved for validation" if jobs else f"{name}: {expected} draft artifacts saved for audit", flush=True)
            except Exception as error:
                if call is not None:
                    call["status"] = "needs_reconciliation"
                if isinstance(error, urllib.error.HTTPError):
                    call["http_status"] = error.code
                    try:
                        detail = json.loads(error.read()).get("error", {})
                        safe = {k: str(detail.get(k, "")).replace(key, "[redacted]") for k in ("status", "code", "message")}
                        call["error"] = safe
                        print(json.dumps(safe), file=sys.stderr)
                    except (ValueError, OSError):
                        pass
                    print(f"{provider} API HTTP {error.code}; retry limit reached or error is not retryable", file=sys.stderr)
                else:
                    print(f"Generation stopped: {type(error).__name__}; retry limit reached or error is not retryable", file=sys.stderr)
                return 1
            finally:
                ledger_path.write_text(json.dumps(ledger, indent=2))
        return 0
    finally:
        lock.unlink()


if __name__ == "__main__":
    sys.exit(main())
