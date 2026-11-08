# ONNX export check (final model, test split)

Model: `m3_no-context_ev`. Thresholds: the validation-tuned F1 ones (balanced mode).

| Runtime | Turn macro-F1 | Dialogue macro-F1 | Genre macro-F1 | ms per turn (CPU, 1 at a time) | Model size (MB) |
|---|---|---|---|---|---|
| PyTorch (reference) | 0.585 | 0.368 | 0.799 | - | - |
| ONNX int8 | 0.601 | 0.368 | 0.799 | 100.1 | 23.1 |
| ONNX fp32 | 0.585 | 0.368 | 0.799 | 109.3 | 91.3 |

int8 and fp32 agree on 98.6% of the turn-level tactic decisions.
The PyTorch row uses the cached sentence-transformers embeddings; small differences come from
re-tokenising and from int8 weights.
