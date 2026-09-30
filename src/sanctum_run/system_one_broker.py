"""Runner-side System One broker (docs/intelligence-layer/system-one-providers.md §6).

The SUT asks through the gateway proxy's `system_one.decide` tool; the broker decides what is
sent. Each call is bound independently of the SUT's claims:

- request and caller: the proxy's per-request binding; the query comes from that binding, and the
  SUT's `query`, `candidate_source_ids` and `max_calls` are untrusted hints (max_calls is only
  ever lowered);
- candidate sources and descriptors: the gateway's own view (released hubs) and the pinned
  descriptors from trusted configuration; a `d2:<source>` question for any other source is
  dropped into `invalid_ids`;
- data class: the trusted run configuration, never the SUT;
- provider, model, payload size, call count and deadline: `configs/system_one_providers.yaml`
  and its latency profile. The protocol work (batching, over-budget refusal without truncation,
  one retry within the deadline, handshake point 8 validation) is `sanctum_systemone`'s client,
  shared with the SUT's providers;
- observation: one `ModelCall` per tool call in the request's trace, apart from source calls;
- replay: the raw provider request/response pairs (never the Authorization header) under
  `<run>/system_one/`.

The key is read here, on the runner side, from the environment or `.env`; the SUT process
environment is scrubbed and never receives it. The tool result is `CallOutcome` JSON.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import anyio
import httpx
import yaml

from sanctum_eval.trace import ModelCall
from sanctum_systemone import CallOutcome, ProviderSpec, SystemOneClient, UnavailableReason, load_provider_specs

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROVIDERS = ROOT / "configs" / "system_one_providers.yaml"
DEFAULT_DESCRIPTORS = ROOT / "configs" / "d2_standin.yaml"
DECIDE_TOOL = "system_one.decide"
QUESTION_TYPES = ("noul", "choice", "score")


@dataclass(frozen=True)
class ProfileConfig:
    name: str
    deadline_ms: int
    max_calls_per_round: int


def load_provider(name: str, profile: str, path: Path = DEFAULT_PROVIDERS) -> tuple[ProviderSpec, ProfileConfig]:
    spec = load_provider_specs(path)[name]
    if spec.kind != "http":
        raise ValueError(f"System One provider {name!r} is {spec.kind!r}; the broker serves HTTP providers only")
    row = (yaml.safe_load(Path(path).read_text()).get("profiles") or {})[profile]
    return spec, ProfileConfig(profile, int(row["deadline_ms"]), int(row["max_calls_per_round"]))


def load_descriptors(path: Path = DEFAULT_DESCRIPTORS) -> dict[str, str]:
    return dict(yaml.safe_load(Path(path).read_text())["descriptors"])


def descriptor_release(descriptors: dict[str, Any]) -> str:
    """Identifies the exact descriptor dict sent in `state` (calibration binds to it)."""
    return "sha256:" + hashlib.sha256(json.dumps(descriptors, sort_keys=True).encode()).hexdigest()[:16]


def load_secret(variable: Optional[str], env_file: Path = ROOT / ".env") -> Optional[str]:
    """The provider key, runner side only: the process environment first, then `.env`."""
    if not variable:
        return None
    if os.environ.get(variable):
        return os.environ[variable]
    if Path(env_file).is_file():
        for line in Path(env_file).read_text(encoding="utf-8").splitlines():
            key, _, value = line.strip().partition("=")
            if key.strip() == variable and value:
                return value.strip().strip('"').strip("'")
    return None


class _RecordingTransport(httpx.BaseTransport):
    """Keeps each provider exchange's bodies for decision-layer replay; headers are not kept."""

    def __init__(self, inner: httpx.BaseTransport):
        self.inner, self.exchanges = inner, []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        body = _json_or_text(request.content)
        try:
            response = self.inner.handle_request(request)
        except httpx.HTTPError as error:
            self.exchanges.append({"request": body, "status": None, "response": None, "error": type(error).__name__})
            raise
        response.read()
        self.exchanges.append({"request": body, "status": response.status_code,
                               "response": _json_or_text(response.content)})
        return response

    def close(self) -> None:
        self.inner.close()


