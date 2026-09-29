"""World linter (lab plan §5.4 plus the M1 rules).

`lint(world, build_dir)` reads the authored world and a rendered build and returns typed
findings; an empty list means the build is fit to derive gold from. Rules:

- planted_missing: a planted situation is absent from the build or not detectable in it.
- fact_unasserted: a fact has no asserting span (unless it belongs to a planted coverage gap).
- coverage_gap_asserted: a planted coverage-gap fact is asserted somewhere after all.
- span_mismatch: a provenance span's text[start:end] does not render its value.
- acl_mismatch: a rendered core row's ACL differs from the authored access policy.
- duplicate_path: two artifacts in one hub share a native path.
- restricted_leak: a restricted canary, title, place name or authored sentence appears
  outside the restricted place (or inside it under a weakened ACL).
- unexpected_field: a hub-visible row carries a field outside the public allowlist.
- vocabulary_leak: hub-visible output names a native the hub does not declare.
- private_id_leak: a fact id, entity id, opaque entity ref, planted label, world artifact id
  or canary (outside its own artifact) appears in hub-visible output.
- filler_collision: a filler service or native collides with a core entity or native.

The side documents `hubs/<hub>/capabilities.json` (hub-visible) and `identity/principals.json`
(token service only) are covered by private_id_leak and restricted_leak, and each
capabilities file by vocabulary_leak for its hub.

`python -m sanctum_world.lint --leak-scan <build_dir>` runs only private_id_leak, with the
exact identifiers listed under `<build_dir>/private/` (no world file, no regex guessing).
"""
import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .render import HUB_VISIBLE_KEYS, public_text
from .filler import filler_natives, load_filler
from .schema import (
    PlantedCapabilityGap, PlantedConflict, PlantedCoverageGap, PlantedExactDuplicate,
    PlantedHomonym, PlantedHubSpecificNames, PlantedInjection, PlantedMultiHubFact,
    PlantedNewerNotApplicable, PlantedRestricted, PlantedVersionBranching, World, load_world,
)

DEFAULT_WORLD_DIR = Path(__file__).resolve().parents[2] / "world"
MIN_DISTINCTIVE_LINE = 20


@dataclass(frozen=True)
class Finding:
    rule: str
    where: str
    message: str

    def __str__(self) -> str:
        return f"[{self.rule}] {self.where}: {self.message}"


@dataclass
class BuildView:
    """Rendered build loaded from disk: hub rows plus the private index."""
    rows_by_hub: dict[str, list[dict]]
    provenance: list[dict]
    entity_refs: dict[str, str]
    canaries: list[dict]
    planted_index: dict[str, dict]
    artifact_map: dict[str, dict]
    side_documents: dict[str, str] = field(default_factory=dict)   # relative path -> public text

    def side_documents_for(self, hub_id: str) -> dict[str, str]:
        prefix = f"hubs/{hub_id}/"
        return {path: text for path, text in self.side_documents.items() if path.startswith(prefix)}

    def rows_for(self, opaque_artifact_id: str) -> list[dict]:
        return [row for rows in self.rows_by_hub.values() for row in rows
                if row["artifact_id"] == opaque_artifact_id]


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_build(build_dir: Path) -> BuildView:
    build_dir = Path(build_dir)
    private_dir = build_dir / "private"
    rows_by_hub = {
        hub_dir.name: _read_jsonl(hub_dir / "artifacts.jsonl")
        for hub_dir in sorted((build_dir / "hubs").iterdir())
        if (hub_dir / "artifacts.jsonl").exists()
    }
    side_paths = sorted(build_dir.glob("hubs/*/capabilities.json")) + sorted(
        build_dir.glob("identity/*.json"))
    side_documents = {path.relative_to(build_dir).as_posix(): public_text(json.loads(path.read_text()))
                      for path in side_paths}
    return BuildView(
        side_documents=side_documents,
        rows_by_hub=rows_by_hub,
        provenance=_read_jsonl(private_dir / "provenance.jsonl"),
        entity_refs=json.loads((private_dir / "entity_refs.json").read_text()),
        canaries=json.loads((private_dir / "canaries.json").read_text()),
        planted_index=json.loads((private_dir / "planted_index.json").read_text()),
        artifact_map=json.loads((private_dir / "artifact_map.json").read_text()),
    )


