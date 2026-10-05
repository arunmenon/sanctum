# Review: Sanctum lab documentation for team handover

| | |
|---|---|
| Reviewed | Branch `lab/pdlc-harness-docs-20261004`, as rendered on GitHub, 5 October 2026 |
| Reviewer | Claude (single independent pass; no files edited, no commands run) |
| Scope | `docs/lab/` pack, the dated experiment records it links to, and the routing-mode code it describes |
| Audience assumed | An engineering team unfamiliar with Sanctum |
| Parts | Part 1: handover review. Part 2: scanability and plain-language pass |

## Overall verdict

**Ready with minor fixes.** The pack explains itself well to a newcomer, and it separates "ran", "scored" and "completed" better than most. Two things have to be fixed before the walkthrough: the latest findings are not findable in one place, and one results page still leads with numbers that a later audit superseded.

After the scanability pass the verdict stays "ready with minor fixes" for the newcomer path, but three pages are too dense to hand over as they are: `scoring.md`, the runbook's real-run sections, and the experiment records.

## How this review was done

- Read the rendered GitHub pages in the browser, in the documented order: the start page, walkthrough, architecture, corpus and hubs, routing memory, System One, agent harness, scoring, quickstart and runbook.
- Read three dated records (unconstrained Jev results, four-variant follow-up, scorer v3 audit) and the active-Jev plan.
- Checked all 113 relative links across 11 lab pages against the branch's file tree: none broken.
- Confirmed the `jev_unconstrained` switch exists in `src/sanctum_ref/pipeline.py`.
- Did not run any commands or edit anything.
- The scanability pass (Part 2) was applied to the same pages as read; the browser was not re-opened, so it covers the branch as it stood at the first read.

---

# Part 1: Handover review

## Three reader journeys

| Reader | Where it works | Where they get stuck |
|---|---|---|
| **Newcomer** (explain what Sanctum does and how components fit) | The walkthrough follows one question end to end and defines 12 terms in a table. "A repository is not a hub" and "MemoryHub is different from routing memory" are stated early and repeated where they matter. | Routing memory's link table (DENOTES, SELECTS_FOR, ABOUT) arrives before the reader has seen what a "canonical entity" or "selector" is. "Arm", "broker", "gateway" and "runtime release" are used in the architecture table before they are defined. |
| **Engineer** (find and follow the offline onboarding path) | The quickstart has exact commands and says what each should print (3,009 artifacts, `0 finding(s)`, `ready_for_paid_dispatch: false`, `task_complete: false`). | There is no troubleshooting for the offline path itself. `task_complete: false` on a successful run will read as a failure. The real-run path depends on local `build/` inputs and a "developer-local Claude 2.1.288 binary". |
| **Experiment reader** (locate the latest findings and say what they establish) | Each record states limits honestly: same-model judge, pending human acceptance, small task counts, intervals that include zero. | There is no results index. The direct-hub comparison lives only inside a scoring-audit page. The unconstrained results page still shows a superseded table as its main content. |

## Prioritized findings

### 1. High: no results index; the direct-hub comparison is buried

- **Location:** `docs/lab/README.md`, "Current behavior and experiment history".
- **Evidence:** the start page links two records. The direct-hub result (unconstrained vs direct, +13.63 points, interval +7.33 to +20.39) appears only in `docs/experiments/pdlc-scorer-v3-audit.md` under "Complete-cohort update". The guarded-mode result (+3.04, interval -1.13 to +7.41) appears only inside `docs/experiments/pdlc-jev-active-plan.md`, a plan page.
- **Reader impact:** a reader cannot answer "what did each experiment find?" without reading five pages in the right order.
- **Fix:** add one index page with a row per experiment: question, cohort, what changed, headline, status, link.

### 2. High: the unconstrained results page leads with superseded numbers

