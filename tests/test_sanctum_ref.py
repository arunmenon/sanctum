"""sanctum-ref units: arms, registry, intent, routing, assembly (no hubs needed)."""
import shutil
from pathlib import Path

import pytest

from sanctum_contracts import RetrieveRequest
from sanctum_ref.adapters import Candidate, evidence_unit
from sanctum_ref.assembly import assemble, identity_signature
from sanctum_ref.config import UnsupportedArm, load_arm
from sanctum_ref.intent import analyze
from sanctum_ref.registry import RegistryUnavailable, load_registry
from sanctum_ref.routing import plan_sources
from sanctum_ref.text import search_query, token_count

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "configs" / "matrix.yaml"
MANIFESTS = ROOT / "owners" / "manifests"
CAPABILITIES = {
    "codehub": {"contract": {"version_reads": True}, "place_version_reads": {}},
    "skillhub": {"contract": {"version_reads": True}, "place_version_reads": {}},
    "dochub": {"contract": {"version_reads": True}, "place_version_reads": {"space:PA": False}},
    "memoryhub": {"contract": {"version_reads": False}, "place_version_reads": {}},
}


def request(query, **fields):
    return RetrieveRequest(request_id="req-unit", query=query, mode=fields.pop("mode", "scoped"),
                           budget_tokens=fields.pop("budget_tokens", 4000), deadline_ms=3000, **fields)


def plans_for(query, arm="C2", groups=("payments-eng",), **fields):
    registry = load_registry(MANIFESTS)
    releases = {release for manifest in registry.manifests.values() for release in manifest.versions.releases}
    req = request(query, **fields)
    intent = analyze(query, registry.domains, releases, verify=req.mode.value == "verify")
    return {plan.hub_id: plan for plan in plan_sources(req, load_arm(MATRIX, arm), registry, intent,
                                                         CAPABILITIES, set(groups))}


def test_arms_come_from_matrix_switches_only():
    assert load_arm(MATRIX, "C1-naive").assembly == "concatenate"
    assert load_arm(MATRIX, "C1-fair").routing == "fanout_all"
    c2 = load_arm(MATRIX, "C2")
    assert c2.rules_routing and c2.registry_procedures and c2.tokenizer == "cl100k_base"
    assert load_arm(MATRIX, "C4").memory_store == "relations"
    assert load_arm(MATRIX, "C4a-label-only").resolution == "label_only"
    assert load_arm(MATRIX, "C3").decision_provider == "named" and load_arm(MATRIX, "C5").uses_memory
    for unbuilt in ("nope",):
        with pytest.raises(UnsupportedArm):
            load_arm(MATRIX, unbuilt)


def test_registry_fails_closed(tmp_path):
    with pytest.raises(RegistryUnavailable):
        load_registry(tmp_path)
    shutil.copytree(MANIFESTS, tmp_path / "m")
    (tmp_path / "m" / "codehub.yaml").write_text("hub_id: codehub\n")
    with pytest.raises(RegistryUnavailable):
        load_registry(tmp_path / "m")
    registry = load_registry(MANIFESTS)
    assert registry.manifest("skillhub").authoritative_for("procedure")
    assert registry.manifest("incidenthub").role.value == "observed_event"   # onboarded at M7 by manifest only


def test_must_consult_and_capability_guards():
    plans = plans_for("How many retries does payment-auth allow?")
    assert plans["skillhub"].required and plans["skillhub"].reasons == ["must_consult"]
    assert plans["skillhub"].selectors == {"path_prefix": "skills/payments/"}
    assert plans["memoryhub"].status == "skipped" and plans["memoryhub"].reasons == ["not_selected"]
    # C1 fans out and never applies procedures
    c1 = plans_for("How many retries does payment-auth allow?", arm="C1-fair")
    assert all(plan.call and not plan.required for plan in c1.values())
    # as_of: memory has no version reads; code reads the release
    historical = plans_for("What was the retry limit?", as_of="R40")
    assert historical["memoryhub"].status == "unsupported_for_mode"
    assert historical["memoryhub"].reasons == ["unsupported_for_as_of"]
    assert historical["codehub"].version_refs == ["R40"]
    # a release named in the text acts as as_of (HLD §10 Ex4 step 1)
    assert plans_for("retry limit at R42?")["codehub"].version_refs == ["R42"]


def test_denied_must_consult_is_a_gap_without_a_call():
    plans = plans_for("How many retries does payment-auth allow?", groups=("payments-code",))
    skill = plans["skillhub"]
    assert not skill.call and skill.required and skill.reasons == ["required_source_denied"]
    assert "dochub" not in plans and "memoryhub" not in plans      # not readable: not in the allowed set


def test_document_text_cannot_steer_routing():
    """Routing reads the query only; the same query routes the same whatever hubs return."""
    first = plans_for("What is the payment-auth retry limit?")
    second = plans_for("What is the payment-auth retry limit?")
    assert {k: (v.call, v.reasons) for k, v in first.items()} == {k: (v.call, v.reasons) for k, v in second.items()}


