"""World to per-hub corpora with span provenance (lab plan §5.5).

Hub-visible rows carry only what a real hub would expose. Which facts a span asserts,
entity ids, planted labels and canary lists live only under `private/`.

Seeds: core artifacts, entity refs and core noise derive from `world.seed`, so core
provenance is identical for any build seed; filler derives from the build seed.
"""
import hashlib
import json
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from sanctum_contracts import HubCapabilities as ContractHubCapabilities

from .filler import FillerFile, filler_natives, generate_filler, load_filler, noise_paragraph
from .rng import opaque_id, sub_rng
from .schema import (
    Artifact, PlantedCapabilityGap, PlantedCompositeSubject, PlantedConflict,
    PlantedCoverageGap, PlantedExactDuplicate, PlantedHomonym, PlantedHubSpecificNames,
    PlantedInjection, PlantedMultiHubFact, PlantedNewerNotApplicable, PlantedRestricted,
    PlantedRuleMissedRelation,
    PlantedVersionBranching, World, load_world, parse_assertion,
)

HUB_VISIBLE_KEYS = (
    "acl", "artifact_id", "environment", "kind", "location", "metadata", "path", "text",
    "title", "version",
)
TEMPLATE_SLOT = re.compile(r"\{\{([A-Za-z_]+)(?::([^}]*))?\}\}")
STRUCTURAL_SLOTS = ("title", "place", "path", "name", "namespace", "principal", "noise")
NO_VERSION_REF = "current"
DEFAULT_HUB_CONFIG = Path(__file__).resolve().parents[2] / "configs" / "hubs.yaml"


class RenderError(ValueError):
    pass


@dataclass
class SpanRecord:
    fact_id: str
    value_text: str
    start: int
    end: int


@dataclass
class TextBuilder:
    """Appends text and records the exact [start, end) of every fact value it writes."""
    parts: list[str] = field(default_factory=list)
    length: int = 0
    spans: list[SpanRecord] = field(default_factory=list)

    def literal(self, text: str) -> None:
        self.parts.append(text)
        self.length += len(text)

    def fact(self, fact_id: str, value_text: str) -> None:
        start = self.length
        self.literal(value_text)
        self.spans.append(SpanRecord(fact_id, value_text, start, self.length))

    def text(self) -> str:
        return "".join(self.parts)


def value_text(value) -> str:
    return str(value)


def _emit_body(builder: TextBuilder, body: str, fact_values: dict[str, str]) -> None:
    cursor = 0
    for match in TEMPLATE_SLOT.finditer(body):
        builder.literal(body[cursor:match.start()])
        if match.group(1) != "fact":
            raise RenderError(f"body may only contain fact slots, found {match.group(0)!r}")
        fact_id = match.group(2)
        if fact_id not in fact_values:
            raise RenderError(f"body slot {fact_id!r} is not asserted by this version")
        builder.fact(fact_id, fact_values[fact_id])
        cursor = match.end()
    builder.literal(body[cursor:])


def fill_template(template: str, fields: dict[str, str], body: str,
                  fact_values: dict[str, str]) -> TextBuilder:
    builder = TextBuilder()
    cursor = 0
    for match in TEMPLATE_SLOT.finditer(template):
        builder.literal(template[cursor:match.start()])
        slot = match.group(1)
        if slot == "body":
            _emit_body(builder, body, fact_values)
        elif slot in STRUCTURAL_SLOTS:
            builder.literal(fields.get(slot) or "")
        else:
            raise RenderError(f"unknown template slot {match.group(0)!r}")
        cursor = match.end()
    builder.literal(template[cursor:])
    return builder


def load_template(world_dir: Path, hub: str, kind: str) -> str:
    for candidate in (world_dir / "templates" / hub / f"{kind}.txt",
                      world_dir / "templates" / "shared" / f"{kind}.txt"):
        if candidate.exists():
            return candidate.read_text()
    raise RenderError(f"no template for {hub}/{kind}")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _dump_json(data) -> str:
    return json.dumps(data, sort_keys=True, ensure_ascii=False, indent=1) + "\n"


def _dump_jsonl(rows: list[dict]) -> str:
    return "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows)


@dataclass
class RenderedVersion:
    ref: str
    env: Optional[str]
    text: str
    spans: list[SpanRecord]
    assertions: dict[str, str]          # fact_id -> "fact@release[/env]"


