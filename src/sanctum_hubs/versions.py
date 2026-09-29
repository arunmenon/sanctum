"""Declared version reads (plan decision 6).

A read without a version returns the current version (highest revision in environment prod
or with no environment). A read with a version is honoured only where the hub, and for
DocHub the place, declares version reads; otherwise it is a typed `capability_unsupported`
error, never a silent fallback to the current version. Callers check access first, so the
capability error is only ever returned for items the caller may read.
"""
from __future__ import annotations

from typing import Optional

from .corpus import HubRow, HubStore
from .interfaces import ErrorCode, HubError, denied_or_not_found


def require_hub_version_reads(store: HubStore, version: Optional[str]) -> None:
    """For hubs with no version reads at all, refuse a version argument up front."""
    if version is not None and not store.contract.version_reads:
        raise HubError(ErrorCode.CAPABILITY_UNSUPPORTED, f"{store.hub_id} has no version reads")


def read_version(store: HubStore, artifact_id: str, version: Optional[str]) -> HubRow:
    """The row to return for an already-authorised artifact."""
    if version is None:
        row = store.current(artifact_id)
    else:
        latest = store.versions_of(artifact_id)[-1]
        if not store.capabilities.version_reads_for(latest.location):
            raise HubError(ErrorCode.CAPABILITY_UNSUPPORTED,
                           f"{latest.location or store.hub_id} has no version reads")
        row = store.at_version(artifact_id, version)
    if row is None:
        raise denied_or_not_found()
    return row


def visible_versions(store: HubStore, artifact_id: str) -> list[str]:
    """Versions a caller may name, in revision order; empty where version reads are absent."""
    rows = store.versions_of(artifact_id)
    if not rows or not store.capabilities.version_reads_for(rows[-1].location):
        return []
    return [row.version for row in rows]
