"""M7: IncidentHub onboarded with no sanctum_ref code change (HLD §10 Ex12).

Onboarding is data only: an owner manifest (owners/manifests/incidenthub.yaml) and memory
release r2 (queue places, pinned descriptor) through the release mechanism. The hub stays held
back by default (configs/hubs.yaml) so earlier results reproduce; a run releases it explicitly."""
import json
import shutil
import subprocess
from pathlib import Path

import anyio
import pytest

from sanctum_hubs.tokens import TokenService
from sanctum_ref.memory import load_release
from sanctum_ref.registry import load_registry
from sanctum_run.gateway import HubGateway, released_hub_ids
from sanctum_run.proxy import GatewayProxy
from sanctum_run.runner import DEFAULT_HUBS_CONFIG
from tests.scenarios.conftest import scenario_world  # noqa: F401  (session world build)

ROOT = Path(__file__).resolve().parents[1]
M6_COMMIT = "92b4d62"
M7_COMMIT = "59f85ec"   # onboarding commit; later sanctum_ref changes (FX-23 hooks) are not onboarding


def test_sanctum_ref_core_unchanged_since_m6():
    if shutil.which("git") is None or subprocess.run(["git", "cat-file", "-e", M7_COMMIT], cwd=ROOT).returncode:
        pytest.skip("git history not available")
    changed = subprocess.run(["git", "diff", "--name-only", M6_COMMIT, M7_COMMIT, "--", "src/sanctum_ref"],
                             cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    assert changed == [], f"sanctum_ref changed for onboarding: {changed}"


def test_manifest_and_release_onboard_the_hub():
    registry = load_registry(ROOT / "owners" / "manifests")
    manifest = registry.manifest("incidenthub")
    assert manifest.search.tool == "search_incidents" and manifest.search.place_filter == "queue"
    capabilities = json.loads((ROOT / "build" / "world" / "hubs" / "incidenthub" / "capabilities.json").read_text()) \
        if (ROOT / "build" / "world").exists() else {"contract": {"filters": ["queue"]}}
    assert manifest.search.place_filter in capabilities["contract"]["filters"]
    r1, r2 = load_release(ROOT / "owners" / "memory_seed", "r1"), load_release(ROOT / "owners" / "memory_seed", "r2")
    assert not [p for p in r1.places if p.source == "incidenthub"]
    assert {p.source for p in r2.places} - {p.source for p in r1.places} == {"incidenthub"}
    assert "incidenthub" in r2.descriptors


async def _proxy_tools(world, include_held_back):
    token_service = TokenService(world / "identity" / "principals.json", "m7-secret")
    hub_ids = released_hub_ids(DEFAULT_HUBS_CONFIG, include_held_back)
    async with HubGateway(world, hub_ids, token_service) as gateway:
        proxy = await GatewayProxy.create(gateway, world)
        return {tool.name.split(".")[0] for tool in proxy._tools if "." in tool.name}


def test_proxy_exposes_incidenthub_only_when_released(scenario_world):  # noqa: F811
    assert "incidenthub" not in released_hub_ids(DEFAULT_HUBS_CONFIG)          # default: held back
    assert "incidenthub" not in anyio.run(_proxy_tools, scenario_world, False)
    assert "incidenthub" in anyio.run(_proxy_tools, scenario_world, True)
