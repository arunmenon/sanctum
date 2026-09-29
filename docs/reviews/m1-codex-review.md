1. **P1 — Gold requires an unauthorized conflict witness.** [gold.py:345](/Users/arunmenon/projects/sanctum/sanctum-lab-m0/src/sanctum_world/gold.py:345)  
   For `kestrel-identity` querying Payments retries, implementation evidence is correctly marked unobtainable, but gold still requires a divergence relation citing Payments-only `RetryConfig.java`. An ACL-respecting SUT cannot satisfy that relation. **Fix:** generate required relations only when both witnesses are obtainable; preserve the denied-source gap.

2. **P1 — Missing coverage can produce `sufficient`.** [gold.py:219](/Users/arunmenon/projects/sanctum/sanctum-lab-m0/src/sanctum_world/gold.py:219)  
   A query requesting Gateway timeout and FX quote TTL produces one obligation and `evidence_status: sufficient`, although FX TTL has no evidence. Missing facts disappear before completeness is calculated. **Fix:** track uncovered requested facts separately and require `partial` plus the appropriate gap reason when some evidence exists.

3. **P2 — Restricted pages can become public without failing lint.** [lint.py:239](/Users/arunmenon/projects/sanctum/sanctum-lab-m0/src/sanctum_world/lint.py:239)  
   Changing a restricted incident page’s rendered ACL to `[payments-eng]` leaves every lint rule green, including its embedded canary. The check requires only a nonempty ACL, while leak checks exempt the owning artifact. **Fix:** validate rendered ACLs against the authored access policy before granting canary exemptions.

4. **P2 — Restricted content leakage is not checked.** [lint.py:260](/Users/arunmenon/projects/sanctum/sanctum-lab-m0/src/sanctum_world/lint.py:260)  
   Copying the incident’s root-cause sentence into the unrestricted PA overview passes all lint rules. The scanner checks canaries, titles and place names, but not restricted factual text. **Fix:** include restricted assertion spans or distinctive content in the leakage check.

5. **P2 — Historical gold accepts sources without historical reads.** [gold.py:174](/Users/arunmenon/projects/sanctum/sanctum-lab-m0/src/sanctum_world/gold.py:174)  
   Ledger batch size at `R41` accepts MemoryHub’s `current` span as a complete alternative while simultaneously declaring MemoryHub a capability gap. This rewards the historical fallback the HLD prohibits. **Fix:** apply version-read capability checks when selecting obtainable spans, before creating bundles.

6. **P2 — Authorized restricted evidence is discarded.** [gold.py:217](/Users/arunmenon/projects/sanctum/sanctum-lab-m0/src/sanctum_world/gold.py:217)  
   Deriving the incident-root-cause question for `admin-probe` returns unanswerable/`no_coverage`, despite that principal having `restricted-incidents` access. Planted-place membership overrides authorization. **Fix:** determine evidence eligibility through principal access; keep forbidden canaries principal-specific.

7. **P2 — A valid historical query crashes derivation.** [gold.py:171](/Users/arunmenon/projects/sanctum/sanctum-lab-m0/src/sanctum_world/gold.py:171)  
   Identity `max_retries` at `R40`, with default fact kinds, raises `ValueError` because its procedure starts at `R41`; implementation evidence at `R40` exists. **Fix:** handle facts not yet applicable at the requested release explicitly instead of aborting the whole case.

8. **P2 — Leak scanning omits public fields.** [lint.py:85](/Users/arunmenon/projects/sanctum/sanctum-lab-m0/src/sanctum_world/lint.py:85)  
   Setting a filler row’s `version` to `f.retry-limit.impl` passes all lint rules. `version`, `environment`, `acl`, `kind`, and unexpected fields are outside the scan; the renderer guard has the same omission. **Fix:** scan the complete serialized public row and enforce its field allowlist.

Verification: 24 selected schema/isolation tests passed; all ten committed gold cases match derivation. Existing build input/output hashes match. Probes were in memory; no builds or file changes were made.

**Verdict: Request changes—gold correctness and leakage enforcement need fixes before M1 acceptance.**