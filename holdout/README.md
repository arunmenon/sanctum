# Holdout questions

40 question specs in `specs/` (family counts 6, 6, 4, 4, 4, 3, 3, 3, 4, 3 per lab plan §8.2) and
their derived gold in `gold/`.

## Author independence

This is an **agent-authored holdout, not an independent human** holdout. The authoring agent
worked from `world/world.yaml`, the rendered hub corpora, lab plan §8, HLD §10, the sample spec
format and the `QuestionSpec` fields only. It did not read `src/sanctum_ref/`, `owners/`,
`questions/specs/dev/`, `gold/dev/` or any `.claude/tasks` file, so the questions were not shaped
against the system under test or the dev set.

Gold is derived by the same generator as dev gold:

```bash
PYTHONPATH=src uv run --no-project --python 3.12 --with pydantic==2.9.2 --with pyyaml==6.0.2 \
  --with mcp==1.12.4 python tools/derive_gold.py --specs holdout/specs --out holdout/gold
```

## Contents

- Questions where plain rules should win (single entity, one visible source, no conflict).
- Questions no configuration can answer; the correct status is `insufficient`:
  h-006, h-031, h-032, h-033 (FX Quote coverage gap), h-039 (incident fact only in the held-back
  hub), h-040 (restricted postmortem for a principal without access).
- Natural phrasing with some typos.

## Run once per milestone

Run the holdout **once per milestone**, after the configuration is frozen. Do not tune against
holdout failures; debug on the dev set. Any spec edit after a run invalidates the holdout for that
milestone and must be recorded.
