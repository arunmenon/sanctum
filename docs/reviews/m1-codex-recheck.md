Seven findings are fixed; #4 is partial because the new content scanner has a reproducible escaping blind spot.

1. **FIXED — Unauthorized conflict witness.** Payments retries queried by `kestrel-identity` now yields no required relations, while retaining the unobtainable implementation obligation and `required_source_denied`. Both divergence witnesses must be obtainable. [gold.py:364](/Users/arunmenon/projects/sanctum/sanctum-lab-m0/src/sanctum_world/gold.py:364)

2. **FIXED — Missing coverage produces `sufficient`.** Gateway timeout plus FX TTL now produces `partial` with `no_coverage`. Uncovered applicable facts are counted separately and prevent sufficiency. [gold.py:244](/Users/arunmenon/projects/sanctum/sanctum-lab-m0/src/sanctum_world/gold.py:244), [gold.py:293](/Users/arunmenon/projects/sanctum/sanctum-lab-m0/src/sanctum_world/gold.py:293)

3. **FIXED — Weakened restricted ACL passes lint.** Changing the incident ACL to `[payments-eng]` now triggers `acl_mismatch`, `restricted_leak`, and `private_id_leak`. Canary exemptions require the authored ACL. [lint.py:98](/Users/arunmenon/projects/sanctum/sanctum-lab-m0/src/sanctum_world/lint.py:98), [lint.py:268](/Users/arunmenon/projects/sanctum/sanctum-lab-m0/src/sanctum_world/lint.py:268)

4. **PARTIAL — Restricted factual content leakage.** Copying the original root-cause sentence into the PA overview now triggers `restricted_leak`. Distinctive restricted lines are scanned, but quoted text escapes detection; see the new defect below. [lint.py:280](/Users/arunmenon/projects/sanctum/sanctum-lab-m0/src/sanctum_world/lint.py:280)

5. **FIXED — Historical sources without historical reads.** Ledger batch size at `R41` now accepts CodeHub evidence, excludes MemoryHub bundles, and retains MemoryHub’s capability gap. Capability filtering happens before bundle creation. [gold.py:190](/Users/arunmenon/projects/sanctum/sanctum-lab-m0/src/sanctum_world/gold.py:190)

6. **FIXED — Authorized restricted evidence discarded.** The incident-root-cause query for `admin-probe` now returns answerable/`sufficient`, with no forbidden canaries. Restricted evidence exclusion now depends on access. [gold.py:207](/Users/arunmenon/projects/sanctum/sanctum-lab-m0/src/sanctum_world/gold.py:207)

7. **FIXED — Historical derivation crash.** Identity `max_retries` at `R40`, using default fact kinds, now completes with the implementation obligation and `sufficient`; the not-yet-applicable procedure is skipped. [gold.py:200](/Users/arunmenon/projects/sanctum/sanctum-lab-m0/src/sanctum_world/gold.py:200), [gold.py:240](/Users/arunmenon/projects/sanctum/sanctum-lab-m0/src/sanctum_world/gold.py:240)

8. **FIXED — Public fields omitted from scanning.** In-memory identifier injections into `version`, `environment`, `acl`, and `kind` are detected; unexpected fields also trigger `unexpected_field`. The renderer rejects all these mutations. [lint.py:89](/Users/arunmenon/projects/sanctum/sanctum-lab-m0/src/sanctum_world/lint.py:89), [render.py:369](/Users/arunmenon/projects/sanctum/sanctum-lab-m0/src/sanctum_world/render.py:369)

**New defect — P2: JSON escaping defeats restricted-content matching.** The scanner compares raw restricted lines against JSON-serialized rows, where double quotes become escaped. In memory, I appended `Internal finding: the "gateway retry loop" amplified the outage.` to the restricted incident and copied it into the public PA overview. **All lint rules passed.** Compare decoded string values recursively, or consistently escape both sides. [lint.py:91](/Users/arunmenon/projects/sanctum/sanctum-lab-m0/src/sanctum_world/lint.py:91), [lint.py:313](/Users/arunmenon/projects/sanctum/sanctum-lab-m0/src/sanctum_world/lint.py:313)

Verification: 20 gold test functions passed against the existing build; all ten committed cases match derivation. Another 24 schema/isolation tests passed. Build input/output hashes match. Full-suite verification remains limited by the read-only environment and dependency mismatch: Python 3.14/Pydantic 2.12.5 reports a schema-freeze mismatch; Python 3.12 lacks dependencies. No files were changed.

**Request changes.**