"""Round 3 state layout r3-state-v2 (prompt review §2): broker-built, provenance-backed records."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from sanctum_run.round3_state import STATE_V1, STATE_V2, build_record, excerpt_of
from sanctum_world.render import build

ROOT = Path(__file__).resolve().parents[1]

CONFIG = """# repo:payments/payment-auth
# payments/payment-auth/config/retry.yaml
environment: prod
release: R42
retry:
  max_retries: 5
  backoff_ms: 200
# Load tests ran in the staging cluster overnight.
owner: payments team
"""


def _row(text, source="codehub", location="repo:payments/payment-auth", **extra):
    return SimpleNamespace(text=text, version=extra.get("version", "R42"), environment=extra.get("environment", "prod"),
                           artifact_id="art-1", location=location)


def test_offsets_map_back_to_the_artifact_text():
    excerpt, spans, _ = excerpt_of(CONFIG, 0, len(CONFIG), "how many retries on payment auth?")
    assert excerpt == "\n".join(CONFIG[span["start"]:span["end"]] for span in spans)
    assert all(0 <= s["start"] <= s["end"] <= len(CONFIG) for s in spans)
    assert [s["start"] for s in spans] == sorted(s["start"] for s in spans)          # original order


def test_qualifiers_are_kept_with_a_value_line():
    excerpt, _, _ = excerpt_of(CONFIG, 0, len(CONFIG), "retry limit")
    assert "max_retries: 5" in excerpt
    assert "environment: prod" in excerpt and "release: R42" in excerpt
    assert "owner: payments team" not in excerpt                                    # not selected, not adjacent


def test_excerpt_stays_inside_the_retrieved_span():
    start = CONFIG.index("retry:")
    end = CONFIG.index("backoff_ms")
    _, spans, _ = excerpt_of(CONFIG, start, end, "retries")
    assert all(start <= s["start"] and s["end"] <= end for s in spans)


def test_prefix_fallback_is_bounded():
    text = "word " * 400
    excerpt, spans, _ = excerpt_of(text, 0, len(text), "zzz")
    assert len(excerpt) == 400 and spans == [{"start": 0, "end": 400}]


def test_v2_record_fields_and_v1_unchanged():
    ref = {"source_id": "codehub", "start": 0, "end": len(CONFIG)}
    record = build_record(STATE_V2, ref, _row(CONFIG), "retry limit")
    assert set(record) == {"source_id", "artifact_id", "version", "environment", "subject", "attribute",
                           "assertion_role", "excerpt", "excerpt_spans"}
    assert record["attribute"] == "max_retries" and record["assertion_role"] == "implemented_behavior"
    assert record["subject"] == "payments/payment-auth"
    assert build_record(STATE_V1, ref, _row(CONFIG), "x") == {"source_id": "codehub", "version": "R42",
                                                             "environment": "prod", "text": CONFIG[:1200]}


@pytest.fixture(scope="module")
def world_build(tmp_path_factory):
    out = tmp_path_factory.mktemp("r3-build") / "world"
    build(ROOT / "world", 20260930, out)
    return out


def test_no_gold_vocabulary_in_records(world_build):
    private = json.loads((world_build / "private" / "entity_refs.json").read_text())
    world_ids = set(private) | set(private.values())
    checked = 0
    for hub in ("codehub", "skillhub", "dochub", "memoryhub"):
        for line in (world_build / "hubs" / hub / "artifacts.jsonl").read_text().splitlines()[:150]:
            row = json.loads(line)
            ref = {"source_id": hub, "start": 0, "end": len(row["text"])}
            record = build_record(STATE_V2, ref, SimpleNamespace(**{k: row[k] for k in (
                "text", "version", "environment", "artifact_id", "location")}), "retry limit timeout batch size")
            for field in ("subject", "attribute"):
                value = record[field]
                assert value is None or value in row["text"] or value in (row["location"] or ""), (field, value)
            serialized = json.dumps(record)
            assert not any(world_id in serialized for world_id in world_ids if world_id.startswith(("svc.", "f.", "ent-")))
            checked += 1
    assert checked == 600
