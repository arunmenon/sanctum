"""Test double: a local, deterministic `/v1/systemone` server (tests only; never used in runs).

It speaks the wire protocol (design page §3) over real HTTP on localhost, answers every question
deterministically from a hash of (state, question id), and can be told to misbehave so the
adapter and the conformance checks can be exercised without live calls:
`delay_ms`, `fail_times` (5xx before succeeding), `invalid` (wrong type / unknown id / bad
probability), `model_sequence` (resolved model per call), `require_key`, and declared limits
(`max_questions_per_call`, `max_options`) that are rejected with 422, never truncated."""
from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Optional


@dataclass
class ServerBehavior:
    model_sequence: list[str] = field(default_factory=lambda: ["test-model-1"])
    delay_ms: int = 0
    fail_times: int = 0
    invalid: Optional[str] = None           # wrong_type | unknown_id | bad_probability | not_json
    require_key: Optional[str] = None
    max_questions_per_call: int = 3
    max_options: int = 5
    requests: list[dict] = field(default_factory=list)


def _unit(seed: str) -> float:
    return int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def answer(state: Any, qid: str, question: dict[str, Any]) -> dict[str, Any]:
    seed = json.dumps(state, sort_keys=True) + "|" + qid
    kind = question.get("type")
    if kind == "noul":
        return {"type": "noul", "noul": round(_unit(seed), 6)}
    options = list((question.get("criteria") or {}).keys())
    weights = [(_unit(seed + option) + 0.01) for option in options]
    total = sum(weights)
    probabilities = {option: round(weight / total, 6) for option, weight in zip(options, weights)}
    if kind == "choice":
        top = max(probabilities, key=probabilities.get)
        # like the hosted backend, `confidence` is deliberately not the top probability
        return {"type": "choice", "choice": top, "probabilities": probabilities,
                "confidence": round(probabilities[top] / 2, 6)}
    return {"type": "score", "score": round(sum(int(level) * p for level, p in probabilities.items()), 6)}


class SystemOneTestServer:
    def __init__(self, behavior: Optional[ServerBehavior] = None):
        self.behavior = behavior or ServerBehavior()
        self._calls = 0
        server = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *arguments):
                pass

            def _send(self, status: int, body: Any) -> None:
                raw = body if isinstance(body, bytes) else json.dumps(body).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_POST(self):
                behavior = server.behavior
                length = int(self.headers.get("Content-Length") or 0)
                request = json.loads(self.rfile.read(length) or b"{}")
                behavior.requests.append(request)
                if self.path != "/v1/systemone":
                    return self._send(404, {"detail": "not found"})
                if behavior.require_key and self.headers.get("Authorization") != f"Bearer {behavior.require_key}":
                    return self._send(401, {"detail": "unauthorized"})
                if behavior.delay_ms:
                    time.sleep(behavior.delay_ms / 1000)
                if behavior.fail_times > 0:
                    behavior.fail_times -= 1
                    return self._send(503, {"detail": "unavailable"})
                questions = request.get("questions") or {}
                if len(questions) > behavior.max_questions_per_call:
                    return self._send(422, {"detail": "too many questions"})
                for question in questions.values():
                    if len(question.get("criteria") or {}) > behavior.max_options:
                        return self._send(422, {"detail": "too many options"})
                if behavior.invalid == "not_json":
                    return self._send(200, b"not json")
                model = behavior.model_sequence[min(server._calls, len(behavior.model_sequence) - 1)]
                server._calls += 1
                answers = {qid: answer(request.get("state"), qid, q) for qid, q in questions.items()}
                if behavior.invalid == "wrong_type" and answers:
                    first = next(iter(answers))
                    answers[first] = {"type": "score", "score": 1.0}
                if behavior.invalid == "unknown_id":
                    answers["never-asked"] = {"type": "noul", "noul": 0.5}
                if behavior.invalid == "bad_probability" and answers:
                    first = next(iter(answers))
                    answers[first] = {"type": "noul", "noul": 1.7}
                usage = {"input_tokens": 10 * len(questions) + 50, "output_tokens": 5 * len(questions)}
                return self._send(200, {"model": model, "answers": answers, "usage": usage})

        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.base_url = f"http://127.0.0.1:{self._httpd.server_address[1]}"
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)

    def __enter__(self) -> "SystemOneTestServer":
        self._thread.start()
        return self

    def __exit__(self, *exc_info) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
