# Review request: Sanctum intelligence-layer HLD as a research MVP

You are reviewing a **research-stage MVP design**. Its job is to state a small set of tenets clearly enough to be tested, and to be internally consistent. It is not a production specification. Review it on those terms.

## Scope rules for this review (read first)

- **In scope:** clarity, coherence and testability of four pillars: the decision cascade, the System One model strategy, the memory substrate, and the ontology.
- **Out of scope, do not raise:** production hardening of any kind. That includes execution contexts and budget ledgers, caching, observability and retention contracts, multi-tenancy, capability-negotiation frameworks, cryptographic or content-addressed releases, governance workflows and approval machinery, circuit breakers and outage policy, drift monitoring, cost accounting, SLAs, and scale. A previous review proposed these and they were deliberately removed (see `review-history.md`, v5.2.1). Do not re-propose them.
- **Prefer subtraction.** If a section is more complex than the tenet it serves, say what to cut. A recommendation that adds a mechanism must name the tenet it protects and be expressible in a sentence or two of design text.
- **Do not review the lab code** except where a pillar's claim can only be judged against it, and then only to answer "does the design say what was actually built and tested?".

Read: `design/intelligence-layer/README.md`, `hld.md`, `memory-design.md`, `contracts-and-scenarios.md`, `system-one-providers.md`, `review-history.md` (v5.2.1 section). For evidence only, never as design: `docs/milestones.md` and `docs/experiments/system-one-lab.md` (synthetic, measured once). Do not read `holdout/`, `acceptance/` or `gold/`.

## The tenets the MVP sets out to prove

1. Policy decides access with rules only; a model never grants or widens access.
2. Judgment is a cascade: rules first, then a cheap System One model, with a safe default when the model is uncertain, unavailable or invalid. Intelligence must beat a rules baseline before it is switched on.
3. Memory is Sanctum's notebook about sources, not about content: names, subjects and places are three different relations, and only reviewed names establish identity.
4. The ontology is agnostic to the underlying knowledge hubs: what each source calls things (the meta-taxonomy) is data supplied by owners, not code.
5. Evidence is never hidden: conflicts are flagged and both sides kept; gaps are reported honestly.

## Questions, one per pillar

### Pillar 1: the cascade

- Is the cascade described once, consistently, across `hld.md` and `system-one-providers.md`: rounds, what each round may see, which decisions (D1 to D9) sit where, and each decision's safe default?
- For the MVP, which decisions actually need to exist? Identify any decision or round that could be dropped or merged without weakening tenets 1, 2 or 5.
- Is "beats the rules baseline before it is switched on" stated as a testable rule with a named comparison, or only as an intention?

### Pillar 2: System One model strategy

- Is the strategy minimal and coherent: typed questions, calibrated probabilities, shadow-only without a calibration, safe default on uncertainty, provider behind one interface?
- Is anything on `system-one-providers.md` more elaborate than the MVP needs? Name sections to cut or shorten.
- Does the design say plainly what the model may and may not change (it may skip an optional source; it may never remove a required one, widen access, establish identity, or hide a conflict)?

### Pillar 3: memory substrate

- Are the five kinds of memory and the names / subjects / places distinction stated clearly enough that two readers would build the same thing?
- Is `Artifact ABOUT Entity` (memory §8.10) now carried through to evidence, or does the design still fall back to lexical guessing anywhere?
- What is the smallest memory that proves tenet 3? List what in `memory-design.md` is beyond that and could be marked "later" or removed.

### Pillar 4: ontology and hub-agnosticism

- Is every node and relation type necessary for the MVP? Which could go?
- Does anything in the ontology or the adapter contract assume a particular hub's shape, vocabulary or identity scheme? Give the sentence and the fix.
- Is the meta-taxonomy described as owner-supplied data in one place, with one example, so a reader can see what an owner would actually write?

### Across the pillars

- Internal contradictions between pages (same term defined two ways, a rule stated differently in two places).
- Places where the design claims more than the lab tested. State the claim, what was tested, and the smaller claim the design should make.
- The shortest honest statement of what this MVP has and has not shown for each of the five tenets.

## Output

For each pillar: findings ranked by how much they would improve clarity or testability, each with the page and section, the problem, and the change (say "cut", "shorten", "reword" or "add one sentence"). Then:

1. The five things to cut or simplify first.
2. At most three things to add, each one or two sentences long and tied to a tenet.
3. A one-paragraph verdict per tenet: stated clearly, testable, tested, or not yet.

Keep the whole review short. If a finding needs more than a short paragraph, it is probably out of scope.
