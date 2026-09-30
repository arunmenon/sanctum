"""Runner-side System One broker (docs/intelligence-layer/system-one-providers.md §6).

The SUT asks through the gateway proxy's `system_one.decide` tool; the broker decides what is
sent. Each call is bound independently of the SUT's claims:

- request and caller: the proxy's per-request binding (the SUT's ids are only looked up there);
- candidate sources and descriptors: the gateway's own view (released hubs and their pinned
  capabilities); a `d2:<source>` question for any other source is refused;
- data class: the trusted run configuration, never the SUT;
- provider, model, payload size, calls per round and deadline: provider configuration and the
  profile's round budget. Declared context and option budgets are enforced by refusing the call,
  never by trusting a provider's truncation;
- validity: handshake point 8; one invalid answer makes the whole response unavailable;
- observation: one `ModelCall` per provider call in the request's trace, apart from source calls;
- replay: request/response pairs (no credentials) under `<run>/system_one/`.

The credential is read here, on the runner side, from the environment or `.env`; the SUT
process environment is scrubbed and never receives it.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import anyio
import yaml

from sanctum_eval.trace import ModelCall

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROVIDERS = ROOT / "configs" / "system_one_providers.yaml"
DECIDE_TOOL = "system_one.decide"
UNAVAILABLE = "decision_layer_unavailable"
QUESTION_TYPES = ("noul", "choice", "score")


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    base_url: str
    model: Optional[str]
    credential_env: Optional[str]
    primitives: tuple
    max_questions_per_call: int
    max_options: int
    max_context_chars: int
    data_classes_allowed: tuple
    hosted: bool = False


@dataclass(frozen=True)
class ProfileConfig:
    name: str
    deadline_ms: int
    max_calls_per_round: int


# Round budgets per latency profile (design page §5 point 7) unless the provider file declares them.
DEFAULT_PROFILES = {"strict": {"deadline_ms": 300, "max_calls_per_round": 2},
                    "relaxed": {"deadline_ms": 15000, "max_calls_per_round": 4}}


def load_provider(name: str, profile: str, path: Path = DEFAULT_PROVIDERS) -> tuple[ProviderConfig, ProfileConfig]:
    data = yaml.safe_load(Path(path).read_text())
    row = data["providers"][name]
    if row.get("kind", "http") != "http":
        raise ValueError(f"System One provider {name!r} is not an HTTP provider; the broker serves HTTP backends only")
    profiles = {**DEFAULT_PROFILES, **(data.get("profiles") or {})}
    return provider_from_dict(name, row), profile_from_dict(profile, profiles[profile])


def provider_from_dict(name: str, row: dict) -> ProviderConfig:
    """Accepts literal values or `*_env` names resolved here, on the runner side."""
    capabilities = row.get("capabilities") or {}
    base_url = row.get("base_url") or os.environ.get(row.get("base_url_env") or "", "")
    if not base_url:
        raise ValueError(f"System One provider {name!r} has no base URL (set {row.get('base_url_env')})")
    model = os.environ.get(row.get("model_env") or "") or row.get("model")
    return ProviderConfig(
        name=name, base_url=base_url.rstrip("/"), model=model,
        credential_env=row.get("api_key_env") or row.get("credential_env"),
        hosted=bool(row.get("hosted", capabilities.get("hosted", False))),
        primitives=tuple(capabilities.get("primitives", ("noul",))),
        max_questions_per_call=int(capabilities.get("max_questions_per_call", 20)),
        max_options=int(capabilities.get("max_options", 20)),
        max_context_chars=int(capabilities.get("max_state_chars", capabilities.get("max_context_chars", 16000))),
        data_classes_allowed=tuple(capabilities.get("data_classes_allowed", ("synthetic",))))


def profile_from_dict(name: str, row: dict) -> ProfileConfig:
    return ProfileConfig(name=name, deadline_ms=int(row["deadline_ms"]),
                         max_calls_per_round=int(row["max_calls_per_round"]))


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


@dataclass
class _Round:
    started: float
    calls: int = 0


@dataclass
class SystemOneBroker:
    provider: ProviderConfig
    profile: ProfileConfig
    data_class: str                               # from trusted run configuration
    allowed_sources: list[str]                    # the gateway's released hubs
    descriptors: dict[str, Any]                   # the gateway's pinned hub capabilities
    store_dir: Optional[Path] = None
    secret: Optional[str] = None
    _rounds: dict[tuple[str, str], _Round] = field(default_factory=dict)
    _stored: int = 0

    # ---- entry point (called by the proxy with a bound request only) -------------------------
    async def decide(self, gateway, request_id: str, query: str, arguments: dict[str, Any]) -> dict[str, Any]:
        round_id = str(arguments.get("round") or "r1")
        questions = arguments.get("questions")
        if not isinstance(questions, dict) or not questions:
            return self._refused_result(gateway, request_id, round_id, {}, "invalid_request")
        refusal = self._refuse(questions)
        if refusal:
            return self._refused_result(gateway, request_id, round_id, questions, refusal)
        state = {"query": query, "sources": sorted(self._asked_sources(questions)),
                 "descriptors": {source: self.descriptors.get(source) for source in sorted(self._asked_sources(questions))}}
        round_state = self._rounds.setdefault((request_id, round_id), _Round(started=time.perf_counter()))
        answers, unavailable, models, usage, elapsed_total = {}, {}, set(), [], 0.0
        ids = list(questions)
        for start in range(0, len(ids), self.provider.max_questions_per_call):
            batch = {qid: questions[qid] for qid in ids[start:start + self.provider.max_questions_per_call]}
            outcome = await self._call(gateway, request_id, round_id, round_state, state, batch)
            elapsed_total += outcome["elapsed_ms"]
            if outcome["ok"]:
                answers.update(outcome["answers"])
                if outcome["model"]:
                    models.add(outcome["model"])
                if outcome["usage"] is not None:
                    usage.append(outcome["usage"])
            else:
                unavailable.update({qid: outcome["reason"] for qid in batch})
        resolved = sorted(models)
        return {"provider": self.provider.name, "model": resolved[0] if len(resolved) == 1 else (resolved or None),
                "answers": answers, "unavailable": unavailable, "elapsed_ms": round(elapsed_total, 3),
                "usage": usage or None}

    # ---- binding checks ----------------------------------------------------------------------
    def _asked_sources(self, questions: dict) -> set[str]:
        return {qid.split(":", 1)[1] for qid in questions if qid.startswith("d2:")}

    def _refuse(self, questions: dict) -> Optional[str]:
        if self.data_class not in self.provider.data_classes_allowed:
            return "data_class_ineligible"
        for qid, question in questions.items():
            if not isinstance(question, dict) or question.get("type") not in QUESTION_TYPES:
                return "invalid_request"
            if question["type"] not in self.provider.primitives:
                return "primitive_unsupported"
            if qid.startswith("d2:") and qid.split(":", 1)[1] not in self.allowed_sources:
                return "not_allowed"
            if question["type"] in ("choice", "score"):
                criteria = options_of(question)
                if not criteria:
                    return "invalid_request"
                if len(criteria) > self.provider.max_options:
                    return "over_budget"
        return None

    def _refused_result(self, gateway, request_id: str, round_id: str, questions: dict, reason: str) -> dict:
        gateway.record_model_call(request_id, ModelCall(
            provider=self.provider.name, profile=self.profile.name, round=round_id, questions=sorted(questions),
            outcome="refused", reason=reason, elapsed_ms=0.0))
        return {"provider": self.provider.name, "model": None, "answers": {},
                "unavailable": {qid: reason for qid in questions}, "elapsed_ms": 0.0, "usage": None}

    # ---- one provider call -------------------------------------------------------------------
    async def _call(self, gateway, request_id, round_id, round_state: _Round, state, batch) -> dict:
        body = {"state": state, "model": self.provider.model, "questions": batch}
        payload = json.dumps(body, sort_keys=True)
        request_sha256 = hashlib.sha256(payload.encode()).hexdigest()
        common = dict(provider=self.provider.name, profile=self.profile.name, round=round_id,
                      questions=sorted(batch), request_sha256=request_sha256)
        if len(payload) > self.provider.max_context_chars:
            return self._unavailable(gateway, request_id, common, "refused", "over_budget", 0.0, body, None)
        started = time.perf_counter()
        attempts = 0
        while True:
            remaining_ms = self.profile.deadline_ms - (time.perf_counter() - round_state.started) * 1000.0
            if round_state.calls >= self.profile.max_calls_per_round:
                return self._unavailable(gateway, request_id, common, "refused", "call_limit",
                                         (time.perf_counter() - started) * 1000.0, body, None)
            if remaining_ms <= 0:
                return self._unavailable(gateway, request_id, common, "timeout", UNAVAILABLE,
                                         (time.perf_counter() - started) * 1000.0, body, None)
            round_state.calls += 1
            attempts += 1
            status, response = await anyio.to_thread.run_sync(self._post, payload, remaining_ms / 1000.0)
            elapsed = (time.perf_counter() - started) * 1000.0
            if status == "ok":
                break
            # at most one retry, only for an error and only while the round has time left
            if status == "error" and attempts == 1:
                continue
            return self._unavailable(gateway, request_id, common, status, UNAVAILABLE, elapsed, body, response)
        problem = validate_answers(batch, response)
        if problem:
            return self._unavailable(gateway, request_id, common, "invalid_output", problem, elapsed, body, response)
        model, usage = response.get("model"), response.get("usage")
        gateway.record_model_call(request_id, ModelCall(model=model, outcome="ok", elapsed_ms=round(elapsed, 3),
                                                        usage=usage, **common))
        self._store(request_id, round_id, body, response, "ok", elapsed)
        return {"ok": True, "answers": response["answers"], "model": model, "usage": usage, "elapsed_ms": elapsed}

    def _unavailable(self, gateway, request_id, common, outcome, reason, elapsed, body, response) -> dict:
        gateway.record_model_call(request_id, ModelCall(outcome=outcome, reason=reason,
                                                        elapsed_ms=round(elapsed, 3), **common))
        self._store(request_id, common["round"], body, response, outcome, elapsed)
        return {"ok": False, "reason": reason, "elapsed_ms": elapsed}

    def _post(self, payload: str, timeout_s: float) -> tuple[str, Optional[dict]]:
        headers = {"Content-Type": "application/json"}
        if self.secret:
            headers["Authorization"] = f"Bearer {self.secret}"
        request = urllib.request.Request(f"{self.provider.base_url}/v1/systemone", data=payload.encode(),
                                         headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=max(timeout_s, 0.001)) as reply:
                return "ok", json.loads(reply.read().decode())
        except TimeoutError:
            return "timeout", None
        except urllib.error.URLError as error:
            if isinstance(getattr(error, "reason", None), TimeoutError):
                return "timeout", None
            return "error", None
        except (ValueError, OSError):
            return "error", None

    def _store(self, request_id, round_id, body, response, outcome, elapsed) -> None:
        """Decision-layer replay pairs; the credential is never part of `body`."""
        if self.store_dir is None:
            return
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self._stored += 1
        path = self.store_dir / f"{self._stored:05d}-{request_id}-{round_id}.json"
        path.write_text(json.dumps({"request_id": request_id, "round": round_id, "provider": self.provider.name,
                                    "profile": self.profile.name, "request": body, "response": response,
                                    "outcome": outcome, "elapsed_ms": round(elapsed, 3)},
                                   indent=1, sort_keys=True) + "\n", encoding="utf-8")


def validate_answers(asked: dict[str, dict], response: Any) -> Optional[str]:
    """Handshake point 8: only asked ids, every asked id answered, the asked type, choices among the
    offered options, probabilities in [0, 1]. Returns the first problem, or None."""
    if not isinstance(response, dict) or not isinstance(response.get("answers"), dict):
        return "invalid_output"
    answers = response["answers"]
    if set(answers) != set(asked):
        return "invalid_output"
    for qid, answer in answers.items():
        question = asked[qid]
        if not isinstance(answer, dict) or answer.get("type") != question["type"]:
            return "invalid_output"
        if question["type"] == "noul" and not _probability(answer.get("noul")):
            return "invalid_output"
        if question["type"] == "choice":
            options = options_of(question)
            probabilities = answer.get("probabilities") or {}
            if str(answer.get("choice")) not in options or not isinstance(probabilities, dict):
                return "invalid_output"
            if any(str(key) not in options or not _probability(value) for key, value in probabilities.items()):
                return "invalid_output"
            if "confidence" in answer and answer["confidence"] is not None and not _probability(answer["confidence"]):
                return "invalid_output"
        if question["type"] == "score":
            score = answer.get("score")
            if isinstance(score, bool) or not isinstance(score, (int, float)) \
                    or not 0 <= score <= len(options_of(question)) - 1:
                return "invalid_output"
    return None


def options_of(question: dict) -> list[str]:
    """`criteria` for choice/score: a list of options, or a mapping option -> description."""
    criteria = question.get("criteria")
    if isinstance(criteria, dict):
        return [str(key) for key in criteria]
    if isinstance(criteria, list):
        return [str(option) for option in criteria]
    return []


def _probability(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0.0 <= float(value) <= 1.0


__all__ = ["DECIDE_TOOL", "ProfileConfig", "ProviderConfig", "SystemOneBroker", "load_provider", "load_secret",
           "validate_answers"]
