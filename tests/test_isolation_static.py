"""Static isolation checks (M0). Runtime image allowlists and canary probes arrive at M1/M2;
a static scan alone is NOT sufficient isolation (lab-plan review L03)."""
import ast
from pathlib import Path

import yaml

from sanctum_contracts import RetrieveRequest
from sanctum_stub.stub import StubSUT

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

RULES = {
    "sanctum_contracts": {"forbid_imports": {"sanctum_eval", "sanctum_stub", "sut_ref", "gen", "world", "sanctum_world"}},
    "sanctum_stub": {"forbid_imports": {"sanctum_eval", "gen", "world", "sanctum_world"}},
    "sanctum_eval": {"forbid_imports": {"sanctum_stub", "sut_ref"}},
}
FORBIDDEN_LITERALS_RUNTIME = (
    "gold/", "gold\\", "world.yaml", "filler.yaml", "world/templates", "build/world",
    "build/world/private", "provenance.jsonl", "entity_refs.json", "tests/fixtures",
)


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            out |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
            out.add(n.module.split(".")[0])
    return out


def test_import_boundaries():
    for pkg, rule in RULES.items():
        for f in (SRC / pkg).rglob("*.py"):
            bad = _imports(f) & rule["forbid_imports"]
            assert not bad, f"{f.relative_to(ROOT)} imports {bad}"


def test_world_package_is_evaluator_side_only():
    """Only the evaluator side and tools may import sanctum_world; the runtime packages never."""
    assert (SRC / "sanctum_world").is_dir()
    for pkg in ("sanctum_contracts", "sanctum_stub"):
        for f in (SRC / pkg).rglob("*.py"):
            assert "sanctum_world" not in _imports(f), f"{f.relative_to(ROOT)} imports sanctum_world"


def test_runtime_packages_do_not_reference_evaluator_paths():
    for pkg in ("sanctum_contracts", "sanctum_stub"):
        for f in (SRC / pkg).rglob("*"):
            if f.is_file() and f.suffix in {".py", ".json", ".yaml"}:
                text = f.read_text()
                for lit in FORBIDDEN_LITERALS_RUNTIME:
                    assert lit not in text, f"{f.relative_to(ROOT)} mentions {lit!r}"


def test_stub_responses_carry_no_gold_fields():
    for f in (SRC / "sanctum_stub" / "responses").glob("*.json"):
        text = f.read_text()
        for key in ('"gold"', '"obligations"', '"answerable"', '"family"', '"case_id"', '"bundle_id"'):
            assert key not in text, f"{f.name} contains {key}"


def test_gold_only_mutation_invariance(tmp_path):
    """Changing gold alone must not change SUT output."""
    gold = yaml.safe_load((ROOT / "gold" / "m0" / "m0-001.yaml").read_text())
    req = RetrieveRequest.model_validate(gold["request"])
    before = StubSUT().retrieve(req)
    gold["expected"]["evidence_status"] = "insufficient"
    gold["forbidden"]["canaries"].append("NEW-CANARY")
    (tmp_path / "m0-001.yaml").write_text(yaml.safe_dump(gold))
    after = StubSUT().retrieve(req)
    assert before == after


def test_request_ids_do_not_encode_cases():
    for f in (ROOT / "gold" / "m0").glob("*.yaml"):
        g = yaml.safe_load(f.read_text())
        rid = g["request"]["request_id"]
        assert g["case_id"] not in rid and g["family"] not in rid
