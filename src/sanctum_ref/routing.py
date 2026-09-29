"""Stage 2-3 (HLD §5.1): what is allowed, and what is worth asking.

Precedence (HLD §9.4): policy (caller access, capabilities) first, then explicit request
constraints (as_of, environment), then must-consult procedures within permitted sources, then
the arm's routing rule (fan-out or intent rules) for optional sources. Must-consult can never
reach a source the caller cannot read: that is a visible `required_source_denied` gap.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from sanctum_contracts import RetrieveRequest

from .config import ArmConfig
from .intent import Intent
from .registry import HubManifest, Procedure, Registry

# Fact kinds a hub is asked for under rules routing: its declared authority kinds; reference
# docs back any implementation or procedure question.
REFERENCE_BACKED = {"implementation", "procedure"}


@dataclass
class SourcePlan:
    hub_id: str
    manifest: HubManifest
    call: bool
    status: str                         # called | skipped | unsupported_for_mode (before the call)
    reasons: list[str]
    required: bool = False
    selectors: dict[str, str] = field(default_factory=dict)
    version_refs: list[Optional[str]] = field(default_factory=lambda: [None])   # one search per ref
    as_of: Optional[str] = None
    procedure_refs: list[str] = field(default_factory=list)


DEFAULT_ENVIRONMENTS = {None, "prod", "production"}


def effective_as_of(request: RetrieveRequest, intent: Intent) -> Optional[str]:
    """Explicit `as_of`, else a single release the query names (HLD §10 Ex4 step 1)."""
    if request.as_of:
        return request.as_of
    return intent.releases[0] if len(intent.releases) == 1 else None


def _version_refs(manifest: HubManifest, capabilities: dict[str, Any], request: RetrieveRequest,
                  intent: Intent, as_of: Optional[str]) -> tuple[bool, list[Optional[str]]]:
    """(supported, refs to search) under the request's time and environment constraints.

    Release-versioned hubs read the named release; revision-versioned hubs that declare version
    reads are asked for their current revision (applicability stays unknown); hubs without
    version reads cannot answer a time-bound question (`unsupported_for_as_of`)."""
    contract = capabilities.get("contract", {})
    releases = manifest.versions.semantics == "release" and manifest.search.version_filter
    if request.environment not in DEFAULT_ENVIRONMENTS and request.mode.value != "verify":
        ref = manifest.versions.environment_refs.get(request.environment) if releases else None
        return (True, [ref]) if ref else (True, [None])
    refs: list[Optional[str]] = [None]
    if as_of:
        if not contract.get("version_reads"):
            return False, []
        if releases:
            if as_of not in manifest.versions.releases:
                return False, []
            refs = [as_of]
    if releases:
        for environment in sorted(intent.environments):
            ref = manifest.versions.environment_refs.get(environment)
            if ref and ref not in refs:
                refs.append(ref)
    return True, refs


def _wanted(manifest: HubManifest, intent: Intent) -> bool:
    kinds = set(intent.fact_kinds)
    if kinds & REFERENCE_BACKED:
        kinds.add("reference")
    return bool(kinds & set(manifest.authority))


def plan_sources(request: RetrieveRequest, arm: ArmConfig, registry: Registry, intent: Intent,
                 capabilities: dict[str, dict[str, Any]], groups: set[str]) -> list[SourcePlan]:
    plans: dict[str, SourcePlan] = {}
    as_of = effective_as_of(request, intent)
    for hub_id in sorted(capabilities):
        manifest = registry.manifest(hub_id)
        if manifest is None or not manifest.accessible(groups):
            continue                   # unregistered or not readable: not part of the allowed set
        supported, refs = _version_refs(manifest, capabilities[hub_id], request, intent, as_of)
        if not supported:
            plans[hub_id] = SourcePlan(hub_id, manifest, False, "unsupported_for_mode", ["unsupported_for_as_of"],
                                       as_of=as_of)
            continue
        wanted = not arm.rules_routing or _wanted(manifest, intent)
        plans[hub_id] = SourcePlan(hub_id, manifest, wanted, "called" if wanted else "skipped",
                                   ["routing_selected" if wanted else "not_selected"],
                                   version_refs=refs, as_of=as_of)

    if arm.registry_procedures:
        for procedure in registry.procedures:
            if _triggered(procedure, intent):
                _apply_must_consult(procedure, registry, plans, request, capabilities, groups)
    if sum(len(plan.version_refs) for plan in plans.values() if plan.call) > arm.calls:
        raise ValueError("routing exceeds the arm's call budget")
    return [plans[hub_id] for hub_id in sorted(plans)]


def _triggered(procedure: Procedure, intent: Intent) -> bool:
    return (procedure.trigger.domain in intent.domains
            and procedure.trigger.fact_kind_needed in intent.detected_fact_kinds)


def _apply_must_consult(procedure: Procedure, registry: Registry, plans: dict[str, SourcePlan],
                        request: RetrieveRequest, capabilities: dict[str, dict[str, Any]],
                        groups: set[str]) -> None:
    hub_id = procedure.action.must_consult
    manifest = registry.manifest(hub_id)
    selector = dict(procedure.action.selector)
    place = next(iter(selector.values()), "")
    readable = manifest.place_accessible(place, groups) if manifest else False
    if hub_id not in capabilities or not readable:
        plans[hub_id] = SourcePlan(hub_id, manifest, False, "skipped", ["required_source_denied"],
                                   required=True, procedure_refs=[procedure.procedure_id])
        return
    plan = plans.get(hub_id)
    if plan is not None and plan.status == "unsupported_for_mode":
        plan.required = True           # explicit request constraint outranks must-consult
        plan.procedure_refs.append(procedure.procedure_id)
        return
    if plan is None:
        plan = SourcePlan(hub_id, manifest, True, "called", [])
        plans[hub_id] = plan
    plan.call, plan.status, plan.required = True, "called", True
    plan.reasons = ["must_consult"]
    plan.selectors.update(selector)
    plan.procedure_refs.append(procedure.procedure_id)
