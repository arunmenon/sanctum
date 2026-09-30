# Prompt campaign, row 10: order, context size, single versus batched, identical repeats (shadow, dev subset)

> SYNTHETIC, NOT PRODUCTION EVIDENCE. **Measured once**, shadow-only. Numbers only; no conclusion about either model is drawn here.

## Setup

| Item | Value |
|---|---|
| Tool | `tools/row10_batching.py`; D2 with the broker's state shape (query plus descriptors), template `d2-noul-v1` |
| Frozen subset | the first 5 dev case ids (20 judgments: 5 cases x 4 sources; 2 positive under the counterfactual labels); single-question calls on the first 3 (12 judgments, 0 positive) |
| Variants | sorted question order (one batched call per case); an identical repeat; reversed order; longer context (descriptors v2, same questions); single-question calls |
| Metric | paired absolute probability change on the same judgments; AUC where both classes exist (with 2 positives, AUC moves in steps of 1/36) |

## Results

| Provider | Comparison | Paired judgments | Mean abs change in p | Max abs change | AUC (first / second) |
|---|---|---|---|---|---|
| Jev | sorted vs identical repeat | 20 | 0.012 | 0.03 | 0.750 / 0.750 |
| Jev | sorted vs reversed order | 20 | 0.015 | 0.04 | 0.750 / 0.750 |
| Jev | short vs longer context | 20 | 0.132 | 0.35 | 0.750 / 0.694 |
| Jev | batched vs single-question calls | 12 | 0.008 | 0.02 | undefined (no positive) |
| Laya | sorted vs identical repeat | 20 | 0.000 | 0.00 | 0.528 / 0.528 |
| Laya | short vs longer context | 20 | 0.108 | 0.41 | 0.528 / 0.861 |

Laya takes one question per call, so order and batching do not apply. No call was truncated. Spend: Jev 32 calls, 18,603 input / 1,991 output tokens; Laya 60 calls, 14,647 input tokens.
