"""Hub conformance suite (lab plan §6.3, plan M2 task 4), over the in-memory MCP transport and
parametrized over all 5 hubs. Tests may read the build's private index (canaries, artifact
map); hubs never can."""
import json
import re
from dataclasses import dataclass
from pathlib import Path

import anyio
import pytest

from sanctum_contracts import HubCapabilities
from sanctum_hubs.access import readable
from sanctum_hubs.admin import AdminClient
from sanctum_hubs.change_feed import ChangeFeed
from sanctum_hubs.corpus import HUB_IDS, HubStore
from sanctum_hubs.failure import load_failure_injector
from sanctum_hubs.index import HubIndex
from sanctum_hubs.interfaces import FailureOutcome, NoFailures, TokenClaims

ROOT = Path(__file__).resolve().parents[2]
FAILURE_PROFILES = ROOT / "configs" / "failure_profiles.yaml"
PRINCIPALS = ("kestrel-payments", "kestrel-identity", "admin-probe")
WORD = re.compile(r"[^\W_]+")
DENIED_CODE = "denied_or_not_found"


@dataclass(frozen=True)
class HubTools:
    search: str
    get: str
    get_key: str                 # argument name of the get tool
    get_by: str                  # row attribute passed to the get tool: "path" or "artifact_id"
    version_argument: str | None # version argument of the get tool
    listing: str | None
    list_attribute: str | None   # row attribute a listing returns

    def get_arguments(self, row) -> dict:
        return {self.get_key: getattr(row, self.get_by)}


TOOLS = {
    "codehub": HubTools("search_code", "get_file", "path", "path", "ref", "list_repos", "location"),
    "skillhub": HubTools("search_skills", "get_skill", "path", "path", "version", "list_tree", "path"),
    "dochub": HubTools("search", "get_page", "page_id", "artifact_id", "version", "list_spaces", "location"),
    "memoryhub": HubTools("search_sessions", "get_session", "id", "artifact_id", "version", None, None),
    "incidenthub": HubTools("search_incidents", "get_incident", "id", "artifact_id", "version", None, None),
}

# Another hub's distinctive native names, by the service they denote (world.yaml hubs).
FOREIGN_NAMES = {
    "PA-svc": ("memoryhub", "svc.payment-auth"),
    "idauth": ("memoryhub", "svc.identity-auth"),
    "fxq": ("memoryhub", "svc.fx-quote"),
    "ledgerd": ("memoryhub", "svc.ledger-post"),
    "edgegw": ("memoryhub", "svc.gateway-edge"),
    "Auth Service": ("skillhub", None),        # homonym: payment-auth and identity-auth
    "FX Quote": ("skillhub", "svc.fx-quote"),
    "Ledger Posting": ("skillhub", "svc.ledger-post"),
    "Edge Gateway": ("skillhub", "svc.gateway-edge"),
    "space:PA": ("dochub", "svc.payment-auth"),
    "space:IDN": ("dochub", "svc.identity-auth"),
    "space:LEDGER": ("dochub", "svc.ledger-post"),
    "repo:payments/payment-auth": ("codehub", "svc.payment-auth"),
    "repo:identity/auth": ("codehub", "svc.identity-auth"),
}
BROAD_QUERIES = ("retry timeout", "checklist config", "incident follow up", "session note", "auth")


def run(coroutine_function):
    return anyio.run(coroutine_function)


@pytest.fixture(scope="module")
def private_index(hub_build):
    private = hub_build / "private"
    return {
        "canaries": json.loads((private / "canaries.json").read_text()),
        "artifact_map": json.loads((private / "artifact_map.json").read_text()),
    }


@pytest.fixture(scope="module")
def stores(hub_build):
    return {hub_id: HubStore.load(hub_build / "hubs" / hub_id) for hub_id in HUB_IDS}


def claims_for(token_service, principal: str) -> TokenClaims:
    return TokenClaims(principal, token_service.groups_of(principal), "test", 0, "test")