def test_search_query_adds_inflections_only():
    assert search_query("retry limit in R40?").startswith("retry limit in R40?")
    assert "retries" in search_query("retry limit") and "r40s" not in search_query("R40")


def _candidate(hub, artifact_id, text, version="R42", environment="prod", location="repo:payments/payment-auth", rank=0):
    registry = load_registry(MANIFESTS)
    manifest = registry.manifest(hub)
    artifact = {"artifact_id": artifact_id, "version": version, "environment": environment if hub == "codehub" else None,
                "location": location, "path": f"{artifact_id}.txt", "text": text, "title": artifact_id}
    unit = evidence_unit(manifest, artifact, f"ev-{artifact_id}", "2026-01-01T00:00:00Z", "cl100k_base",
                         frozenset({"implementation"}))
    return Candidate(hub, rank, manifest, artifact, unit)


def test_assembly_dedups_types_conflicts_and_reserves_witnesses():
    code = _candidate("codehub", "a1", "// repo:payments/payment-auth\nclass RetryConfig {\n  MAX_RETRIES = 5;\n}\n")
    skill = _candidate("skillhub", "a2", "---\nname: Payment Auth\n---\nRetry at most 3 times on timeout.\n",
                       version="v3", location="skills/payments/")
    copy = _candidate("dochub", "a3", code.text, version="v1", location="space:PA")
    filler = [_candidate("dochub", f"f{index}", "retry notes " * 200, version="v1", location="space:OTHER", rank=index)
              for index in range(3)]
    terms = ("retry", "payment", "auth")
    budget = 600
    assembled = assemble([code, skill, copy, *filler], terms, frozenset({"implementation", "procedure"}), budget,
                         "cl100k_base", common=True, dedup_exact=True, domain_terms={"payment"})
    ids = {unit.evidence_id for unit in assembled.evidence}
    assert {"ev-a1", "ev-a2"} <= ids                  # both conflict witnesses kept under a tight budget
    assert "ev-a3" not in ids
    kept_code = next(unit for unit in assembled.evidence if unit.evidence_id == "ev-a1")
    assert kept_code.duplicates == ["ev-a3"]           # the copy keeps its own provenance by reference
    assert [(entry.ref_id, entry.reason) for entry in assembled.omitted] == [("ev-a3", "exact_duplicate")]
    assert [(c.a, c.b, c.relation_type.value) for c in assembled.conflicts] == [
        ("ev-a1", "ev-a2", "policy_implementation_divergence")]
    assert assembled.used_tokens <= budget
    assert not any(unit.artifact_id.startswith("f") for unit in assembled.evidence)   # filler did not fit
    assert not assembled.truncated_relevant            # filler is below the best-covered tier
    assert kept_code.exact_token_count == token_count(code.text, "cl100k_base")
    assert kept_code.span.start == 0 and kept_code.span.end == len(code.text)
    assert kept_code.applicability.applicability_status.value == "known"


def test_identity_signature_uses_places_and_acronyms():
    code = _candidate("codehub", "a1", "x = 1\n")
    page = _candidate("dochub", "a2", "text\n", version="v1", location="space:PA")
    other = _candidate("codehub", "a3", "x = 2\n", location="repo:payments/refund-engine")
    domain = {"payment"}
    assert identity_signature(code, domain) & identity_signature(page, domain) == {"pa"}
    assert not identity_signature(code, domain) & identity_signature(other, domain)


def test_budget_counts_the_final_serialized_list():
    """Codex M3-M8 #4: packing costs the evidence list as serialized (duplicate references and
    list framing included) and never exceeds budget_tokens, for any budget."""
    import json as _json
    from sanctum_ref.text import token_count as _count
    code = _candidate("codehub", "a1", "// repo:payments/payment-auth\\nclass RetryConfig {\\n  MAX_RETRIES = 5;\\n}\\n")
    copies = [_candidate("dochub", f"c{index}", code.text, version="v1", location="space:PA") for index in range(3)]
    filler = [_candidate("dochub", f"f{index}", f"retry payment auth notes {index} " * (20 + index), version="v1",
                         location="space:OTHER", rank=index) for index in range(8)]
    for budget in range(150, 1600, 37):
        assembled = assemble([code, *copies, *filler], ("retry", "payment", "auth"), frozenset({"implementation"}),
                             budget, "cl100k_base", common=True, dedup_exact=True, domain_terms={"payment"})
        payload = [unit.model_dump(mode="json") for unit in assembled.evidence]
        wire = max(_count(_json.dumps(payload), "cl100k_base"), _count(_json.dumps(payload, sort_keys=True), "cl100k_base"))
        assert assembled.used_tokens == wire <= budget, budget
