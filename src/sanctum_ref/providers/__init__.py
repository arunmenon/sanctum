"""System One providers: a registry by name over `configs/system_one_providers.yaml`.

`rules` and `standin` are local; `kind: http` entries become a `SystemOneHttpAdapter` that talks
to the runner's broker (the SUT never sees base URLs or keys). `jev` is the old name and refuses."""
from __future__ import annotations

from pathlib import Path

from sanctum_systemone import load_provider_specs

from .http_systemone import SystemOneHttpAdapter
from .interface import (  # noqa: F401
    POLICY_VERSION, TARGET, DecisionUnavailable, ProviderNotApproved, SystemOneProvider, d2_request, unavailable,
)
from .llm_escalation import LLMEscalationProvider, NotConfigured  # noqa: F401
from .standin import JevProvider, RulesProvider, StandinProvider, tfidf_cosine  # noqa: F401


def provider_names(specs_path: Path) -> list[str]:
    return sorted({"rules", "standin", "jev", *load_provider_specs(specs_path)})


def build_provider(name: str, params_path: Path, specs_path: Path | None = None,
                   calibration_dir: Path | None = None, template_ids: dict | None = None,
                   templates_path: Path | None = None):
    if name == "rules":
        return RulesProvider()
    if name == "standin":
        return StandinProvider(params_path)
    if name == "jev":
        return JevProvider(params_path)
    specs = load_provider_specs(specs_path) if specs_path else {}
    spec = specs.get(name)
    if spec is None or spec.kind != "http":
        raise ValueError(f"unknown decision provider {name!r}")
    from .templates import DEFAULT_TEMPLATES, TemplateRegistry
    return SystemOneHttpAdapter(spec, calibration_dir or Path("configs/calibration"),
                                templates=TemplateRegistry(templates_path or DEFAULT_TEMPLATES),
                                template_ids=template_ids)
