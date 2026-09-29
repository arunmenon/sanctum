"""Independent token recount of a response's evidence (discrepancy register 9).

The budget counts the serialized evidence list: `json.dumps([unit, ...], sort_keys=True)` over the
units' JSON form, encoded with the matrix tokenizer (cl100k_base). The evaluator recounts it
rather than trusting the SUT's `budget.used`.
"""
import json
from functools import lru_cache

import tiktoken

from sanctum_contracts import EvidenceResponse

TOKENIZER = "cl100k_base"


@lru_cache(maxsize=4)
def _encoding(name: str):
    return tiktoken.get_encoding(name)


def evidence_tokens(response: EvidenceResponse, tokenizer: str = TOKENIZER) -> int:
    return serialized_evidence_tokens([unit.model_dump(mode="json") for unit in response.evidence], tokenizer)


def serialized_evidence_tokens(evidence: list[dict], tokenizer: str = TOKENIZER) -> int:
    """Same count from a response row as written to responses.jsonl (the units' JSON form)."""
    return len(_encoding(tokenizer).encode(json.dumps(evidence, sort_keys=True)))
