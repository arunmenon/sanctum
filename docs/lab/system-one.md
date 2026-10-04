# System One decisions

System One is a bounded decision-provider layer used by Sanctum. This page owns its contract and fallback behavior; the [runbook](runbook.md) owns execution prerequisites.

## Provider and broker boundary

[sanctum_systemone.protocol](../../src/sanctum_systemone/protocol.py) defines provider capabilities, request/answer validation, token estimates and campaign budgets. [system_one_broker.py](../../src/sanctum_run/system_one_broker.py) holds credentials, records requests/responses and mediates external calls on the runner side. Sanctum reaches it through the gateway rather than receiving a provider key.

[providers/](../../src/sanctum_ref/providers/__init__.py) implements decision behavior. Rules and the local stand-in provide baselines; the named provider path permits configured hosted or verified local implementations. A test provider exercises transport without making a real inference claim.

Runtime bundles pin provider configuration, descriptors, prompt templates, calibration files, resolved model and verification proof. An environment alias cannot silently replace the verified model during a campaign. Actual native/provider records are the evidence for which model ran.

## Safe routing behavior and accounting

Required source obligations are applied by routing policy. Optional-source usefulness decisions are not permission checks and cannot override source ACLs. When the decision layer is unavailable or uncertain, preserve candidates and record the fallback rather than pretending a successful model decision occurred.

Calibration is scoped by decision/profile. In the original pilot, uncalibrated D2 decisions preserve sources in shadow mode; making a live call does not prove pruning benefit. A [new active-Jev development ablation](../experiments/pdlc-jev-active-plan.md) binds a separate calibration and is running. Non-shadow decisions are verified, but source pruning remains constrained by required-source and no-empty-source guards; no quality improvement is claimed. Model probabilities alone are not a quality result.

The agent runtime requires positive per-attempt call and input-token limits. The current pilot uses at most two broker calls and a 10,000-input-token reservation per attempt. Limits live in the bundle, not the generic harness. Agent calls and nested System One calls are accounted separately; unknown provider usage stays unknown and stops reconciliation. A rejected call that provably never dispatched is distinct from a failed request with missing usage.

Credential variables are resolved at the broker boundary. `.env`, provider keys and auth tokens are ignored/local inputs, never authored evidence or release content. Provider choice does not authorize sending nonsynthetic content externally.

Verification tests: [test_system_one_providers.py](../../tests/test_system_one_providers.py), [test_system_one_broker.py](../../tests/test_system_one_broker.py), [test_agent_runtime.py](../../tests/test_agent_runtime.py).

Next: [agent harness](agent-harness.md), [scoring](scoring.md).

The separate `jev_unconstrained` experimental switch lets raw Jev usefulness decisions select among all four hubs, including selecting none, without forced-source or nonempty fallbacks. See the [follow-on experiment](../experiments/pdlc-jev-active-plan.md#follow-on-jev-owns-candidate-selection); the earlier shadow and calibrated modes retain their behavior.
