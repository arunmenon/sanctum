"""Design/lab separation: the HLD set under design/ states design only. It never links into the
lab (reports, experiments, runs, holdout, acceptance), cites commits, or carries measured-once
results; the lab may link to design/."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "design"
EXPECTED = {"hld.md", "memory-design.md", "contracts-and-scenarios.md", "system-one-providers.md", "README.md",
            "section-map.md", "review-history.md", "preservation-check.json"}
LAB_TARGETS = re.compile(r"(^|/)(docs/reports|docs/experiments|reports|experiments|runs|holdout|acceptance)(/|$)")
LINK = re.compile(r"\]\(([^)\s]+)\)|href=[\"']([^\"']+)[\"']")
COMMIT = re.compile(r"(?<![0-9a-zA-Z_./-])[0-9a-f]{7,40}(?![0-9a-zA-Z_-])")


def _files():
    return sorted(path for path in DESIGN.rglob("*") if path.is_file())


def test_design_set_is_design_pages_only():
    assert {path.name for path in (DESIGN / "intelligence-layer").iterdir() if path.is_file()} == EXPECTED


def test_design_never_links_into_the_lab():
    for path in _files():
        for match in LINK.finditer(path.read_text(encoding="utf-8")):
            target = (match.group(1) or match.group(2)).split("#")[0]
            if target.startswith(("http://", "https://", "mailto:")) or not target:
                continue
            resolved = (path.parent / target).resolve()
            relative = resolved.relative_to(ROOT).as_posix() if resolved.is_relative_to(ROOT) else target
            assert not LAB_TARGETS.search(relative), f"{path.relative_to(ROOT)} links into the lab: {target}"
            assert resolved.is_relative_to(DESIGN), f"{path.relative_to(ROOT)} links outside design/: {target}"


def test_design_has_no_measurements_or_commit_citations():
    for path in _files():
        text = path.read_text(encoding="utf-8")
        assert "measured once" not in text.lower(), path
        if path.suffix == ".md":
            hashes = [h for h in COMMIT.findall(text) if not h.isdigit() and re.search(r"\d", h) and re.search(r"[a-f]", h)]
            assert not hashes, f"{path.relative_to(ROOT)} cites commit-like hashes {hashes}"


def test_lab_pages_link_back_to_design():
    lab = (ROOT / "docs" / "experiments" / "system-one-lab.md").read_text(encoding="utf-8")
    assert "../../design/intelligence-layer/system-one-providers.md#" in lab
