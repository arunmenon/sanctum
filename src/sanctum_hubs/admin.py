"""Lab-only admin API (plan M2 decision 8).

`AdminClient` mutates live `HubStore`s and the `TokenService`, and records one change-feed
event per mutation. It is never registered as an MCP tool; only lab code holding the admin
secret can construct one. `at_revision` is the hub store's `generation` after the mutation
(monotonic per hub, which the search index also watches); revocation is hub-independent and
records 0. Each event also records who could read the subject before the mutation, and after it,
so the per-reader feed view is decided at write time and can notify readers who just lost
access.
"""
from __future__ import annotations

import hmac
from pathlib import Path
from typing import Mapping, Optional

from .change_feed import ALL_HUBS, ChangeEvent, ChangeFeedWriter, ChangeKind, PriorAccess
from .corpus import HubRow, HubStore
from .tokens import TokenService


class AdminDenied(PermissionError):
    pass


class AdminClient:
    def __init__(self, admin_secret: str, expected_admin_secret: str, stores: Mapping[str, HubStore],
                 token_service: TokenService, feed_path: Path):
        if not expected_admin_secret or not hmac.compare_digest(
                admin_secret.encode("utf-8"), expected_admin_secret.encode("utf-8")):
            raise AdminDenied("admin secret rejected")
        self._stores = dict(stores)
        self._token_service = token_service
        self._feed = ChangeFeedWriter(feed_path)

    def _store(self, hub: str) -> HubStore:
        if hub not in self._stores:
            raise KeyError(f"no live store for hub {hub}")
        return self._stores[hub]

    def _record(self, store: HubStore, kind: ChangeKind, subject: str,
                prior_access: tuple[PriorAccess, ...], post_access: tuple[PriorAccess, ...]) -> ChangeEvent:
        return self._feed.append(store.hub_id, kind, subject, store.generation,
                                 store.contract.principal_scoped, prior_access, post_access)

    def rename_path(self, hub: str, artifact_id: str, new_path: str) -> ChangeEvent:
        store = self._store(hub)
        prior_access = PriorAccess.of_rows(store.versions_of(artifact_id))
        store.rename_path(artifact_id, new_path)
        return self._record(store, ChangeKind.PATH_RENAMED, artifact_id, prior_access,
                            PriorAccess.of_rows(store.versions_of(artifact_id)))

    def unshare_place(self, hub: str, location: str, acl: list[str]) -> ChangeEvent:
        """Replace the ACL of every artifact in `location` (typically narrowing it)."""
        store = self._store(hub)
        prior_access = PriorAccess.of_rows(row for row in store.rows() if row.location == location)
        store.set_place_acl(location, acl)
        return self._record(store, ChangeKind.PLACE_UNSHARED, location, prior_access,
                            PriorAccess.of_rows(row for row in store.rows() if row.location == location))

    def change_owner(self, hub: str, artifact_id: str, principal: str) -> ChangeEvent:
        store = self._store(hub)
        prior_access = PriorAccess.of_rows(store.versions_of(artifact_id))
        store.set_owner(artifact_id, principal)
        return self._record(store, ChangeKind.OWNER_CHANGED, artifact_id, prior_access,
                            PriorAccess.of_rows(store.versions_of(artifact_id)))

    def publish_version(self, hub: str, artifact_id: str, version: str, text: str,
                        environment: Optional[str] = None) -> tuple[HubRow, ChangeEvent]:
        store = self._store(hub)
        prior_access = PriorAccess.of_rows(store.versions_of(artifact_id))
        new_row = store.publish_version(artifact_id, version, text, environment=environment)
        return new_row, self._record(store, ChangeKind.VERSION_PUBLISHED, artifact_id, prior_access,
                                     PriorAccess.of_rows(store.versions_of(artifact_id)))

    def revoke_principal(self, principal: str) -> ChangeEvent:
        self._token_service.revoke(principal)
        return self._feed.append(ALL_HUBS, ChangeKind.PRINCIPAL_REVOKED, principal, 0)
