"""Derive M0-shaped gold cases from world.yaml plus the private build index (lab plan §8.3).

Inputs are the authored world (ground truth) and `<build>/private/` (opaque ids and provenance
spans written by the renderer). Output is validated by `sanctum_eval.gold.GoldCase`, unchanged.

Derivation rules (task 5 of the M1 plan):
- interpretations: entities the spec's term denotes that the principal can see at least one
  unrestricted core artifact about.
- obligations: one per (interpretation, fact) for facts on the requested attributes. Each
  artifact contributes its latest version at or before `as_of` (default: newest release) in the
  requested environment, and only if that span's value equals the world truth there. Every
  qualifying span is an alternative single-span bundle, so exact duplicates satisfy together.
  Facts with no value yet at `as_of` are skipped; with `as_of`, sources without version reads
  are not eligible. A requested fact with no eligible span is a coverage gap (`no_coverage`,
  and at best `partial`).
- spans in planted restricted places are gold only for principals who can read them; for
  everyone else they only feed `forbidden.canaries`. Other spans the principal cannot read
  stay as bundles of an unobtainable obligation.
- source obligations: SkillHub is must-consult for procedure facts; any hub that alone supplies
  an obligation is mandatory; with `as_of`, hubs holding the entity without version reads are
  capability gaps.
- relations (only between obtainable witnesses): same attribute, different values. Implemented vs procedure/policy gives
  policy_implementation_divergence; `contrast.release` gives version_difference and
  `contrast.environment` gives environment_difference.
- wrong_entities: homonym siblings (entities sharing a native name) not among interpretations.
"""
import hashlib
import json
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sanctum_contracts import RetrieveRequest
from sanctum_contracts.enums import EvidenceStatus, Mode, RelationType, SourceStatus
from sanctum_eval.gold import (
    Bundle, ExpectedSourceOutcome, Expected, Forbidden, GoldCase, GoldInterpretation,
    InterpretationPolicy, Obligation, RelationGold, SourceObligation, SpanRef,
)

from .schema import Assertion, PlantedHomonym, PlantedRestricted, World

FAMILIES = (
    "named_service", "hub_specific_name", "same_name_two_meanings", "historical",
    "conflicting_sources", "verify_claim", "vague", "no_source", "multi_hub", "restricted_content",
)


class _Spec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class NamedTerm(_Spec):
    native: str
    hub: Optional[str] = None
    namespace: Optional[str] = None


class Contrast(_Spec):
    release: Optional[str] = None
    environment: Optional[str] = None


class QuestionSpec(_Spec):
    id: str
    family: Literal[FAMILIES]  # type: ignore[valid-type]
    principal: str
    text: str
    mode: Mode = Mode.scoped
    scope: Optional[str] = None
    as_of: Optional[str] = None
    environment: Optional[str] = None
    entities: list[str] = Field(default_factory=list)   # explicit targets (world entity ids)
    name: Optional[NamedTerm] = None                     # or a native term to resolve
    attributes: list[str] = Field(min_length=1)
    fact_kinds: list[str] = Field(default_factory=list)  # empty means all except incident
    contrast: Optional[Contrast] = None
    expected_ambiguity: Optional[InterpretationPolicy] = None
    bundle_id: Optional[str] = None
    budget_tokens: int = 4000
    deadline_ms: int = 3000

    @model_validator(mode="after")
    def _one_target(self):
        if bool(self.entities) == bool(self.name):
            raise ValueError("spec needs exactly one of entities or name")
        return self


class BuildIndex:
    """Private build outputs the derivation reads."""

    def __init__(self, build_dir: Path):
        private = Path(build_dir) / "private"
        self.entity_refs: dict[str, str] = json.loads((private / "entity_refs.json").read_text())
        self.artifact_map: dict[str, dict] = json.loads((private / "artifact_map.json").read_text())
        self.canaries: list[dict] = json.loads((private / "canaries.json").read_text())
        self.provenance: list[dict] = [
            json.loads(line) for line in (private / "provenance.jsonl").read_text().splitlines()
            if line.strip()
        ]


