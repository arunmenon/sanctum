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
    interpretation: Optional[int] = None     # index into the resolution's interpretations
    aliases: list[str] = field(default_factory=list)


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

    if arm.registry_procedures or arm.uses_memory:
        for procedure in registry.procedures:
            if _triggered(procedure, intent):
                _apply_must_consult(procedure, registry, plans, request, capabilities, groups)
    return [plans[hub_id] for hub_id in sorted(plans)]


def search_calls(plans: list[SourcePlan]) -> int:
    return sum(len(plan.version_refs) for plan in plans if plan.call)


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


def apply_memory(base: list[SourcePlan], resolution, store, registry: Registry, intent: Intent,
                 groups: set[str], invalidated_places: set[str], query: str, arm: ArmConfig):
    """Overlay memory on the base plans (HLD §9.3-§9.5): one plan per source per interpretation,
    with SELECTS_FOR selectors and preferred-label aliases (translation), and memory procedures
    triggered through explicit MEMBER_OF. Returns (plans, activations, response reasons)."""
    from copy import deepcopy

    from sanctum_contracts.receipt import Activation

    from .resolution import compatible, entity_plan, procedure_activations

    if not resolution.interpretations:
        return base, [], []
    plans: list[SourcePlan] = []
    activations: list = []
    reasons: list[str] = []
    for index, interpretation in enumerate(resolution.interpretations):
        by_hub: dict[str, SourcePlan] = {}
        for plan in base:
            copy = deepcopy(plan)
            copy.interpretation = index
            by_hub[plan.hub_id] = copy
        # memory procedures (policy and explicit constraints already applied in `base`)
        for procedure, activation in procedure_activations(store, interpretation.entity_id,
                                                           interpretation.entity_ref, intent.detected_fact_kinds):
            activations.append(activation)
            hub_id = procedure.action.must_consult
            manifest = registry.manifest(hub_id)
            place = next(iter(procedure.action.selector.values()), "")
            plan = by_hub.get(hub_id)
            if manifest is None or not manifest.place_accessible(place, groups):
                by_hub[hub_id] = SourcePlan(hub_id, manifest, False, "skipped", ["required_source_denied"],
                                            required=True, procedure_refs=[procedure.procedure_id],
                                            interpretation=index)
                continue
            if plan is None:
                plan = SourcePlan(hub_id, manifest, True, "called", [], interpretation=index)
                by_hub[hub_id] = plan
            if plan.status == "unsupported_for_mode":
                plan.required = True
                continue
            plan.call, plan.status, plan.required, plan.reasons = True, "called", True, ["must_consult"]
            plan.selectors.update(procedure.action.selector)
            if procedure.procedure_id not in plan.procedure_refs:
                plan.procedure_refs.append(procedure.procedure_id)
        for hub_id, plan in by_hub.items():
            if not plan.call:
                continue
            memory_plan = entity_plan(store, registry, interpretation.entity_id, hub_id, groups,
                                      invalidated_places, query)
            for key, value in memory_plan.selectors.items():
                if key in plan.selectors:
                    narrowed = compatible(plan.selectors[key], value,
                                          prefix=plan.manifest.search.filter_semantics == "prefix")
                    if narrowed is None:
                        reasons.append("procedure_conflict")   # never a filter union, never a guess
                        continue
                    plan.selectors[key] = narrowed
                else:
                    plan.selectors[key] = value
                activations.extend(Activation(kind="selector", ref=ref, entity_ref=interpretation.entity_ref,
                                              source_id=hub_id) for ref in memory_plan.selector_refs)
            if arm.translation:
                plan.aliases = memory_plan.aliases
        plans.extend(by_hub[hub_id] for hub_id in sorted(by_hub))
    # stay within the call budget: required sources first, then interpretation order
    while search_calls(plans) > arm.calls:
        optional = [plan for plan in plans if plan.call and not plan.required]
        if not optional:
            break
        victim = optional[-1]
        victim.call, victim.status, victim.reasons = False, "skipped", ["not_selected"]
    return plans, activations, sorted(set(reasons))
