"""Seeded sub-RNG derivation and opaque identifiers.

Every random decision draws from a sub-RNG keyed by (seed, labels), so adding a new
consumer never shifts the stream of an existing one.
"""
import hashlib
import random

OPAQUE_HEX_LENGTH = 10  # 40 bits keeps ~3,000 ids collision-free in practice


def _digest(*parts: object) -> str:
    joined = "\x1f".join(str(part) for part in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def sub_rng(seed: int, *labels: object) -> random.Random:
    return random.Random(int(_digest(seed, *labels)[:16], 16))


def opaque_id(seed: int, prefix: str, key: str) -> str:
    """Stable opaque id such as art-3f09c1a2b4 or ent-77d0e1c9aa."""
    return f"{prefix}-{_digest(seed, prefix, key)[:OPAQUE_HEX_LENGTH]}"
