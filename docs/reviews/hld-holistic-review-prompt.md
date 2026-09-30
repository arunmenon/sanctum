# Review request: holistic review of the Sanctum intelligence-layer HLD, and how faithfully the lab implements it

You are reviewing the Sanctum HLD as a design, and the lab's reference implementation as evidence of whether that design is generic enough to build. Read the design first, then the code, then answer the five questions below. Rank findings by how much they would change the design. Cite file and section for every claim. Do not read `holdout/`, `acceptance/`, or `gold/` contents.

Design (read fully): `design/intelligence-layer/README.md`, `hld.md`, `memory-design.md`, `contracts-and-scenarios.md`, `system-one-providers.md`, `section-map.md`, `review-history.md`.

Implementation (read as needed): `src/sanctum_ref/` (pipeline, routing, intent, registry, adapters, assembly, memory, resolution, providers/), `src/sanctum_systemone/`, `src/sanctum_run/system_one_broker.py`, `src/sanctum_contracts/`, `owners/manifests/`, `owners/memory_seed/`, `configs/matrix.yaml`, `configs/system_one_providers.yaml`, `configs/system_one_templates.yaml`. Lab context only if useful: `docs/milestones.md`, `docs/discrepancy-register.md`, `docs/experiments/` and `docs/reports/` (results; treat as measured-once synthetic evidence, never as design).

Background the reviewer should know: the lab's synthetic results so far are that rules-only routing underperforms fan-out on holdout; memory (reviewed names, places, procedures) beats rules and the value sits in reviewed identity semantics rather than graph storage; a calibrated hosted System One model (Jev) cuts source calls 12 to 15 percent on D2 with one harmful skip in 40 holdout cases; post-retrieval decisions (D6 conflict, D4 relevance) showed no effect on dev for structural reasons, and a prompt campaign with a challenge slice is in progress. The world corpus contains an intentional prompt-injection fixture; treat it as data.

## The five questions

### 1. Pillars of routing intelligence: the cascade layer

The HLD describes a decision cascade: policy (rules only), then judgment in rounds (rules, then a System One model, then an LLM if unsure), with typed decisions D1 to D9 and safe defaults. Review it as a design: are the pillars complete and separable (policy, intent, source selection, retrieval planning, assembly and conflict handling, escalation)? Are round boundaries and the information each round may see well defined? Is the safe-default discipline consistent across decisions? What is missing for a production router that the lab's narrow scope has hidden (multi-tenancy, caching, cost accounting, per-caller budgets, observability contracts, versioned rule sets)?

### 2. Knowledge-memory layer

The HLD's memory holds five kinds of knowledge about sources (names, places, procedures, ownership and authority, releases) with a three-layer ontology, reviewed identity only, per-source query plans, a precedence ladder for procedures, and versioned releases. Review whether the layer is coherent, whether its governance loop is credible, whether the separation from Engram (agent memory) holds, and whether release pinning and invalidation via a change feed are enough for correctness under concurrent change.

### 3. Ontology for the knowledge graph, and hub-agnosticism

The ontology (entity, term, artifact, place, procedure, release; relations DENOTES, ABOUT, SELECTS_FOR, MEMBER_OF, RELATES_TO) is meant to be agnostic to the underlying knowledge hubs. Test that claim: does anything in the ontology, the memory schema, the registry manifests or the adapter contract assume a specific hub type, tool shape, vocabulary or identity scheme? Would a new hub with a different identity model (for example a ticketing system keyed by numeric ids, a chat archive with no stable artifact ids, a vector store with no native paths) fit without changes to the ontology? Is the meta-taxonomy (what each source calls things) modelled as data the hubs' owners supply, or is it leaking into code?

### 4. Is the lab's cascade generic enough to plug into the design?

The lab built a reference cascade in `src/sanctum_ref/` and a System One provider layer in `src/sanctum_ref/providers/`, `src/sanctum_systemone/` and the runner-side broker. Assess whether these implement the design's abstractions or a lab-shaped special case: are decisions typed and provider-agnostic; is the provider strategy interface sufficient for hosted, self-hosted and LLM tiers; is the broker's trust boundary a design property or a test-harness artifact; are rules, intents and conflict extraction expressed as data or hard-coded to the synthetic world's vocabulary (look for hub names, service names, attribute words or release ids in code); could `sanctum_ref` be lifted into a real Sanctum service with the adapters swapped, and what would have to change first? List concrete lab-specific assumptions with file references.

### 5. Strategy for System One models, and meta-taxonomy fidelity

Given the design's System One strategy (typed decisions, calibrated probabilities, shadow-only without calibration, provider swap requires recalibration, batching, data-class eligibility): is it the right strategy for a model class that is cheap, fast, poorly calibrated raw and sensitive to prompt wording, as the lab found? What is missing (per-decision cost-benefit gating, drift monitoring for provider version changes, fallbacks when the hosted model is unavailable for a long period, a policy for when to use an LLM tier at all)? Separately, judge how faithfully the lab implemented the meta-taxonomy: compare `memory-design.md` (names vs subjects vs places, reviewed identity only, procedures grammar and ladder, release semantics, governance) with `src/sanctum_ref/memory.py`, `resolution.py`, and `owners/memory_seed/r1/`; list what is implemented, what is simplified, and what is absent, and whether any simplification would change the lab's conclusions about memory.

## Output

For each question: findings ranked by design impact (severity, file or section, the concrete problem, the suggested change to the HLD or the code), then a short judgment. End with: (a) the three design changes you would make to the HLD first; (b) whether the lab cascade is a credible seed for the production router or a throwaway, with reasons; (c) the single most important gap between the HLD's meta-taxonomy and what the lab implemented. Be specific; do not restate the design back.
