# Acceptance set (H1, source usefulness)

20 question specs in `specs/` (a-001..a-020) and derived gold in `gold/`.

## Authorship and independence

This set is **agent-authored**, not written by an independent human. The authoring agent worked
from `world/world.yaml`, the rendered hub corpora, lab plan §8 and the `QuestionSpec` fields only.
It did not read `src/sanctum_ref/`, `owners/`, `questions/specs/dev/`, `gold/dev/`,
`docs/reports/` or any `.claude/tasks` file. The lead and the SUT team must not see these specs
or gold before the acceptance run.

Gold is derived with the same generator as dev gold:

```bash
PYTHONPATH=src uv run --no-project --python 3.12 --with pydantic==2.9.2 --with pyyaml==6.0.2 \
  --with mcp==1.12.4 python tools/derive_gold.py --specs acceptance/specs --out acceptance/gold
```

## Mix

| Group | Specs | Intent |
|---|---|---|
| One optional source holds the only necessary evidence | a-001..a-006 | Skipping that hub (dochub or codehub) is a harmful omission |
| Required (must-consult) source matters | a-007..a-010 | SkillHub procedure facts |
| Same name or hub-specific name | a-011..a-014 | Auth Service homonym, ledgerd, idauth, Edge Gateway |
| Honest insufficient | a-015..a-017 | FX Quote coverage gap; code-only principal denied the procedure |
| Historical or conflict | a-018..a-020 | R40 vs R42, R41 code vs procedure, R42 code vs procedure |

## Run once

Run the acceptance set **once**, against the frozen configuration. Do not tune against its
results. Any spec edit after the run invalidates it and must be recorded.
