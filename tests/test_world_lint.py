"""World linter: the real build lints clean; one mutated copy per rule trips it (M1 task 4)."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from sanctum_world.lint import leak_scan, lint, main as lint_main
from sanctum_world.render import build
from sanctum_world.schema import load_world

ROOT = Path(__file__).resolve().parents[1]
WORLD_DIR = ROOT / "world"
SEED = 20260930


@pytest.fixture(scope="module")
def world():
    return load_world(WORLD_DIR / "world.yaml")


@pytest.fixture(scope="module")
def pristine_build(tmp_path_factory) -> Path:
    out_dir = tmp_path_factory.mktemp("lint") / "world"
    build(WORLD_DIR, SEED, out_dir)
    return out_dir


@pytest.fixture
def mutable_build(pristine_build, tmp_path) -> Path:
    copy_dir = tmp_path / "world"
    shutil.copytree(pristine_build, copy_dir)
    return copy_dir


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))


def opaque_artifact_id(build_dir: Path, world_artifact_id: str) -> str:
    artifact_map = json.loads((build_dir / "private" / "artifact_map.json").read_text())
    return artifact_map[world_artifact_id]["artifact_id"]


def append_to_first_row(build_dir: Path, hub_id: str, extra_text: str) -> str:
    """Append text to the first unrestricted row of a hub; returns that row's artifact id."""
    path = build_dir / "hubs" / hub_id / "artifacts.jsonl"
    rows = read_jsonl(path)
    target = next(row for row in rows if row["location"] != "space:Incidents")
    target["text"] += f"\n{extra_text}\n"
    write_jsonl(path, rows)
    return target["artifact_id"]


def rules_of(findings) -> set[str]:
    return {finding.rule for finding in findings}


def test_real_world_lints_clean(world, pristine_build):
    assert lint(world, pristine_build, WORLD_DIR) == []


def test_real_world_leak_scan_is_clean(pristine_build):
    assert leak_scan(pristine_build) == []


def test_dropped_planted_artifact_is_reported(world, mutable_build):
    injection_id = opaque_artifact_id(mutable_build, "a.doc.injection")
    path = mutable_build / "hubs" / "dochub" / "artifacts.jsonl"
    write_jsonl(path, [row for row in read_jsonl(path) if row["artifact_id"] != injection_id])
    findings = lint(world, mutable_build, WORLD_DIR)
    assert any(finding.rule == "planted_missing" and "p.dochub-injection" in finding.where
               for finding in findings), findings


def test_missing_planted_index_entry_is_reported(world, mutable_build):
    path = mutable_build / "private" / "planted_index.json"
    index = json.loads(path.read_text())
    del index["p.composite-auth-skill"]
    path.write_text(json.dumps(index))
    findings = lint(world, mutable_build, WORLD_DIR)
    assert any(finding.rule == "planted_missing" and finding.where == "p.composite-auth-skill"
               for finding in findings)


def test_leaked_canary_is_reported(world, mutable_build):
    leaking_id = append_to_first_row(mutable_build, "skillhub", "see CANARY-INC-4417")
    findings = lint(world, mutable_build, WORLD_DIR)
    assert any(finding.rule == "restricted_leak" and leaking_id in finding.where for finding in findings)
    assert any(finding.rule == "private_id_leak" and leaking_id in finding.where
               for finding in leak_scan(mutable_build))


def test_leaked_restricted_title_is_reported(world, mutable_build):
    leaking_id = append_to_first_row(mutable_build, "memoryhub", "recalled INC-2291 postmortem today")
    findings = lint(world, mutable_build, WORLD_DIR)
    assert any(finding.rule == "restricted_leak" and leaking_id in finding.where
               and "INC-2291 postmortem" in finding.message for finding in findings)


def test_leaked_fact_id_is_reported(world, mutable_build):
    leaking_id = append_to_first_row(mutable_build, "codehub", "// f.retry-limit.impl")
    for findings in (lint(world, mutable_build, WORLD_DIR), leak_scan(mutable_build)):
        assert any(finding.rule == "private_id_leak" and leaking_id in finding.where
                   and "f.retry-limit.impl" in finding.message for finding in findings)


