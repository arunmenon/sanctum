"""Registry: owner manifests (`owners/manifests/<hub>.yaml`) validated into typed records.

The registry is policy input (HLD §5.1 stage 2). If it cannot be read or does not validate,
`load_registry` raises `RegistryUnavailable` and the pipeline fails closed: no hub is called
and the response claims nothing (HLD §10 Ex9, registry half of EX-09c).
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from sanctum_contracts import EvidenceKind, EvidenceRole


class RegistryUnavailable(RuntimeError):
    pass


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class SearchSpec(_Model):
    tool: str
    place_filter: Optional[str] = None
    version_filter: Optional[str] = None


class FetchSpec(_Model):
    tool: str
    id_field: str                      # hit field holding the id
    id_argument: str                   # tool argument that takes it
    version_argument: Optional[str] = None


class VersionSpec(_Model):
    semantics: str                     # release | revision | none
    releases: list[str] = Field(default_factory=list)
    environment_refs: dict[str, str] = Field(default_factory=dict)
    branch_by_environment: dict[str, str] = Field(default_factory=dict)


class Place(_Model):
    prefix: str
    groups: list[str]
    domain: str


class Trigger(_Model):
    domain: str
    fact_kind_needed: str


class Action(_Model):
    must_consult: str
    selector: dict[str, str] = Field(default_factory=dict)


class Procedure(_Model):
    procedure_id: str
    version: int
    status: str
    owner: str
    attested_by: str
    trigger: Trigger
    action: Action


class HubManifest(_Model):
    manifest_version: int
    hub_id: str
    owner: str
    evidence_kind: EvidenceKind
    role: EvidenceRole
    authority: dict[str, str]
    search: SearchSpec
    fetch: FetchSpec
    versions: VersionSpec
    places: list[Place]
    procedures: list[Procedure] = Field(default_factory=list)
    domains: dict[str, list[str]] = Field(default_factory=dict)

    def authoritative_for(self, fact_kind: str) -> bool:
        return self.authority.get(fact_kind) == "authoritative"

    def accessible(self, groups: set[str]) -> bool:
        return any(groups & set(place.groups) for place in self.places)

    def place_accessible(self, prefix: str, groups: set[str]) -> Optional[bool]:
        """True/False for a declared place covering `prefix`; None when undeclared."""
        for place in self.places:
            if prefix.startswith(place.prefix):
                return bool(groups & set(place.groups))
        return None


class Registry:
    def __init__(self, manifests: dict[str, HubManifest], version: str):
        self.manifests = manifests
        self.version = version

    def manifest(self, hub_id: str) -> Optional[HubManifest]:
        return self.manifests.get(hub_id)

    @property
    def procedures(self) -> list[Procedure]:
        return [procedure for manifest in self.manifests.values() for procedure in manifest.procedures
                if procedure.status == "accepted"]

    @property
    def domains(self) -> dict[str, set[str]]:
        merged: dict[str, set[str]] = {}
        for manifest in self.manifests.values():
            for domain, terms in manifest.domains.items():
                merged.setdefault(domain, set()).update(term.lower() for term in terms)
        return merged


def load_registry(directory: Path) -> Registry:
    directory = Path(directory)
    try:
        paths = sorted(directory.glob("*.yaml"))
        if not paths:
            raise RegistryUnavailable(f"no manifests under {directory}")
        digest = hashlib.sha256()
        manifests: dict[str, HubManifest] = {}
        for path in paths:
            raw = path.read_bytes()
            digest.update(path.name.encode() + b"\0" + raw)
            data: Any = yaml.safe_load(raw)
            manifest = HubManifest.model_validate(data)
            if manifest.hub_id in manifests:
                raise RegistryUnavailable(f"duplicate manifest for {manifest.hub_id}")
            manifests[manifest.hub_id] = manifest
    except (OSError, yaml.YAMLError, ValidationError) as error:
        raise RegistryUnavailable(f"registry unreadable: {type(error).__name__}") from None
    for manifest in manifests.values():
        for procedure in manifest.procedures:
            if procedure.action.must_consult not in manifests:
                raise RegistryUnavailable(f"{procedure.procedure_id} names unknown hub")
    return Registry(manifests, "registry-" + digest.hexdigest()[:12])
