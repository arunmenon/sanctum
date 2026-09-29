"""One hub's corpus: typed rows, versions and lab-only mutations (plan decisions 1, 3, 6, 8).

`HubStore.load(hub_dir)` reads exactly two files, `<hub_dir>/artifacts.jsonl` and
`<hub_dir>/capabilities.json`, from a directory shaped `.../hubs/<hub_id>`. It refuses any
other shape and any path with a `private` component, so a hub can never be pointed at the
evaluator's side of a build or at the authored world.

Mutations (`rename_path`, `set_acl`, `set_place_acl`, `set_owner`, `publish_version`) are for
the lab admin API only; each bumps `generation`, which the search index watches.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from sanctum_contracts import HubCapabilities

from .interfaces import ErrorCode, HubError

HUB_IDS = ("codehub", "skillhub", "dochub", "memoryhub", "incidenthub")
CORPUS_FILE = "artifacts.jsonl"
CAPABILITIES_FILE = "capabilities.json"
CURRENT_ENVIRONMENTS = (None, "prod")
# Name of a build's non-public directory component (compared to path parts, never joined).
PRIVATE_COMPONENT = "private"


class CorpusPathRefused(ValueError):
    pass


class HubRow(BaseModel):
    """One version of one artifact, exactly the public row keys the renderer writes."""
    model_config = ConfigDict(extra="forbid")

    acl: list[str]
    artifact_id: str
    environment: Optional[str]
    kind: str
    location: Optional[str]
    metadata: dict[str, Any]
    path: Optional[str]
    text: str
    title: str
    version: str

    @property
    def revision(self) -> int:
        return int(self.metadata.get("revision") or 0)

    @property
    def owner(self) -> Optional[str]:
        return self.metadata.get("principal")


class HubCapabilityDocument(BaseModel):
    """`capabilities.json`: the frozen contract plus per-place version reads."""
    model_config = ConfigDict(extra="forbid")

    contract: HubCapabilities
    place_version_reads: dict[str, bool] = Field(default_factory=dict)

    def version_reads_for(self, location: Optional[str]) -> bool:
        if not self.contract.version_reads:
            return False
        return self.place_version_reads.get(location or "", True)


def check_hub_dir(hub_dir: Path) -> Path:
    resolved = Path(hub_dir).resolve()
    for ancestor in resolved.parents:
        # A build's non-public directory sits beside its `hubs/` and `manifest.json`; system
        # directories that merely share the name (the macOS system var directory) are not refused.
        if ancestor.name == PRIVATE_COMPONENT and any(
                (ancestor.parent / sibling).exists() for sibling in ("hubs", "manifest.json")):
            raise CorpusPathRefused(f"{hub_dir}: hubs may not read non-public build output")
    if resolved.parent.name != "hubs" or resolved.name not in HUB_IDS:
        raise CorpusPathRefused(f"{hub_dir}: expected a directory shaped .../hubs/<hub_id>")
    for name in (CORPUS_FILE, CAPABILITIES_FILE):
        if not (resolved / name).is_file():
            raise CorpusPathRefused(f"{hub_dir}: missing {name}")
    return resolved


class HubStore:
    """In-memory rows of one hub, grouped by artifact and ordered by revision."""

    def __init__(self, hub_id: str, rows: list[HubRow], capabilities: HubCapabilityDocument):
        if capabilities.contract.hub_id != hub_id:
            raise ValueError(f"capabilities are for {capabilities.contract.hub_id}, not {hub_id}")
        self.hub_id = hub_id
        self.capabilities = capabilities
        self.generation = 0
        self._rows_by_artifact: dict[str, list[HubRow]] = {}
        for row in rows:
            self._rows_by_artifact.setdefault(row.artifact_id, []).append(row)
        for artifact_rows in self._rows_by_artifact.values():
            artifact_rows.sort(key=lambda row: row.revision)

    @classmethod
    def load(cls, hub_dir: Path) -> "HubStore":
        resolved = check_hub_dir(hub_dir)
        with (resolved / CORPUS_FILE).open(encoding="utf-8") as corpus:
            rows = [HubRow.model_validate_json(line) for line in corpus if line.strip()]
        capabilities = HubCapabilityDocument.model_validate(
            json.loads((resolved / CAPABILITIES_FILE).read_text(encoding="utf-8")))
        return cls(resolved.name, rows, capabilities)

    # ---- reads -----------------------------------------------------------------------------
    @property
    def contract(self) -> HubCapabilities:
        return self.capabilities.contract

    def artifact_ids(self) -> list[str]:
        return sorted(self._rows_by_artifact)

    def rows(self) -> list[HubRow]:
        return [row for artifact_id in self.artifact_ids() for row in self._rows_by_artifact[artifact_id]]

    def versions_of(self, artifact_id: str) -> list[HubRow]:
        return list(self._rows_by_artifact.get(artifact_id, []))

    def current(self, artifact_id: str) -> Optional[HubRow]:
        """Highest revision in environment prod or no environment; None if only experiments."""
        candidates = [row for row in self._rows_by_artifact.get(artifact_id, [])
                      if row.environment in CURRENT_ENVIRONMENTS]
        return candidates[-1] if candidates else None

    def current_rows(self) -> list[HubRow]:
        return [row for row in (self.current(artifact_id) for artifact_id in self.artifact_ids()) if row]

    def at_version(self, artifact_id: str, version: str) -> Optional[HubRow]:
        return next((row for row in self._rows_by_artifact.get(artifact_id, []) if row.version == version),
                    None)

    def ids_with_path(self, path: str) -> list[str]:
        return sorted(artifact_id for artifact_id, artifact_rows in self._rows_by_artifact.items()
                      if any(row.path == path for row in artifact_rows))

    def ids_with_session(self, session: str) -> list[str]:
        return sorted(artifact_id for artifact_id, artifact_rows in self._rows_by_artifact.items()
                      if any(row.metadata.get("session") == session for row in artifact_rows))

    def locations(self) -> list[str]:
        return sorted({row.location for row in self.rows() if row.location})

    # ---- lab-only mutations (admin API) -------------------------------------------------------
    def _require(self, artifact_id: str) -> list[HubRow]:
        if artifact_id not in self._rows_by_artifact:
            raise HubError(ErrorCode.INVALID_ARGUMENT, f"unknown artifact {artifact_id}")
        return self._rows_by_artifact[artifact_id]

    def _replace(self, artifact_id: str, artifact_rows: list[HubRow]) -> None:
        self._rows_by_artifact[artifact_id] = sorted(artifact_rows, key=lambda row: row.revision)
        self.generation += 1

    def rename_path(self, artifact_id: str, new_path: str) -> None:
        self._replace(artifact_id, [row.model_copy(update={"path": new_path})
                                    for row in self._require(artifact_id)])

    def set_acl(self, artifact_id: str, acl: list[str]) -> None:
        self._replace(artifact_id, [row.model_copy(update={"acl": sorted(acl)})
                                    for row in self._require(artifact_id)])

    def set_place_acl(self, location: str, acl: list[str]) -> list[str]:
        """Change the ACL of every artifact in a place; returns the affected artifact ids."""
        affected = sorted(artifact_id for artifact_id, artifact_rows in self._rows_by_artifact.items()
                          if any(row.location == location for row in artifact_rows))
        for artifact_id in affected:
            self.set_acl(artifact_id, acl)
        return affected

    def set_owner(self, artifact_id: str, principal: str) -> None:
        if not self.contract.principal_scoped:
            raise HubError(ErrorCode.CAPABILITY_UNSUPPORTED, "owner applies to principal-scoped hubs")
        self._replace(artifact_id, [
            row.model_copy(update={"metadata": {**row.metadata, "principal": principal}})
            for row in self._require(artifact_id)])

    def publish_version(self, artifact_id: str, version: str, text: str,
                        environment: Optional[str] = None) -> HubRow:
        """Append a new revision copied from the latest one, with new version, text and env.

        Where the place has no version reads the hub keeps one version, so the content is
        overwritten in place and `version` is ignored (as a real wiki or memory store would)."""
        artifact_rows = self._require(artifact_id)
        latest = artifact_rows[-1]
        if not self.capabilities.version_reads_for(latest.location):
            overwritten = latest.model_copy(update={"text": text, "environment": environment})
            self._replace(artifact_id, artifact_rows[:-1] + [overwritten])
            return overwritten
        if any(row.version == version for row in artifact_rows):
            raise HubError(ErrorCode.INVALID_ARGUMENT, f"version {version} already exists")
        new_row = latest.model_copy(update={
            "version": version, "text": text, "environment": environment,
            "metadata": {**latest.metadata, "revision": latest.revision + 1}})
        self._replace(artifact_id, artifact_rows + [new_row])
        return new_row