def tokens_of(row) -> set[str]:
    text = " ".join(part for part in (row.title, row.text, row.location, row.path) if part)
    return {token.lower() for token in WORD.findall(text)}


def query_tokens(query: str) -> set[str]:
    return {token.lower() for token in WORD.findall(query)}


# ---- capabilities -----------------------------------------------------------------------------
@pytest.mark.parametrize("hub_id", HUB_IDS)
def test_capabilities_contract_validates(hub_build, hub_id):
    document = json.loads((hub_build / "hubs" / hub_id / "capabilities.json").read_text())
    contract = HubCapabilities.model_validate(document["contract"])
    assert contract.hub_id == hub_id
    assert contract.error_semantics == "timeout_distinct_from_empty"
    assert set(document) == {"contract", "place_version_reads"}


# ---- scope isolation and restricted absence ---------------------------------------------------
@pytest.mark.parametrize("hub_id", HUB_IDS)
@pytest.mark.parametrize("principal", PRINCIPALS)
def test_every_result_is_readable_by_its_principal(open_hub, stores, token_service, hub_id, principal):
    store = stores[hub_id]
    claims = claims_for(token_service, principal)
    scoped = store.contract.principal_scoped
    tools = TOOLS[hub_id]

    async def scenario():
        async with open_hub(hub_id, principal, store=store) as client:
            for query in BROAD_QUERIES:
                found = await client.call(tools.search, query=query, top_k=store.contract.max_results)
                for hit in found["results"]:
                    row = store.at_version(hit["artifact_id"], hit["version"])
                    assert readable(row, claims, scoped), (hub_id, principal, hit["artifact_id"])
            if tools.listing:
                listed = set((await client.call(tools.listing))["items"])
                readable_values = {getattr(row, tools.list_attribute) for row in store.current_rows()
                                   if readable(row, claims, scoped)}
                assert listed == readable_values
    run(scenario)


@pytest.mark.parametrize("hub_id", HUB_IDS)
def test_payments_and_identity_scopes_differ(open_hub, stores, token_service, hub_id):
    """An item readable only by identity is invisible to payments in search, get and lists."""
    store = stores[hub_id]
    payments = claims_for(token_service, "kestrel-payments")
    identity = claims_for(token_service, "kestrel-identity")
    scoped = store.contract.principal_scoped
    identity_only = next(row for row in store.current_rows()
                         if readable(row, identity, scoped) and not readable(row, payments, scoped))
    tools = TOOLS[hub_id]

    async def scenario():
        async with open_hub(hub_id, "kestrel-identity", store=store) as client:
            got = await client.call(tools.get, **tools.get_arguments(identity_only))
            assert got["artifact"]["artifact_id"] == identity_only.artifact_id
        async with open_hub(hub_id, "kestrel-payments", store=store) as client:
            got = await client.call(tools.get, **tools.get_arguments(identity_only))
            assert got["error"]["code"] == DENIED_CODE
            found = await client.call(tools.search, query=identity_only.title,
                                      top_k=store.contract.max_results)
            assert identity_only.artifact_id not in {hit["artifact_id"] for hit in found["results"]}
    run(scenario)


@pytest.mark.parametrize("hub_id", HUB_IDS)
def test_restricted_get_body_equals_unknown_id_body(open_hub, stores, token_service, hub_id):
    store = stores[hub_id]
    payments = claims_for(token_service, "kestrel-payments")
    hidden = next(row for row in store.current_rows()
                  if not readable(row, payments, store.contract.principal_scoped))
    tools = TOOLS[hub_id]
    unknown = {tools.get_key: "art-0000000000" if tools.get_by == "artifact_id" else "no/such/path.md"}

    async def scenario():
        async with open_hub(hub_id, "kestrel-payments", store=store) as client:
            restricted_body = await client.call(tools.get, **tools.get_arguments(hidden))
            unknown_body = await client.call(tools.get, **unknown)
            assert restricted_body == unknown_body
            assert restricted_body["error"]["code"] == DENIED_CODE
            if tools.version_argument and store.contract.version_reads:
                versioned = await client.call(tools.get, **tools.get_arguments(hidden),
                                              **{tools.version_argument: hidden.version})
                assert versioned == unknown_body
    run(scenario)