- **Location:** `docs/experiments/pdlc-jev-unconstrained-results.md`, the main table.
- **Evidence:** the table shows out-of-scope at -11.11 points and overall at +9.15. The v3 audit says that decline "was driven by the mechanical claim-type rule" and gives a rescored +13.06 overall, with boundary coverage rising to 97.22%. The results page has a one-paragraph amendment at the top, but its body still says "boundary handling worsened".
- **Reader impact:** a presenter reading the table will report a regression that the project itself has retracted.
- **Fix:** put the rescored table first, move the original into a section titled "Original scoring (superseded)", and correct the body sentence.

### 3. High: cross-cohort numbers sit close enough to be compared

- **Location:** the follow-up page (73.61% unchanged baseline) and the v3 audit (90.86% supported coverage).
- **Evidence:** the follow-up does say its scores "must not be compared directly with the previous thirty-task cohort", but only in its final section.
- **Reader impact:** the same configuration appears to drop from about 90% to 74% between pages.
- **Fix:** state the cohort (30 tasks x 3 runs vs 12 new tasks x 1 run) directly above every table, and repeat the no-comparison warning in the index.

### 4. Medium: System One's budget statement is stale for the experiments the pack reports

- **Location:** `docs/lab/system-one.md`, "Budgets and credentials".
- **Evidence:** it says the allowance is "at most two broker calls and a 10,000-input-token reservation per attempt". The active plan says the unconstrained mode expanded this to 32 calls and 500,000 input tokens.
- **Fix:** give the limit per mode in the modes table.

### 5. Medium: the three Jev modes are accurate but not traceable to results

- **Location:** `docs/lab/system-one.md`, the modes table.
- **Evidence:** the descriptions of shadow, guarded and unconstrained match the plan and the code switch. But the table does not say which run used which mode, or that unconstrained selection means a raw yes/no at 0.5 with no calibration (stated only in the plan).
- **Fix:** add two columns: "selection rule" and "result record".

### 6. Medium: setup and findings are mixed in the same files

- **Evidence:** `pdlc-jev-active-plan.md` contains a plan, preflight findings, a results summary and a second experiment's design. `docs/lab/scoring.md` contains current-campaign status ("The current PDLC judge is Sonnet 5.5 low... still pending").
- **Reader impact:** adding the next experiment means editing method pages.
- **Fix:** the hierarchy proposed below.

### 7. Medium: dense passages in reference pages

The scoring "Failures and acceptance" section and the routing-memory "Responsibilities and checks" table assume terms never introduced (quality driver, packet hash, grants, projection). Rewrites are below and in Part 2.

### 8. Low: handover wording

- The start page heading "For tomorrow's walkthrough" will be wrong the day after.
- The runbook names a personal binary version and macOS Keychain. It flags this itself, which is good, but it should sit in a "not portable yet" box.

### 9. Low: `docs/experiments/` mixes 30 files of different kinds

Plans, results, reviewer prompts and audits sit together with no index. `docs/lab-documentation-plan.md` is still in `docs/`.

### Diagrams and rendered Markdown

- All 9 Mermaid diagrams render on GitHub.
- The routing-memory diagram was inspected closely: it is legible, labelled and matches its caption.
- Tables render cleanly without horizontal scrolling at a normal desktop width.
- The architecture diagrams were seen only partially because of screenshot problems on the reviewer's side, so their layout is not fully verified.

## Coverage against the review dimensions

| Dimension | Assessment |
|---|---|
| Readability and cognitive load | Good on the start page, walkthrough and quickstart. Reference pages introduce terms before explaining them (see Part 2). |
| Logical structure and navigation | The pack does progress purpose, setup, components, execution, evaluation, with working "next" links. Introductory, operational and reference content are distinguishable at the page level but mixed inside `corpus-and-hubs.md`, `scoring.md` and `runbook.md`. |
| Reference implementation coverage | Each component's job is stated in the architecture table. What runs locally vs what calls a model service is stated clearly. What is in Git vs generated under `build/` is stated on the start page. MemoryHub vs routing memory, repositories vs hubs, and direct-hub vs Sanctum execution are each explained at least twice. Implemented vs planned is stated (fixture agent, future Codex/Pi adapters, no hostile-code sandbox). |
| Grounding and consistency | Mode descriptions match the plan and the code switch. Stale items: the System One budget (finding 4) and the superseded results table (finding 2). |
| Experiment setup vs findings | Not separated (finding 6). No results index (finding 1). |
| Completeness and interpretation of findings | Negative and mixed findings are preserved (description variant declined; memory variant regressed on partial evidence; nothing promoted). Fact coverage, checklist scores, execution completion and accepted completion are distinguished. Cross-cohort comparison risk remains (finding 3). Observations and causes are kept apart in the records' limits paragraphs, but those paragraphs are dense. |
| Practical handover | Offline path is runnable from the page. Real runs depend on undocumented local inputs and a personal binary (finding 8). |

