# ADR-014: Run fresh Claude sessions with one restricted MCP tool surface

- **Bucket:** [Agent harness](README.md)
- **Status:** Implemented — lab scope only
- **Recorded:** 2026-10-06, retrospectively from baseline `848da1f`

## Context

Direct filesystem access or prior conversation history could bypass the evidence path being compared.

## Decision

- Start fresh isolated home/config/workspace state for each attempt.
- Expose direct hub tools or Sanctum-only retrieval according to the arm.
- Let Claude search iteratively; do not script the answer path.
- Choose subscription or API authentication explicitly, without silent fallback.

## Why this approach?

This tests the evidence-routing contribution under controlled agent access.

## Tradeoffs and limits

- The current empty workspace excludes repository editing and test execution.
- Installed-CLI checks are bound to the exact binary/model/auth mode; these are not hostile-code containment.

## Evidence

- [agent_session.py](../../../src/sanctum_run/agent_session.py)
- [agent_mcp.py](../../../src/sanctum_run/agent_mcp.py)
- [test_agent_session.py](../../../tests/test_agent_session.py)
- [agent-harness.md](../../lab/agent-harness.md)

[Catalog](../README.md) · [Recording conventions](../README.md#how-to-read-these-records)