def test_leaked_opaque_entity_ref_is_found_by_leak_scan(mutable_build):
    entity_refs = json.loads((mutable_build / "private" / "entity_refs.json").read_text())
    entity_ref = entity_refs["svc.payment-auth"]
    leaking_id = append_to_first_row(mutable_build, "dochub", f"owner {entity_ref}")
    assert any(leaking_id in finding.where and entity_ref in finding.message
               for finding in leak_scan(mutable_build))
    assert lint_main(["--leak-scan", str(mutable_build)]) == 1


def test_removed_asserting_artifact_is_reported(world, mutable_build):
    path = mutable_build / "private" / "provenance.jsonl"
    write_jsonl(path, [row for row in read_jsonl(path) if row["fact_id"] != "f.identity-lockout.policy"])
    findings = lint(world, mutable_build, WORLD_DIR)
    assert any(finding.rule == "fact_unasserted" and finding.where == "f.identity-lockout.policy"
               for finding in findings)


def test_asserted_coverage_gap_is_reported(world, mutable_build):
    path = mutable_build / "private" / "provenance.jsonl"
    rows = read_jsonl(path)
    forged = dict(rows[0], fact_id="f.fx-quote.ttl", entity_id="svc.fx-quote")
    write_jsonl(path, rows + [forged])
    findings = lint(world, mutable_build, WORLD_DIR)
    assert any(finding.rule == "coverage_gap_asserted" and finding.where == "f.fx-quote.ttl"
               for finding in findings)


def test_shifted_span_is_reported(world, mutable_build):
    path = mutable_build / "private" / "provenance.jsonl"
    rows = read_jsonl(path)
    rows[0]["start"] += 1
    rows[0]["end"] += 1
    write_jsonl(path, rows)
    assert "span_mismatch" in rules_of(lint(world, mutable_build, WORLD_DIR))


def test_cross_hub_name_is_reported(world, mutable_build):
    leaking_id = append_to_first_row(mutable_build, "skillhub", "ask the PA-svc owners")
    findings = lint(world, mutable_build, WORLD_DIR)
    assert any(finding.rule == "vocabulary_leak" and leaking_id in finding.where
               and "'PA-svc'" in finding.message for finding in findings)


def test_filler_name_colliding_with_core_is_reported(world, pristine_build, tmp_path):
    world_copy = tmp_path / "world"
    shutil.copytree(WORLD_DIR, world_copy)
    filler_path = world_copy / "filler.yaml"
    filler = yaml.safe_load(filler_path.read_text())
    filler["services"][0]["skill_name"] = "Auth Service"
    filler_path.write_text(yaml.safe_dump(filler, sort_keys=False))
    findings = lint(world, pristine_build, world_copy)
    assert any(finding.rule == "filler_collision" and "'Auth Service'" in finding.message
               for finding in findings)


def test_lint_cli_exit_codes(pristine_build, mutable_build):
    append_to_first_row(mutable_build, "skillhub", "ask the PA-svc owners")
    environment = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    command = [sys.executable, str(ROOT / "tools" / "lint_world.py"), "--build"]
    clean = subprocess.run(command + [str(pristine_build)], capture_output=True, text=True, env=environment)
    broken = subprocess.run(command + [str(mutable_build)], capture_output=True, text=True, env=environment)
    assert clean.returncode == 0, clean.stdout + clean.stderr
    assert broken.returncode == 1 and "vocabulary_leak" in broken.stdout


def restricted_rows(build_dir: Path) -> tuple[Path, list[dict]]:
    path = build_dir / "hubs" / "dochub" / "artifacts.jsonl"
    return path, read_jsonl(path)