@pytest.mark.parametrize("hub_id", HUB_IDS)
def test_counts_exclude_unreadable_rows(open_hub, stores, token_service, hub_id):
    """`total_matches` for a principal equals the admin count minus matching rows it cannot read."""
    store = stores[hub_id]
    payments = claims_for(token_service, "kestrel-payments")
    scoped = store.contract.principal_scoped
    hidden = next(row for row in store.current_rows() if not readable(row, payments, scoped))
    query = hidden.title
    tools = TOOLS[hub_id]

    async def scenario():
        async with open_hub(hub_id, "kestrel-payments", store=store) as client:
            found = await client.call(tools.search, query=query, top_k=store.contract.max_results)
        wanted = query_tokens(query)
        expected = sum(1 for row in store.current_rows()
                       if readable(row, payments, scoped) and tokens_of(row) & wanted)
        assert found["total_matches"] == expected
    run(scenario)


def test_canaries_never_reach_principals_without_restricted_group(open_hub, stores, token_service,
                                                                   private_index):
    canaries = private_index["canaries"]
    assert canaries
    unprivileged = [principal for principal in token_service.principals
                    if "restricted-incidents" not in token_service.groups_of(principal)]

    async def scenario():
        for hub_id in HUB_IDS:
            tools = TOOLS[hub_id]
            for principal in unprivileged:
                async with open_hub(hub_id, principal, store=stores[hub_id]) as client:
                    for canary in canaries:
                        found = await client.call(tools.search, query=canary["token"], top_k=25)
                        assert canary["token"] not in json.dumps(found)
                        assert canary["artifact_id"] not in json.dumps(found)
                        if canary["hub"] == hub_id:
                            row = stores[hub_id].current(canary["artifact_id"])
                            got = await client.call(tools.get, **tools.get_arguments(row))
                            assert got["error"]["code"] == DENIED_CODE
                    if tools.listing:
                        listed = json.dumps(await client.call(tools.listing))
                        assert not any(canary["place"] in listed for canary in canaries
                                       if canary["hub"] == hub_id)
        async with open_hub("dochub", "admin-probe", store=stores["dochub"]) as client:
            found = await client.call("search", query=canaries[0]["token"], top_k=5)
            assert canaries[0]["artifact_id"] in {hit["artifact_id"] for hit in found["results"]}
    run(scenario)


# ---- versions ---------------------------------------------------------------------------------
@pytest.mark.parametrize("hub_id", HUB_IDS)
def test_version_reads_as_declared(open_hub, stores, hub_id):
    store = stores[hub_id]
    tools = TOOLS[hub_id]
    multi = [artifact_id for artifact_id in store.artifact_ids()
             if len(store.versions_of(artifact_id)) > 1 and store.current(artifact_id)
             and store.capabilities.version_reads_for(store.current(artifact_id).location)]
    single_only = [row for row in store.current_rows()
                   if not store.capabilities.version_reads_for(row.location)]

    async def scenario():
        principal = "kestrel-both" if store.contract.principal_scoped else "admin-probe"
        async with open_hub(hub_id, principal, store=store) as client:
            if multi:
                artifact_id = multi[0]
                oldest = store.versions_of(artifact_id)[0]
                current = store.current(artifact_id)
                got = await client.call(tools.get, **tools.get_arguments(current),
                                        **{tools.version_argument: oldest.version})
                assert got["artifact"]["version"] == oldest.version
                assert got["artifact"]["text"] == oldest.text
                default = await client.call(tools.get, **tools.get_arguments(current))
                assert default["artifact"]["version"] == current.version
                missing = await client.call(tools.get, **tools.get_arguments(current),
                                            **{tools.version_argument: "no-such-version"})
                assert missing["error"]["code"] == DENIED_CODE
            owned = [row for row in single_only if row.owner in (None, principal)]
            if owned:
                refused = await client.call(tools.get, **tools.get_arguments(owned[0]),
                                            **{tools.version_argument: owned[0].version})
                assert refused["error"]["code"] == "capability_unsupported"
    assert multi or single_only
    if hub_id in ("dochub", "memoryhub", "incidenthub"):
        assert single_only, "hub must have places without version reads"
    if hub_id in ("codehub", "skillhub"):
        assert multi and not single_only
    run(scenario)


