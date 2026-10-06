# ADR-012: Let raw Jev decisions own eligible hub selection in an experimental arm

- **Bucket:** [System One](README.md)
- **Status:** Experimental — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

Filtering a rule-selected shortlist could not test Jev’s ability to choose previously excluded hubs.

## Decision

- Offer all eligible hubs to Jev rather than an authority-based candidate shortlist.
- A hub is not excluded merely because it cannot read the requested release. Search its available revision and retain metadata describing where that evidence applies; do not present it as the requested version.
- Select on raw usefulness probability at or above 0.5; use no fitted calibration band.
- Apply no forced-source or nonempty override; memory may translate searches but cannot add or remove a hub.

## Why this approach?

*Retrospective explanation based on the linked implementation and records; not a new approval.*

The owner requested a test of Jev’s choices, including zero selected hubs and selection mistakes.

## Tradeoffs and limits

- If the decision provider is unavailable, rules do not select replacement hubs. A hub without an answered selection decision is skipped.
- Access controls, provenance, execution limits and scoring still apply.
- Several setup factors changed together, so historical improvements do not isolate a causal Jev benefit.
- This is an implemented experiment, not a general HLD-conformance or production-default claim.

## Related decisions

[ADR-011](011-shadow-and-guarded-controls.md) records the earlier shadow and guarded controls. This arm overrides those controls experimentally; it does not remove them or become a production default.

## Evidence

- [pipeline.py](../../../src/sanctum_ref/pipeline.py)
- [http_systemone.py](../../../src/sanctum_ref/providers/http_systemone.py)
- [pdlc-jev-active-plan.md](../../experiments/pdlc-jev-active-plan.md#follow-on-jev-owns-candidate-selection)
- [pdlc-jev-unconstrained-results.md](../../experiments/pdlc-jev-unconstrained-results.md)

*Documentation reviewed and clarified on 2026-10-06; runtime choices unchanged.*

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
