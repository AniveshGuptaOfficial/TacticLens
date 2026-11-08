"""Shared helpers for the phase-3 analyses: load a trained model, score arbitrary turns,
bootstrap a mean, and Holm-correct a family of p-values."""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np

from ..models.common import TACTICS, threshold_pair


def load_model(root: Path, name: str, encoder=None, log=print):
    """A model trained by `train`, ready to predict, plus its (turn, dialogue) thresholds."""
    d = root / "models" / name
    if (d / "m3_config.json").exists():
        from ..models.m3 import M3
        model = M3.load(d, root / "models" / "embeddings", encoder=encoder, log=log)
    elif (d / f"{name}.pkl").exists():
        with open(d / f"{name}.pkl", "rb") as f:
            model = pickle.load(f)
    else:
        raise SystemExit(f"models/{name}: no saved model (only M0 and M3 runs are saved)")
    th = threshold_pair(np.load(d / "test_predictions.npz")["thresholds"])
    return model, th


def standalone(records: list[dict], texts: list[str], tag: str = "x") -> list[dict]:
    """Copies of `records` with new texts, each its own one-turn dialogue (no context leaks in)."""
    out = []
    for i, (r, t) in enumerate(zip(records, texts)):
        out.append({**r, "dialogue_id": f"{tag}{i}", "turn_id": 0, "text": t, "spans": []})
    return out


def scores(model, records: list[dict]) -> np.ndarray:
    if not records:
        return np.zeros((0, len(TACTICS)))
    return np.asarray(model.predict(records)[0])


def boot_mean(x: np.ndarray, groups: np.ndarray | None = None, n_boot: int = 1000, seed: int = 42):
    """Mean and 95% CI; resamples whole groups (dialogues) when given."""
    x = np.asarray(x, dtype=float)
    if len(x) == 0:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    if groups is None:
        idx = rng.integers(0, len(x), size=(n_boot, len(x)))
        means = x[idx].mean(axis=1)
    else:
        groups = np.asarray(groups)
        uniq = np.unique(groups)
        rows = [np.flatnonzero(groups == g) for g in uniq]
        means = []
        for _ in range(n_boot):
            pick = rng.integers(0, len(uniq), size=len(uniq))
            means.append(x[np.concatenate([rows[k] for k in pick])].mean())
        means = np.array(means)
    lo, hi = np.quantile(means, [0.025, 0.975])
    return float(x.mean()), float(lo), float(hi)


def holm(p: list[float]) -> list[float]:
    """Holm-Bonferroni adjusted p-values (same order as given)."""
    p = np.asarray(p, dtype=float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    running = 0.0
    m = len(p)
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * p[i]))
        adj[i] = running
    return adj.tolist()


def fmt_ci(m: float, lo: float, hi: float, d: int = 3) -> str:
    return f"{m:.{d}f} ({lo:.{d}f} to {hi:.{d}f})"
