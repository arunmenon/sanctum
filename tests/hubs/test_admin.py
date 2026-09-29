"""Admin API and change feed (plan M2 decision 8)."""
import json
import random
from pathlib import Path

import pytest

from sanctum_hubs.admin import AdminClient, AdminDenied
from dataclasses import fields

from sanctum_hubs.change_feed import ChangeFeed, ChangeKind, ReaderEvent
from sanctum_hubs.corpus import HubStore
from sanctum_hubs.interfaces import TokenRejected
from sanctum_hubs.tokens import TokenService

WORLD = Path(__file__).resolve().parents[2] / "build" / "world"
ADMIN_SECRET = "lab-admin-secret"
pytestmark = pytest.mark.skipif(not (WORLD / "hubs").is_dir(), reason="world not built")


def visible_rows(store: HubStore, groups: set[str], needle: str):
    """What an ACL-filtered search over current rows would return (index.py applies the same filter)."""
    return [row for row in store.current_rows() if groups & set(row.acl)
            and (needle in row.text or needle in (row.path or ""))]


@pytest.fixture
def stores():
    return {hub: HubStore.load(WORLD / "hubs" / hub) for hub in ("codehub", "dochub", "memoryhub")}


@pytest.fixture
def token_service():
    return TokenService(WORLD / "identity" / "principals.json", "lab-token-secret")


@pytest.fixture
def feed_path(tmp_path):
    return tmp_path / "runs" / "run-1" / "change_feed.jsonl"


@pytest.fixture
def admin(stores, token_service, feed_path):
    return AdminClient(ADMIN_SECRET, ADMIN_SECRET, stores, token_service, feed_path)


def test_admin_requires_secret(stores, token_service, feed_path):
    with pytest.raises(AdminDenied):
        AdminClient("wrong", ADMIN_SECRET, stores, token_service, feed_path)
    with pytest.raises(AdminDenied):
        AdminClient("", "", stores, token_service, feed_path)


def test_rename_path_visible_to_next_search(admin, stores):
    store = stores["codehub"]
    row = next(row for row in store.current_rows() if row.path)
    new_path = "renamed/zz-admin-probe-path.yaml"
    admin.rename_path("codehub", row.artifact_id, new_path)
    hits = visible_rows(store, set(row.acl), "zz-admin-probe-path")
    assert [hit.artifact_id for hit in hits] == [row.artifact_id]
    assert store.ids_with_path(row.path) == [] or row.artifact_id not in store.ids_with_path(row.path)


def test_unshare_removes_from_results_and_counts(admin, stores):
    store = stores["dochub"]
    location = store.locations()[0]
    in_place = [row for row in store.current_rows() if row.location == location]
    groups = set(in_place[0].acl)
    before = {row.artifact_id for row in store.current_rows() if groups & set(row.acl)}
    admin.unshare_place("dochub", location, ["restricted-incidents"])
    after = {row.artifact_id for row in store.current_rows() if groups & set(row.acl)}
    assert not after & {row.artifact_id for row in in_place}
    assert len(after) == len(before - {row.artifact_id for row in in_place})


def test_change_owner_and_publish_version(admin, stores):
    memory = stores["memoryhub"]
    note = memory.current_rows()[0]
    admin.change_owner("memoryhub", note.artifact_id, "kestrel-identity")
    assert memory.current(note.artifact_id).owner == "kestrel-identity"

    code = stores["codehub"]
    target = next(row for row in code.current_rows() if code.capabilities.version_reads_for(row.location))
    new_row, event = admin.publish_version("codehub", target.artifact_id, "v-admin-9", "zz-published-body")
    assert new_row.revision == target.revision + 1
    assert code.current(target.artifact_id).text == "zz-published-body"
    assert visible_rows(code, set(target.acl), "zz-published-body")[0].artifact_id == target.artifact_id
    assert event.kind is ChangeKind.VERSION_PUBLISHED


def test_revoke_principal_immediate(admin, token_service):
    caller_token = token_service.issue_caller_token("kestrel-payments")
    hub_token = token_service.exchange(caller_token, "codehub")
    admin.revoke_principal("kestrel-payments")
    with pytest.raises(TokenRejected):
        token_service.verify(hub_token, "codehub")
    with pytest.raises(TokenRejected):
        token_service.exchange(caller_token, "codehub")