@dataclass
class Vocabulary:
    """Declared natives per hub (core + filler) and the global set."""
    declared: dict[str, list[str]]

    @property
    def all_natives(self) -> list[str]:
        return sorted({native for natives in self.declared.values() for native in natives})

    def undeclared_for(self, hub: str) -> list[str]:
        own = set(self.declared.get(hub, []))
        return [native for native in self.all_natives if native not in own]


def build_vocabulary(world: World, filler: FillerFile) -> Vocabulary:
    extra = filler_natives(filler)
    declared = {
        hub_id: sorted(set(world.hubs[hub_id].declared_natives()) | set(extra.get(hub_id, [])))
        for hub_id in sorted(world.hubs)
    }
    vocabulary = Vocabulary(declared)
    natives = vocabulary.all_natives
    for native in natives:
        for other in natives:
            if native != other and native in other:
                raise RenderError(f"native {native!r} is a substring of {other!r}; names must be distinct")
    core_entities = {entity.id for entity in world.entities}
    for service in filler.services:
        if service.entity_id in core_entities:
            raise RenderError(f"filler service {service.entity_id} collides with a core entity")
    return vocabulary


def _render_core_versions(world: World, artifact: Artifact, template: str, fields: dict[str, str],
                          rendered: dict[str, list[RenderedVersion]]) -> list[RenderedVersion]:
    if artifact.copy_of:
        source_versions = rendered[artifact.copy_of]
        return [
            RenderedVersion(version.ref, version.env, source.text, source.spans, source.assertions)
            for version, source in zip(artifact.versions, source_versions)
        ]
    versions = []
    for version in artifact.versions:
        assertions: dict[str, str] = {}
        fact_values: dict[str, str] = {}
        for assertion_text in version.asserts:
            assertion = parse_assertion(assertion_text)
            assertions[assertion.fact] = assertion_text
            fact_values[assertion.fact] = value_text(world.resolve_value(assertion).value)
        builder = fill_template(template, fields, artifact.body or "", fact_values)
        versions.append(RenderedVersion(version.ref, version.env, builder.text(), builder.spans, assertions))
    return versions


def _metadata(hub: str, *, revision: int, namespace: Optional[str], principal: Optional[str],
              session: Optional[str], place: Optional[str]) -> dict:
    if hub == "codehub":
        return {"revision": revision}
    if hub == "skillhub":
        return {"namespace": namespace, "revision": revision}
    if hub == "dochub":
        return {"space": place, "revision": revision}
    if hub == "memoryhub":
        return {"principal": principal, "session": session}
    if hub == "incidenthub":
        return {"queue": place}
    return {}


def _hub_row(*, artifact_id: str, kind: str, place: Optional[str], path: Optional[str], title: str,
             version: str, env: Optional[str], acl: list[str], metadata: dict, text: str) -> dict:
    row = {
        "acl": sorted(acl), "artifact_id": artifact_id, "environment": env, "kind": kind,
        "location": place, "metadata": metadata, "path": path, "text": text, "title": title,
        "version": version,
    }
    assert tuple(sorted(row)) == HUB_VISIBLE_KEYS
    return row


def load_hub_config(path: Path = DEFAULT_HUB_CONFIG) -> dict[str, dict]:
    return yaml.safe_load(Path(path).read_text())["hubs"]


def hub_capabilities(world: World, hub_config: dict[str, dict]) -> dict[str, dict]:
    """Hub-visible `capabilities.json` per hub (plan decision 3).

    The `contract` part validates as the frozen `HubCapabilities`; a hub whose version reads
    differ by place declares `version_reads: true` there and lists the places without version
    reads under `place_version_reads` (discrepancy register: capabilities extension)."""
    documents = {}
    for hub_id, hub in sorted(world.hubs.items()):
        if hub_id not in hub_config:
            raise RenderError(f"configs/hubs.yaml has no entry for {hub_id}")
        if bool(hub_config[hub_id].get("held_back", False)) != hub.held_back:
            raise RenderError(f"configs/hubs.yaml held_back for {hub_id} disagrees with world.yaml")
        reads = hub.capabilities.version_reads
        place_reads = dict(sorted(reads.items())) if isinstance(reads, dict) else {}
        contract = ContractHubCapabilities(
            hub_id=hub_id,
            version_reads=reads if isinstance(reads, bool) else True,
            filters=list(hub.capabilities.filters),
            max_results=hub_config[hub_id]["max_results"],
            principal_scoped="principal" in hub.capabilities.filters,
        )
        documents[hub_id] = {"contract": contract.model_dump(mode="json"),
                             "place_version_reads": place_reads}
    return documents