def test_codehub_ref_filter_searches_that_version(open_hub, stores):
    store = stores["codehub"]

    async def scenario():
        async with open_hub("codehub", "admin-probe", store=store) as client:
            found = await client.call("search_code", query="RetryConfig", ref="R40", top_k=25)
            assert found["results"] and {hit["version"] for hit in found["results"]} == {"R40"}
            experiment = await client.call("search_code", query="config", ref="exp-branch", top_k=25)
            assert {hit["environment"] for hit in experiment["results"]} == {"experiment"}
            current = await client.call("search_code", query="config", top_k=25)
            assert "experiment" not in {hit["environment"] for hit in current["results"]}
    run(scenario)


# ---- honest search ----------------------------------------------------------------------------
@pytest.mark.parametrize("hub_id", HUB_IDS)
def test_every_hit_contains_a_query_token(open_hub, stores, hub_id):
    """No synonym expansion: each hit for another hub's native name contains a query token in
    its own title, text, location or path; a core artifact of the denoted service is returned
    only through such a lexical match."""
    store = stores[hub_id]
    principal = "kestrel-both" if store.contract.principal_scoped else "admin-probe"

    async def scenario():
        async with open_hub(hub_id, principal, store=store) as client:
            for name, (owner_hub, _service) in FOREIGN_NAMES.items():
                if owner_hub == hub_id:
                    continue
                found = await client.call(TOOLS[hub_id].search, query=name, top_k=25)
                for hit in found["results"]:
                    row = store.at_version(hit["artifact_id"], hit["version"])
                    assert tokens_of(row) & query_tokens(name), (hub_id, name, hit["artifact_id"])
    run(scenario)


def without_own_place(row) -> str:
    """Title, text and path with the row's own place name removed (both `space:LEDGER` and
    `LEDGER`, `repo:payments/fx-quote` and `payments/fx-quote`)."""
    text = " \n ".join(part for part in (row.title, row.text, row.path) if part)
    if row.location:
        for native in sorted({row.location, row.location.split(":", 1)[-1]}, key=len, reverse=True):
            text = text.replace(native, " | ")
    return text


@pytest.mark.parametrize("hub_id", HUB_IDS)
def test_foreign_alias_phrase_never_matches(stores, hub_id):
    """Honest miss, crisp form: the full alias as an FTS phrase (all tokens adjacent) matches
    no row of a hub that does not declare that name, except where the adjacency is produced by
    the row's own place name (CodeHub repo `payments/fx-quote` tokenizes to "fx quote";
    DocHub `space:LEDGER / Posting replay runbook` to "ledger posting"). Such phrase hits must
    vanish once the row's own place name is removed.

    Search itself stays OR-joined for recall, so single-token lexical noise is expected and
    allowed: "PA-svc" in CodeHub hits the `com/kestrel/pa/` package path, and "Auth Service"
    in MemoryHub hits filler text mentioning the "service catalog". Neither is synonym
    expansion (see test_every_hit_contains_a_query_token)."""
    store = stores[hub_id]
    connection = HubIndex(store).connection()
    rows = store.rows()
    for name, (owner_hub, _service) in FOREIGN_NAMES.items():
        if owner_hub == hub_id:
            continue
        tokens = WORD.findall(name)
        phrase_pattern = re.compile(r"(?<![^\W_])" + r"[\W_]+".join(map(re.escape, tokens)) + r"(?![^\W_])",
                                    re.IGNORECASE)
        hits = connection.execute("SELECT rowid FROM documents WHERE documents MATCH ?",
                                  ('"' + " ".join(tokens) + '"',)).fetchall()
        for (row_number,) in hits:
            row = rows[row_number - 1]
            assert not phrase_pattern.search(without_own_place(row)), (hub_id, name, row.artifact_id)
    assert rows


