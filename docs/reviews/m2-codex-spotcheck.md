1. **FIXED — Cancelled calls are traced.** A 50 ms caller deadline against a 1 s hub call recorded one `timeout`; cancelling two fan-out calls recorded two more, exactly once each. Cancellation propagated. An injected transport exception also recorded one `error`.

2. **FIXED — Hidden activity counts are removed.** Visible event → another principal’s revocation → visible event returned reader positions `[1, 2]`, with neither global `seq` nor `at_revision`.

3. **PARTIAL — Invalidation delivery works, but cursor polling can miss it.** Removing payments access to `space:LEDGER` delivered `PLACE_UNSHARED`. Transferring ownership delivered `OWNER_CHANGED` to the former owner. However, the regression below can suppress these notifications during incremental polling.

4. **FIXED — Validation errors no longer crash decoding.** `search_code({"query": {"nested": 1}})` returned `invalid_argument` and recorded exactly one `error`, without raising.

5. **FIXED — Partial startup unwinds sessions.** Injecting a DocHub load failure after CodeHub started left zero sessions and zero background tasks. Cancelling startup while opening the second hub also left zero sessions/tasks.

**New P2 defect — Reader cursors become invalid when visibility changes.** [change_feed.py:133](/Users/arunmenon/projects/sanctum/sanctum-lab-m0/src/sanctum_hubs/change_feed.py:133) recomputes positions over currently visible history. Reproduced by transferring a payments-owned note away, renaming it twice, transferring it back, and saving cursor `4`. Transferring it away again shrank the visible feed to positions `[1, 2]`; polling with `after_seq=4` returned `[]`, losing the new ownership-loss notification. Reader positions must remain stable across access changes.

Targeted in-memory probes used MCP **1.26.0** / Pydantic **2.12.5**, rather than the earlier versions. No files changed; full suite and runner output-writing were not rerun.

Request changes
## Follow-up (lead)

The new P2 (reader cursors unstable across access changes) was fixed after this spot-check: visibility is now decided from access recorded at event time, so reader history is append-only. Covered by test_reader_cursor_stable_across_ownership_round_trip (Codex repro) and test_reader_views_are_append_only (randomized prefix property). Not re-reviewed by Codex per the single-review scope.