def principal_directory(world: World) -> list[dict]:
    """`identity/principals.json`: read only by the lab token service (an IdP stand-in)."""
    return [{"principal": principal.id, "groups": sorted(principal.groups)}
            for principal in sorted(world.principals, key=lambda principal: principal.id)]


def render(world: World, seed: int, out_dir: Path, world_dir: Path,
           hub_config_path: Path = DEFAULT_HUB_CONFIG) -> dict:
    """Render every hub corpus and the private index into `out_dir`; return the manifest."""
    world_dir = Path(world_dir)
    out_dir = Path(out_dir)
    hub_config = load_hub_config(hub_config_path)
    capabilities = hub_capabilities(world, hub_config)
    filler = load_filler(world_dir / world.filler.file)
    vocabulary = build_vocabulary(world, filler)

    entity_refs = {entity.id: opaque_id(world.seed, "ent", entity.id) for entity in world.entities}
    for service in filler.services:
        entity_refs[service.entity_id] = opaque_id(world.seed, "ent", service.entity_id)

    core_ids = {artifact.id: opaque_id(world.seed, "art", artifact.id) for artifact in world.artifacts}
    rows_by_hub: dict[str, list[tuple[str, int, dict]]] = {hub_id: [] for hub_id in world.hubs}
    provenance: list[dict] = []
    artifact_map: dict[str, dict] = {}
    rendered: dict[str, list[RenderedVersion]] = {}
    counts = {hub_id: {"artifacts": 0, "core_artifacts": 0, "rows": 0} for hub_id in world.hubs}

    ordered = sorted(world.artifacts, key=lambda artifact: (artifact.copy_of is not None, artifact.id))
    for artifact in ordered:
        hub = world.hubs[artifact.hub]
        if hub.version_reads_for(artifact.place) is False:
            for version in artifact.versions:
                if version.ref != NO_VERSION_REF:
                    raise RenderError(f"{artifact.id}: {artifact.place or artifact.hub} has no version "
                                      f"reads, version must be {NO_VERSION_REF!r}")
        noise = noise_paragraph(sub_rng(world.seed, "core-noise", artifact.id), filler)
        fields = {"title": artifact.title, "place": artifact.place, "path": artifact.path,
                  "name": artifact.name, "namespace": artifact.namespace,
                  "principal": artifact.principal, "noise": noise}
        template = load_template(world_dir, artifact.hub, artifact.kind)
        versions = _render_core_versions(world, artifact, template, fields, rendered)
        rendered[artifact.id] = versions
        artifact_id = core_ids[artifact.id]
        acl = artifact.acl if artifact.acl is not None else (
            hub.place(artifact.place).acl if artifact.place else [])
        session = opaque_id(world.seed, "sess", artifact.id) if artifact.hub == "memoryhub" else None
        for version_index, version in enumerate(versions):
            metadata = _metadata(artifact.hub, revision=version_index + 1, namespace=artifact.namespace,
                                 principal=artifact.principal, session=session, place=artifact.place)
            row = _hub_row(artifact_id=artifact_id, kind=artifact.kind, place=artifact.place,
                           path=artifact.path, title=artifact.title, version=version.ref,
                           env=version.env, acl=acl, metadata=metadata, text=version.text)
            rows_by_hub[artifact.hub].append((artifact_id, version_index, row))
            for span in version.spans:
                assertion = parse_assertion(version.assertions[span.fact_id])
                fact = world.fact(span.fact_id)
                provenance.append({
                    "artifact_id": artifact_id, "world_artifact_id": artifact.id,
                    "hub": artifact.hub, "version": version.ref, "environment": version.env,
                    "fact_id": fact.id, "entity_id": fact.entity, "fact_kind": fact.fact_kind,
                    "attribute": fact.attribute, "assertion": version.assertions[span.fact_id],
                    "release": assertion.release,
                    "value": world.resolve_value(assertion).value, "value_text": span.value_text,
                    "start": span.start, "end": span.end,
                })
        artifact_map[artifact.id] = {
            "artifact_id": artifact_id, "hub": artifact.hub, "place": artifact.place,
            "path": artifact.path, "title": artifact.title, "about": list(artifact.about),
            "acl": sorted(acl), "versions": [version.ref for version in versions],
            "copy_of": artifact.copy_of,
        }
        counts[artifact.hub]["artifacts"] += 1
        counts[artifact.hub]["core_artifacts"] += 1

    used_ids = set(core_ids.values())
    if len(used_ids) != len(core_ids):
        raise RenderError("opaque artifact id collision among core artifacts")
    for filler_artifact in generate_filler(world, filler, seed):
        artifact_id = opaque_id(seed, "art", filler_artifact.key)
        if artifact_id in used_ids:
            raise RenderError(f"opaque artifact id collision for {filler_artifact.key}")
        used_ids.add(artifact_id)
        template = load_template(world_dir, filler_artifact.hub, filler_artifact.kind)
        fields = {"title": filler_artifact.title, "place": filler_artifact.place,
                  "path": filler_artifact.path, "name": filler_artifact.name,
                  "namespace": filler_artifact.namespace, "principal": filler_artifact.principal,
                  "noise": filler_artifact.noise}
        session = (opaque_id(seed, "sess", filler_artifact.key)
                   if filler_artifact.hub == "memoryhub" else None)
        for version_index, version in enumerate(filler_artifact.versions):
            builder = fill_template(template, fields, version.body, {})
            metadata = _metadata(filler_artifact.hub, revision=version_index + 1,
                                 namespace=filler_artifact.namespace, principal=filler_artifact.principal,
                                 session=session, place=filler_artifact.place)
            row = _hub_row(artifact_id=artifact_id, kind=filler_artifact.kind, place=filler_artifact.place,
                           path=filler_artifact.path, title=filler_artifact.title, version=version.ref,
                           env=version.env, acl=filler_artifact.acl, metadata=metadata,
                           text=builder.text())
            rows_by_hub[filler_artifact.hub].append((artifact_id, version_index, row))
        counts[filler_artifact.hub]["artifacts"] += 1

    canaries = sorted(
        ({"token": token, "artifact_id": core_ids[artifact.id], "world_artifact_id": artifact.id,
          "hub": artifact.hub, "place": artifact.place}
         for artifact in world.artifacts for token in artifact.canaries),
        key=lambda entry: entry["token"],
    )
    _guard_hub_rows(world, rows_by_hub, vocabulary, entity_refs, canaries)
    planted_index = _planted_index(world, core_ids)

    # ---- write ---------------------------------------------------------------------
    for stale in (out_dir / "hubs", out_dir / "private", out_dir / "identity"):
        if stale.exists():
            shutil.rmtree(stale)
    outputs: dict[str, str] = {}
    for hub_id in sorted(rows_by_hub):
        rows = [row for _, _, row in sorted(rows_by_hub[hub_id], key=lambda item: (item[0], item[1]))]
        counts[hub_id]["rows"] = len(rows)
        outputs[f"hubs/{hub_id}/artifacts.jsonl"] = _dump_jsonl(rows)
        outputs[f"hubs/{hub_id}/capabilities.json"] = _dump_json(capabilities[hub_id])
    outputs["identity/principals.json"] = _dump_json(principal_directory(world))
    provenance.sort(key=lambda row: (row["artifact_id"], row["version"], row["start"]))
    outputs["private/provenance.jsonl"] = _dump_jsonl(provenance)
    outputs["private/entity_refs.json"] = _dump_json(entity_refs)
    outputs["private/canaries.json"] = _dump_json(canaries)
    outputs["private/planted_index.json"] = _dump_json(planted_index)
    outputs["private/artifact_map.json"] = _dump_json(artifact_map)
    for relative_path, content in outputs.items():
        target = out_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)

    input_paths = [world_dir / "world.yaml", world_dir / world.filler.file] + sorted(
        (world_dir / "templates").rglob("*.txt"))
    held_back = sorted(hub_id for hub_id, hub in world.hubs.items() if hub.held_back)
    for hub_id in counts:
        counts[hub_id]["held_back"] = hub_id in held_back
    manifest = {
        "seed": seed,
        "world_seed": world.seed,
        "world_version": world.world_version,
        "inputs": {path.relative_to(world_dir).as_posix(): _sha256(path.read_bytes())
                   for path in input_paths if path.exists()},
        "hub_config": _sha256(Path(hub_config_path).read_bytes()),
        "files": {relative_path: _sha256(content.encode("utf-8"))
                  for relative_path, content in sorted(outputs.items())},
        "counts": counts,
        "held_back_hubs": held_back,
        "total_artifacts": sum(entry["artifacts"] for hub_id, entry in counts.items()
                               if hub_id not in held_back),
        "total_rows": sum(entry["rows"] for hub_id, entry in counts.items() if hub_id not in held_back),
    }
    (out_dir / "manifest.json").write_text(_dump_json(manifest))
    return manifest


