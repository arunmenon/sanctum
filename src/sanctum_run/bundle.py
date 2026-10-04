"""Offline validation of reusable task bundles. Does not dispatch agent calls.

This first slice validates corpus pinning, task/gold linkage and configurable
diversity gates; it is not a complete experiment-config or scoring implementation.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import yaml


class BundleError(ValueError):
    pass


def _file(root: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value:
        raise BundleError("expected a bundle-relative file path")
    path = (root / value).resolve()
    if Path(value).is_absolute() or not path.is_relative_to(root) or not path.is_file():
        raise BundleError("referenced file missing or outside bundle")
    return path


def _records(path: Path) -> dict[str, dict]:
    records = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise BundleError("task/gold record must be an object")
        task_id = row.get("task_id")
        if not isinstance(task_id, str) or not task_id or task_id in records:
            raise BundleError("missing or duplicate task ID")
        records[task_id] = row
    if not records:
        raise BundleError("empty task/gold file")
    return records


def validate_bundle(config_path: Path) -> dict:
    """Return a safe summary, never private facts/prompts or credential contents."""
    try:
        return _validate(config_path)
    except (OSError, KeyError, TypeError, UnicodeError, json.JSONDecodeError, yaml.YAMLError):
        # Parser messages may contain private source text; do not forward them.
        raise BundleError("invalid or unreadable bundle structure") from None


def _validate(config_path: Path) -> dict:
    root = config_path.resolve().parent
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict) or config.get("schema_version") != 1:
        raise BundleError("unsupported bundle schema")
    manifest = _file(root, config["corpus"]["manifest"])
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    if digest != config["corpus"]["expected_sha256"]:
        raise BundleError("corpus manifest hash mismatch")
    manifest_body = json.loads(manifest.read_text())
    if not isinstance(manifest_body, dict):
        raise BundleError("corpus manifest must be an object")
    for name, expected in manifest_body.get("files", {}).items():
        artifact_file = _file(manifest.parent, name)
        if hashlib.sha256(artifact_file.read_bytes()).hexdigest() != expected:
            raise BundleError("corpus snapshot file hash mismatch")
    public_path = _file(root, config["tasks"])
    gold_path = _file(root, config["gold"])
    if public_path == gold_path:
        raise BundleError("public tasks and private gold must be separate files")
    tasks, gold = _records(public_path), _records(gold_path)
    if tasks.keys() != gold.keys():
        raise BundleError("task/gold IDs do not match")
    families = Counter()
    scopes = Counter()
    domains, sources, difficulties, answerability = set(), set(), set(), set()
    fact_sets: dict[frozenset[str], list[str]] = {}
    for task_id, task in tasks.items():
        if not isinstance(task.get("prompt"), str) or not task["prompt"].strip():
            raise BundleError("task prompt missing")
        family = task.get("family")
        if not isinstance(family, str) or not family:
            raise BundleError("task family missing")
        families[family] += 1
        facts = gold[task_id].get("required_facts")
        if not isinstance(facts, list) or not facts:
            raise BundleError("task needs at least one required fact")
        fact_ids = [f.get("fact_id") for f in facts if isinstance(f, dict)]
        if len(fact_ids) != len(facts) or any(not isinstance(f, str) or not f for f in fact_ids):
            raise BundleError("invalid required fact IDs")
        if len(set(fact_ids)) != len(fact_ids):
            raise BundleError("duplicate fact ID within task")
        fact_sets.setdefault(frozenset(fact_ids), []).append(task_id)
        matrix = gold[task_id].get("matrix", {})
        if not isinstance(matrix, dict):
            raise BundleError("diversity matrix must be an object")
        scope = matrix.get("scope")
        if scope is not None:
            if scope not in ("in_scope", "partial", "out_of_scope"):
                raise BundleError("invalid task scope")
            scopes[scope] += 1
            expected_answerability = {"in_scope": "complete", "partial": "partial", "out_of_scope": "unavailable"}
            if matrix.get("answerability") != expected_answerability[scope]:
                raise BundleError("scope and answerability disagree")
        for name, values in (("domains", domains), ("sources", sources)):
            entries = matrix.get(name, [])
            if not isinstance(entries, list) or any(not isinstance(v, str) or not v for v in entries):
                raise BundleError("invalid diversity matrix values")
            values.update(entries)
        for name, values in (("difficulty", difficulties), ("answerability", answerability)):
            entry = matrix.get(name)
            if entry is not None:
                if not isinstance(entry, str) or not entry:
                    raise BundleError("invalid diversity matrix label")
                values.add(entry)
    diversity = config.get("diversity", {})
    if not isinstance(diversity, dict):
        raise BundleError("diversity requirements must be an object")
    if diversity.get("family_counts") is not None and dict(families) != diversity["family_counts"]:
        raise BundleError("task family quotas not satisfied")
    if diversity.get("scope_counts") is not None and dict(scopes) != diversity["scope_counts"]:
        raise BundleError("task scope quotas not satisfied")
    for key, observed in (("required_domains", domains), ("required_sources", sources),
                          ("required_difficulties", difficulties), ("required_answerability", answerability)):
        required = diversity.get(key, [])
        if not isinstance(required, list) or any(not isinstance(v, str) or not v for v in required):
            raise BundleError("diversity requirements must be lists of labels")
        if not set(required).issubset(observed):
            raise BundleError("task diversity coverage incomplete")
    duplicate_count = sum(len(ids) - 1 for ids in fact_sets.values())
    exceptions = diversity.get("duplicate_fact_set_exceptions", [])
    if not isinstance(exceptions, list) or any(
        not isinstance(group, list) or len(group) < 2 or
        any(not isinstance(tid, str) or tid not in tasks for tid in group) or
        len(group) != len(set(group)) for group in exceptions
    ):
        raise BundleError("invalid duplicate fact-set exception")
    observed_duplicates = {frozenset(ids) for ids in fact_sets.values() if len(ids) > 1}
    declared_exceptions = {frozenset(group) for group in exceptions}
    if not declared_exceptions.issubset(observed_duplicates):
        raise BundleError("fact-set exception does not match an actual duplicate group")
    if diversity.get("reject_duplicate_fact_sets", False) and observed_duplicates - declared_exceptions:
        raise BundleError("duplicate required-fact sets need revision or reviewed exception")
    return {"task_count": len(tasks), "family_counts": dict(families),
            "scope_counts": dict(scopes),
            "domain_count": len(domains), "duplicate_fact_sets": duplicate_count,
            "manifest_sha256": digest, "validation_scope": "task_bundle_only",
            "ready_for_paid_dispatch": False}
