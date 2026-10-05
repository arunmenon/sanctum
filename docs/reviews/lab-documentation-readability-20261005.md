# Lab documentation readability and coverage review

Reviewed 2026-10-05 for a team walkthrough. Scope: the current engineer documentation pack, its root entry point and the rendered GitHub reading experience. This was a documentation pass, not a new independent Astra review or runtime evaluation.

## What needed improvement

The pack covered the major subsystems, but introduced contracts and file names before explaining their purpose. It lacked a guided top-down route and a component inventory. Plain-text architecture drawings did not show the preparation and scoring stages clearly.

The System One page still described an active development experiment as running and emphasized guarded behavior before the later unconstrained mode. The scoring completion row still referred to an exhausted-evidence gate that the current scorer reports separately.

## What changed

| Reader need | Documentation change |
|---|---|
| Understand the purpose without prior project knowledge | Start page and guided walkthrough explain the research question and one illustrative evidence flow |
| Know the reference implementation’s components | Architecture names preparation, hub, gateway, router, memory, System One, harness and evaluation components |
| Know what runs locally | Architecture and start page distinguish local data, external model calls and checked-in versus generated inputs |
| Understand repository and domain organization | Corpus guide distinguishes containers from cross-links and shows code/document hierarchy |
| Understand the two meanings of memory | Routing-memory guide distinguishes the search map from session evidence and explains graph implementation |
| Understand Jev’s actual role | System One guide separates shadow, guarded and unconstrained modes, with dated result links |
| Understand a reusable experiment | Harness explains controller and adapter jobs before implementation details |
| Interpret scores correctly | Scoring gives the five-fact example, 0/1/2 checklist meanings, task strata and design criteria |
| Follow operations without guessing | Quickstart retains command blocks; runbook adds an operation chooser and explains dispatch |
| Find detail after orientation | Technical contracts, code links, output records and extension limitations remain in subsystem pages |

Added Mermaid diagrams for the two evidence paths, separate scoring, artifact hierarchy, ingestion, memory relations and preparation, System One, and harness execution. Each diagram has a nearby text explanation.

## Coverage limits made explicit

The documentation does not promise production connectors, coding inside local repositories, Codex/Pi adapters, or external graph storage. Those remain extension work. The generated PDLC corpus and raw runs are local inputs, not recoverable from a checkout alone.

Experiment findings remain exploratory. Human acceptance and grading-disagreement work are still pending; documentation changes do not resolve those research questions.

## Verification

- Checked all eleven guide pages plus the root README: 117 relative links and anchors resolved; code fences balanced.
- `git diff --check` passed.
- Existing tutorial command blocks retained; no model calls or runtime changes made by this pass.
- Verified the published start page and its walkthrough link in Chrome, then inspected rendered architecture and subsystem diagrams. All nine Mermaid diagrams loaded. GitHub briefly showed a client-side renderer error on two pages; full reloads cleared it. The walkthrough is left open for the user.
- Published the documentation rewrite in commit `b037b67` on `lab/pdlc-harness-docs-20261004`.
