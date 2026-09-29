from pathlib import Path

import yaml

REG = yaml.safe_load((Path(__file__).resolve().parents[1] / "docs" / "scenario-register.yaml").read_text())
ALIGN = {"checked", "discrepancy", "pending"}
EXEC = {"planned", "implemented-and-tested", "negative-contract-only", "deferred"}


def test_all_hld_examples_and_fixtures_present():
    ids = {r["id"] for r in REG["rows"]}
    for n in range(1, 16):
        assert any(i.startswith(f"EX-{n:02d}") for i in ids), n
    for n in range(16, 26):
        assert f"FX-{n}" in ids


def test_states_valid_and_nothing_claimed_as_run():
    for r in REG["rows"]:
        assert r["spec_alignment"] in ALIGN
        assert r["execution_status"] in EXEC
        assert r["execution_status"] != "implemented-and-tested", r["id"]


def test_partial_and_deferred_are_labelled():
    rows = {r["id"]: r for r in REG["rows"]}
    assert rows["EX-07"]["scope"] == "partial"      # verify without D7
    assert rows["EX-06"]["scope"] == "partial"      # no LLM decomposition
    assert rows["EX-11"]["execution_status"] == "negative-contract-only"