## Proposed documentation hierarchy

```
docs/lab/                      how the lab works (no results, no dated status)
  README, walkthrough, architecture, corpus-and-hubs,
  routing-memory, system-one, agent-harness, scoring
  how-to/  quickstart, runbook, extending
  reference/  codebase-map, glossary
docs/experiments/
  README.md                    results index (one row per experiment)
  method/                      tasks, corpus, arms, repetitions, budgets, scoring policy
  records/                     one dated file per experiment, results only
    2026-10-04-direct-vs-shadow.md
    2026-10-04-jev-guarded.md
    2026-10-05-jev-unconstrained.md   (rescored table first)
    2026-10-05-scorer-v3-rescore.md
    2026-10-05-four-variant-followup.md
  plans/                       plans as written, frozen
  reviews/                     reviewer prompts and audit outputs
```

Each record should use the same headings: question, what changed, what stayed constant, cohort, results, limits, decision.

## Plain-language rewrites for the three densest passages

**1. `scoring.md`, "Failures and acceptance" (second paragraph).**

> If the judge's reply is malformed, we ask once more and keep both replies. If it is still malformed, that answer is marked "not graded". It is not given a zero, and the report shows it as missing. In the latest follow-up, one reply added plan scores for a task that had no plan checklist. We removed only those extra scores and recorded the change; nothing else in the judgment was touched. If two graders disagree, we investigate. We never pick the more favourable grade.

**2. `routing-memory.md`, "How the graph is implemented".**

> Routing memory is a set of Python dictionaries held in memory. There is no graph database. Each subject (for example, Payment Authorization) has a list of links leaving it. Before Sanctum uses memory, it copies the reviewed and accepted links into fast lookup tables. A link that is stored but not accepted is kept for review and is never followed.

**3. `system-one.md`, the unconstrained row and the paragraph after it.**

> In unconstrained mode, Jev is shown all four hubs for every retrieval and answers yes or no for each. Sanctum searches exactly the hubs Jev said yes to, even if that is none. No rule adds a hub back, and no calibration adjusts Jev's answers. Access checks and run limits still apply. We built this mode to see Jev's own choices, including its mistakes.

## Unverified claims and inaccessible evidence

- **Local evidence:** every results page cites files under `build/` (for example `build/agent-runs/sonnet55-jev-unconstrained-02/`). These are ignored in Git, so no reader of this branch can check a number against its source. The reviewer could not either.
- **Quickstart outputs:** not run; the expected outputs are unverified.
- **Not read:** `extending.md` and `codebase-map.md` (links checked only), the pilot plan and the rubric gap diagnosis.
- **Code claims:** the mode switch was confirmed to exist. The 0.5 rule and the budget numbers were not verified in code.
- **Architecture diagrams:** rendering confirmed, layout only partially inspected.

## Smallest set of changes before the team walkthrough

1. Add `docs/experiments/README.md` as a results index with five rows, and link it from the lab start page.
2. On the unconstrained results page, put the rescored numbers first and mark the original table superseded.
3. Add the cohort line above each results table, and the "do not compare across cohorts" note to the index.
4. In `system-one.md`, add per-mode limits and a "result record" link per mode.
5. Rename "For tomorrow's walkthrough" to "Reading order", and add one line to the quickstart saying `task_complete: false` is expected for the fixture.

---

# Part 2: Scanability and plain-language pass