def test_foreign_alias_misses_in_skillhub(open_hub, stores, private_index):
    about = {entry["artifact_id"]: entry["about"] for entry in private_index["artifact_map"].values()}

    async def scenario():
        async with open_hub("skillhub", "admin-probe", store=stores["skillhub"]) as client:
            found = await client.call("search_skills", query="PA-svc", top_k=25)
            assert not [hit for hit in found["results"]
                        if "svc.payment-auth" in about.get(hit["artifact_id"], [])]
    run(scenario)


# ---- determinism ------------------------------------------------------------------------------
@pytest.mark.parametrize("hub_id", HUB_IDS)
def test_same_query_same_ordered_results(open_hub, stores, hub_build, hub_id):
    store = stores[hub_id]
    principal = "kestrel-both" if store.contract.principal_scoped else "admin-probe"

    async def scenario():
        async with open_hub(hub_id, principal, store=store) as client:
            first = [await client.call(TOOLS[hub_id].search, query=query, top_k=25) for query in BROAD_QUERIES]
        async with open_hub(hub_id, principal, store=HubStore.load(hub_build / "hubs" / hub_id)) as client:
            second = [await client.call(TOOLS[hub_id].search, query=query, top_k=25) for query in BROAD_QUERIES]
        assert first == second
        assert any(result["results"] for result in first)
    run(scenario)


# ---- failure knobs ----------------------------------------------------------------------------
@pytest.mark.parametrize("hub_id", HUB_IDS)
def test_flaky_profile_outcomes_match_seeded_draws(open_hub, stores, hub_id):
    store = stores[hub_id]
    tools = TOOLS[hub_id]
    injector = load_failure_injector(FAILURE_PROFILES, "flaky", run_seed=7, time_scale=0)
    principal = "kestrel-both" if store.contract.principal_scoped else "admin-probe"
    calls = 120
    query = "retry timeout config session incident degraded"

    async def scenario():
        observed = []
        async with open_hub(hub_id, principal, failures=injector, store=store) as client:
            for call_index in range(calls):
                observed.append(await client.call(tools.search, query=query,
                                                  top_k=10, request_id="conformance"))
        return observed

    observed = anyio.run(scenario)
    seen = set()
    for call_index, payload in enumerate(observed):
        draw = injector.draw("conformance", hub_id, tools.search, call_index)
        seen.add(draw.outcome)
        if draw.outcome is FailureOutcome.TIMEOUT:
            assert payload["error"]["code"] == "timeout"
        elif draw.outcome is FailureOutcome.ERROR:
            assert payload["error"]["code"] == "upstream_error"
        elif draw.outcome is FailureOutcome.PARTIAL:
            assert payload["partial"] is True and "results" in payload
        else:
            assert payload["partial"] is False and payload["results"]
    assert seen == set(FailureOutcome)


@pytest.mark.parametrize("hub_id", HUB_IDS)
def test_none_profile_never_fails(open_hub, stores, hub_id):
    store = stores[hub_id]
    injector = load_failure_injector(FAILURE_PROFILES, "none", run_seed=7, time_scale=0)
    principal = "kestrel-both" if store.contract.principal_scoped else "admin-probe"

    async def scenario():
        async with open_hub(hub_id, principal, failures=injector, store=store) as client:
            for _ in range(30):
                payload = await client.call(TOOLS[hub_id].search, query="retry timeout", top_k=10,
                                            request_id="none")
                assert "error" not in payload and payload["partial"] is False
    run(scenario)
    assert isinstance(NoFailures().draw("r", hub_id, "t", 0).outcome, FailureOutcome)


# ---- admin mutations through the live index and server ----------------------------------------
ADMIN_SECRET = "conformance-admin-secret"