def public_text(value) -> str:
    """Every decoded string in a public row (keys and leaf values, recursively), newline-joined,
    so matching sees text exactly as a hub consumer would, with no JSON escaping."""
    if isinstance(value, dict):
        return "\n".join(f"{key}\n{public_text(item)}" for key, item in sorted(value.items()))
    if isinstance(value, (list, tuple)):
        return "\n".join(public_text(item) for item in value)
    return "" if value is None else str(value)


def _guard_hub_rows(world: World, rows_by_hub, vocabulary: Vocabulary, entity_refs: dict[str, str],
                    canaries: list[dict]) -> None:
    """Refuse to write a hub corpus that leaks private identifiers or another hub's vocabulary."""
    private_tokens = sorted(
        {fact.id for fact in world.facts}
        | set(entity_refs) | set(entity_refs.values())
        | {planted.id for planted in world.planted}
        | {artifact.id for artifact in world.artifacts}
    )
    canary_owner = {entry["token"]: entry["artifact_id"] for entry in canaries}
    for hub_id, rows in rows_by_hub.items():
        foreign = vocabulary.undeclared_for(hub_id)
        for artifact_id, _, row in rows:
            if tuple(sorted(row)) != HUB_VISIBLE_KEYS:
                raise RenderError(f"{hub_id} {artifact_id}: row fields {sorted(row)} are not the public allowlist")
            visible = public_text(row)
            for token in private_tokens:
                if token in visible:
                    raise RenderError(f"{hub_id} {artifact_id}: private identifier {token!r} in hub output")
            for native in foreign:
                if native in visible:
                    raise RenderError(f"{hub_id} {artifact_id}: {native!r} is not declared by {hub_id}")
            for token, owner in canary_owner.items():
                if token in visible and artifact_id != owner:
                    raise RenderError(f"{hub_id} {artifact_id}: canary {token} outside its artifact")