The standard applied: a reader should understand each section without a wall of prose. Short paragraphs of three to four sentences, one idea each. Bullets for responsibilities, steps, checks and findings. Tables for comparisons. Diagrams for flows or relationships. A descriptive heading that leads with the point. Unfamiliar terms explained before use, with deep technical detail after the plain explanation. The test is whether a newcomer could explain the section afterwards, not word count.

## Scanability by page

| Page | Newcomer could explain it after one read? | What is dense |
|---|---|---|
| Start page (`README.md`) | Yes | Last section packs five ideas into one paragraph (modes, two results, not promoted, acceptance pending, grading disputes) |
| `walkthrough.md` | Yes | Nothing. Short sections, one idea each, a terms table. This is the model for the others |
| `quickstart.md` | Yes | Expected outputs are buried in prose after each command block |
| `architecture.md` | Mostly | "Inside Sanctum" is two paragraphs carrying six components; the 11-row component table uses "broker", "gateway" and "arm" before defining them |
| `corpus-and-hubs.md` | First half yes | From "Artifact contract and hierarchy" on, it becomes a string of unrelated reference facts in prose |
| `routing-memory.md` | Partly | The link table comes before the reader knows the terms in it; "What active means" is three paragraphs of rules |
| `system-one.md` | Partly | The modes table is good; the three paragraphs after it carry the important caveats as prose |
| `agent-harness.md` | Partly | Config table cells list five or six items each; "Sessions and authentication" mixes rules and limits |
| `scoring.md` | **No** | "Failures and acceptance" and "Comparison rules" are walls; the "Completion" table cell holds nine conditions |
| `runbook.md` | Steps yes, prerequisites no | Real-run prerequisites are one sentence listing eight things; the `run_quality_evaluation.py` paragraph is the densest in the pack |
| Unconstrained results | **No** | One paragraph holds nine numbers; the limits paragraph lists seven confounds in a sentence |
| Active-Jev plan | **No** | Numbered steps of 60 to 80 words each; a 200-word "Follow-on" paragraph defining the unconstrained mode |
| Four-variant follow-up | Mostly | Good table up front; findings then revert to number-heavy prose |

## The six rewrites that matter most

### 1. `scoring.md`: "provisionally complete" vs "complete"

Today this is a seven-sentence paragraph mixing two definitions, three prerequisites and the current campaign's status. Split it into a lead sentence, a table and a status box:

> A task has two completion levels. Automated checks give the first; a human gives the second.
>
> | Level | Field | What it requires |
> |---|---|---|
> | Passed automated checks | `provisional_task_complete` | Every item in the checklist below |
> | Accepted | `task_complete` | The above, plus a recorded human acceptance tied to that exact answer |
>
> **Automated checklist** (all must hold):
> - every required fact is established
> - every citation supports its claim
> - every mandatory plan item is met
> - uncertainties and caller obligations are stated
> - no unsupported claims or unresolved contradictions
> - the run finished, and it retrieved evidence
>
> **Status of the current campaign:** no task has human acceptance yet. The judge is the same model family as the agent. Treat all scores as exploratory.

The same checklist replaces the nine-condition "Completion" cell in the scoring table; that cell should just say "see checklist".

### 2. `scoring.md`: "Failures and acceptance"

Five paragraphs become a table, since each is a "when X happens, we do Y" rule:

| Situation | What we do | What we never do |
|---|---|---|
| The agent's answer is not valid JSON | Score it zero and keep it in the totals | Rewrite the answer or rerun the agent |
| The judge's reply is malformed | Ask once more; keep both replies | Fill in missing labels ourselves |
| Still malformed after the retry | Mark the answer "not graded"; the report shows a gap | Record a zero |
| Two graders disagree | Investigate before reporting | Pick the more favourable grade |

### 3. `runbook.md`: what a real run needs

The eight-item sentence becomes a checklist, split by arm:

> **Before any real Claude run you need:**
> - an accepted bundle (questions and criteria reviewed and frozen)
> - an exact model and effort setting
> - an explicit spending limit and a spend ledger
> - proof that the installed CLI is isolated and respects round limits
> - a snapshot of who the caller is
>
> **The Sanctum arm also needs:**
> - a reviewed routing-memory release
> - verified System One settings
>
> The shipping example has none of these on purpose, so it cannot start a paid run.

