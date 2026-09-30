# Codex review: System One handshake and prompt optimization

Read-only review against docs/reviews/system-one-prompt-review-prompt.md (2026-09-30). No templates, calibrations or runs were changed by the reviewer. Disposition by the lead follows the review.

## Verdict

D6 null: primarily target mismatch (instructions ask for strict same-fact-scope-version contradiction; labels count all four relation types incl. environment and version differences) plus a candidate population with little room for promotion. D4 null: primarily measurement (metrics ignore order) and lack of operational headroom (budget rarely binds). Model limitation not isolated; Laya's inverted D6 slope is a clue, not proof.

## Corrections to starting assumptions
- Broker state.items are lists of {source_id, version, environment, text}; no artifact_id, no a/b keys.
- D6 instructions and labels disagree (calibration_labels.py:80).
- round3_fit checks max_calls after collecting; needs a pre-dispatch campaign cap.
- "use band 1.0" is not a never-promote switch (p >= use); shadow must come from a missing binding.
- D4 superset guarantee needs a tight-budget test (assembly.py:284 reorder can change serialization cost).

## Ranked recommendations (summary; full text below)
1. d6-noul-v2-relations: align the D6 question with the four labelled relation types.
2. Assertion-bearing excerpts with provenance-backed fields (artifact_id, environment, subject/attribute via deterministic extraction or null, excerpt_spans) for D6 and D4.
3. d2-noul-v2-loss (predict evidence loss, not topical usefulness) and d2-descriptors-v2, tested separately.
4. d4-noul-v2-support plus score diagnostic; order-sensitive metric (support in first K tokens) and predefined budget stress 1,000/2,000/4,000.
5. D6 decomposition (same subject+attribute? / values differ?) and relation choice, diagnostics only.
6. Laya framing diagnostics (positive vs negative wording) at two context sizes, one pair per call.
7. Calibration discipline: nested case-grouped CV, regularized Platt, source intercepts for D2; do not loosen tolerance.

Campaign ceiling: 432 Jev calls, ~374k input tokens; run rows 1-3 first (<= 84 calls, ~95k tokens) and stop if raw discrimination does not appear.

## Full review text
(Verbatim from the reviewer; see the conversation record. Key template texts are reproduced in the implementation commits that adopt them.)
