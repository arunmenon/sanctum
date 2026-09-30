# Sanctum hardening backlog

[Overview and reading guide](README.md) · [Section map](section-map.md) · [HLD](hld.md)

> Status: backlog, version 5.2.1. The HLD is a design for proving the tenets; it is not a production specification. The items below were drafted in v5.2 from the holistic review (R-Holistic) and moved out in v5.2.1. None is part of the design the lab tests. Each becomes necessary at the stage named, and is designed then.

| Concern | Why it matters | When it becomes necessary | Review finding |
|---|---|---|---|
| One trusted execution context per request (tenant, principal, effective scope with recorded narrowing steps, absolute deadline, pinned versions) | Stages that derive their own deadlines, budgets or versions can disagree within one request | Before a shared service runs concurrent callers with separate stage owners | R-H 1.1 |
| Budget ledger spanning rules, searches, fetches, model calls, retries, decomposition and serialization, with reservation before dispatch | Retries and later stages can overrun the caller's budget unnoticed | When caller-facing budgets or spend limits are enforced in production | R-H 1.1 |
| Policy-epoch recheck before egress | A revocation between resolution and response could let already-retrieved evidence leave | When access can change while requests are in flight on real data | R-H 2.1 |
| Cache keys covering tenant, scope, policy epoch, rule set, memory release, source and index versions and the complete model binding | A cache hit under a different scope or binding can serve wrong or unauthorized results | When any result or decision cache is introduced | R-H 1.4 |
| Stable observation ids per call (request, stage, sequence, attempt) | Receipts, ledgers and replay records need to refer to the same call unambiguously | When receipts are consumed by operations or audit tooling | R-H 1.4 |
| Separate retention and erasure rules for assertion storage, routing observations, retained evidence and inference replay | Queries and provider payloads can hold sensitive content outside memory | Before any real, non-synthetic data is stored | R-H 2.3 |
| Richer observability and cache rules in HLD §14.1 and §14.3 (ledger charges, observation ids, scope steps) | Operating a shared service needs attributable cost and behavior | With the execution context and ledger | R-H 1.4 |
| Capability negotiation for identity stability, addressability, immutable version reads, snapshot retention, typed selector semantics, subject attribution and change feeds, with honest partial support | New hubs differ in what they can promise; plans must not rely on undeclared behavior | When onboarding hubs beyond the lab's protocol (tickets, vector stores, chat archives) | R-H 3.1, 3.3 |
| Exact-version evidence handles for re-reads | A re-read of "the artifact" may not be the version that was served | When an inference gateway or verifier re-reads evidence on real sources | R-H 4.1 |
| Per-decision behavior matrix for D1 to D9 under uncertain, invalid, denied, failed and budget-exhausted conditions | Safe defaults drift between decisions and documents without one table | When more than D2 and D6 run live, or before an acceptance review of failure behavior | R-H 1.2 |
| Bounded reservation share for D6-promoted conflict witnesses, with displaced units listed | Promotions reserve budget and could crowd out other evidence at a fixed budget | If D6 promotions are allowed to reserve beyond leftover budget | R-H 5.1 |
| Reason codes `displaced_by_conflict_reservation`, `budget_exhausted`, `freshness_unknown` | Make the backlog behaviors visible on the wire | With the items that introduce them | R-H 1.2, 2.1 |
| Releases as content-addressed dependency closures, with descriptors and calibration bindings drawn from the release | Configuration loaded from outside the release can silently diverge from it | Before memory releases are published by more than one team | R-H 2.1 |
| Live policy epoch paired with the immutable release | Distinguishes configuration consistency from permission currency | With the egress recheck | R-H 2.1 |
| Change-feed watermarks, gap detection, reconciliation and per-source freshness limits | A feed error or gap must not read as "unchanged" | When sources change faster than releases, on real data | R-H 2.1 |
| Governed assertion envelope (namespace, applicability, metadata permission, provenance, reviewer identities and delegations, dependencies, lifecycle history) with publication checks | Governance is a workflow until publication can enforce reviewer authority, uniqueness and dependency closure | When more than one owner group approves assertions | R-H 2.2, 3.2 |
| Governance of `ABOUT` assertions (proposal, scoped approval, release pinning) | Reviewed subject bindings need the same control as names | When assembly relies on reviewed `ABOUT` beyond adapter-declared subject fields | R-H 3.3 |
| Resolved procedure-conflict status (Q16) | The status for incompatible procedures is still open | Before an acceptance review of procedure handling | R-H 1.2 |
| D2 subset-selection planner (marginal value, minimum coverage, bounded exploration) | Independent per-source probabilities do not define a set | If D2 moves from shadow toward skipping sources | R-H 1.3 |
| Discriminated decision schemas and one shared decision executor across tiers | Keeps calibration, disposition and fallback uniform | When a third decision runs live | R-H 4.2 |
| Per-decision economic activation gates and drift monitoring | Calibration alone does not show inference is worth paying for | Before any decision is adopted outside the lab | R-H 5.1, 5.2 |
| Outage policy: circuit breaking, sustained fallback capacity, recovery probes, purpose-bound LLM use | Request-level fallback does not cover long outages | Before a production dependency on a hosted provider | R-H 5.3 |
