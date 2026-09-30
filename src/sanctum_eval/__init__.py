"""Independent evaluator. Consumes only sanctum_contracts, gold, and observed traces.

Must never import sut_ref or sanctum_stub (checked by tests/test_isolation_static.py).
Metric definitions follow the lab-plan review §3 (normative); METRICS_REVISION is
recorded in every run manifest.
"""
METRICS_REVISION = "metrics-0.3.0"    # 0.3.0: E3 D6 conflict metrics and the D4 reorder-only gate