def _planted_index(world: World, core_ids: dict[str, str]) -> dict:
    def in_hub(hub_id: str, native: str) -> list[str]:
        return [artifact.id for artifact in world.artifacts
                if artifact.hub == hub_id and native in (artifact.name, artifact.place)]

    index = {}
    for planted in world.planted:
        details = planted.model_dump(exclude={"id", "kind"})
        if isinstance(planted, PlantedHomonym):
            members = in_hub(planted.hub, planted.name)
        elif isinstance(planted, PlantedHubSpecificNames):
            members = [artifact_id for hub_id, native in sorted(planted.names.items())
                       for artifact_id in in_hub(hub_id, native)]
        elif isinstance(planted, (PlantedConflict, PlantedExactDuplicate, PlantedMultiHubFact,
                                  PlantedRuleMissedRelation)):
            members = list(planted.artifacts)
        elif isinstance(planted, (PlantedVersionBranching, PlantedNewerNotApplicable,
                                  PlantedCompositeSubject, PlantedInjection)):
            members = [planted.artifact]
        elif isinstance(planted, (PlantedRestricted, PlantedCapabilityGap)):
            members = in_hub(planted.hub, planted.place)
        elif isinstance(planted, PlantedCoverageGap):
            members = []
            details["gap_facts"] = sorted(fact.id for fact in world.facts if fact.entity == planted.entity)
            details["non_asserting_artifacts"] = sorted(
                artifact.id for artifact in world.artifacts if planted.entity in artifact.about)
            details["non_asserting_artifact_ids"] = [core_ids[artifact_id]
                                                     for artifact_id in details["non_asserting_artifacts"]]
        else:  # pragma: no cover - the discriminated union is closed
            raise RenderError(f"unhandled planted kind {planted.kind}")
        if not members and not isinstance(planted, PlantedCoverageGap):
            raise RenderError(f"planted {planted.id} is not realised by any artifact")
        index[planted.id] = {
            "kind": planted.kind,
            "world_artifact_ids": members,
            "artifact_ids": [core_ids[artifact_id] for artifact_id in members],
            "details": details,
        }
    return index


def build(world_dir: Path, seed: Optional[int], out_dir: Path,
          hub_config_path: Path = DEFAULT_HUB_CONFIG, overlays: tuple = ()) -> dict:
    world = load_world(Path(world_dir) / "world.yaml", tuple(overlays))
    return render(world, world.seed if seed is None else seed, out_dir, world_dir, hub_config_path)
