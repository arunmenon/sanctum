"""Effective run configuration and input hashes, recorded into a run manifest (M8 review item 6).

Pairing checks compare what a run actually used (from its manifest), not today's matrix: the
arm's switches, released hubs, registry, memory release, decision-provider parameters, SUT code
and the other inputs, each as a content hash.
"""
import hashlib
import json
from pathlib import Path
from typing import Optional

import yaml

ROOT = Path(__file__).resolve().parents[2]


def tree_sha256(path: Optional[Path], pattern: str = "*") -> Optional[str]:
    """Content hash of a file or of every file under a directory (paths included)."""
    if path is None:
        return None
    path = Path(path)
    if not path.exists():
        return None
    digest = hashlib.sha256()
    files = [path] if path.is_file() else sorted(p for p in path.rglob(pattern)
                                                 if p.is_file() and "__pycache__" not in p.parts)
    for file in files:
        digest.update(str(file.relative_to(path.parent if path.is_file() else path)).encode())
        digest.update(file.read_bytes())
    return digest.hexdigest()


def effective_configuration(*, sut: str, config_id: str, hubs: list[str], cases_dir: Path,
                            registry: Optional[Path] = None, memory_release: Optional[str] = None,
                            memory_seed: Optional[Path] = None, decision_provider: Optional[str] = None,
                            decision_params: Optional[Path] = None, matrix_path: Path = ROOT / "configs" / "matrix.yaml",
                            hubs_config: Path = ROOT / "configs" / "hubs.yaml",
                            failure_profiles: Path = ROOT / "configs" / "failure_profiles.yaml") -> dict:
    matrix = yaml.safe_load(Path(matrix_path).read_text())
    arm = matrix["arms"].get(config_id)
    memory_dir = Path(memory_seed) / memory_release if memory_seed and memory_release else None
    return {
        "sut": sut,
        "arm_switches": dict(arm) if arm is not None else None,
        "shared": matrix["shared"],
        "released_hubs": sorted(hubs),
        "registry_sha256": tree_sha256(registry),
        "memory_release": memory_release,
        "memory_release_sha256": tree_sha256(memory_dir),
        "decision_provider": decision_provider,
        "decision_params_sha256": tree_sha256(decision_params) if decision_provider else None,
        "sut_code_sha256": tree_sha256(ROOT / "src" / ("sanctum_ref" if sut == "ref" else "sanctum_stub"), "*.py"),
        "hubs_config_sha256": tree_sha256(hubs_config),
        "failure_profiles_sha256": tree_sha256(failure_profiles),
        "cases_sha256": tree_sha256(cases_dir, "*.yaml"),
    }


def record_effective(run_dir: Path, effective: dict) -> dict:
    path = Path(run_dir) / "manifest.json"
    manifest = json.loads(path.read_text())
    system_one = manifest.get("system_one")
    # provider and resolved model versions are effective inputs (handshake point 12); counts are not
    effective = {**effective, "system_one": None if not system_one else {
        key: system_one.get(key) for key in ("provider", "requested_model", "resolved_models", "profile", "data_class")}}
    manifest["effective"] = effective
    path.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


# Recorded inputs a matrix switch may change between paired runs, when it turns a component on/off.
INPUTS_BY_SWITCH = {
    "memory_store": ("memory_release", "memory_release_sha256"),
    "resolution": ("memory_release", "memory_release_sha256"),
    "decision_provider": ("decision_provider", "decision_params_sha256", "system_one"),
}


def effective_problems(effective_a: Optional[dict], effective_b: Optional[dict], may_differ: list[str]) -> list[str]:
    if effective_a is None or effective_b is None:
        return ["a run manifest has no recorded effective configuration (rerun with tools/run_lab.py)"]
    problems = []
    switches_a, switches_b = effective_a.get("arm_switches") or {}, effective_b.get("arm_switches") or {}
    for switch in sorted(set(switches_a) | set(switches_b)):
        if switches_a.get(switch) != switches_b.get(switch) and switch not in may_differ:
            problems.append(f"recorded switch {switch} differs outside may_differ")
    # a switch's inputs may differ only where the switch turns the component on or off (C2 has no
    # memory release, C4 has one); two arms that both use memory must use the same release
    allowed = {key for switch in may_differ for key in INPUTS_BY_SWITCH.get(switch, ())
               if "none" in (switches_a.get(switch), switches_b.get(switch))}
    for key in sorted(set(effective_a) | set(effective_b)):
        if key == "arm_switches" or key in allowed:
            continue
        if effective_a.get(key) != effective_b.get(key):
            problems.append(f"recorded {key} differs between runs")
    return problems
