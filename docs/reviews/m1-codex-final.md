**FIXED.** Reproduced both cases entirely in memory, copying restricted lines into public `a.doc.pa-overview`:

- Quote-bearing sentence: old JSON comparison missed it; current check reported `restricted_leak`.
- Backslash/Unicode variant (`C:\vault\秘密\café`): same result.

Baseline and restricted-only controls produced zero findings. No new real defect found in this change. No files modified.

**Accept M1** — scoped to this targeted recheck.