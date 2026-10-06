# Agent harness

The harness launches Claude, connects the selected tools and saves what happened. These records explain how the same controller can run different experiment kits while keeping attempts comparable and recoverable.

| Record | Decision | Status |
|---|---|---|
| [ADR-013](013-scenario-bundles.md) | Separate reusable harness logic from scenario bundles | Implemented |
| [ADR-014](014-fresh-evidence-only-sessions.md) | Run fresh Claude sessions with one restricted MCP tool surface | Implemented |
| [ADR-015](015-evidence-delivery-and-limits.md) | Normalize delivered evidence and enforce shared attempt limits | Implemented |
| [ADR-016](016-durable-attempt-ledgers.md) | Freeze schedules and preserve durable attempt outcomes | Implemented |

[Back to catalog](../README.md)
