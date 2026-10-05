# Experiment method

This page explains the setup. It contains no findings. Use the [results index](../README.md) to see what happened in a specific campaign.

## Evidence and tasks

- The PDLC evidence is synthetic and versioned: code, documents, procedures and prior-session records.
- Public questions and private criteria are written against exact corpus versions.
- The main cohort has 30 tasks: 18 supported, six partially supported and six out of scope.
- The follow-up has 12 different questions: six supported, three partial and three boundary questions.
- The original cohort uses three repetitions per task/setup. The follow-up uses one.

The task families cover behavior, dependency/impact, implementation/design, rollout/recovery, testing and uncertainty. HLD and LLD questions use task-specific design criteria, not a single preferred architecture.

## What changes between setups?

| Setup | Evidence path or change |
|---|---|
| Direct hubs | Claude chooses hub tools directly |
| Shadow Sanctum | Claude calls Sanctum; Jev advice is recorded without applying uncalibrated skips |
| Guarded Sanctum | Calibrated advice filters candidates, subject to required-source and nonempty overrides |
| Unconstrained Sanctum | Raw Jev decisions choose among eligible hubs, without those selection overrides |
| Follow-up variations | Unconstrained Sanctum with changed hub descriptions, reviewed place memory, or both |

Each attempt starts a fresh Claude session. The agent receives public tasks and delivered evidence, not private criteria. The [harness guide](../../lab/agent-harness.md) explains the controller and saved files.

## Resource limits

These are the PDLC campaign settings, not generic harness defaults. A new experiment must read and pin its own bundle limits.

| Resource per attempt | Original and guarded | Unconstrained and follow-up |
|---|---:|---:|
| Assistant rounds | 8 | 8 |
| Agent tool calls | 32 | 32 |
| Cumulative evidence tokens | 8,000 | 8,000 |
| Deadline | 120 seconds | 120 seconds |
| System One broker calls | 2 | 32 |
| System One input-token reservation | 10,000 | 500,000 |

The broker-call and input-token limits are separate from hub calls. One retrieval can make several hub searches or fetches. Capacity was expanded for the unconstrained campaign, so the guarded comparison changes more than one factor.

## How answers are scored

- Check answer format and whether citations identify evidence actually delivered.
- Judge whether the answer establishes the required facts and supports its claims.
- Score each applicable plan dimension as missing/wrong, partial, or fully met (0/1/2).
- Check uncertainty, unsupported claims and declared unmet requirements.
- Report provisional completion separately from human-accepted completion.

The [scoring guide](../../lab/scoring.md) defines these checks. The scoring-policy version belongs in each result record. If a policy changes, regrade applicable saved answers consistently and preserve the prior reports.

## How comparisons are read

1. Average repetitions within each task and setup.
2. Compare paired task scores; keep supported, partial and boundary results separate.
3. Report uncertainty by resampling whole tasks, not individual facts or repetitions.
4. State whether runs were randomized together or compared with an earlier campaign.

A descriptive interval gives the range produced by that task-resampling procedure. It does not remove judging bias or historical timing differences. High fact coverage alone does not establish completed PDLC work.

[Back to results](../README.md)
