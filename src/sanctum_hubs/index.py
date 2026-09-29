"""Honest per-hub search: SQLite FTS5 BM25, no stemming, no synonyms (plan decision 5).

The index holds every row of the hub. Access (ACL groups, principal scope), version scope
and filters are applied inside the SQL before `LIMIT`, so neither the results nor
`total_matches` can ever include a row the caller may not read. User text never reaches FTS
syntax: it is split into word tokens, each token is double-quoted, and tokens are OR-joined.
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from typing import Optional

from .corpus import HubStore
from .interfaces import ErrorCode, HubError, TokenClaims

WORD = re.compile(r"[^\W_]+")
SNIPPET_TOKENS = 16
MAX_QUERY_CHARS = 4000
MAX_QUERY_TOKENS = 64


@dataclass(frozen=True)
class SearchFilters:
    """Filters in hub-native terms, already normalised by the server."""
    location: Optional[str] = None       # CodeHub repo, DocHub space, IncidentHub queue
    path_prefix: Optional[str] = None    # SkillHub
    version: Optional[str] = None        # CodeHub ref; None means current versions only


@dataclass(frozen=True)
class SearchHit:
    artifact_id: str
    title: str
    location: Optional[str]
    path: Optional[str]
    version: str
    environment: Optional[str]
    snippet: str
    score: float

    def to_dict(self) -> dict:
        return {"artifact_id": self.artifact_id, "title": self.title, "location": self.location,
                "path": self.path, "version": self.version, "environment": self.environment,
                "snippet": self.snippet, "score": self.score}


def match_expression(query: str) -> str:
    """Distinct word tokens (first occurrence order, case-insensitive), each quoted, OR-joined.
    Bounded so a long query cannot make search cost grow without limit."""
    if len(query or "") > MAX_QUERY_CHARS:
        raise HubError(ErrorCode.INVALID_ARGUMENT, f"query longer than {MAX_QUERY_CHARS} characters")
    tokens = list(dict.fromkeys(token.lower() for token in WORD.findall(query or "")))
    if not tokens:
        raise HubError(ErrorCode.INVALID_ARGUMENT, "query has no searchable words")
    if len(tokens) > MAX_QUERY_TOKENS:
        raise HubError(ErrorCode.INVALID_ARGUMENT, f"query has more than {MAX_QUERY_TOKENS} distinct words")
    return " OR ".join('"' + token + '"' for token in tokens)


class HubIndex:
    """In-memory FTS5 index of one `HubStore`, rebuilt when the store's generation changes."""

    def __init__(self, store: HubStore):
        self.store = store
        self._generation = -1
        self._connection: Optional[sqlite3.Connection] = None

    def _rebuild(self) -> sqlite3.Connection:
        connection = sqlite3.connect(":memory:")
        connection.executescript("""
            CREATE TABLE rows (
                row_number INTEGER PRIMARY KEY, artifact_id TEXT NOT NULL, version TEXT NOT NULL,
                is_current INTEGER NOT NULL, location TEXT, path TEXT, environment TEXT,
                owner TEXT, title TEXT NOT NULL);
            CREATE TABLE row_groups (row_number INTEGER NOT NULL, group_name TEXT NOT NULL);
            CREATE INDEX row_groups_by_row ON row_groups (row_number, group_name);
            CREATE VIRTUAL TABLE documents USING fts5(title, text, native, tokenize = 'unicode61');
        """)
        current = {(row.artifact_id, row.version) for row in self.store.current_rows()}
        for row_number, row in enumerate(self.store.rows(), start=1):
            connection.execute(
                "INSERT INTO rows VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (row_number, row.artifact_id, row.version, int((row.artifact_id, row.version) in current),
                 row.location, row.path, row.environment, row.owner, row.title))
            connection.executemany("INSERT INTO row_groups VALUES (?, ?)",
                                   [(row_number, group) for group in row.acl])
            connection.execute("INSERT INTO documents (rowid, title, text, native) VALUES (?, ?, ?, ?)",
                               (row_number, row.title, row.text,
                                " ".join(part for part in (row.location, row.path) if part)))
        connection.commit()
        return connection

    def connection(self) -> sqlite3.Connection:
        if self._connection is None or self._generation != self.store.generation:
            if self._connection is not None:
                self._connection.close()
            self._connection = self._rebuild()
            self._generation = self.store.generation
        return self._connection

    def _scope_sql(self, claims: TokenClaims, filters: SearchFilters) -> tuple[str, list]:
        """WHERE clauses over `rows AS r` for access, version scope and filters."""
        groups = sorted(set(claims.groups))
        clauses = [f"EXISTS (SELECT 1 FROM row_groups g WHERE g.row_number = r.row_number "
                   f"AND g.group_name IN ({', '.join('?' for _ in groups) or 'NULL'}))"]
        parameters: list = list(groups)
        if self.store.contract.principal_scoped:
            clauses.append("r.owner = ?")
            parameters.append(claims.sub)
        if filters.version is None:
            clauses.append("r.is_current = 1")
        else:
            clauses.append("r.version = ?")
            parameters.append(filters.version)
        if filters.location is not None:
            clauses.append("r.location = ?")
            parameters.append(filters.location)
        if filters.path_prefix is not None:
            clauses.append("substr(r.path, 1, ?) = ?")
            parameters += [len(filters.path_prefix), filters.path_prefix]
        return " AND ".join(clauses), parameters

    def search(self, query: str, claims: TokenClaims, filters: SearchFilters,
               top_k: int) -> tuple[list[SearchHit], int]:
        """Return (hits ordered by BM25 then artifact_id, total visible matches)."""
        expression = match_expression(query)
        scope, scope_parameters = self._scope_sql(claims, filters)
        connection = self.connection()
        base = (f"FROM documents JOIN rows r ON r.row_number = documents.rowid "
                f"WHERE documents MATCH ? AND {scope}")
        parameters = [expression] + scope_parameters
        total = connection.execute(f"SELECT count(*) {base}", parameters).fetchone()[0]
        selected = connection.execute(
            f"SELECT r.artifact_id, r.title, r.location, r.path, r.version, r.environment, "
            f"snippet(documents, 1, '', '', ' ... ', {SNIPPET_TOKENS}), bm25(documents) AS rank "
            f"{base} ORDER BY rank, r.artifact_id, r.version LIMIT ?",
            parameters + [top_k]).fetchall()
        hits = [SearchHit(artifact_id, title, location, path, version, environment, snippet,
                          round(-rank, 6))
                for artifact_id, title, location, path, version, environment, snippet, rank in selected]
        return hits, total