def test_feed_ordered_and_leak_free(admin, stores, feed_path):
    code = stores["codehub"]
    row = next(row for row in code.current_rows() if row.path)
    admin.rename_path("codehub", row.artifact_id, "renamed/one.yaml")
    admin.unshare_place("dochub", stores["dochub"].locations()[0], ["restricted-incidents"])
    admin.revoke_principal("kestrel-both")
    admin.publish_version("codehub", row.artifact_id, "v-admin-2", "secret body text zz-leak-canary")

    events = ChangeFeed(feed_path).events()
    assert [event.seq for event in events] == [1, 2, 3, 4]
    assert [event.kind for event in events] == [ChangeKind.PATH_RENAMED, ChangeKind.PLACE_UNSHARED,
                                                ChangeKind.PRINCIPAL_REVOKED, ChangeKind.VERSION_PUBLISHED]
    assert ChangeFeed(feed_path).events(after_seq=2)[0].seq == 3
    raw_lines = feed_path.read_text().splitlines()
    for line in raw_lines:
        assert set(json.loads(line)) == {"seq", "hub", "kind", "subject", "at_revision", "principal_scoped",
                                         "prior_access", "post_access"}
    raw = feed_path.read_text()
    # The raw feed is lab-internal and records prior ACLs, but never content.
    for leaked in ("zz-leak-canary", "renamed/one.yaml", row.title):
        assert leaked not in raw
    assert not hasattr(ChangeFeed(feed_path), "append")


def test_feed_resumes_sequence(stores, token_service, feed_path):
    first = AdminClient(ADMIN_SECRET, ADMIN_SECRET, stores, token_service, feed_path)
    first.revoke_principal("kestrel-both")
    second = AdminClient(ADMIN_SECRET, ADMIN_SECRET, stores, token_service, feed_path)
    assert second.revoke_principal("kestrel-identity").seq == 2


def _claims(token_service, principal):
    return token_service.verify(token_service.exchange(token_service.issue_caller_token(principal), "dochub"),
                                "dochub")


def test_reader_view_hides_restricted_subjects(admin, stores, token_service, feed_path):
    dochub = stores["dochub"]
    restricted = next(row for row in dochub.current_rows() if row.location == "space:Incidents")
    assert restricted.acl == ["restricted-incidents"]
    admin.unshare_place("dochub", "space:Incidents", ["restricted-incidents"])
    admin.publish_version("dochub", restricted.artifact_id, "v-admin-restricted", "restricted update")
    open_row = next(row for row in dochub.current_rows() if "payments-eng" in row.acl)
    admin.rename_path("dochub", open_row.artifact_id, "renamed/open.md")
    admin.revoke_principal("kestrel-both")

    feed = ChangeFeed(feed_path)
    assert len(feed.events()) == 4
    payments_view = feed.events_for(_claims(token_service, "kestrel-payments"), stores)
    assert [(event.kind, event.subject) for event in payments_view] == [
        (ChangeKind.PATH_RENAMED, open_row.artifact_id)]
    probe_view = feed.events_for(_claims(token_service, "admin-probe"), stores)
    assert {event.subject for event in probe_view} >= {"space:Incidents", restricted.artifact_id}
    assert "kestrel-both" not in {event.subject for event in probe_view}
    assert feed.events_for(_claims(token_service, "kestrel-payments"), stores, after_seq=1) == []
    assert {field.name for field in fields(ReaderEvent)} == {"reader_seq", "hub", "kind", "subject"}


def test_reader_positions_do_not_reveal_hidden_events(admin, stores, token_service, feed_path):
    dochub = stores["dochub"]
    readable_ids = [row.artifact_id for row in dochub.current_rows() if row.acl == ["payments-eng"]][:2]
    admin.rename_path("dochub", readable_ids[0], "renamed/first.md")
    admin.revoke_principal("kestrel-both")
    restricted = next(row for row in dochub.current_rows() if row.location == "space:Incidents")
    admin.publish_version("dochub", restricted.artifact_id, "v-hidden", "hidden update")
    admin.rename_path("dochub", readable_ids[1], "renamed/second.md")

    raw_seqs = [event.seq for event in ChangeFeed(feed_path).events()]
    assert raw_seqs == [1, 2, 3, 4]
    view = ChangeFeed(feed_path).events_for(_claims(token_service, "kestrel-payments"), stores)
    assert [event.reader_seq for event in view] == [1, 2]
    assert [event.subject for event in view] == readable_ids
    assert not any(hasattr(event, name) for event in view for name in ("seq", "at_revision"))
    resumed = ChangeFeed(feed_path).events_for(_claims(token_service, "kestrel-payments"), stores,
                                               after_seq=1)
    assert [(event.reader_seq, event.subject) for event in resumed] == [(2, readable_ids[1])]


