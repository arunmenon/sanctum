# Sanctum lab: start here

Sanctum helps a coding agent find evidence across code, documents, procedures and past investigations. This lab tests whether that help produces better answers than letting the agent search those sources directly.

**All lab evidence is synthetic.** The hubs are working local services. The experiments test a research implementation, not a production deployment.

## For tomorrow’s walkthrough

Start with the [guided walkthrough](walkthrough.md). It follows one question through the system and explains the terms as they appear. Then open these pages in order:

| Order | Page | Question it answers |
|---|---|---|
| 1 | [Architecture](architecture.md) | Who calls whom, and where does the evidence go? |
| 2 | [Corpus and hubs](corpus-and-hubs.md) | What information is stored, and how is it organized? |
| 3 | [Routing memory](routing-memory.md) | How does Sanctum connect names, subjects and search locations? |
| 4 | [System One](system-one.md) | What does Jev decide, and which decisions actually affect routing? |
| 5 | [Agent harness](agent-harness.md) | How do we run the same questions fairly? |
| 6 | [Scoring](scoring.md) | How do we tell whether an answer is good? |

## For hands-on work

| Goal | Page |
|---|---|
| Try the lab without model calls | [Quickstart](quickstart.md) |
| Run, inspect, resume or troubleshoot an experiment | [Runbook](runbook.md) |
| Bring a different corpus, hub or coding agent | [Extending](extending.md) |
| Locate implementation and tests | [Codebase map](../codebase-map.md) |

## What is available in Git?

The code, documentation and small [shipping example](../../examples/agent-bundles/shipping/README.md) are checked in. That example is enough to try the harness without Claude or Jev.

The larger PDLC corpus contains 120 artifacts. Its corpus files, reviewed memory release, private task bundle and raw run records are generated local inputs under ignored `build/` directories. A fresh checkout does not contain them. See [corpus and hubs](corpus-and-hubs.md) before trying to reproduce that campaign.

## Current behavior and experiment history

This pack describes implementation as of **2026-10-05**. The [HLD artifacts](../../design/intelligence-layer/README.md) describe design intent. The root README’s milestones preserve older experiments.

The lab supports several System One modes. Earlier campaigns recorded Jev advice without applying it, or applied it with routing overrides. Later experiments let Jev choose all, some or none of the eligible hubs. These are different conditions; see [System One](system-one.md).

For results, read the [unconstrained Jev comparison](../experiments/pdlc-jev-unconstrained-results.md) and the [four-variant follow-up](../experiments/pdlc-rubric-followup-results.md). The follow-up compares Sanctum configurations, not Sanctum against direct hub access. Its changes have not been promoted. Human acceptance is still pending, and grading disagreements remain under investigation. These records support exploratory findings, not a production recommendation.
