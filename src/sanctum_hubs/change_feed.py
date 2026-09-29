"""Append-only change feed (plan M2 decision 8).

Each admin mutation appends one line to `runs/<id>/change_feed.jsonl`:
`{seq, hub, kind, subject, at_revision, principal_scoped, prior_access, post_access}`. The raw
feed is lab-internal: subjects include restricted items and other principals, `seq` and
`at_revision` count every mutation, and `prior_access` / `post_access` record who could read
the subject just before and just after the mutation (ACL and owner of each affected row). It
never carries text, titles or paths.

A SUT gets only `ChangeFeed.events_for(claims, stores)`, a per-reader view of `ReaderEvent`
`{reader_seq, hub, kind, subject}`:

- an event is delivered when the reader could read its subject just before or just after the
  mutation, decided from what was recorded at write time and never from current store state,
  so a reader who just lost access still gets the invalidation, nobody learns that items they
  never could read exist, and a reader's history is append-only;
- `principal_revoked` is delivered only to the revoked principal;
- `reader_seq` numbers the delivered events densely (1, 2, ...) and is recomputed from the raw
  feed on every call; because visibility is fixed at write time the numbering is stable
  forever, so it is also the reader's `after_seq` cursor; no global `seq` or store revision is
  exposed, so hidden events leave no gaps.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Iterable, Iterator, Mapping, Optional

from .corpus import HubRow, HubStore
from .interfaces import TokenClaims

# Hub value for events that apply to every hub (principal revocation lives in the token service).
ALL_HUBS = "*"


class ChangeKind(StrEnum):
    PATH_RENAMED = "path_renamed"
    PLACE_UNSHARED = "place_unshared"
    PRINCIPAL_REVOKED = "principal_revoked"
    OWNER_CHANGED = "owner_changed"
    VERSION_PUBLISHED = "version_published"


@dataclass(frozen=True)
class PriorAccess:
    """Who could read one affected row before a mutation."""
    acl: tuple[str, ...]
    owner: Optional[str] = None

    @classmethod
    def of_rows(cls, rows: Iterable[HubRow]) -> tuple["PriorAccess", ...]:
        return tuple(sorted({cls(acl=tuple(sorted(row.acl)), owner=row.owner) for row in rows},
                            key=lambda access: (access.acl, access.owner or "")))


@dataclass(frozen=True)
class ChangeEvent:
    """A raw, lab-internal feed line."""
    seq: int
    hub: str
    kind: ChangeKind
    subject: str
    at_revision: int
    principal_scoped: bool = False
    prior_access: tuple[PriorAccess, ...] = ()
    post_access: tuple[PriorAccess, ...] = ()

    def to_dict(self) -> dict:
        data = asdict(self)
        data["kind"] = self.kind.value
        for name in ("prior_access", "post_access"):
            data[name] = [{"acl": list(access.acl), "owner": access.owner}
                          for access in getattr(self, name)]
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "ChangeEvent":
        def accesses(name: str) -> tuple[PriorAccess, ...]:
            return tuple(PriorAccess(acl=tuple(entry["acl"]), owner=entry.get("owner"))
                         for entry in data.get(name) or [])
        return cls(seq=int(data["seq"]), hub=str(data["hub"]), kind=ChangeKind(data["kind"]),
                   subject=str(data["subject"]), at_revision=int(data["at_revision"]),
                   principal_scoped=bool(data.get("principal_scoped", False)),
                   prior_access=accesses("prior_access"), post_access=accesses("post_access"))


@dataclass(frozen=True)
class ReaderEvent:
    """What one reader sees: an invalidation notice with no content and no global position."""
    reader_seq: int
    hub: str
    kind: ChangeKind
    subject: str


def _read_events(feed_path: Path) -> list[ChangeEvent]:
    if not feed_path.exists():
        return []
    with feed_path.open(encoding="utf-8") as feed:
        return [ChangeEvent.from_dict(json.loads(line)) for line in feed if line.strip()]


class ChangeFeedWriter:
    """Appends events with a strictly increasing `seq`, resuming after any existing lines."""

    def __init__(self, feed_path: Path):
        self.feed_path = Path(feed_path)
        existing = _read_events(self.feed_path)
        self._last_seq = existing[-1].seq if existing else 0

    def append(self, hub: str, kind: ChangeKind, subject: str, at_revision: int,
               principal_scoped: bool = False, prior_access: tuple[PriorAccess, ...] = (),
               post_access: tuple[PriorAccess, ...] = ()) -> ChangeEvent:
        event = ChangeEvent(seq=self._last_seq + 1, hub=hub, kind=ChangeKind(kind), subject=subject,
                            at_revision=int(at_revision), principal_scoped=principal_scoped,
                            prior_access=tuple(prior_access), post_access=tuple(post_access))
        self.feed_path.parent.mkdir(parents=True, exist_ok=True)
        with self.feed_path.open("a", encoding="utf-8") as feed:
            feed.write(json.dumps(event.to_dict(), sort_keys=True) + "\n")
        self._last_seq = event.seq
        return event


class ChangeFeed:
    """Read-only reader; exposes no way to write."""

    def __init__(self, feed_path: Path):
        self._feed_path = Path(feed_path)

    def events(self, after_seq: int = 0) -> list[ChangeEvent]:
        """The raw feed. Lab-internal: never hand this to a SUT."""
        return [event for event in _read_events(self._feed_path) if event.seq > after_seq]

    def __iter__(self) -> Iterator[ChangeEvent]:
        return iter(self.events())

    def events_for(self, claims: TokenClaims, stores: Optional[Mapping[str, HubStore]] = None,
                   after_seq: int = 0) -> list[ReaderEvent]:
        """The per-reader view; `after_seq` is a previously returned `reader_seq`.

        `stores` is accepted for call-site compatibility and deliberately unused: visibility
        comes only from the access recorded in each event at write time."""
        delivered = [event for event in _read_events(self._feed_path) if _delivered_to(event, claims)]
        return [ReaderEvent(reader_seq=position, hub=event.hub, kind=event.kind, subject=event.subject)
                for position, event in enumerate(delivered, start=1) if position > after_seq]


def _delivered_to(event: ChangeEvent, claims: TokenClaims) -> bool:
    if event.kind is ChangeKind.PRINCIPAL_REVOKED:
        return event.subject == claims.sub
    groups = set(claims.groups)
    return any(groups & set(access.acl) and (not event.principal_scoped or access.owner == claims.sub)
               for access in event.prior_access + event.post_access)
