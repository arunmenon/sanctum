"""Hub core behaviour over in-memory MCP (plan M2 task 2). Full cross-hub conformance is in
test_conformance.py."""
import time

import anyio
import pytest

from sanctum_hubs.corpus import CorpusPathRefused, HubStore
from sanctum_hubs.index import match_expression
from sanctum_hubs.interfaces import HubError
from sanctum_hubs.servers import HUB_TOOLS

DENIED = {"error": {"code": "denied_or_not_found", "message": "not found or access denied"}}


def run(coroutine_function):
    return anyio.run(coroutine_function)


def test_loader_refuses_non_hub_paths(hub_build, tmp_path):
    for bad in (hub_build / "private", hub_build, hub_build / "hubs",
                hub_build / "private" / "hubs" / "codehub"):
        with pytest.raises(CorpusPathRefused):
            HubStore.load(bad)
    (tmp_path / "manifest.json").write_text("{}")
    sneaky = tmp_path / "private" / "hubs" / "codehub"
    sneaky.mkdir(parents=True)
    for name in ("artifacts.jsonl", "capabilities.json"):
        (sneaky / name).write_text((hub_build / "hubs" / "codehub" / name).read_text())
    with pytest.raises(CorpusPathRefused):
        HubStore.load(sneaky)


def test_query_text_cannot_inject_fts_syntax():
    assert match_expression('auth" OR NEAR(x*') == '"auth" OR "or" OR "near" OR "x"'
    with pytest.raises(HubError):
        match_expression('" * ()')


@pytest.mark.parametrize("hub_id", sorted(HUB_TOOLS))
def test_server_exposes_exactly_the_plan_tools(open_hub, hub_id):
    async def scenario():
        async with open_hub(hub_id, "admin-probe") as client:
            tools = await client.session.list_tools()
            assert sorted(tool.name for tool in tools.tools) == sorted(HUB_TOOLS[hub_id])
    run(scenario)


def test_search_and_get_as_payments(open_hub):
    async def scenario():
        async with open_hub("codehub", "kestrel-payments") as client:
            found = await client.call("search_code", query="RetryConfig", top_k=5)
            assert found["partial"] is False and found["results"]
            top = found["results"][0]
            assert set(top) == {"artifact_id", "title", "location", "path", "version", "environment",
                                "snippet", "score"}
            fetched = await client.call("get_file", path=top["path"])
            assert fetched["artifact"]["artifact_id"] == top["artifact_id"]
            assert fetched["artifact"]["versions"]
            again = await client.call("search_code", query="RetryConfig", top_k=5)
            assert again == found
    run(scenario)


def test_missing_and_passthrough_tokens_are_denied(open_hub, token_service):
    async def scenario():
        async with open_hub("dochub", "kestrel-payments") as client:
            assert await client.call("list_spaces", token=None) == DENIED
            caller = token_service.issue_caller_token("kestrel-payments")
            assert await client.call("list_spaces", token=caller) == DENIED
            other_hub = token_service.exchange(caller, "codehub")
            assert await client.call("list_spaces", token=other_hub) == DENIED
    run(scenario)


def test_restricted_page_indistinguishable_from_unknown(open_hub, hub_build):
    store = HubStore.load(hub_build / "hubs" / "dochub")
    restricted = [row for row in store.current_rows() if "restricted-incidents" in row.acl]
    assert restricted

    async def scenario():
        async with open_hub("dochub", "kestrel-both") as client:
            assert await client.call("get_page", page_id=restricted[0].artifact_id) == DENIED
            assert await client.call("get_page", page_id="art-does-not-exist") == DENIED
            spaces = await client.call("list_spaces")
            assert restricted[0].location not in spaces["items"]
            hits = await client.call("search", query=restricted[0].title, top_k=25)
            assert restricted[0].artifact_id not in {hit["artifact_id"] for hit in hits["results"]}
        async with open_hub("dochub", "admin-probe") as client:
            page = await client.call("get_page", page_id=restricted[0].artifact_id)
            assert page["artifact"]["artifact_id"] == restricted[0].artifact_id
    run(scenario)


def test_version_reads_as_declared(open_hub, hub_build):
    docs = HubStore.load(hub_build / "hubs" / "dochub")
    pa_page = next(row for row in docs.current_rows() if row.location == "space:PA")

    async def scenario():
        async with open_hub("dochub", "kestrel-payments") as client:
            refused = await client.call("get_page", page_id=pa_page.artifact_id, version="v1")
            assert refused["error"]["code"] == "capability_unsupported"
        async with open_hub("memoryhub", "kestrel-payments") as client:
            refused = await client.call("get_session", id="anything", version="v1")
            assert refused["error"]["code"] == "capability_unsupported"
    run(scenario)


def test_memoryhub_is_scoped_to_token_subject(open_hub, hub_build):
    store = HubStore.load(hub_build / "hubs" / "memoryhub")
    others = [row for row in store.current_rows() if row.owner == "kestrel-identity"]

    async def scenario():
        async with open_hub("memoryhub", "kestrel-payments") as client:
            assert await client.call("get_session", id=others[0].artifact_id) == DENIED
            hits = await client.call("search_sessions", query=others[0].title, top_k=25)
            owners = {store.current(hit["artifact_id"]).owner for hit in hits["results"]}
            assert owners <= {"kestrel-payments"}
    run(scenario)


def test_top_k_bounds_and_capped_counts(open_hub):
    async def scenario():
        async with open_hub("skillhub", "kestrel-payments") as client:
            too_many = await client.call("search_skills", query="checklist", top_k=1000)
            assert too_many["error"]["code"] == "invalid_argument"
            result = await client.call("search_skills", query="checklist", top_k=3)
            assert len(result["results"]) == 3 and result["total_matches"] >= 3
            scoped = await client.call("search_skills", query="checklist", path_prefix="skills/identity/")
            assert scoped["results"] == [] and scoped["total_matches"] == 0
    run(scenario)


def test_query_size_is_bounded_and_fast(open_hub):
    assert match_expression("Auth auth AUTH service") == '"auth" OR "service"'
    with pytest.raises(HubError):
        match_expression(" ".join(f"w{number}" for number in range(65)))
    with pytest.raises(HubError):
        match_expression("payments " * 1000)

    async def scenario():
        async with open_hub("codehub", "admin-probe") as client:
            started = time.monotonic()
            repeated = await client.call("search_code", query="payments " * 400, top_k=5)
            widest = await client.call("search_code", query=" ".join(f"w{n} retry" for n in range(63)), top_k=5)
            assert time.monotonic() - started < 5.0
            assert repeated["results"] and "results" in widest
            too_long = await client.call("search_code", query="payments " * 1000)
            assert too_long["error"]["code"] == "invalid_argument"
    run(scenario)
