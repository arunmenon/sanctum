# Review request: Sanctum intelligence-layer HLD as a research MVP

You are reviewing a **research-stage MVP design**. Its job is to state a small set of tenets clearly enough to be tested, and to be internally consistent. It is not a production specification. Review it on those terms.

## Scope rules for this review (read first)

- **In scope:** clarity, coherence and testability of four pillars: the decision cascade, the System One model strategy, the memory substrate, and the ontology.
- **Out of scope, do not raise:** production hardening of any kind. That includes execution contexts and budget ledgers, caching, observability and retention contracts, multi-tenancy, capability-negotiation frameworks, cryptographic or content-addressed releases, governance workflows and approval machinery, circuit breakers and outage policy, drift monitoring, cost accounting, SLAs, and scale. A previous review proposed these and they were deliberately removed (see `review-history.md`, v5.2.1). Do not re-propose them.
- **Where to cut and where to go deeper.** Cut only production hardening and anything that serves no tenet. Two areas are priorities to strengthen, not shrink: **the ontology** (pillar 4) and **the System One provider and adapter layer** (pillar 2). For those, judge completeness and rigor, and say what is missing or under-specified. For everything else, a recommendation that adds a mechanism must name the tenet it protects and fit in a sentence or two.
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

### Pillar 2: System One model strategy, providers and adapters (priority: depth)

The lab integrated a hosted model (TypeSafe Jev) and a self-hosted one (Laya on CPU) behind one strategy interface and one HTTP adapter, with a broker that holds credentials and decides what the model may see. That work must be fully represented in the design as rules (not as lab numbers). Check that `system-one-providers.md` captures each of these as a design rule, and name any that is missing, vague or only implied:

- the provider strategy interface and declared capabilities (primitives, questions per call, options, input window, batching, usage reporting, data classes);
- one adapter for every backend speaking the wire protocol, and how hosted and self-hosted providers differ in practice (batching pays on a hosted service and not on CPU; a small input window forces one item per call and compact state; truncation is reported and voids the call);
- the mapping from each decision to a question primitive, and why bands use calibrated yes/no probabilities only;
- the broker's authority: it builds the model's input from trusted inputs, resolves evidence pointers itself, refuses over-limit payloads, validates outputs, and records model calls separately from source calls;
- question templates and state layouts as named, versioned design objects, including per-provider variants and assertion-bearing excerpts;
- calibration bound to provider, model version, template and state layout; shadow-only without a matching calibration; a provider swap requires recalibration;
- the rule that a model's contribution is always read against a no-model control (for example a per-source prior);
- what the model may and may not change (it may skip an optional source; it may never remove a required one, widen access, establish identity, or hide a conflict);
- conformance checks a backend must pass to be called supported.

Then judge the strategy itself: is it coherent for a model class that is cheap, fast, poorly calibrated raw and sensitive to prompt wording? What is under-specified for someone adding a third provider tomorrow?

### Pillar 3: memory substrate

- Are the five kinds of memory and the names / subjects / places distinction stated clearly enough that two readers would build the same thing?
- Is `Artifact ABOUT Entity` (memory §8.10) now carried through to evidence, or does the design still fall back to lexical guessing anywhere?
- What is the smallest memory that proves tenet 3? List what in `memory-design.md` is beyond that and could be marked "later" or removed.

### Pillar 4: ontology and hub-agnosticism (priority: depth)

The ontology is the part of the design to double down on. Review it for rigor and completeness, not for what can be removed.

- **Completeness.** Are the node types (entity, term, artifact, place, procedure, release) and relations (DENOTES, ABOUT, SELECTS_FOR, MEMBER_OF, RELATES_TO) each defined with: what it means, who may assert it, what it may and may not be used for, and an example? Which definitions are thin or missing a rule?
- **The three-way distinction.** Is names vs subjects vs places carried end to end: resolution, query planning, evidence subjects, conflict detection? Where does a relation's meaning stop before it reaches the evidence?
- **Meta-taxonomy.** Is "what each source calls things" modelled fully: hub-specific names and namespaces, homonyms across namespaces, one entity with several names, names that exist in only one hub, composite subjects, names that are missing? Is it clearly owner-supplied data, with a worked example of what an owner writes for one hub?
- **Hub-agnosticism.** Walk three hubs unlike the lab's through the ontology: a ticketing system keyed by numeric ids, a chat archive with no stable artifact ids, a vector store with no native paths. For each, say what maps cleanly, what the ontology cannot express, and the smallest addition that would fix it. Flag any sentence in the ontology or adapter contract that assumes a particular hub's shape, vocabulary or identity scheme.
- **Layers.** Is the three-layer ontology (what is fixed, what owners declare, what is observed) crisp about which layer each type and relation belongs to, and which layers may change without a schema change?
- **What the ontology deliberately does not do.** Is that stated (it does not decide truth, grant access, or infer identity)?
- **Gaps between ontology and lab.** The lab implemented reviewed names, places, membership and one procedure; it did not implement artifact records or operational ABOUT bindings. Say whether the design is honest about which parts of the ontology have been exercised.

### Across the pillars

- Internal contradictions between pages (same term defined two ways, a rule stated differently in two places).
- Places where the design claims more than the lab tested. State the claim, what was tested, and the smaller claim the design should make.
- The shortest honest statement of what this MVP has and has not shown for each of the five tenets.

## Output

For each pillar: findings ranked by how much they would improve clarity or testability, each with the page and section, the problem, and the change (say "cut", "shorten", "reword" or "add one sentence"). Then:

1. For the ontology and for the System One provider and adapter layer: the additions and clarifications you recommend, most important first, each with the text or rule to add. No cap here, but each must be design content, not hardening.
2. For the rest of the design: the five things to cut or simplify first, and at most three additions, each one or two sentences long and tied to a tenet.
3. A one-paragraph verdict per tenet: stated clearly, testable, tested, or not yet.

Keep the review focused. Outside the two priority areas, a finding that needs more than a short paragraph is probably out of scope.
