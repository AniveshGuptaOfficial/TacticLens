"""Metrics with 95% bootstrap confidence intervals (FR-EVA-01).

The bootstrap resamples whole dialogues (cluster bootstrap), because turns inside one
dialogue are not independent.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import average_precision_score, f1_score, precision_recall_fscore_support


def multilabel_report(y_true: np.ndarray, y_pred: np.ndarray, y_score: np.ndarray | None, labels: list[str]) -> dict:
    p, r, f, s = precision_recall_fscore_support(y_true, y_pred, average=None, zero_division=0)
    per = {}
    for j, lab in enumerate(labels):
        ap = None
        if y_score is not None and y_true[:, j].sum() > 0:
            ap = float(average_precision_score(y_true[:, j], y_score[:, j]))
        per[lab] = {"precision": float(p[j]), "recall": float(r[j]), "f1": float(f[j]), "support": int(s[j]), "auc_pr": ap}
    present = [j for j in range(len(labels)) if y_true[:, j].sum() > 0]
    return {
        "macro_f1": float(f1_score(y_true[:, present], y_pred[:, present], average="macro", zero_division=0)) if present else 0.0,
        "micro_f1": float(f1_score(y_true, y_pred, average="micro", zero_division=0)),
        "per_label": per,
        "labels_with_support": [labels[j] for j in present],
    }


def bootstrap_ci(metric_fn, groups: np.ndarray, n_boot: int = 1000, seed: int = 42, alpha: float = 0.05) -> tuple[float, float]:
    """metric_fn(idx) -> float on the rows `idx`. Resamples unique groups with replacement."""
    rng = np.random.default_rng(seed)
    uniq = np.unique(groups)
    rows_of = {g: np.flatnonzero(groups == g) for g in uniq}
    vals = []
    for _ in range(n_boot):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([rows_of[g] for g in pick])
        vals.append(metric_fn(idx))
    lo, hi = np.quantile(vals, [alpha / 2, 1 - alpha / 2])
    return float(lo), float(hi)


def tune_thresholds(y_true: np.ndarray, y_score: np.ndarray, grid: np.ndarray | None = None) -> np.ndarray:
    """Per-label threshold that maximises F1 on validation data (FR-MOD-07). Default 0.5 if no positives."""
    grid = grid if grid is not None else np.linspace(0.05, 0.95, 19)
    th = np.full(y_true.shape[1], 0.5)
    for j in range(y_true.shape[1]):
        if y_true[:, j].sum() == 0:
            continue
        best = max(grid, key=lambda t: f1_score(y_true[:, j], (y_score[:, j] >= t).astype(int), zero_division=0))
        th[j] = best
    return th
