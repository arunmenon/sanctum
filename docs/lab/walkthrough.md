# A guided walkthrough of the lab

This lab is a **reference implementation of Sanctum**, a layer that helps coding agents find evidence across knowledge sources. It turns the design into working software so we can study how the components behave together. We use synthetic evidence to test whether Sanctum helps an agent produce better answers than searching the sources directly.

## What has been implemented?

- **Searchable hubs:** local services for code, documents, procedures and prior investigations.
- **Sanctum retrieval:** a router that searches selected hubs and returns evidence with citation details.
- **Routing memory:** a reviewed map of names, subjects and search locations.
- **System One:** a decision layer, using Jev in the hosted experiments, that judges which hubs may help.
- **Agent harness and scorer:** tools that run Claude Code, save its evidence and answers, and evaluate them against private criteria.

The current experiments use local simulated hubs and an evidence-only Claude workflow. They do not demonstrate production connectors or coding inside checked-out repositories. The [architecture guide](architecture.md) explains the component boundaries.

## What this walkthrough covers

1. How information is organized in the hubs.
2. How an agent receives a question and retrieves evidence.
3. How routing memory and System One help Sanctum.
4. How answers are saved, scored and interpreted.

The sections below follow that flow. An example question appears once the evidence and agent setup have been introduced.

## 1. Start with the information

The lab has synthetic code, designs, procedures and prior investigations. They live in four hubs, grouped by evidence type. Payments, fraud and other business domains appear across those hubs.

A repository is a container for code artifacts. It is not a hub. A design document can link to a repository, a service and several domains without becoming part of CodeHub. Open [corpus and hubs](corpus-and-hubs.md) for the hierarchy.

## 2. Give Claude a question

To illustrate the flow, consider: **“What happens when fraud checking times out, and what should we test?”** This example shows how a request moves through the components; it is not a claim about a particular evaluated answer.

The harness starts a fresh Claude Code session in an empty workspace. In this experiment Claude reads evidence through MCP tools; it does not have a local repository to edit.

The direct-hub setup lets Claude choose hub searches. The Sanctum setup gives it a single retrieval tool. Open [architecture](architecture.md) to see both paths.

## 3. Let Sanctum find evidence

Routing memory connects the names in the question to subjects and useful locations. Jev evaluates which hubs may help. Those are different jobs: memory can help translate a subject into a hub’s vocabulary; Jev chooses hubs according to the configured routing mode.

In the unconstrained experiment, Jev can choose no hubs. If that happens, Claude receives no hub evidence from that retrieval. We preserve that outcome so the experiment can reveal a selection failure. Open [routing memory](routing-memory.md) and [System One](system-one.md).

## 4. Let Claude answer, then score it

Claude may retrieve again before answering. We save what it asked, what evidence it received, and its final answer.

The evaluator compares the answer with private criteria written before the run. It checks meaning and evidence, not exact wording. A design proposal can be sound in more than one way. Open [agent harness](agent-harness.md) and [scoring](scoring.md).

## 5. Explain what the result means

Three statements mean different things:

| Statement | Meaning |
|---|---|
| “The run completed” | Claude finished within the execution rules |
| “Fact coverage was 80%” | The answer earned 80% of the required fact weight |
| “The task was completed” | All required facts and task-specific obligations passed, with the required acceptance |

High fact coverage can coexist with an incomplete plan or missing uncertainty statement. A score can also be wrong: the grading audit compares the source, answer and judgment before we change routing.

The [latest follow-up](../experiments/pdlc-rubric-followup-results.md) used twelve questions, each under four Sanctum configurations. It tested hub descriptions and routing-memory changes. It did not add a new direct-hub baseline, and no variation has been promoted.

## Terms you will encounter

| Term | Plain meaning |
|---|---|
| Artifact | One versioned piece of evidence, such as a file, document or session record |
| Corpus | The collection of evidence used in an experiment |
| Hub | A service that searches and fetches one evidence type |
| MCP | The protocol used to call those tools |
| Routing memory | Sanctum’s reviewed map of names, subjects and search locations |
| MemoryHub | Evidence from prior investigations and sessions |
| System One / Jev | Decision layer / provider used to judge source usefulness |
| Scenario bundle | Experiment folder linking evidence, questions, private criteria and settings |
| Gold / rubric | Private expected facts / rules for judging the answer |
| Pinned input | A specific version whose hash is recorded so it cannot change unnoticed |
| Receipt | Saved evidence of a call, decision, review or result |
| Candidate / release | Proposed data awaiting acceptance / a version prepared for runtime use |

[Back to start](README.md) · [Try the offline example](quickstart.md)
