"""The Laya D4 live experiment arm (owner-approved) binds exactly: provider, resolved model,
template and the state layout the broker reports for that template. A binding that did not match
would leave the arm in shadow, and the grid would equal C4 by construction."""
from pathlib import Path

from sanctum_ref.providers.http_systemone import Calibration
from sanctum_ref.providers.templates import DEFAULT_TEMPLATES, TemplateRegistry
from tools.fit_system_one import round3_release

ROOT = Path(__file__).resolve().parents[1]
ARM_TEMPLATE = "d4-noul-v2-support-compact-150"
BINDING = ROOT / "configs" / "calibration" / "laya-local@laya-rl-agent.d4.yaml"


def test_binding_names_the_arm_layout_exactly():
    template = TemplateRegistry(DEFAULT_TEMPLATES).templates[ARM_TEMPLATE]
    calibration = Calibration(BINDING)
    layout = round3_release(template.state)
    assert layout == "r3-state-v2-compact-150"
    assert calibration.binding["descriptor_release"] == layout
    assert calibration.matches("laya-local", "laya-rl-agent", layout, ARM_TEMPLATE)
    assert not calibration.matches("laya-local", "laya-rl-agent", "r3-state-v2", ARM_TEMPLATE)
    assert not calibration.matches("laya-local", "laya-rl-agent", layout, "d4-noul-v1")


def test_round3_release_matches_the_broker():
    assert round3_release("refs") == "none" and round3_release(None) == "none"
    assert round3_release("excerpts") == "r3-state-v2"