def visible_text(row: dict) -> str:
    """The whole public row: every key and decoded value, recursively (no JSON escaping)."""
    return public_text(row)


def authored_acl_by_opaque_id(view: BuildView) -> dict[str, list[str]]:
    return {entry["artifact_id"]: sorted(entry["acl"]) for entry in view.artifact_map.values()}


def acl_is_authored(row: dict, authored_acl: dict[str, list[str]]) -> bool:
    return authored_acl.get(row["artifact_id"]) == sorted(row.get("acl") or [])


def _row_where(hub_id: str, row: dict) -> str:
    return f"{hub_id}/{row['artifact_id']}@{row['version']}"


# ---- hub-visible leak rule (shared with --leak-scan) -----------------------------------
def private_identifiers(view: BuildView) -> list[str]:
    """Every exact identifier the private index knows about, never allowed in hub output."""
    identifiers = {row["fact_id"] for row in view.provenance}
    identifiers |= {row["entity_id"] for row in view.provenance}
    identifiers |= set(view.entity_refs) | set(view.entity_refs.values())
    identifiers |= set(view.planted_index)
    identifiers |= set(view.artifact_map)
    return sorted(identifiers)


def check_private_leaks(view: BuildView, extra_identifiers: tuple[str, ...] = ()) -> list[Finding]:
    identifiers = sorted(set(private_identifiers(view)) | set(extra_identifiers))
    canary_owner = {entry["token"]: entry["artifact_id"] for entry in view.canaries}
    authored_acl = authored_acl_by_opaque_id(view)
    findings = []
    for hub_id, rows in sorted(view.rows_by_hub.items()):
        for row in rows:
            unexpected = sorted(set(row) - set(HUB_VISIBLE_KEYS))
            if unexpected:
                findings.append(Finding("unexpected_field", _row_where(hub_id, row),
                                        f"fields {unexpected} are not in the public allowlist"))
            text = visible_text(row)
            for identifier in identifiers:
                if identifier in text:
                    findings.append(Finding("private_id_leak", _row_where(hub_id, row),
                                            f"private identifier {identifier!r} in hub output"))
            for token, owner in sorted(canary_owner.items()):
                if token in text and (row["artifact_id"] != owner or not acl_is_authored(row, authored_acl)):
                    findings.append(Finding("private_id_leak", _row_where(hub_id, row),
                                            f"canary {token!r} outside its own artifact"))
    for path, text in sorted(view.side_documents.items()):
        for identifier in identifiers:
            if identifier in text:
                findings.append(Finding("private_id_leak", path, f"private identifier {identifier!r}"))
        for token in sorted(canary_owner):
            if token in text:
                findings.append(Finding("private_id_leak", path, f"canary {token!r} outside its own artifact"))
    return findings


# ---- world-aware rules -----------------------------------------------------------------
def check_facts(world: World, view: BuildView) -> list[Finding]:
    gap_entities = {planted.entity for planted in world.planted if isinstance(planted, PlantedCoverageGap)}
    asserted = {row["fact_id"] for row in view.provenance}
    findings = []
    for fact in world.facts:
        if fact.entity in gap_entities:
            if fact.id in asserted:
                findings.append(Finding("coverage_gap_asserted", fact.id,
                                        f"planted coverage-gap fact is asserted by an artifact"))
        elif fact.id not in asserted:
            findings.append(Finding("fact_unasserted", fact.id, "no artifact asserts this fact"))
    return findings


def check_spans(view: BuildView) -> list[Finding]:
    texts = {(row["artifact_id"], row["version"]): row["text"]
             for rows in view.rows_by_hub.values() for row in rows}
    findings = []
    for span in view.provenance:
        where = f"{span['artifact_id']}@{span['version']}:{span['start']}"
        text = texts.get((span["artifact_id"], span["version"]))
        if text is None:
            findings.append(Finding("span_mismatch", where, f"{span['fact_id']} span has no hub row"))
        elif text[span["start"]:span["end"]] != span["value_text"]:
            findings.append(Finding("span_mismatch", where,
                                    f"{span['fact_id']} span does not render {span['value_text']!r}"))
    return findings


