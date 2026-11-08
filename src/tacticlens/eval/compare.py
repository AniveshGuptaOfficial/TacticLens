"""Compare two models on the same test set: paired bootstrap on macro-F1 (FR-EVA-02, AC-02/AC-03).

Both models' saved test predictions are aligned on (dialogue_id, turn_id). Each bootstrap
round resamples dialogues once and scores both models on that same sample, so the
difference is paired. p_b_not_better = share of rounds where B - A <= 0, so p < 0.05 means B is
better and p > 0.95 means A is better (each one-sided at 5%).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from sklearn.metrics import f1_score

from ..models.common import TACTICS, dialogue_pool, threshold_pair, turn_labels


def _load(path: Path) -> dict:
    z = np.load(path, allow_pickle=False)
    return {k: z[k] for k in z.files}


def _align(a: dict, b: dict) -> tuple[np.ndarray, np.ndarray]:
    ka = {(d, int(t)): i for i, (d, t) in enumerate(zip(a["dialogue_id"], a["turn_id"]))}
    ib = [i for i, (d, t) in enumerate(zip(b["dialogue_id"], b["turn_id"])) if (d, int(t)) in ka]
    ia = [ka[(b["dialogue_id"][i], int(b["turn_id"][i]))] for i in ib]
    return np.array(ia), np.array(ib)


def paired_bootstrap(test: list[dict], pred_a: Path, pred_b: Path, level: str = "turn",
                     n_boot: int = 2000, seed: int = 42) -> dict:
    a, b = _load(pred_a), _load(pred_b)
    ia, ib = _align(a, b)
    key = {(r["dialogue_id"], int(r["turn_id"])): r for r in test}
    recs = [key[(a["dialogue_id"][i], int(a["turn_id"][i]))] for i in ia]
    sa, sb = a["tactic_scores"][ia], b["tactic_scores"][ib]
    (ta_t, ta_d), (tb_t, tb_d) = threshold_pair(a["thresholds"]), threshold_pair(b["thresholds"])
    pa, pb = (sa >= ta_t).astype(int), (sb >= tb_t).astype(int)

    if level == "turn":
        m = np.array([r["label_level"] == "turn" for r in recs])
        Y = np.stack([turn_labels(r) for r, k in zip(recs, m) if k])
        A, B = pa[m], pb[m]
        groups = np.array([r["dialogue_id"] for r, k in zip(recs, m) if k])
    else:
        dids, poolA, Y = dialogue_pool(recs, sa)
        _, poolB, _ = dialogue_pool(recs, sb)
        A, B = (poolA >= ta_d).astype(int), (poolB >= tb_d).astype(int)
        groups = np.array(dids)
    present = [j for j in range(len(TACTICS)) if Y[:, j].sum() > 0]

    def mf1(P, idx):
        return f1_score(Y[idx][:, present], P[idx][:, present], average="macro", zero_division=0)

    full = np.arange(len(Y))
    fa, fb = mf1(A, full), mf1(B, full)
    rng = np.random.default_rng(seed)
    uniq = np.unique(groups)
    rows_of = {g: np.flatnonzero(groups == g) for g in uniq}
    diffs = []
    for _ in range(n_boot):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([rows_of[g] for g in pick])
        diffs.append(mf1(B, idx) - mf1(A, idx))
    diffs = np.array(diffs)
    lo, hi = np.quantile(diffs, [0.025, 0.975])
    return {"level": level, "n": int(len(Y)), "macro_f1_a": float(fa), "macro_f1_b": float(fb),
            "diff": float(fb - fa), "diff_ci95": [float(lo), float(hi)],
            "p_b_not_better": float((diffs <= 0).mean())}
