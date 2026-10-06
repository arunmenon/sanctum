# ADR-011: Retain shadow and calibrated guarded decision controls

- **Bucket:** [System One](README.md)
- **Status:** Historical — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

Earlier campaigns protected retrieval candidates until the matching decision profile was calibrated.

## Decision

- In shadow mode, record uncalibrated advice without applying source skips.
- In guarded mode, apply calibration while retaining required-source and nonempty overrides.
- Keep both modes distinct in campaign configuration and result interpretation.

## Why this approach?

*Retrospective explanation based on the linked implementation and records; not a new approval.*

These controls preserve access to evidence when usefulness estimates are not calibrated or a skip would break a source requirement. A required-source protection keeps a hub that must be consulted; a nonempty protection prevents skipping every hub.

## Tradeoffs and limits

- Guards can prevent hub skips even when Jev advice is active. The linked guarded result records one campaign example; it is not a universal skip rate.
- These modes still exist; they are not the selection policy of the unconstrained campaigns.

## Related decisions

[ADR-012](012-unconstrained-selection.md) experiments with selection without these controls. It is an experimental override, not a global replacement; both modes remain implemented.

## Evidence

- [pipeline.py](../../../src/sanctum_ref/pipeline.py)
- [http_systemone.py](../../../src/sanctum_ref/providers/http_systemone.py)
- [pdlc-jev-guarded-results.md](../../experiments/pdlc-jev-guarded-results.md)

*Documentation reviewed and clarified on 2026-10-06; runtime choices unchanged.*

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