def check_planted(world: World, view: BuildView) -> list[Finding]:
    spans_by_artifact: dict[str, list[dict]] = defaultdict(list)
    for span in view.provenance:
        spans_by_artifact[span["world_artifact_id"]].append(span)

    def opaque(world_artifact_id: str) -> Optional[str]:
        entry = view.artifact_map.get(world_artifact_id)
        return entry["artifact_id"] if entry else None

    def rows(world_artifact_id: str) -> list[dict]:
        opaque_id = opaque(world_artifact_id)
        return view.rows_for(opaque_id) if opaque_id else []

    def hub_mentions(hub_id: str, native: str) -> bool:
        return any(native in visible_text(row) for row in view.rows_by_hub.get(hub_id, []))

    findings = []
    for planted in world.planted:
        problems: list[str] = []
        entry = view.planted_index.get(planted.id)
        if entry is None:
            findings.append(Finding("planted_missing", planted.id, "not in private/planted_index.json"))
            continue
        if not isinstance(planted, PlantedCoverageGap):
            if not entry["world_artifact_ids"]:
                problems.append("no artifact realises it")
            for world_artifact_id in entry["world_artifact_ids"]:
                if not rows(world_artifact_id):
                    problems.append(f"artifact {world_artifact_id} is not rendered in any hub")

        if isinstance(planted, PlantedHomonym):
            if not hub_mentions(planted.hub, planted.name):
                problems.append(f"{planted.name!r} does not appear in {planted.hub}")
        elif isinstance(planted, PlantedHubSpecificNames):
            for hub_id, native in sorted(planted.names.items()):
                if not hub_mentions(hub_id, native):
                    problems.append(f"{native!r} does not appear in {hub_id}")
        elif isinstance(planted, (PlantedConflict, PlantedMultiHubFact)):
            for fact_id in planted.facts:
                if not any(span["fact_id"] == fact_id
                           for artifact_id in planted.artifacts for span in spans_by_artifact[artifact_id]):
                    problems.append(f"fact {fact_id} is not asserted by {planted.artifacts}")
            if isinstance(planted, PlantedConflict):
                values = {span["value"] for artifact_id in planted.artifacts
                          for span in spans_by_artifact[artifact_id]
                          if span["fact_id"] in planted.facts and span["release"] == planted.at}
                if len(values) < 2:
                    problems.append(f"sources do not disagree at {planted.at} (values {sorted(map(str, values))})")
            else:
                hubs = {span["hub"] for artifact_id in planted.artifacts
                        for span in spans_by_artifact[artifact_id] if span["fact_id"] in planted.facts}
                if len(hubs) < 2:
                    problems.append("asserting spans do not span two hubs")
        elif isinstance(planted, PlantedVersionBranching):
            refs = {row["version"] for row in rows(planted.artifact)}
            for ref in planted.refs:
                if ref not in refs:
                    problems.append(f"version {ref} not rendered")
        elif isinstance(planted, PlantedNewerNotApplicable):
            values_by_ref: dict[str, set] = defaultdict(set)
            for span in spans_by_artifact[planted.artifact]:
                values_by_ref[span["version"]].add(str(span["value"]))
            for ref in (planted.newer_ref, planted.applicable_ref):
                if ref not in values_by_ref:
                    problems.append(f"version {ref} asserts nothing")
            if values_by_ref.get(planted.newer_ref) == values_by_ref.get(planted.applicable_ref):
                problems.append("newer version does not differ from the applicable one")
        elif isinstance(planted, PlantedExactDuplicate):
            texts = {tuple(row["text"] for row in sorted(rows(artifact_id), key=lambda row: row["version"]))
                     for artifact_id in planted.artifacts}
            hubs = {view.artifact_map[artifact_id]["hub"] for artifact_id in planted.artifacts
                    if artifact_id in view.artifact_map}
            if len(texts) != 1:
                problems.append("copies are not byte-identical")
            if len(hubs) < 2:
                problems.append("copies do not span two hubs")
        elif isinstance(planted, PlantedInjection):
            if not any(planted.instruction in row["text"] for row in rows(planted.artifact)):
                problems.append("instruction text not rendered")
        elif isinstance(planted, PlantedRestricted):
            members = [row for row in view.rows_by_hub.get(planted.hub, []) if row["location"] == planted.place]
            tokens = [entry_["token"] for entry_ in view.canaries
                      if entry_["hub"] == planted.hub and entry_["place"] == planted.place]
            if not members:
                problems.append(f"no rows in {planted.place}")
            if any(not row["acl"] for row in members):
                problems.append(f"a row in {planted.place} has no acl")
            if not tokens or not all(any(token in row["text"] for row in members) for token in tokens):
                problems.append("canaries not rendered in the restricted place")
        elif isinstance(planted, PlantedCapabilityGap):
            for world_artifact_id in entry["world_artifact_ids"]:
                if len(rows(world_artifact_id)) > 1:
                    problems.append(f"{world_artifact_id} has several versions in a place without version reads")
        for problem in problems:
            findings.append(Finding("planted_missing", f"{planted.id} ({planted.kind})", problem))
    return findings