The `run_quality_evaluation.py` paragraph becomes a callout titled **"Not portable yet"** with four bullets:

- it is pinned to one developer's Claude binary;
- it reads subscription login from the macOS Keychain;
- it expects the current policy format;
- to reuse it, pin your own binary in a new evaluation rather than editing this one.

### 4. `system-one.md`: the three modes

Keep the table, add two columns ("selection rule", "result record"), and turn the prose after it into bullets. The paragraph beginning "Unconstrained refers to hub selection..." carries several separate rules:

> **In unconstrained mode:**
> - Jev sees all four hubs on every retrieval and answers yes or no for each.
> - Sanctum searches exactly the hubs Jev chose. That can be none.
> - No rule adds a hub back, and no calibration adjusts Jev's answer.
> - Routing memory still helps translate names; it cannot add or remove a hub.
> - Access checks and run limits still apply.

A small flow diagram would help here more than anywhere else in the pack: one question entering, three branches (shadow: advice logged, all sources kept; guarded: advice applied, then rules may override; unconstrained: advice applied as given), each ending in "hubs searched".

### 5. Unconstrained results: the routing paragraph

Nine numbers in one paragraph become a table with one sentence of reading underneath:

| What we counted | Guarded run | Unconstrained run |
|---|---|---|
| Retrieval requests | 154 | 144 |
| Hub calls (searches and fetches) | 881 | 1,768 |
| Jev decisions | not stated on this page | 576 (144 per hub) |
| Skip recommendations followed | 0 applied (per the plan page) | 279 of 279 |
| Requests that searched no hub | not stated | 10 |

> Reading: letting Jev consider every hub roughly doubled hub calls. This run does not show savings.

The limits paragraph becomes a bulleted "What this does not show" list:

- four things changed at once (candidate policy, raw decision policy, source overrides, broker capacity);
- the same development tasks as before;
- a same-model judge;
- independent gold and human acceptance still pending;
- historical timing and order;
- no causal claim about Jev;
- no claim against direct hub access.

### 6. `routing-memory.md`: order and the link table

Move the worked example above the table and add an "Example" column, so each term is seen in use before it is named:

| Link | Plain meaning | Example |
|---|---|---|
| DENOTES | This name means this subject | "PA-svc" means Payment Authorization |
| SELECTS_FOR | This place is worth searching for this subject | The payment-auth repository |
| ABOUT | This specific file or passage discusses this subject | One handler file, at one version |
| MEMBER_OF | This subject belongs to this group | Payment Authorization is in Payments |

The implementation detail (dictionaries, `RelationStore`, `TableStore`, projection) then goes under a heading such as "How it is stored (for implementers)", after the plain explanation.

## Smaller structural fixes

- **`corpus-and-hubs.md`:** split the page after "What runs locally". Everything below is reference: give it headed subsections ("What an artifact record contains", "How a document gets loaded", "Which script does what") and make the last four paragraphs a two-column table of script and job.
- **`architecture.md`, "Inside Sanctum":** replace with a numbered list of the four things Sanctum does (understand the question, choose sources, search them, pack the evidence), each naming the component that helps.
- **`agent-harness.md`:** break the configuration table's cells into bullets, or split it into "what you choose" and "what the harness verifies".
- **`quickstart.md`:** after each command block, add a three-line "You should see" list instead of a paragraph.
- **Active-Jev plan:** leave it as a frozen plan, but lift the definition of unconstrained mode out of its 200-word paragraph into `system-one.md` (rewrite 4), since that paragraph is currently the only complete definition.
- **Start page, last section:** turn it into three bullets: what modes exist, where the two results are, and what is still unsettled.

## One caution on accuracy

Two of the rewrites above fill cells with "not stated on this page". That is deliberate: the guarded run's skip count (three proposed, all overridden) and call count come from the plan page, not the results page. When restructuring, pull each number from its own record rather than from the tables in this review.