def test_weakened_restricted_acl_voids_canary_exemption(world, mutable_build):
    path, rows = restricted_rows(mutable_build)
    target = next(row for row in rows if row["location"] == "space:Incidents")
    target["acl"] = ["payments-eng"]
    write_jsonl(path, rows)
    findings = lint(world, mutable_build, WORLD_DIR)
    assert any(finding.rule == "acl_mismatch" and target["artifact_id"] in finding.where for finding in findings)
    assert any(finding.rule == "restricted_leak" and target["artifact_id"] in finding.where
               and "CANARY-INC" in finding.message for finding in findings)
    assert any(finding.rule == "private_id_leak" and target["artifact_id"] in finding.where
               for finding in leak_scan(mutable_build))


def test_copied_restricted_sentence_is_reported(world, mutable_build):
    _, rows = restricted_rows(mutable_build)
    incident = next(row for row in rows if row["location"] == "space:Incidents"
                    and "Root cause" in row["text"])
    sentence = next(line.strip() for line in incident["text"].splitlines() if line.startswith("Root cause"))
    leaking_id = append_to_first_row(mutable_build, "dochub", sentence)
    findings = lint(world, mutable_build, WORLD_DIR)
    assert any(finding.rule == "restricted_leak" and leaking_id in finding.where
               and "Root cause" in finding.message for finding in findings)


def test_leak_in_non_text_field_is_reported(world, mutable_build):
    path = mutable_build / "hubs" / "codehub" / "artifacts.jsonl"
    rows = read_jsonl(path)
    rows[-1]["version"] = "f.retry-limit.impl"
    write_jsonl(path, rows)
    for findings in (lint(world, mutable_build, WORLD_DIR), leak_scan(mutable_build)):
        assert any(finding.rule == "private_id_leak" and "f.retry-limit.impl" in finding.message
                   for finding in findings)


def test_unexpected_public_field_is_reported(world, mutable_build):
    path = mutable_build / "hubs" / "skillhub" / "artifacts.jsonl"
    rows = read_jsonl(path)
    rows[0]["provenance"] = "hidden"
    write_jsonl(path, rows)
    for findings in (lint(world, mutable_build, WORLD_DIR), leak_scan(mutable_build)):
        assert any(finding.rule == "unexpected_field" and "provenance" in finding.message
                   for finding in findings)


def test_renderer_guard_scans_every_field_and_the_allowlist(world, pristine_build):
    from sanctum_world.filler import load_filler
    from sanctum_world.render import RenderError, _guard_hub_rows, build_vocabulary

    vocabulary = build_vocabulary(world, load_filler(WORLD_DIR / world.filler.file))
    row = read_jsonl(pristine_build / "hubs" / "codehub" / "artifacts.jsonl")[-1]
    leaking = dict(row, version="f.retry-limit.impl")
    extra = dict(row, provenance="hidden")
    for bad_row in (leaking, extra):
        with pytest.raises(RenderError):
            _guard_hub_rows(world, {"codehub": [(bad_row["artifact_id"], 0, bad_row)]}, vocabulary, {}, [])


@pytest.mark.parametrize("secret_line", [
    'Internal finding: the "gateway retry loop" amplified the outage.',
    'Internal finding: path C:\\ops\\retry\\loop and caf\u00e9 \u2192 na\u00efve \U0001F525 amplified it.',
])
def test_restricted_line_with_escapable_characters_is_reported(world, mutable_build, secret_line):
    path, rows = restricted_rows(mutable_build)
    incident = next(row for row in rows if row["location"] == "space:Incidents")
    incident["text"] += secret_line + "\n"
    public = next(row for row in rows if row["location"] != "space:Incidents")
    public["text"] += secret_line + "\n"
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))  # ascii escapes on disk
    findings = lint(world, mutable_build, WORLD_DIR)
    assert any(finding.rule == "restricted_leak" and public["artifact_id"] in finding.where
               and "Internal finding" in finding.message for finding in findings), findings


def test_quoted_private_id_in_decoded_value_is_reported(world, mutable_build):
    leaking_id = append_to_first_row(mutable_build, "codehub", 'key = "f.retry-limit.impl\\\\x"')
    assert any(finding.rule == "private_id_leak" and leaking_id in finding.where
               for finding in leak_scan(mutable_build))
