# Sanctum lab: start here

The lab compares evidence retrieval and agent answers against synthetic, versioned sources. It is a research implementation; results are not production evidence. Start with the [offline tutorial](quickstart.md), then choose the path you need.

| Path | What runs | Where to read |
|---|---|---|
| Reference retrieval | A reference Sanctum process retrieves from simulated MCP hubs; the world evaluator scores evidence and receipts | [Architecture](architecture.md), [corpus and hubs](corpus-and-hubs.md) |
| Agent comparison | Headless Claude answers tasks with direct hub tools or Sanctum; a separate scorer checks grounded answers and plans | [Agent harness](agent-harness.md), [scoring](scoring.md) |

| Engineer goal | Page |
|---|---|
| Set up and run without inference | [Quickstart](quickstart.md) |
| Understand routing knowledge and activation | [Routing memory](routing-memory.md) |
| Understand the decision model and fallback | [System One](system-one.md) |
| Run, inspect, resume or troubleshoot | [Runbook](runbook.md) |
| Bring a new corpus, hub or agent | [Extending the lab](extending.md) |
| Find code and tests | [Codebase map](../codebase-map.md) |

This pack describes implementation as of 2026-10-04. The [architecture artifacts](../../design/intelligence-layer/README.md) own design intent; [experiment records](../experiments/pilot-0-readiness.md) document dated observations. The root README's milestone sections retain historical results.

The checked-in shipping fixture runs from a checkout. The 120-artifact PDLC corpus, reviewed memory release, private task bundle and 180 native run records are generated local inputs under ignored `build/`; pushing code does not publish those inputs. Pilot quality judging remains exploratory until independent gold and human acceptance are complete.