def test_unshare_notifies_readers_who_lost_access(admin, stores, token_service, feed_path):
    dochub = stores["dochub"]
    ledger_rows = [row for row in dochub.current_rows() if row.location == "space:LEDGER"]
    assert ledger_rows and all("payments-eng" in row.acl for row in ledger_rows)
    admin.unshare_place("dochub", "space:LEDGER", ["restricted-incidents"])
    payments_claims = _claims(token_service, "kestrel-payments")
    assert not any("payments-eng" in row.acl
                   for row in dochub.current_rows() if row.location == "space:LEDGER")
    view = ChangeFeed(feed_path).events_for(payments_claims, stores)
    assert [(event.kind, event.subject) for event in view] == [(ChangeKind.PLACE_UNSHARED, "space:LEDGER")]
    identity_view = ChangeFeed(feed_path).events_for(_claims(token_service, "kestrel-identity"), stores)
    assert identity_view == []


def test_owner_change_notifies_former_owner(admin, stores, token_service, feed_path):
    memory = stores["memoryhub"]
    note = next(row for row in memory.current_rows() if row.owner == "kestrel-payments")
    admin.change_owner("memoryhub", note.artifact_id, "kestrel-identity")
    former_owner_claims = _claims(token_service, "kestrel-payments")
    view = ChangeFeed(feed_path).events_for(former_owner_claims, stores)
    assert [(event.kind, event.subject) for event in view] == [(ChangeKind.OWNER_CHANGED, note.artifact_id)]
    bystander_view = ChangeFeed(feed_path).events_for(_claims(token_service, "admin-probe"), stores)
    assert bystander_view == []


def test_reader_cursor_stable_across_ownership_round_trip(admin, stores, token_service, feed_path):
    """Codex repro: a note leaves and returns to its owner, then leaves again; the saved cursor
    must still deliver the second ownership-loss notice."""
    memory = stores["memoryhub"]
    note = next(row for row in memory.current_rows() if row.owner == "kestrel-payments")
    admin.change_owner("memoryhub", note.artifact_id, "kestrel-identity")
    admin.rename_path("memoryhub", note.artifact_id, "renamed/a")
    admin.rename_path("memoryhub", note.artifact_id, "renamed/b")
    admin.change_owner("memoryhub", note.artifact_id, "kestrel-payments")
    feed = ChangeFeed(feed_path)
    owner_claims = _claims(token_service, "kestrel-payments")
    before = feed.events_for(owner_claims, stores)
    assert [event.kind for event in before] == [ChangeKind.OWNER_CHANGED, ChangeKind.OWNER_CHANGED]
    cursor = before[-1].reader_seq
    admin.change_owner("memoryhub", note.artifact_id, "kestrel-identity")
    after = feed.events_for(owner_claims, stores)
    assert after[:len(before)] == before
    assert [(event.reader_seq, event.kind) for event in feed.events_for(owner_claims, stores, after_seq=cursor)] \
        == [(cursor + 1, ChangeKind.OWNER_CHANGED)]


@pytest.mark.parametrize("seed", range(6))
def test_reader_views_are_append_only(admin, stores, token_service, feed_path, seed):
    """Property: for random mutation sequences, every reader's view at time t is a prefix of
    its view at any later time."""
    generator = random.Random(seed)
    principals = token_service.principals
    claims_by_principal = {principal: _claims(token_service, principal) for principal in principals}
    dochub, memory = stores["dochub"], stores["memoryhub"]
    doc_ids = generator.sample(dochub.artifact_ids(), 6)
    note_ids = generator.sample(memory.artifact_ids(), 6)
    locations = dochub.locations()
    groups = ["payments-eng", "identity-eng", "platform-eng", "restricted-incidents"]
    feed = ChangeFeed(feed_path)
    history = {principal: [] for principal in principals}
    revocable = [principal for principal in principals if principal != "admin-probe"]
    for step in range(30):
        action = generator.choice(["rename", "unshare", "owner", "publish", "revoke"])
        if action == "rename":
            admin.rename_path("dochub", generator.choice(doc_ids), f"renamed/{seed}-{step}")
        elif action == "unshare":
            admin.unshare_place("dochub", generator.choice(locations), generator.sample(groups, generator.randint(1, 2)))
        elif action == "owner":
            admin.change_owner("memoryhub", generator.choice(note_ids), generator.choice(principals))
        elif action == "publish":
            admin.publish_version("memoryhub", generator.choice(note_ids), f"v{seed}-{step}", f"body {step}")
        elif revocable:
            admin.revoke_principal(revocable.pop(generator.randrange(len(revocable))))
        for principal, claims in claims_by_principal.items():
            view = feed.events_for(claims, stores)
            assert view[:len(history[principal])] == history[principal], (principal, step)
            assert [event.reader_seq for event in view] == list(range(1, len(view) + 1))
            history[principal] = view