def opaque_request_id(world: World, spec: QuestionSpec) -> str:
    digest = hashlib.sha256(f"{world.seed}|{spec.id}|{spec.text}".encode()).hexdigest()
    return f"req-{digest[:16]}"


class _Deriver:
    def __init__(self, world: World, index: BuildIndex, spec: QuestionSpec):
        self.world, self.index, self.spec = world, index, spec
        self.groups = set(next(p for p in world.principals if p.id == spec.principal).groups)
        self.restricted_places = {
            (planted.hub, planted.place) for planted in world.planted
            if isinstance(planted, PlantedRestricted)
        }
        self.target_release = spec.as_of or world.releases[-1]
        self.target_env = spec.environment or "prod"

    # ---- access --------------------------------------------------------------------
    def is_restricted(self, world_artifact_id: str) -> bool:
        artifact = self.world.artifact(world_artifact_id)
        return (artifact.hub, artifact.place) in self.restricted_places

    def can_read(self, world_artifact_id: str) -> bool:
        artifact = self.world.artifact(world_artifact_id)
        hub = self.world.hubs[artifact.hub]
        if hub.held_back:
            return False
        if artifact.hub == "memoryhub" and artifact.principal != self.spec.principal:
            return False    # session memory is personal
        acl = set(self.index.artifact_map[world_artifact_id]["acl"])
        return bool(acl & self.groups)

    def entity_visible(self, entity_id: str) -> bool:
        return any(
            entity_id in artifact.about and not self.is_restricted(artifact.id)
            and self.can_read(artifact.id)
            for artifact in self.world.artifacts
        )

    # ---- interpretations -------------------------------------------------------------
    def denoted_entities(self) -> list[str]:
        if self.spec.entities:
            return list(self.spec.entities)
        term = self.spec.name
        found: list[str] = []
        for hub_id, hub in self.world.hubs.items():
            if term.hub and hub_id != term.hub:
                continue
            for name in hub.names:
                if name.native == term.native and (not term.namespace or name.namespace == term.namespace):
                    found.append(name.denotes)
            for place in hub.places:
                if place.native == term.native and place.selects_for:
                    found.append(place.selects_for)
        return list(dict.fromkeys(found))

    def entity_has_artifacts(self, entity_id: str) -> bool:
        return any(entity_id in artifact.about and not self.is_restricted(artifact.id)
                   and not self.world.hubs[artifact.hub].held_back for artifact in self.world.artifacts)

    def reviewed_name_visible(self, entity_id: str) -> bool:
        """HLD §8.5: only reviewed names establish identity. A name counts when the principal can
        see the DENOTES name (or selecting place) itself; artifacts merely about the entity, such
        as a shared composite skill, add no interpretation."""
        term = self.spec.name
        for hub_id, hub in self.world.hubs.items():
            if (term.hub and hub_id != term.hub) or hub.held_back:
                continue
            for place in hub.places:
                if place.native == term.native and place.selects_for == entity_id \
                        and set(place.acl) & self.groups:
                    return True
            for name in hub.names:
                if name.native != term.native or name.denotes != entity_id \
                        or (term.namespace and name.namespace != term.namespace):
                    continue
                if name.namespace:
                    home = hub.place(f"skills/{name.namespace.lower()}/")
                    if home is not None and set(home.acl) & self.groups:
                        return True
                elif any(artifact.hub == hub_id and entity_id in artifact.about
                         and not self.is_restricted(artifact.id) and self.can_read(artifact.id)
                         for artifact in self.world.artifacts):
                    return True
        return False

    def homonym_siblings(self, entity_ids: list[str]) -> list[str]:
        siblings: list[str] = []
        for planted in self.world.planted:
            if isinstance(planted, PlantedHomonym) and set(planted.entities) & set(entity_ids):
                siblings += [e for e in planted.entities if e not in entity_ids]
        for hub in self.world.hubs.values():
            for name in hub.names:
                if name.denotes not in entity_ids:
                    continue
                siblings += [other.denotes for other in hub.names
                             if other.native == name.native and other.denotes not in entity_ids]
        return list(dict.fromkeys(siblings))

    # ---- spans ---------------------------------------------------------------------
    def applicable_rows(self, fact_id: str, release: str, env: str) -> list[dict]:
        """Latest version per artifact at or before `release` in `env`, when it states the truth.
        Empty when the fact has no value yet at `release` (not applicable, not a coverage gap).
        With `as_of`, sources that cannot read old versions are not eligible."""
        if not self.fact_applicable(fact_id, release, env):
            return []
        truth = self.world.resolve_value(Assertion(fact=fact_id, release=release, env=env))
        target_index = self.world.release_index(release)
        best_by_artifact: dict[str, dict] = {}
        for row in self.index.provenance:
            if row["fact_id"] != fact_id or self.world.hubs[row["hub"]].held_back:
                continue
            if row["environment"] not in (None, env):
                continue
            if self.world.release_index(row["release"]) > target_index:
                continue
            artifact = self.world.artifact(row["world_artifact_id"])
            if self.spec.as_of and not self.world.hubs[artifact.hub].version_reads_for(artifact.place):
                continue
            current = best_by_artifact.get(row["world_artifact_id"])
            if current is None or self.world.release_index(row["release"]) > self.world.release_index(current["release"]):
                best_by_artifact[row["world_artifact_id"]] = row
        return sorted(
            (row for row in best_by_artifact.values() if row["value"] == truth.value),
            key=lambda row: (row["hub"], row["artifact_id"], row["version"], row["start"]),
        )

    def fact_applicable(self, fact_id: str, release: str, env: str) -> bool:
        try:
            self.world.resolve_value(Assertion(fact=fact_id, release=release, env=env))
        except ValueError:
            return False
        return True

    def is_hidden(self, world_artifact_id: str) -> bool:
        """Restricted content the principal may not read never becomes gold."""
        return self.is_restricted(world_artifact_id) and not self.can_read(world_artifact_id)

    @staticmethod
    def span(row: dict) -> SpanRef:
        return SpanRef(source_id=row["hub"], artifact_id=row["artifact_id"], version=row["version"],
                       start=row["start"], end=row["end"])

    # ---- derivation ------------------------------------------------------------------
    def facts_for(self, entity_id: str):
        allowed_kinds = set(self.spec.fact_kinds) or {"implemented", "procedure", "policy"}
        return [fact for fact in self.world.facts
                if fact.entity == entity_id and fact.attribute in self.spec.attributes
                and fact.fact_kind in allowed_kinds]

    def derive(self) -> GoldCase:
        spec, refs = self.spec, self.index.entity_refs
        denoted = self.denoted_entities()
        if spec.name:
            visible = [entity_id for entity_id in denoted
                       if self.reviewed_name_visible(entity_id) and self.entity_visible(entity_id)]
        else:
            visible = [entity_id for entity_id in denoted if self.entity_visible(entity_id)]
        # Invisible denoted entities that have artifacts are denied, not uncovered.
        denied_entities = any(self.entity_has_artifacts(entity_id) for entity_id in denoted
                              if entity_id not in visible)
        interpretation_ids = {entity_id: f"i{n}" for n, entity_id in enumerate(visible, start=1)}

        obligations: list[Obligation] = []
        obligation_meta: list[tuple[str, str, list[dict], bool]] = []   # (entity, kind, rows, obtainable)
        relations: list[RelationGold] = []
        mandatory_hubs: dict[str, ExpectedSourceOutcome] = {}
        denied = False
        uncovered = 0

        for entity_id in visible:
            for fact in self.facts_for(entity_id):
                if not self.fact_applicable(fact.id, self.target_release, self.target_env):
                    continue    # no value yet at this release
                rows = [row for row in self.applicable_rows(fact.id, self.target_release, self.target_env)
                        if not self.is_hidden(row["world_artifact_id"])]
                if not rows:
                    uncovered += 1    # coverage gap: nothing the principal may know of asserts it
                    continue
                readable = [row for row in rows if self.can_read(row["world_artifact_id"])]
                obtainable = bool(readable)
                chosen = readable or rows
                obligation = Obligation(
                    obligation_id=f"o{len(obligations) + 1}",
                    interpretation_id=interpretation_ids[entity_id],
                    weight=1.0,
                    bundles=[Bundle(spans=[self.span(row)]) for row in chosen],
                    obtainable=obtainable,
                    acceptable_gap_reasons=[] if obtainable else ["required_source_denied"],
                )
                obligations.append(obligation)
                obligation_meta.append((entity_id, fact.fact_kind, chosen, obtainable))
                hubs = {row["hub"] for row in chosen}
                if fact.fact_kind == "procedure":
                    hubs_needed = {"skillhub"} & hubs or hubs
                elif len(hubs) == 1:
                    hubs_needed = hubs
                else:
                    hubs_needed = set()
                for hub_id in hubs_needed:
                    outcome = ExpectedSourceOutcome.attempted if obtainable else ExpectedSourceOutcome.denied_gap
                    if mandatory_hubs.get(hub_id) != ExpectedSourceOutcome.attempted:
                        mandatory_hubs[hub_id] = outcome
                denied |= not obtainable

                if obtainable:
                    relations += self.contrast_relations(fact.id, chosen, len(relations))

        relations += self.divergence_relations(obligation_meta, len(relations))

        source_obligations = [
            SourceObligation(source_id=hub_id, mandatory=True, expected=outcome)
            for hub_id, outcome in sorted(mandatory_hubs.items())
        ]
        if spec.as_of:
            source_obligations += [
                SourceObligation(source_id=hub_id, mandatory=False,
                                 expected=ExpectedSourceOutcome.capability_gap)
                for hub_id in self.hubs_without_version_reads(visible) if hub_id not in mandatory_hubs
            ]

        policy = spec.expected_ambiguity or (
            InterpretationPolicy.separate_alternatives if len(visible) > 1 else InterpretationPolicy.unique)
        obtainable_count = sum(1 for obligation in obligations if obligation.obtainable)
        answerable = obtainable_count > 0
        if obligations and obtainable_count == len(obligations) and not uncovered:
            evidence_status = EvidenceStatus.sufficient
        elif answerable:
            evidence_status = EvidenceStatus.partial
        else:
            evidence_status = EvidenceStatus.insufficient
        required_reasons: list[str] = []
        if spec.name and not denoted:
            required_reasons.append("unresolved_term")    # no reviewed name: no invented identity
        elif (uncovered or not obligations) and (visible or not denied_entities):
            required_reasons.append("no_coverage")
        if denied or (not visible and denied_entities):
            required_reasons.append("required_source_denied")
        if policy == InterpretationPolicy.clarify:
            required_reasons.append("ambiguous_term")

        source_status = {
            hub_id: SourceStatus.called if outcome == ExpectedSourceOutcome.attempted else SourceStatus.skipped
            for hub_id, outcome in mandatory_hubs.items()
        }
        wrong_entities = [refs[entity_id] for entity_id in self.homonym_siblings(visible)
                          if entity_id not in visible]
        wrong_entities += [refs[entity_id] for entity_id in denoted if entity_id not in visible]

        return GoldCase(
            case_id=spec.id,
            bundle_id=spec.bundle_id or f"b-{spec.id}",
            family=spec.family,
            request=RetrieveRequest(
                request_id=opaque_request_id(self.world, spec), query=spec.text, mode=spec.mode,
                scope=spec.scope, as_of=spec.as_of, environment=spec.environment,
                budget_tokens=spec.budget_tokens, deadline_ms=spec.deadline_ms,
            ),
            principal=spec.principal,
            answerable=answerable,
            interpretation_policy=policy,
            interpretations=[GoldInterpretation(interpretation_id=interpretation_ids[e], entity_ref=refs[e])
                             for e in visible],
            obligations=obligations,
            source_obligations=source_obligations,
            relations=relations,
            forbidden=Forbidden(
                canaries=sorted(c["token"] for c in self.index.canaries
                                if not self.can_read(c["world_artifact_id"])),
                wrong_entities=list(dict.fromkeys(wrong_entities)),
            ),
            expected=Expected(evidence_status=evidence_status, required_reasons=required_reasons,
                              source_status=source_status),
        )

    def contrast_relations(self, fact_id: str, chosen: list[dict], offset: int) -> list[RelationGold]:
        contrast = self.spec.contrast
        if not contrast:
            return []
        release = contrast.release or self.target_release
        env = contrast.environment or self.target_env
        relation_type = (RelationType.environment_difference if contrast.environment
                         else RelationType.version_difference)
        chosen_artifacts = {row["world_artifact_id"] for row in chosen}
        other_rows = [row for row in self.applicable_rows(fact_id, release, env)
                      if row["world_artifact_id"] in chosen_artifacts and self.can_read(row["world_artifact_id"])]
        relations = []
        for row in chosen:
            other = next((o for o in other_rows if o["world_artifact_id"] == row["world_artifact_id"]
                          and o["value"] != row["value"]), None)
            if other:
                relations.append(RelationGold(
                    relation_id=f"r{offset + len(relations) + 1}", relation_type=relation_type,
                    witness_a=Bundle(spans=[self.span(row)]), witness_b=Bundle(spans=[self.span(other)])))
        return relations

    def divergence_relations(self, obligation_meta, offset: int) -> list[RelationGold]:
        relations = []
        for entity_id, kind, rows, obtainable in obligation_meta:
            if kind != "implemented" or not obtainable:
                continue
            for other_entity, other_kind, other_rows, other_obtainable in obligation_meta:
                if not other_obtainable or other_entity != entity_id or other_kind not in ("procedure", "policy"):
                    continue
                if rows[0]["attribute"] != other_rows[0]["attribute"] or rows[0]["value"] == other_rows[0]["value"]:
                    continue
                relations.append(RelationGold(
                    relation_id=f"r{offset + len(relations) + 1}",
                    relation_type=RelationType.policy_implementation_divergence,
                    witness_a=Bundle(spans=[self.span(_preferred(rows, "codehub"))]),
                    witness_b=Bundle(spans=[self.span(_preferred(other_rows, "skillhub"))])))
        return relations

    def hubs_without_version_reads(self, entity_ids: list[str]) -> list[str]:
        hubs = set()
        for artifact in self.world.artifacts:
            if not set(artifact.about) & set(entity_ids) or self.is_restricted(artifact.id):
                continue
            if self.world.hubs[artifact.hub].held_back or not self.can_read(artifact.id):
                continue
            if not self.world.hubs[artifact.hub].version_reads_for(artifact.place):
                hubs.add(artifact.hub)
        return sorted(hubs)


def _preferred(rows: list[dict], hub_id: str) -> dict:
    return next((row for row in rows if row["hub"] == hub_id), rows[0])


def derive(world: World, build_dir: Path, spec: QuestionSpec, index: Optional[BuildIndex] = None) -> GoldCase:
    """Derive and validate one gold case. `index` may be passed to reuse a loaded build."""
    gold = _Deriver(world, index or BuildIndex(build_dir), spec).derive()
    return GoldCase.model_validate(gold.model_dump(mode="json"))
