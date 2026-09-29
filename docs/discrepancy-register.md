# Discrepancy register (lab ↔ HLD v5.1)

| # | Item | HLD v5.1 | Lab choice | Status |
|---|---|---|---|---|
| 1 | Request contract | §12.0 sketch | `RetrieveRequest` with `extra=forbid`; rejects credential-like fields | Frozen at M0 |
| 2 | Reason codes | §12.2 table | `reason_codes.yaml` v1.0.0 adds `must_consult`, `routing_selected` for source outcomes | **Propose back to HLD** |
| 3 | Conflict `relation_type` | §12.2 names the field | Enum: contradiction, policy_implementation_divergence, environment_difference, version_difference | **Propose back to HLD** |
| 4 | Receipt fields | §9.5 step 8, §9.6 | `Receipt` model (resolutions, activations, query plans, decisions, self-reported calls) | Lab extension; propose as HLD appendix |
| 5 | `verdicts` shape | Absent until D7 | `Optional[list[dict]]`, must be null in pilot | Open until D7 |
| 6 | Applicability consistency | §7.1 | `known` requires branch, environment, effective_from; `unknown` carries none | Frozen at M0 |
| 7 | Entity refs | Opaque "if needed" | Always opaque in lab responses | Frozen at M0 |
| 8 | Python version | Plan says pin one minor | 3.12 (container toolchain) | Confirm at M0 review |
| 9 | MCP SDK, tokenizer pins | Plan: pin at M0 | Deferred to M2 (MCP) and M3 (tokenizer), noted in pyproject | Open |
