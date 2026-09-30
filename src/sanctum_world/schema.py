"""Pydantic models for world/world.yaml (lab plan §5.1).

The world file is the single authored ground truth. `World` resolves every cross
reference (entity, fact, release, hub, principal group, artifact, planted target) and
raises with the offending path, so a broken world never reaches the renderer.
"""
import re
from pathlib import Path
from typing import Annotated, Literal, Optional, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

HUB_IDS = ("codehub", "skillhub", "dochub", "memoryhub", "incidenthub")
FACT_SLOT = re.compile(r"\{\{fact:([^}]+)\}\}")
ASSERTION = re.compile(r"^(?P<fact>[^@]+)@(?P<release>[^/]+)(?:/(?P<env>.+))?$")


class _W(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Principal(_W):
    id: str
    groups: list[str] = Field(min_length=1)


class Entity(_W):
    id: str
    type: Literal["service", "domain", "topic"]
    member_of: Optional[str] = None


class Branch(_W):
    id: str
    base: str
    env: str


class FactValue(_W):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)
    value: Union[int, float, str]
    from_release: str = Field(alias="from")
    env: Optional[str] = None
    branch: Optional[str] = None


class Fact(_W):
    id: str
    entity: str
    fact_kind: Literal["implemented", "procedure", "policy", "incident"]
    attribute: str
    values: list[FactValue] = Field(min_length=1)


class HubName(_W):
    native: str
    namespace: Optional[str] = None
    denotes: str


class HubPlace(_W):
    native: str
    selects_for: Optional[str] = None
    acl: list[str] = Field(default_factory=list)


class HubCapabilities(_W):
    version_reads: Union[bool, dict[str, bool]]
    filters: list[str] = Field(default_factory=list)


class HubSpec(_W):
    names: list[HubName] = Field(default_factory=list)
    places: list[HubPlace] = Field(default_factory=list)
    capabilities: HubCapabilities
    held_back: bool = False

    def declared_natives(self) -> list[str]:
        natives = [name.native for name in self.names] + [place.native for place in self.places]
        return sorted(set(natives))

    def place(self, native: str) -> Optional[HubPlace]:
        return next((place for place in self.places if place.native == native), None)

    def version_reads_for(self, place_native: Optional[str]) -> bool:
        reads = self.capabilities.version_reads
        if isinstance(reads, bool):
            return reads
        return reads.get(place_native or "", True)


class ArtifactVersion(_W):
    ref: str
    env: Optional[str] = None
    asserts: list[str] = Field(default_factory=list)   # "fact@release[/env]"


class Artifact(_W):
    id: str
    hub: str
    kind: str                           # template name under world/templates/<hub>/ or shared/
    title: str
    path: Optional[str] = None
    place: Optional[str] = None         # declared native place in this hub
    name: Optional[str] = None          # declared native name in this hub
    namespace: Optional[str] = None
    principal: Optional[str] = None     # memoryhub session owner
    body: Optional[str] = None          # text with {{fact:<id>}} slots
    versions: list[ArtifactVersion] = Field(min_length=1)
    about: list[str] = Field(default_factory=list)
    acl: Optional[list[str]] = None     # defaults to the place acl
    canaries: list[str] = Field(default_factory=list)
    copy_of: Optional[str] = None       # byte-identical copy of another artifact's text


class _PlantedBase(_W):
    id: str


class PlantedHomonym(_PlantedBase):
    kind: Literal["homonym"]
    name: str
    hub: str
    entities: list[str] = Field(min_length=2)


class PlantedHubSpecificNames(_PlantedBase):
    kind: Literal["hub_specific_names"]
    entity: str
    names: dict[str, str] = Field(min_length=2)       # hub -> native name or place


class PlantedConflict(_PlantedBase):
    kind: Literal["conflict"]
    facts: list[str] = Field(min_length=2, max_length=2)
    at: str
    artifacts: list[str] = Field(min_length=2)


class PlantedVersionBranching(_PlantedBase):
    kind: Literal["version_branching"]
    artifact: str
    refs: list[str] = Field(min_length=3)


class PlantedNewerNotApplicable(_PlantedBase):
    kind: Literal["newer_not_applicable"]
    artifact: str
    newer_ref: str
    applicable_ref: str


class PlantedExactDuplicate(_PlantedBase):
    kind: Literal["exact_duplicate"]
    artifacts: list[str] = Field(min_length=2)


class PlantedCompositeSubject(_PlantedBase):
    kind: Literal["composite_subject"]
    artifact: str
    about: list[str] = Field(min_length=2)


class PlantedCoverageGap(_PlantedBase):
    kind: Literal["coverage_gap"]
    entity: str


