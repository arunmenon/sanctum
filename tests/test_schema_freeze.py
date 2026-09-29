from pathlib import Path

from tools.export_schemas import OUT, render


def test_committed_schemas_match_models():
    """Contract changes must be deliberate: re-run tools/export_schemas.py and review the diff."""
    for name, text in render().items():
        committed = (OUT / name).read_text()
        assert committed == text, f"{name} out of date; run tools/export_schemas.py"
