"""Seeded noise services and artifacts (lab plan §5.2).

Filler exists so fan-out and token budgets matter. It reuses the hub templates with
filler vocabulary and never asserts a core fact: filler bodies carry no fact slots.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field

from .rng import sub_rng
from .schema import World

Domain = Literal["payments", "identity", "platform"]
SLOT_KEYS = ("class", "param2", "param", "word", "Word", "name", "place")


class _F(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class FillerService(_F):
    key: str
    domain: Domain
    repo: str
    skill_name: str
    doc_space: str
    memory_name: str

    @property
    def entity_id(self) -> str:
        return f"svc.{self.key}"


class FillerFile(_F):
    services: list[FillerService] = Field(min_length=1)
    domain_places: dict[str, dict[str, str]]
    domain_groups: dict[str, str]
    namespaces: dict[str, str]
    artifact_counts: dict[str, int]
    kinds: dict[str, list[str]]
    version_refs: dict[str, list[str]]
    class_stems: list[str]
    class_suffixes: list[str]
    words: list[str]
    java_headers: list[str]
    java_fields: list[str]
    java_comments: list[str]
    yaml_keys: list[str]
    bodies: dict[str, list[str]]
    extra_sentences: dict[str, list[str]]
    titles: dict[str, list[str]]
    noise_sentences: list[str] = Field(min_length=3)


@dataclass
class FillerVersion:
    ref: str
    env: Optional[str]
    body: str


@dataclass
class FillerArtifact:
    key: str                       # stable private key used for the opaque id
    hub: str
    kind: str
    title: str
    path: Optional[str]
    place: Optional[str]
    name: Optional[str]
    namespace: Optional[str]
    principal: Optional[str]
    acl: list[str]
    service_key: str
    noise: str
    versions: list[FillerVersion] = field(default_factory=list)


def load_filler(path: Path) -> FillerFile:
    return FillerFile.model_validate(yaml.safe_load(Path(path).read_text()))


def filler_natives(filler: FillerFile) -> dict[str, list[str]]:
    """Natives each hub declares for filler services (on top of the core world's)."""
    return {
        "codehub": sorted(service.repo for service in filler.services),
        "skillhub": sorted(service.skill_name for service in filler.services),
        "dochub": sorted(service.doc_space for service in filler.services),
        "memoryhub": sorted(service.memory_name for service in filler.services),
        "incidenthub": [],
    }


def noise_paragraph(rng, filler: FillerFile, minimum: int = 2, maximum: int = 4) -> str:
    count = rng.randint(minimum, maximum)
    return " ".join(rng.sample(filler.noise_sentences, count))


def _fill(template: str, values: dict[str, str]) -> str:
    text = template
    for key in SLOT_KEYS:
        text = text.replace("{{" + key + "}}", values.get(key, ""))
    if "{{" in text.replace("{{param}}", ""):
        raise ValueError(f"unfilled filler slot in {template!r}")
    return text


def _body_skeleton(rng, filler: FillerFile, kind: str) -> str:
    """Seeded structure for one artifact; `{{param}}` slots stay open so each version
    gets fresh values while keeping the same shape."""
    if kind == "java_class":
        lines = [rng.choice(filler.java_headers)]
        if rng.random() < 0.5:
            lines.insert(0, rng.choice(filler.java_comments))
        fields = rng.sample(filler.java_fields, rng.randint(2, 4))
        lines += ["    " + line for line in fields] + ["}"]
        return "\n".join(lines)
    if kind == "yaml_config":
        keys = rng.sample(filler.yaml_keys, rng.randint(2, 4))
        return "{{word}}:\n" + "\n".join("  " + key for key in keys)
    sentences = [rng.choice(filler.bodies[kind])]
    extras = filler.extra_sentences.get(kind, [])
    if extras:
        sentences += rng.sample(extras, rng.randint(0, 3))
    rng.shuffle(sentences)
    return " ".join(sentences)


def _fill_params(rng, text: str) -> str:
    """Give every `{{param}}` its own seeded value."""
    while "{{param}}" in text:
        text = text.replace("{{param}}", str(rng.randint(2, 900)), 1)
    return text


def _unique_path(path: str, used: set[str]) -> str:
    """Deterministic dedupe: add -2, -3, ... to the file stem (to the parent directory for
    Java, whose file name must match the class)."""
    if path not in used:
        return path
    directory, file_name = path.rsplit("/", 1)
    stem, extension = file_name.rsplit(".", 1)
    counter = 2
    while True:
        if extension == "java":
            candidate = f"{directory}-{counter}/{file_name}"
        else:
            candidate = f"{directory}/{stem}-{counter}.{extension}"
        if candidate not in used:
            return candidate
        counter += 1


def generate_filler(world: World, filler: FillerFile, seed: int) -> list[FillerArtifact]:
    principals_by_group = {
        group: sorted(principal.id for principal in world.principals
                      if group in principal.groups and "restricted-incidents" not in principal.groups)
        for group in sorted(set(filler.domain_groups.values()))
    }
    artifacts: list[FillerArtifact] = []
    used_paths = {hub_id: {artifact.path for artifact in world.artifacts
                           if artifact.hub == hub_id and artifact.path}
                  for hub_id in filler.artifact_counts}
    for hub_id in sorted(filler.artifact_counts):
        weight_rng = sub_rng(seed, "filler-weights", hub_id)
        weights = [weight_rng.randint(1, 6) for _ in filler.services]
        for index in range(filler.artifact_counts[hub_id]):
            rng = sub_rng(seed, "filler", hub_id, index)
            service = rng.choices(filler.services, weights=weights, k=1)[0]
            kind = rng.choice(filler.kinds[hub_id])
            word = rng.choice(filler.words)
            class_name = rng.choice(filler.class_stems) + rng.choice(filler.class_suffixes)
            suffix = rng.randrange(100, 1000)
            group = filler.domain_groups[service.domain]
            namespace: Optional[str] = None
            principal: Optional[str] = None
            name: Optional[str] = None
            place: Optional[str] = None
            path: Optional[str] = None
            if hub_id == "codehub":
                place = service.repo
                repo_path = service.repo.split(":", 1)[1]
                if kind == "java_class":
                    path = f"{repo_path}/src/main/java/com/kestrel/m{suffix}/{class_name}.java"
                    title = f"{class_name}.java"
                elif kind == "yaml_config":
                    path = f"{repo_path}/config/{word}-{suffix}.yaml"
                    title = f"{word}-{suffix}.yaml"
                else:
                    path = f"{repo_path}/docs/{word}-{suffix}.md"
                    title = f"{word}-{suffix}.md"
            elif hub_id == "skillhub":
                name = service.skill_name
                namespace = filler.namespaces[service.domain]
                place = filler.domain_places["skillhub"][service.domain]
                path = f"{place}{service.key}-{word}-{suffix}.md"
            elif hub_id == "dochub":
                place = service.doc_space
            elif hub_id == "memoryhub":
                name = service.memory_name
                principal = rng.choice(principals_by_group[group])
            elif hub_id == "incidenthub":
                place = filler.domain_places["incidenthub"][service.domain]
            values = {"class": class_name, "word": word, "Word": word.capitalize(),
                      "name": name or "", "place": place or ""}
            if hub_id != "codehub":
                title = _fill(rng.choice(filler.titles[kind]), values)

            refs = filler.version_refs.get(hub_id)
            if refs:
                first = rng.randrange(len(refs))
                chosen_refs = refs[first:first + rng.randint(1, len(refs) - first)]
            else:
                chosen_refs = ["current"]
            body_skeleton = _body_skeleton(rng, filler, kind)
            versions = []
            for ref in chosen_refs:
                body = _fill_params(rng, _fill(body_skeleton, {**values, "param": "{{param}}"}))
                env = ("experiment" if ref == "exp-branch" else "prod") if hub_id == "codehub" else None
                versions.append(FillerVersion(ref=ref, env=env, body=body))
            if path:
                path = _unique_path(path, used_paths[hub_id])
                used_paths[hub_id].add(path)
                if hub_id == "codehub":
                    title = path.rsplit("/", 1)[1]
            artifacts.append(FillerArtifact(
                key=f"filler/{hub_id}/{index}", hub=hub_id, kind=kind, title=title, path=path,
                place=place, name=name, namespace=namespace, principal=principal, acl=[group],
                service_key=service.key, noise=noise_paragraph(rng, filler), versions=versions,
            ))
    return artifacts