class PlantedInjection(_PlantedBase):
    kind: Literal["injection"]
    artifact: str
    instruction: str


class PlantedRestricted(_PlantedBase):
    kind: Literal["restricted"]
    hub: str
    place: str


class PlantedCapabilityGap(_PlantedBase):
    kind: Literal["capability_gap"]
    hub: str
    place: str
    capability: Literal["version_reads"]


class PlantedMultiHubFact(_PlantedBase):
    kind: Literal["multi_hub_fact"]
    facts: list[str] = Field(min_length=2)
    artifacts: list[str] = Field(min_length=2)


class PlantedRuleMissedRelation(_PlantedBase):
    """D6 challenge slice (added after E3, for measurement): implemented values restated by
    procedure and policy artifacts in other wording or units, so typed rules see noise; policy
    equals procedure, so their pair is a hard negative."""
    kind: Literal["rule_missed_relation"]
    facts: list[str] = Field(min_length=2)
    artifacts: list[str] = Field(min_length=2)


Planted = Annotated[
    Union[
        PlantedHomonym, PlantedHubSpecificNames, PlantedConflict, PlantedVersionBranching,
        PlantedNewerNotApplicable, PlantedExactDuplicate, PlantedCompositeSubject,
        PlantedCoverageGap, PlantedInjection, PlantedRestricted, PlantedCapabilityGap,
        PlantedMultiHubFact, PlantedRuleMissedRelation,
    ],
    Field(discriminator="kind"),
]
PLANTED_KINDS = (
    "homonym", "hub_specific_names", "conflict", "version_branching", "newer_not_applicable",
    "exact_duplicate", "composite_subject", "coverage_gap", "injection", "restricted",
    "capability_gap", "multi_hub_fact", "rule_missed_relation",
)


class FillerSpec(_W):
    file: str = "filler.yaml"


class Assertion(_W):
    fact: str
    release: str
    env: Optional[str] = None


def parse_assertion(text: str) -> Assertion:
    match = ASSERTION.match(text)
    if not match:
        raise ValueError(f"assertion {text!r} is not fact@release[/env]")
    return Assertion(fact=match["fact"], release=match["release"], env=match["env"])


