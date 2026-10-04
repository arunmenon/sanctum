# PDLC optional-source candidate diagnostic

Observed 2026-10-04 while the calibrated Jev ablation runs. This is a diagnosis, not an implemented fix. Existing shadow and active bundles remain unchanged.

## Verified observations

The original 90 Sanctum attempts made 150 retrieval requests. Receipts contain 130 D2 optional-source decisions; all identify CodeHub. Twenty requests contain no D2 optional-source decision. Jev therefore was not choosing among four optional hubs in those requests.

`src/sanctum_ref/routing.py:_wanted` intersects the query's fact kinds with the keys in a manifest's `authority` map. The pilot registry gives CodeHub `implementation: authoritative`; DocHub, MemoryHub and SkillHub have empty maps. Their evidence roles remain reference, session_history and intended_procedure, respectively. Source roles are not used by that optional rules selector.

A direct function probe on “Explain the gateway design documentation and previous session notes” detects reference/session_history intent and returns false for `_wanted` on all four manifests. The release has twenty accepted procedures spanning implementation, procedure, reference and session_history; procedure/entity resolution can still bring hubs into a plan. The observation does not imply every request calls only CodeHub or that those procedures are absent.

Replaying the new calibration over the original 130 raw D2 responses recommends three skips, all on requests whose observed sole source was CodeHub. The no-empty-source guard preserves that source. Thirty-six active development probes also recorded no applied hub skip, despite calibrated non-shadow decisions where D2 was used.

## Implications and proposed separate work

Calibration makes scores usable but cannot expand a candidate list that was already narrowed. Optional source discoverability appears coupled to authority declaration, which may suppress useful nonauthoritative drafts and session evidence. Review this against the HLD's distinction between source usefulness and fact authority before changing behavior.

A future isolated fix should define how evidence roles/descriptors create optional candidates without granting authority, retain ACL/time/version restrictions and must-consult obligations, and test ambiguous/unresolved subjects as well as design/history questions. First verify actual receipts on task failures; a function probe alone is not proof of end-to-end impact.

Do not fold that change into the current Jev-only ablation. Test it as another declared comparison, and evaluate fresh tasks after development tuning. Local diagnostic replay: `build/pdlc-jev-active/prior-decision-replay.json`; active preflight records: `build/pdlc-jev-active/activation-proof-01/`.