def _json_or_text(content: bytes) -> Any:
    try:
        return json.loads(content)
    except ValueError:
        return content.decode("utf-8", "replace")


@dataclass
class SystemOneBroker:
    spec: ProviderSpec
    profile: ProfileConfig
    data_class: str                               # from trusted run configuration
    allowed_sources: list[str]                    # the gateway's released hubs
    descriptors: dict[str, str]                   # pinned, from trusted configuration
    store_dir: Optional[Path] = None
    secret: Optional[str] = None
    environment: dict[str, str] = field(default_factory=lambda: dict(os.environ))
    transport: Optional[httpx.BaseTransport] = None     # tests may inject; default is real HTTP
    _stored: int = 0

    async def decide(self, gateway, request_id: str, query: str, arguments: dict[str, Any]) -> dict[str, Any]:
        round_id = str(arguments.get("round") or "d2")
        raw = arguments.get("questions")
        questions = {str(qid): q for qid, q in raw.items()} if isinstance(raw, dict) else {}
        sources = {source: text for source, text in sorted(self.descriptors.items()) if source in self.allowed_sources}
        release = descriptor_release(sources)
        # questions about a source outside the gateway's view, or malformed, are never sent
        refused = sorted(qid for qid, q in questions.items() if not isinstance(q, dict)
                         or q.get("type") not in QUESTION_TYPES
                         or (qid.startswith("d2:") and qid.split(":", 1)[1] not in sources))
        asked = {qid: q for qid, q in questions.items() if qid not in refused}
        requested_calls = arguments.get("max_calls")
        max_calls = self.profile.max_calls_per_round
        if isinstance(requested_calls, int) and not isinstance(requested_calls, bool) and requested_calls > 0:
            max_calls = min(max_calls, requested_calls)

        reason = None
        base_url = self.spec.resolved_base_url(self.environment)
        if not base_url:
            reason = UnavailableReason.NOT_CONFIGURED
        elif self.data_class not in self.spec.capabilities.data_classes_allowed:
            reason = UnavailableReason.DATA_CLASS_REFUSED
        if reason is not None or not asked:
            outcome = CallOutcome(provider=self.spec.name, unavailable_reason=reason, invalid_ids=refused)
            exchanges: list[dict] = []
        else:
            recorder = _RecordingTransport(self.transport or httpx.HTTPTransport())
            client = SystemOneClient(self.spec, base_url, self.spec.requested_model(self.environment),
                                     api_key=self.secret, transport=recorder)
            state = {"query": query, "sources": sources}
            try:
                outcome = await anyio.to_thread.run_sync(
                    client.decide, state, asked, self.profile.deadline_ms / 1000.0, max_calls)
            finally:
                client.close()
            outcome.invalid_ids = sorted(set(outcome.invalid_ids) | set(refused))
            exchanges = recorder.exchanges
        outcome.descriptor_release = release
        gateway.record_model_call(request_id, ModelCall(
            provider=self.spec.name, model=outcome.model, profile=self.profile.name, round=round_id,
            questions=sorted(questions), outcome="ok" if outcome.unavailable_reason is None else "unavailable",
            reason=None if outcome.unavailable_reason is None else str(outcome.unavailable_reason.value),
            elapsed_ms=float(outcome.latency_ms), usage=outcome.usage, calls=outcome.calls,
            invalid_ids=list(outcome.invalid_ids)))
        self._store(request_id, round_id, outcome, exchanges, release)
        return outcome.model_dump(mode="json")

    def _store(self, request_id: str, round_id: str, outcome: CallOutcome, exchanges: list[dict],
               release: str) -> None:
        if self.store_dir is None:
            return
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self._stored += 1
        path = self.store_dir / f"{self._stored:05d}-{request_id}-{round_id}.json"
        path.write_text(json.dumps({
            "request_id": request_id, "round": round_id, "provider": self.spec.name, "profile": self.profile.name,
            "data_class": self.data_class, "descriptor_release": release, "exchanges": exchanges,
            "outcome": outcome.model_dump(mode="json")}, indent=1, sort_keys=True) + "\n", encoding="utf-8")


__all__ = ["DECIDE_TOOL", "ProfileConfig", "SystemOneBroker", "descriptor_release", "load_descriptors",
           "load_provider", "load_secret"]