class World(_W):
    world_version: int
    seed: int
    principals: list[Principal] = Field(min_length=1)
    entities: list[Entity] = Field(min_length=1)
    releases: list[str] = Field(min_length=1)
    branches: list[Branch] = Field(default_factory=list)
    environments: list[str] = Field(min_length=1)
    facts: list[Fact] = Field(default_factory=list)
    hubs: dict[str, HubSpec]
    artifacts: list[Artifact] = Field(default_factory=list)
    planted: list[Planted] = Field(default_factory=list)
    filler: FillerSpec = FillerSpec()

    # ---- lookups -------------------------------------------------------------------
    def entity(self, entity_id: str) -> Entity:
        return next(entity for entity in self.entities if entity.id == entity_id)

    def fact(self, fact_id: str) -> Fact:
        return next(fact for fact in self.facts if fact.id == fact_id)

    def artifact(self, artifact_id: str) -> Artifact:
        return next(artifact for artifact in self.artifacts if artifact.id == artifact_id)

    def release_index(self, release: str) -> int:
        return self.releases.index(release)

    def version_refs(self) -> list[str]:
        return list(self.releases) + [branch.id for branch in self.branches]

    def resolve_value(self, assertion: Assertion) -> FactValue:
        """Value in effect for a fact at a release and environment (latest `from` <= release;
        an environment-specific value beats an environment-free one at the same release)."""
        fact = self.fact(assertion.fact)
        target_index = self.release_index(assertion.release)
        target_env = assertion.env or "prod"
        candidates = [
            value for value in fact.values
            if self.release_index(value.from_release) <= target_index
            and (value.env is None or value.env == target_env)
        ]
        if not candidates:
            raise ValueError(f"fact {assertion.fact} has no value at {assertion.release}/{target_env}")
        return max(
            candidates,
            key=lambda value: (self.release_index(value.from_release), value.env is not None),
        )

    def all_group_ids(self) -> list[str]:
        return sorted({group for principal in self.principals for group in principal.groups})

    # ---- validation ----------------------------------------------------------------
    @model_validator(mode="after")
    def _resolve_references(self):
        errors: list[str] = []

        def unique(label: str, identifiers: list[str]) -> None:
            seen: set[str] = set()
            for identifier in identifiers:
                if identifier in seen:
                    errors.append(f"{label}: duplicate id {identifier!r}")
                seen.add(identifier)

        unique("principals", [principal.id for principal in self.principals])
        unique("entities", [entity.id for entity in self.entities])
        unique("facts", [fact.id for fact in self.facts])
        unique("artifacts", [artifact.id for artifact in self.artifacts])
        unique("planted", [planted.id for planted in self.planted])
        unique("releases", self.version_refs())

        entity_ids = {entity.id for entity in self.entities}
        fact_ids = {fact.id for fact in self.facts}
        artifact_ids = {artifact.id for artifact in self.artifacts}
        group_ids = set(self.all_group_ids())
        principal_ids = {principal.id for principal in self.principals}
        releases = set(self.releases)
        environments = set(self.environments)
        branch_ids = {branch.id for branch in self.branches}

        for index, entity in enumerate(self.entities):
            if entity.member_of and entity.member_of not in entity_ids:
                errors.append(f"entities[{index}].member_of: unknown entity {entity.member_of!r}")
        for index, branch in enumerate(self.branches):
            if branch.base not in releases:
                errors.append(f"branches[{index}].base: unknown release {branch.base!r}")
            if branch.env not in environments:
                errors.append(f"branches[{index}].env: unknown environment {branch.env!r}")
        for fact_index, fact in enumerate(self.facts):
            if fact.entity not in entity_ids:
                errors.append(f"facts[{fact_index}].entity: unknown entity {fact.entity!r}")
            for value_index, value in enumerate(fact.values):
                where = f"facts[{fact_index}].values[{value_index}]"
                if value.from_release not in releases:
                    errors.append(f"{where}.from: unknown release {value.from_release!r}")
                if value.env and value.env not in environments:
                    errors.append(f"{where}.env: unknown environment {value.env!r}")
                if value.branch and value.branch not in branch_ids:
                    errors.append(f"{where}.branch: unknown branch {value.branch!r}")

        for hub_id, hub in self.hubs.items():
            if hub_id not in HUB_IDS:
                errors.append(f"hubs.{hub_id}: unknown hub")
            for index, name in enumerate(hub.names):
                if name.denotes not in entity_ids:
                    errors.append(f"hubs.{hub_id}.names[{index}].denotes: unknown entity {name.denotes!r}")
            for index, place in enumerate(hub.places):
                if place.selects_for and place.selects_for not in entity_ids:
                    errors.append(
                        f"hubs.{hub_id}.places[{index}].selects_for: unknown entity {place.selects_for!r}")
                for group in place.acl:
                    if group not in group_ids:
                        errors.append(f"hubs.{hub_id}.places[{index}].acl: unknown group {group!r}")
            if isinstance(hub.capabilities.version_reads, dict):
                for place_native in hub.capabilities.version_reads:
                    if hub.place(place_native) is None:
                        errors.append(
                            f"hubs.{hub_id}.capabilities.version_reads: unknown place {place_native!r}")

        if not errors:
            self._validate_artifacts(errors, entity_ids, fact_ids, artifact_ids, group_ids, principal_ids)
        if not errors:
            self._validate_planted(errors, entity_ids, fact_ids, artifact_ids)
        if errors:
            raise ValueError("world validation failed:\n  " + "\n  ".join(errors))
        return self

    def _validate_artifacts(self, errors, entity_ids, fact_ids, artifact_ids, group_ids, principal_ids):
        environments = set(self.environments)
        for index, artifact in enumerate(self.artifacts):
            where = f"artifacts[{index}] ({artifact.id})"
            hub = self.hubs.get(artifact.hub)
            if hub is None:
                errors.append(f"{where}.hub: unknown hub {artifact.hub!r}")
                continue
            if artifact.place and hub.place(artifact.place) is None:
                errors.append(f"{where}.place: {artifact.place!r} not declared by {artifact.hub}")
            if artifact.name and artifact.name not in [name.native for name in hub.names]:
                errors.append(f"{where}.name: {artifact.name!r} not declared by {artifact.hub}")
            if artifact.principal and artifact.principal not in principal_ids:
                errors.append(f"{where}.principal: unknown principal {artifact.principal!r}")
            for group in artifact.acl or []:
                if group not in group_ids:
                    errors.append(f"{where}.acl: unknown group {group!r}")
            for entity_id in artifact.about:
                if entity_id not in entity_ids:
                    errors.append(f"{where}.about: unknown entity {entity_id!r}")
            if artifact.copy_of:
                if artifact.copy_of not in artifact_ids:
                    errors.append(f"{where}.copy_of: unknown artifact {artifact.copy_of!r}")
                    continue
                source = self.artifact(artifact.copy_of)
                if source.copy_of:
                    errors.append(f"{where}.copy_of: chained copies are not supported")
                if len(source.versions) != len(artifact.versions):
                    errors.append(f"{where}.versions: copy must have as many versions as its source")
                if artifact.body is not None:
                    errors.append(f"{where}.body: a copy takes its text from copy_of")
            elif artifact.body is None:
                errors.append(f"{where}.body: required unless copy_of is set")
            if not hub.version_reads_for(artifact.place) and len(artifact.versions) != 1:
                errors.append(f"{where}.versions: {artifact.place} has no version reads, one version only")
            slot_facts = sorted(set(FACT_SLOT.findall(artifact.body or "")))
            for version_index, version in enumerate(artifact.versions):
                version_where = f"{where}.versions[{version_index}]"
                if artifact.hub == "codehub" and version.ref not in self.version_refs():
                    errors.append(f"{version_where}.ref: unknown release or branch {version.ref!r}")
                if version.env and version.env not in environments:
                    errors.append(f"{version_where}.env: unknown environment {version.env!r}")
                if artifact.copy_of:
                    if version.asserts:
                        errors.append(f"{version_where}.asserts: a copy inherits assertions")
                    continue
                asserted_facts = []
                for assertion_text in version.asserts:
                    try:
                        assertion = parse_assertion(assertion_text)
                    except ValueError as error:
                        errors.append(f"{version_where}.asserts: {error}")
                        continue
                    if assertion.fact not in fact_ids:
                        errors.append(f"{version_where}.asserts: unknown fact {assertion.fact!r}")
                        continue
                    if assertion.release not in self.releases:
                        errors.append(f"{version_where}.asserts: unknown release {assertion.release!r}")
                        continue
                    if assertion.env and assertion.env not in environments:
                        errors.append(f"{version_where}.asserts: unknown environment {assertion.env!r}")
                        continue
                    try:
                        self.resolve_value(assertion)
                    except ValueError as error:
                        errors.append(f"{version_where}.asserts: {error}")
                    asserted_facts.append(assertion.fact)
                if sorted(set(asserted_facts)) != slot_facts:
                    errors.append(
                        f"{version_where}.asserts: facts {sorted(set(asserted_facts))} do not match "
                        f"body slots {slot_facts}")

    def _validate_planted(self, errors, entity_ids, fact_ids, artifact_ids):
        def need(where: str, kind: str, identifier: str, known: set[str]) -> None:
            if identifier not in known:
                errors.append(f"{where}: unknown {kind} {identifier!r}")

        hub_ids = set(self.hubs)
        asserted = self.asserted_fact_ids()
        for index, planted in enumerate(self.planted):
            where = f"planted[{index}] ({planted.id})"
            if isinstance(planted, PlantedHomonym):
                need(f"{where}.hub", "hub", planted.hub, hub_ids)
                for entity_id in planted.entities:
                    need(f"{where}.entities", "entity", entity_id, entity_ids)
                if planted.hub in self.hubs:
                    denoted = sorted({name.denotes for name in self.hubs[planted.hub].names
                                      if name.native == planted.name})
                    if denoted != sorted(planted.entities):
                        errors.append(f"{where}: {planted.name!r} in {planted.hub} denotes {denoted}")
            elif isinstance(planted, PlantedHubSpecificNames):
                need(f"{where}.entity", "entity", planted.entity, entity_ids)
                for hub_id, native in planted.names.items():
                    if hub_id not in self.hubs:
                        errors.append(f"{where}.names: unknown hub {hub_id!r}")
                        continue
                    hub = self.hubs[hub_id]
                    denotes = [name.denotes for name in hub.names if name.native == native]
                    selects = [place.selects_for for place in hub.places if place.native == native]
                    if planted.entity not in denotes + selects:
                        errors.append(f"{where}.names.{hub_id}: {native!r} does not denote {planted.entity}")
            elif isinstance(planted, PlantedConflict):
                for fact_id in planted.facts:
                    need(f"{where}.facts", "fact", fact_id, fact_ids)
                for artifact_id in planted.artifacts:
                    need(f"{where}.artifacts", "artifact", artifact_id, artifact_ids)
                if planted.at not in self.releases:
                    errors.append(f"{where}.at: unknown release {planted.at!r}")
            elif isinstance(planted, (PlantedVersionBranching, PlantedNewerNotApplicable)):
                need(f"{where}.artifact", "artifact", planted.artifact, artifact_ids)
                if planted.artifact in artifact_ids:
                    refs = [version.ref for version in self.artifact(planted.artifact).versions]
                    wanted = (planted.refs if isinstance(planted, PlantedVersionBranching)
                              else [planted.newer_ref, planted.applicable_ref])
                    for ref in wanted:
                        if ref not in refs:
                            errors.append(f"{where}: artifact has no version {ref!r}")
                    if isinstance(planted, PlantedNewerNotApplicable) and not errors:
                        if refs.index(planted.newer_ref) <= refs.index(planted.applicable_ref):
                            errors.append(f"{where}: newer_ref must come after applicable_ref")
            elif isinstance(planted, PlantedExactDuplicate):
                for artifact_id in planted.artifacts:
                    need(f"{where}.artifacts", "artifact", artifact_id, artifact_ids)
                if all(artifact_id in artifact_ids for artifact_id in planted.artifacts):
                    roots = {self.artifact(artifact_id).copy_of or artifact_id
                             for artifact_id in planted.artifacts}
                    hubs = {self.artifact(artifact_id).hub for artifact_id in planted.artifacts}
                    if len(roots) != 1:
                        errors.append(f"{where}: artifacts are not copies of one source")
                    if len(hubs) < 2:
                        errors.append(f"{where}: duplicates must span at least two hubs")
            elif isinstance(planted, PlantedCompositeSubject):
                need(f"{where}.artifact", "artifact", planted.artifact, artifact_ids)
                for entity_id in planted.about:
                    need(f"{where}.about", "entity", entity_id, entity_ids)
                if planted.artifact in artifact_ids:
                    about = set(self.artifact(planted.artifact).about)
                    if not set(planted.about) <= about:
                        errors.append(f"{where}: artifact is not about all of {planted.about}")
            elif isinstance(planted, PlantedCoverageGap):
                need(f"{where}.entity", "entity", planted.entity, entity_ids)
                gap_facts = [fact.id for fact in self.facts if fact.entity == planted.entity]
                if not gap_facts:
                    errors.append(f"{where}: coverage gap entity has no facts")
                for fact_id in gap_facts:
                    if fact_id in asserted:
                        errors.append(f"{where}: fact {fact_id} is asserted by an artifact")
            elif isinstance(planted, PlantedInjection):
                need(f"{where}.artifact", "artifact", planted.artifact, artifact_ids)
                if planted.artifact in artifact_ids:
                    if planted.instruction not in (self.artifact(planted.artifact).body or ""):
                        errors.append(f"{where}: instruction text not in artifact body")
            elif isinstance(planted, (PlantedRestricted, PlantedCapabilityGap)):
                if planted.hub not in self.hubs:
                    errors.append(f"{where}.hub: unknown hub {planted.hub!r}")
                    continue
                hub = self.hubs[planted.hub]
                if hub.place(planted.place) is None:
                    errors.append(f"{where}.place: {planted.place!r} not declared by {planted.hub}")
                elif isinstance(planted, PlantedRestricted):
                    if not hub.place(planted.place).acl:
                        errors.append(f"{where}.place: restricted place needs an acl")
                    members = [artifact for artifact in self.artifacts
                               if artifact.hub == planted.hub and artifact.place == planted.place]
                    if not any(artifact.canaries for artifact in members):
                        errors.append(f"{where}: no artifact in the place carries a canary")
                elif hub.version_reads_for(planted.place):
                    errors.append(f"{where}: {planted.place} advertises version reads")
            elif isinstance(planted, (PlantedMultiHubFact, PlantedRuleMissedRelation)):
                for fact_id in planted.facts:
                    need(f"{where}.facts", "fact", fact_id, fact_ids)
                for artifact_id in planted.artifacts:
                    need(f"{where}.artifacts", "artifact", artifact_id, artifact_ids)
                if all(artifact_id in artifact_ids for artifact_id in planted.artifacts):
                    if len({self.artifact(artifact_id).hub for artifact_id in planted.artifacts}) < 2:
                        errors.append(f"{where}: artifacts must span at least two hubs")

        for artifact in self.artifacts:
            if artifact.canaries:
                restricted_places = [planted.place for planted in self.planted
                                     if isinstance(planted, PlantedRestricted) and planted.hub == artifact.hub]
                if artifact.place not in restricted_places:
                    errors.append(f"artifact {artifact.id}: canaries outside a restricted place")
                for canary in artifact.canaries:
                    if canary not in (artifact.body or ""):
                        errors.append(f"artifact {artifact.id}: canary {canary!r} not in body")

    def asserted_fact_ids(self) -> set[str]:
        asserted: set[str] = set()
        for artifact in self.artifacts:
            for version in artifact.versions:
                for assertion_text in version.asserts:
                    match = ASSERTION.match(assertion_text)
                    if match:
                        asserted.add(match["fact"])
        return asserted


def load_world(path: Path) -> World:
    return World.model_validate(yaml.safe_load(Path(path).read_text()))
