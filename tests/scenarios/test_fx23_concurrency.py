"""FX-23 under concurrent load (M8, HLD Fixture 23): many requests in flight against the
out-of-process C4 SUT while the admin publishes release r2 and then rolls back to r1.

Runner side only: the release switch is a change of the seed's ACTIVE file (owners/memory_seed
README), and every observation comes from the wire (response, receipt) or the runner's gateway
trace, never from sanctum_ref internals. Requests launched after the rollback must pin r1; every
request pins exactly one release; nothing errors, is dropped, or goes unobserved.
"""
import shutil
from pathlib import Path

import anyio
import pytest
import yaml

from sanctum_eval.load import load_gold
from sanctum_hubs.tokens import TokenService
from sanctum_run.gateway import HubGateway, released_hub_ids
from sanctum_run.process_sut import ProcessSUT
from sanctum_run.runner import DEFAULT_HUBS_CONFIG, public_request
from sanctum_run.sut import SUTContext

from .conftest import ROOT

GOLD_DEV = ROOT / "gold" / "dev"
WAVE = 12


def _seed_with_r2(target: Path) -> Path:
    source = ROOT / "owners" / "memory_seed"
    shutil.copytree(source / "r1", target / "r1")
    if (source / "r2").is_dir():                 # the owner-published r2, when it exists
        shutil.copytree(source / "r2", target / "r2")
    else:                                        # else r1 content under a new release id
        shutil.copytree(source / "r1", target / "r2")
        release = yaml.safe_load((target / "r2" / "release.yaml").read_text())
        release["release_id"] = "r2"
        (target / "r2" / "release.yaml").write_text(yaml.safe_dump(release, sort_keys=False))
    (target / "ACTIVE").write_text("r1\n")
    return target


def _activate(seed: Path, release_id: str) -> None:
    staging = seed / "ACTIVE.tmp"
    staging.write_text(release_id + "\n")
    staging.replace(seed / "ACTIVE")         # atomic, as an admin publish would be


async def _load(world: Path, seed: Path):
    golds = [load_gold(path) for path in sorted(GOLD_DEV.glob("*.yaml"))][: 3 * WAVE]
    tokens = TokenService(world / "identity" / "principals.json", "lab-run-secret")
    results: dict[str, dict] = {}
    phases: dict[str, set[str]] = {"done_before_publish": set(), "r2_window": set(), "after_rollback": set()}
    state = {"published": False, "rolled_back": False}
    async with HubGateway(world, released_hub_ids(DEFAULT_HUBS_CONFIG), tokens) as gateway:
        sut = ProcessSUT(["--config", "C4", "--memory-seed", str(seed)])
        async with sut.open(gateway, world):
            # tokens are issued before the SUT window so issuance is never attributed to a SUT call
            contexts = {gold.case_id: tokens.issue_caller_token(gold.principal) for gold in golds}
            completed = {"count": 0}
            progress = anyio.Event(), anyio.Event()

            async def one(gold, launched_after_publish: bool):
                request = public_request(gold)
                token = contexts[gold.case_id]
                try:
                    response, receipt = await sut.retrieve(
                        request, SUTContext(caller_token=token, gateway=gateway.handle(request.request_id, token)))
                    results[gold.case_id] = {"response": response, "receipt": receipt}
                except Exception as error:          # recorded, then asserted: nothing may fail
                    results[gold.case_id] = {"error": repr(error)}
                if not state["published"]:
                    phases["done_before_publish"].add(gold.case_id)
                elif launched_after_publish and not state["rolled_back"]:
                    phases["r2_window"].add(gold.case_id)    # started and finished while r2 was ACTIVE
                completed["count"] += 1
                if completed["count"] >= WAVE // 2:
                    progress[0].set()
                if completed["count"] >= WAVE + WAVE // 2:
                    progress[1].set()

            # The SUT pins ACTIVE when it starts a request, which the runner cannot see; so each
            # switch waits for completions, and overlapping waves keep requests in flight across it.
            with gateway.sut_call("fx23-load"):
                async with anyio.create_task_group() as group:
                    for gold in golds[:WAVE]:
                        group.start_soon(one, gold, False)
                    await progress[0].wait()
                    _activate(seed, "r2")                                   # publish mid-run
                    state["published"] = True
                    for gold in golds[WAVE: 2 * WAVE]:
                        group.start_soon(one, gold, True)
                    await progress[1].wait()
                    _activate(seed, "r1")                                   # roll back mid-run
                    state["rolled_back"] = True
                    for gold in golds[2 * WAVE:]:
                        phases["after_rollback"].add(gold.case_id)
                        group.start_soon(one, gold, True)
            traces = {gold.case_id: gateway.trace(gold.request.request_id) for gold in golds}
            anomalies = gateway.anomalies() + sut.anomalies()
    return golds, results, traces, anomalies, phases


@pytest.fixture(scope="module")
def load_run(scenario_world, tmp_path_factory):
    seed = _seed_with_r2(tmp_path_factory.mktemp("fx23-seed"))
    return anyio.run(_load, scenario_world, seed)


def test_no_errors_no_drops_no_anomalies(load_run):
    golds, results, _, anomalies, _ = load_run
    assert set(results) == {gold.case_id for gold in golds}
    assert [case for case, row in results.items() if "error" in row] == []
    assert anomalies == []


def test_every_request_pins_exactly_one_release(load_run):
    _, results, _, _, phases = load_run
    pinned, refs_seen = {}, 0
    for case_id, row in results.items():
        response_release, receipt_release = row["response"].memory_release_id, row["receipt"].memory_release_id
        assert response_release == receipt_release, case_id      # no request mixes releases
        assert response_release in ("r1", "r2"), case_id
        # every identity assertion used carries its release (fd91f01): none from the other release
        refs = [ref for resolution in row["receipt"].resolutions for ref in resolution.assertion_refs]
        assert all(ref.endswith(f"@{response_release}") for ref in refs), (case_id, refs)
        refs_seen += len(refs)
        assert "memory_pinned" in row["receipt"].timings_ms, case_id
        pinned[case_id] = response_release
    assert refs_seen > 0
    assert phases["done_before_publish"] and {pinned[c] for c in phases["done_before_publish"]} == {"r1"}
    assert phases["r2_window"] and {pinned[c] for c in phases["r2_window"]} == {"r2"}
    assert {pinned[c] for c in phases["after_rollback"]} == {"r1"}   # new requests use the restored release


def test_traces_are_complete(load_run):
    golds, results, traces, _, _ = load_run
    for gold in golds:
        receipt, trace = results[gold.case_id]["receipt"], traces[gold.case_id]
        assert receipt.complete, gold.case_id
        assert {call.source_id for call in receipt.calls} == trace.sources_attempted(), gold.case_id
        assert len(receipt.calls) == len(trace.calls), gold.case_id
        assert all(call.outcome in ("ok", "denied") and call.audience_valid for call in trace.calls), gold.case_id

