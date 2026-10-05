# A guided walkthrough of the lab

Use this page to introduce the lab to someone who has not worked on it. Follow one illustrative question: **“What happens when fraud checking times out, and what should we test?”** This is an explanation of the flow, not a claim about a particular scored answer.

## 1. Start with the information

The lab has synthetic code, designs, procedures and prior investigations. They live in four hubs, grouped by evidence type. Payments, fraud and other business domains appear across those hubs.

A repository is a container for code artifacts. It is not a hub. A design document can link to a repository, a service and several domains without becoming part of CodeHub. Open [corpus and hubs](corpus-and-hubs.md) for the hierarchy.

## 2. Give Claude a question

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