def check_acls(view: BuildView) -> list[Finding]:
    authored_acl = authored_acl_by_opaque_id(view)
    findings = []
    for hub_id, rows in sorted(view.rows_by_hub.items()):
        for row in rows:
            if row["artifact_id"] in authored_acl and not acl_is_authored(row, authored_acl):
                findings.append(Finding("acl_mismatch", _row_where(hub_id, row),
                                        f"rendered acl {row.get('acl')} differs from authored "
                                        f"{authored_acl[row['artifact_id']]}"))
    return findings


def check_unique_paths(view: BuildView) -> list[Finding]:
    """A native path names one artifact per hub (versions of one artifact may share it)."""
    findings = []
    for hub_id, rows in sorted(view.rows_by_hub.items()):
        owners: dict[str, set[str]] = {}
        for row in rows:
            if row.get("path"):
                owners.setdefault(row["path"], set()).add(row["artifact_id"])
        for path, artifact_ids in sorted(owners.items()):
            if len(artifact_ids) > 1:
                findings.append(Finding("duplicate_path", f"{hub_id}:{path}",
                                        f"path used by {len(artifact_ids)} artifacts: {sorted(artifact_ids)}"))
    return findings


def distinctive_lines(text: str, noise_sentences: list[str]) -> set[str]:
    """Authored lines of a restricted page: shared filler noise removed, short lines skipped."""
    lines = set()
    for line in text.splitlines():
        for sentence in noise_sentences:
            line = line.replace(sentence, "")
        line = line.strip()
        if len(line) >= MIN_DISTINCTIVE_LINE:
            lines.add(line)
    return lines


def check_restricted(world: World, view: BuildView, world_dir: Path = DEFAULT_WORLD_DIR) -> list[Finding]:
    noise_sentences = load_filler(Path(world_dir) / world.filler.file).noise_sentences
    authored_acl = authored_acl_by_opaque_id(view)
    findings = []
    for planted in world.planted:
        if not isinstance(planted, PlantedRestricted):
            continue
        restricted_rows = [row for row in view.rows_by_hub.get(planted.hub, [])
                           if row["location"] == planted.place]
        restricted_ids = {row["artifact_id"] for row in restricted_rows
                          if acl_is_authored(row, authored_acl)}
        secrets = {entry["token"] for entry in view.canaries
                   if entry["hub"] == planted.hub and entry["place"] == planted.place}
        secrets |= {row["title"] for row in restricted_rows}
        secrets.add(planted.place)
        for row in restricted_rows:
            secrets |= distinctive_lines(row["text"], noise_sentences)
        for hub_id, rows in sorted(view.rows_by_hub.items()):
            for row in rows:
                if hub_id == planted.hub and row["artifact_id"] in restricted_ids:
                    continue
                text = visible_text(row)
                for secret in sorted(secrets):
                    if secret in text:
                        findings.append(Finding("restricted_leak", _row_where(hub_id, row),
                                                f"restricted {secret!r} from {planted.place} appears here"))
        for path, text in sorted(view.side_documents.items()):
            for secret in sorted(secrets):
                if secret in text:
                    findings.append(Finding("restricted_leak", path,
                                            f"restricted {secret!r} from {planted.place} appears here"))
    return findings