def fresh_stores(hub_build) -> dict[str, HubStore]:
    return {hub_id: HubStore.load(hub_build / "hubs" / hub_id) for hub_id in HUB_IDS}


def test_admin_unshare_hides_place_from_next_search_list_count(open_hub, hub_build, token_service, tmp_path):
    live = fresh_stores(hub_build)
    admin = AdminClient(ADMIN_SECRET, ADMIN_SECRET, live, token_service, tmp_path / "feed.jsonl")
    store = live["dochub"]
    page = next(row for row in store.current_rows() if row.location == "space:LEDGER")

    async def scenario():
        async with open_hub("dochub", "kestrel-payments", store=store) as client:
            before = await client.call("search", query=page.title, top_k=25)
            assert page.artifact_id in {hit["artifact_id"] for hit in before["results"]}
            admin.unshare_place("dochub", "space:LEDGER", ["restricted-incidents"])
            after = await client.call("search", query=page.title, top_k=25)
            assert page.artifact_id not in {hit["artifact_id"] for hit in after["results"]}
            ledger_rows = sum(1 for row in store.current_rows() if row.location == "space:LEDGER"
                              and set(tokens_of(row)) & query_tokens(page.title))
            assert after["total_matches"] == before["total_matches"] - ledger_rows
            assert "space:LEDGER" not in (await client.call("list_spaces"))["items"]
            assert (await client.call("get_page", page_id=page.artifact_id))["error"]["code"] == DENIED_CODE
    run(scenario)
    assert [event.kind for event in ChangeFeed(tmp_path / "feed.jsonl")] == ["place_unshared"]


def test_admin_rename_and_publish_visible_on_next_call(open_hub, hub_build, token_service, tmp_path):
    live = fresh_stores(hub_build)
    admin = AdminClient(ADMIN_SECRET, ADMIN_SECRET, live, token_service, tmp_path / "feed.jsonl")
    skill = next(row for row in live["skillhub"].current_rows() if row.location == "skills/payments/")
    code = next(row for row in live["codehub"].current_rows() if row.location == "repo:payments/payment-auth")
    marker = "zanzibarquokka"

    async def scenario():
        async with open_hub("skillhub", "kestrel-payments", store=live["skillhub"]) as client:
            admin.rename_path("skillhub", skill.artifact_id, "skills/payments/renamed-skill.md")
            moved = await client.call("get_skill", path="skills/payments/renamed-skill.md")
            assert moved["artifact"]["artifact_id"] == skill.artifact_id
            assert (await client.call("get_skill", path=skill.path))["error"]["code"] == DENIED_CODE
            assert "skills/payments/renamed-skill.md" in (await client.call("list_tree"))["items"]
        async with open_hub("codehub", "kestrel-payments", store=live["codehub"]) as client:
            assert (await client.call("search_code", query=marker))["total_matches"] == 0
            admin.publish_version("codehub", code.artifact_id, "R99", f"// {marker}\n", environment="prod")
            found = await client.call("search_code", query=marker)
            assert found["total_matches"] == 1 and found["results"][0]["version"] == "R99"
            current = await client.call("get_file", path=code.path)
            assert current["artifact"]["version"] == "R99"
            older = await client.call("get_file", path=code.path, ref=code.version)
            assert older["artifact"]["text"] == code.text
    run(scenario)
    kinds = [event.kind for event in ChangeFeed(tmp_path / "feed.jsonl")]
    assert kinds == ["path_renamed", "version_published"]


def test_admin_revoke_denies_existing_hub_token_on_next_call(open_hub, hub_build, token_service, tmp_path):
    live = fresh_stores(hub_build)
    admin = AdminClient(ADMIN_SECRET, ADMIN_SECRET, live, token_service, tmp_path / "feed.jsonl")

    async def scenario():
        async with open_hub("codehub", "kestrel-payments", store=live["codehub"]) as client:
            assert (await client.call("list_repos"))["items"]
            admin.revoke_principal("kestrel-payments")
            assert (await client.call("list_repos"))["error"]["code"] == DENIED_CODE
    run(scenario)
