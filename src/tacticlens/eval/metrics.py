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


def tune_thresholds(y_true: np.ndarray, y_score: np.ndarray, grid: np.ndarray | None = None,
                    n_boot: int = 0, seed: int = 42, objective: str = "f1") -> np.ndarray:
    """Per-label threshold that maximises F1 on validation data (FR-MOD-07). Default 0.5 if no positives.

    With n_boot > 0 the F1 of each candidate threshold is averaged over bootstrap resamples of the
    validation rows before picking the best. With only a handful of positives (T4, T7 ...) the plain
    argmax jumps to whatever threshold happens to fit those few rows; the average is much steadier.

    objective="accuracy" picks the threshold with the most correct yes/no decisions instead, and may
    choose "never flag" (1.01) when that is what validation data rewards.
    """
    grid = grid if grid is not None else np.linspace(0.05, 0.95, 19)
    if objective == "accuracy":
        grid = np.append(grid, 1.01)
    y_true = np.asarray(y_true)
    n = len(y_true)
    W = np.ones((1, n))
    if n_boot > 0 and n > 0:
        W = np.random.default_rng(seed).multinomial(n, np.full(n, 1.0 / n), size=n_boot).astype(float)
    th = np.full(y_true.shape[1], 0.5)
    for j in range(y_true.shape[1]):
        y = y_true[:, j].astype(float)
        if y.sum() == 0:
            continue
        P = (y_score[:, j][None, :] >= grid[:, None]).astype(float)  # [grid, n]
        tp = W @ (P * y).T  # [boot, grid]
        fp = W @ (P * (1 - y)).T
        fn = W @ y[:, None] - tp
        if objective == "accuracy":
            tn = W @ ((1 - P) * (1 - y)).T
            score = (tp + tn) / W.sum(axis=1, keepdims=True)
        else:
            denom = 2 * tp + fp + fn
            score = np.divide(2 * tp, denom, out=np.zeros_like(tp), where=denom > 0)
        th[j] = grid[int(np.argmax(score.mean(axis=0)))]
    return th
