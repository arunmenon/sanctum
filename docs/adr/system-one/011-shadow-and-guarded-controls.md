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

These were earlier experimental controls; the later unconstrained test asks a different question.

## Tradeoffs and limits

- The guarded run’s three proposed skips were all overridden, so active decisions did not demonstrate pruning.
- These modes still exist; they are not the selection policy of the unconstrained campaigns.

## Evidence

- [pipeline.py](../../../src/sanctum_ref/pipeline.py)
- [http_systemone.py](../../../src/sanctum_ref/providers/http_systemone.py)
- [pdlc-jev-guarded-results.md](../../experiments/pdlc-jev-guarded-results.md)

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
