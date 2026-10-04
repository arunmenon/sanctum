import hashlib
import json

import pytest
import yaml

from sanctum_run.bundle import BundleError, validate_bundle


def make_bundle(root, domain="shipping", source="documents"):
    root.mkdir()
    (root / "manifest.json").write_text(json.dumps({"domain": domain}))
    (root / "tasks.jsonl").write_text(json.dumps({"task_id": "t1", "family": "behavior",
                                               "prompt": "Explain current behavior"}) + "\n")
    (root / "gold.jsonl").write_text(json.dumps({"task_id": "t1", "required_facts": [{"fact_id": "f1"}],
        "matrix": {"domains": [domain], "sources": [source], "difficulty": "simple",
                   "answerability": "complete"}}) + "\n")
    config = {"schema_version": 1, "corpus": {"manifest": "manifest.json", "expected_sha256":
        hashlib.sha256((root / "manifest.json").read_bytes()).hexdigest()},
        "tasks": "tasks.jsonl", "gold": "gold.jsonl", "diversity": {
        "family_counts": {"behavior": 1}, "required_domains": [domain],
        "required_sources": [source], "reject_duplicate_fact_sets": True}}
    path = root / "experiment.yaml"
    path.write_text(yaml.safe_dump(config))
    return path, config


def test_unrelated_bundles_need_no_runner_edits(tmp_path):
    for name, domain, source in (("a", "shipping", "documents"), ("b", "catalog", "code")):
        path, _ = make_bundle(tmp_path / name, domain, source)
        result = validate_bundle(path)
        assert result["task_count"] == 1
        assert result["ready_for_paid_dispatch"] is False
        assert "required_facts" not in result


@pytest.mark.parametrize("failure", ["hash", "gold_id", "quota", "duplicate_facts", "escape"])
def test_invalid_bundle_is_rejected(tmp_path, failure):
    path, config = make_bundle(tmp_path / "bundle")
    if failure == "hash":
        (path.parent / "manifest.json").write_text("changed")
    elif failure == "gold_id":
        gold = json.loads((path.parent / "gold.jsonl").read_text())
        gold["task_id"] = "wrong"
        (path.parent / "gold.jsonl").write_text(json.dumps(gold))
    elif failure == "quota":
        config["diversity"]["family_counts"] = {"behavior": 2}
    elif failure == "duplicate_facts":
        for name in ("tasks.jsonl", "gold.jsonl"):
            row = json.loads((path.parent / name).read_text())
            row["task_id"] = "t2"
            with (path.parent / name).open("a") as stream:
                stream.write(json.dumps(row) + "\n")
        config["diversity"]["family_counts"] = {"behavior": 2}
    else:
        config["tasks"] = "../outside.jsonl"
        (tmp_path / "outside.jsonl").write_text("[]")
    path.write_text(yaml.safe_dump(config))
    with pytest.raises(BundleError):
        validate_bundle(path)


@pytest.mark.parametrize("failure", ["missing_scope", "mismatch", "snapshot_tamper", "false_exception"])
def test_scope_and_snapshot_invariants(tmp_path, failure):
    path, config = make_bundle(tmp_path / "bundle")
    config['diversity']['scope_counts'] = {'in_scope': 1}
    gold_path = path.parent / 'gold.jsonl'
    gold = json.loads(gold_path.read_text())
    if failure != 'missing_scope':
        gold['matrix']['scope'] = 'in_scope'
    if failure == 'mismatch':
        gold['matrix']['answerability'] = 'partial'
    if failure == 'false_exception':
        config['diversity']['duplicate_fact_set_exceptions'] = [['t1', 'unknown']]
    if failure == 'snapshot_tamper':
        artifact = path.parent / 'artifact.txt'
        artifact.write_text('original')
        manifest = path.parent / 'manifest.json'
        manifest.write_text(json.dumps({'files': {'artifact.txt': hashlib.sha256(artifact.read_bytes()).hexdigest()}}))
        config['corpus']['expected_sha256'] = hashlib.sha256(manifest.read_bytes()).hexdigest()
        artifact.write_text('changed after manifest pinning')
    gold_path.write_text(json.dumps(gold)+'\n')
    path.write_text(yaml.safe_dump(config))
    with pytest.raises(BundleError):
        validate_bundle(path)


def test_exact_duplicate_exception_is_bounded(tmp_path):
    path, config = make_bundle(tmp_path / 'bundle')
    for filename in ('tasks.jsonl', 'gold.jsonl'):
        p=path.parent / filename
        row=json.loads(p.read_text());row['task_id']='t2'
        with p.open('a') as f:
            f.write(json.dumps(row)+'\n')
    config['diversity']['family_counts']={'behavior':2}
    config['diversity']['duplicate_fact_set_exceptions']=[['t1','t2']]
    path.write_text(yaml.safe_dump(config))
    assert validate_bundle(path)['duplicate_fact_sets']==1