def declared_vocabulary(world: World, world_dir: Path) -> dict[str, set[str]]:
    filler = load_filler(Path(world_dir) / world.filler.file)
    extra = filler_natives(filler)
    return {hub_id: set(hub.declared_natives()) | set(extra.get(hub_id, []))
            for hub_id, hub in world.hubs.items()}


def check_vocabulary(world: World, view: BuildView, world_dir: Path) -> list[Finding]:
    declared = declared_vocabulary(world, world_dir)
    all_natives = sorted(set().union(*declared.values()))
    findings = []
    for hub_id, rows in sorted(view.rows_by_hub.items()):
        own = declared.get(hub_id, set())
        foreign = [native for native in all_natives
                   if native not in own and not any(native in mine for mine in own)]
        for row in rows:
            text = visible_text(row)
            for native in foreign:
                if native in text:
                    findings.append(Finding("vocabulary_leak", _row_where(hub_id, row),
                                            f"{native!r} is not declared by {hub_id}"))
        for path, text in sorted(view.side_documents_for(hub_id).items()):
            for native in foreign:
                if native in text:
                    findings.append(Finding("vocabulary_leak", path, f"{native!r} is not declared by {hub_id}"))
    return findings


def check_filler(world: World, world_dir: Path) -> list[Finding]:
    filler = load_filler(Path(world_dir) / world.filler.file)
    core_entities = {entity.id for entity in world.entities}
    core_natives = {native for hub in world.hubs.values() for native in hub.declared_natives()}
    findings = []
    seen: dict[str, str] = {}
    for service in filler.services:
        if service.entity_id in core_entities:
            findings.append(Finding("filler_collision", service.key,
                                    f"filler entity {service.entity_id} is a core entity"))
        for native in (service.repo, service.skill_name, service.doc_space, service.memory_name):
            for core_native in sorted(core_natives):
                if native in core_native or core_native in native:
                    findings.append(Finding("filler_collision", service.key,
                                            f"filler native {native!r} collides with core {core_native!r}"))
            if native in seen and seen[native] != service.key:
                findings.append(Finding("filler_collision", service.key,
                                        f"filler native {native!r} is also used by {seen[native]}"))
            seen[native] = service.key
    return findings


def lint(world: World, build_dir: Path, world_dir: Path = DEFAULT_WORLD_DIR) -> list[Finding]:
    """Run every rule against a rendered build; returns findings sorted by rule and location."""
    view = load_build(build_dir)
    canary_tokens = tuple(entry["token"] for entry in view.canaries)
    world_identifiers = tuple(
        [fact.id for fact in world.facts] + [entity.id for entity in world.entities]
        + [planted.id for planted in world.planted] + [artifact.id for artifact in world.artifacts])
    findings = (
        check_planted(world, view)
        + check_facts(world, view)
        + check_spans(view)
        + check_acls(view)
        + check_unique_paths(view)
        + check_restricted(world, view, world_dir)
        + check_vocabulary(world, view, world_dir)
        + check_private_leaks(view, tuple(identifier for identifier in world_identifiers
                                          if identifier not in canary_tokens))
        + check_filler(world, world_dir)
    )
    return sorted(set(findings), key=lambda finding: (finding.rule, finding.where, finding.message))


def leak_scan(build_dir: Path) -> list[Finding]:
    return check_private_leaks(load_build(build_dir))


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Lint a rendered world build.")
    parser.add_argument("--leak-scan", type=Path, metavar="BUILD_DIR",
                        help="only scan hub-visible output for identifiers listed in private/")
    parser.add_argument("--build", type=Path, help="rendered build directory (full lint)")
    parser.add_argument("--world", type=Path, default=DEFAULT_WORLD_DIR, help="world directory")
    arguments = parser.parse_args(argv)
    if arguments.leak_scan:
        findings = leak_scan(arguments.leak_scan)
    elif arguments.build:
        world_dir = arguments.world
        findings = lint(load_world(world_dir / "world.yaml"), arguments.build, world_dir)
    else:
        parser.error("pass --leak-scan BUILD_DIR or --build BUILD_DIR")
    for finding in findings:
        print(finding)
    print(f"{len(findings)} finding(s)", file=sys.stderr)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
