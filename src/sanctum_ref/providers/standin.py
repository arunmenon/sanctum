"""Rules and the local stand-in (M6), the no-network control arms (design page §2).

`DecisionProvider.decide(DecisionRequest) -> DecisionResult` (HLD §6.6), one request per
optional source (round 2). Providers:
- `rules`: tier 0; keeps every candidate the routing rules selected (p = 1, use).
- `standin`: local, no network. TF-IDF cosine between the query and each source's pinned
  descriptor, mapped to P(useful) by a logistic calibration fitted on dev runs only
  (`tools/fit_d2_standin.py`, params and provenance in `configs/d2_standin.yaml`).
- `jev`: the old name; refuses. Hosted Jev is `typesafe-jev` through the broker (`http_systemone`).

Dispositions (bands in the params file): p >= use -> `use` (call); p < skip -> answered `call: false`;
anything between is uncertain -> `preserve_candidate` (call). Uncertainty never drops a source
(§6.4 D2 "keep the source"). A provider that fails or cannot load returns `unavailable` with no
value; the router then keeps every candidate and reports `decision_layer_unavailable`.
D2 only ever sees optional sources: must-consult sources are not candidates (§9.4 level 5).
"""
from __future__ import annotations

import hashlib
import math
import time
from pathlib import Path
from typing import Any, Optional, Protocol

import yaml

from sanctum_contracts import DecisionRequest, DecisionResult
from sanctum_systemone import ProviderCapabilities

from ..text import content_terms
from .interface import (
    POLICY_VERSION, TARGET, DecisionUnavailable, PerRequestProvider, ProviderNotApproved, unavailable,
)

class RulesProvider(PerRequestProvider):
    name = "rules"
    capabilities = ProviderCapabilities(primitives=["noul"], data_classes_allowed=["synthetic", "internal"], conformance="supported")

    def decide(self, request: DecisionRequest) -> DecisionResult:
        return DecisionResult(status="answered", value={"source": request.candidate_ids[0], "p": 1.0, "call": True},
                              target=TARGET, disposition="use", provider=self.name, policy_version=POLICY_VERSION,
                              latency_ms=0, cost=0)


class StandinProvider(PerRequestProvider):
    name = "standin"
    capabilities = ProviderCapabilities(primitives=["noul"], data_classes_allowed=["synthetic", "internal"], conformance="supported")

    def __init__(self, params_path: Path):
        self._params_path = Path(params_path)
        self._params: Optional[dict[str, Any]] = None
        self._version: Optional[str] = None

    def _load(self) -> dict[str, Any]:
        if self._params is None:
            try:
                raw = self._params_path.read_bytes()
                params = yaml.safe_load(raw)
                params["descriptors"], params["calibration"], params["bands"]
            except (OSError, yaml.YAMLError, KeyError, TypeError) as error:
                raise DecisionUnavailable(f"standin params unavailable: {type(error).__name__}") from None
            self._params, self._version = params, "standin-" + hashlib.sha256(raw).hexdigest()[:12]
        return self._params

    def decide(self, request: DecisionRequest) -> DecisionResult:
        started = time.monotonic()
        try:
            params = self._load()
        except DecisionUnavailable:
            return unavailable(self.name, started)
        source_id = request.candidate_ids[0]
        descriptor = params["descriptors"].get(source_id)
        if descriptor is None:
            return unavailable(self.name, started)
        similarity = tfidf_cosine(request.bounded_state["query"], descriptor, params["descriptors"])
        calibration = params["calibration"]
        probability = 1 / (1 + math.exp(-(calibration["a"] * similarity + calibration["b"])))
        bands = params["bands"]
        if probability >= bands["use"]:
            disposition, call = "use", True
        elif probability < bands["skip"]:
            disposition, call = "use", False           # a confident "not useful" answer
        else:
            disposition, call = "preserve_candidate", True
        return DecisionResult(status="answered",
                              value={"source": source_id, "p": round(probability, 4), "call": call,
                                     "similarity": round(similarity, 4)},
                              target=TARGET, distribution={"useful": round(probability, 4),
                                                           "not_useful": round(1 - probability, 4)},
                              calibration={"method": "logistic", "fitted_on": str(params.get("provenance", {}).get("fitted_on", "dev"))},
                              disposition=disposition, provider=self.name, model_version=self._version,
                              policy_version=POLICY_VERSION, latency_ms=int((time.monotonic() - started) * 1000), cost=0)


def tfidf_cosine(query: str, descriptor: str, corpus: dict[str, str]) -> float:
    documents = [set(content_terms(text)) for text in corpus.values()]
    def weights(text: str) -> dict[str, float]:
        counts: dict[str, int] = {}
        for term in content_terms(text):
            counts[term] = counts.get(term, 0) + 1
        return {term: count * math.log(1 + (len(documents) + 1) / (1 + sum(term in d for d in documents)))
                for term, count in counts.items()}
    first, second = weights(query), weights(descriptor)
    dot = sum(value * second.get(term, 0.0) for term, value in first.items())
    norm = math.sqrt(sum(v * v for v in first.values())) * math.sqrt(sum(v * v for v in second.values()))
    return dot / norm if norm else 0.0


class JevProvider:
    name = "jev"

    def __init__(self, *_arguments):
        raise ProviderNotApproved("'jev' is the pre-D-JEV name and refuses; hosted Jev runs as the "
                                  "brokered provider 'typesafe-jev' (configs/system_one_providers.yaml)")


