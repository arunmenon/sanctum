"""Named, versioned System One question templates (configs/system_one_templates.yaml).

A template fixes the question type, the exact instruction text, the state the broker builds and,
for decompositions, the sub-questions. Calibration binds on the template id. Diagnostic templates
are shadow-only: recorded, never calibrated into bands, never applied to routing or assembly."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml


@dataclass(frozen=True)
class Template:
    id: str
    decision: str
    type: str
    state: str
    instructions: str = ""
    criteria: Optional[dict[str, str]] = None
    diagnostic: bool = False
    polarity: str = "positive"
    subquestions: dict[str, str] = field(default_factory=dict)
    descriptors: Optional[str] = None

    def questions(self, qid: str, **fields: Any) -> dict[str, dict[str, Any]]:
        """The protocol questions for one item: one, or one per sub-question (`<qid>#<name>`)."""
        if self.subquestions:
            return {f"{qid}#{name}": {"type": self.type, "instructions": text.format(**fields)}
                    for name, text in self.subquestions.items()}
        question: dict[str, Any] = {"type": self.type, "instructions": self.instructions.format(**fields)}
        if self.criteria:
            question["criteria"] = dict(self.criteria)
        return {qid: question}


class TemplateRegistry:
    def __init__(self, path: Path):
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        self.defaults: dict[str, str] = dict(data.get("defaults") or {})
        self.overrides: dict[str, dict[str, str]] = dict(data.get("provider_overrides") or {})
        self.templates = {name: Template(id=name, **body) for name, body in (data.get("templates") or {}).items()}

    def resolve(self, decision: str, provider: Optional[str] = None, template_id: Optional[str] = None) -> Template:
        name = template_id or (self.overrides.get(provider or "", {}).get(decision)) or self.defaults[decision]
        template = self.templates[name]
        if template.decision != decision:
            raise ValueError(f"template {name!r} is for {template.decision}, not {decision}")
        return template


DEFAULT_TEMPLATES = Path(__file__).resolve().parents[3] / "configs" / "system_one_templates.yaml"
