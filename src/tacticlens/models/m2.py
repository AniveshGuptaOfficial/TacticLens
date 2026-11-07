"""M2 (FR-MOD-03): frozen MiniLM sentence embedding -> 2-layer MLP. One turn, no context, no role.

The neural baseline: same encoder as M3, but each turn is judged alone. The gap between
M2 and M3 is therefore what context and role add (AC-02, AC-03).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from sklearn.neural_network import MLPClassifier

from ..data.schema import GENRES
from .common import TACTICS, genre_index, tactic_training_rows
from .embed import EmbeddingCache


class M2:
    name = "M2 frozen MiniLM + MLP"

    def __init__(self, cache_dir: Path, weak: bool = True, seed: int = 42, encoder=None, hidden: int = 256, max_iter: int = 60):
        self.cache = EmbeddingCache(cache_dir, encoder=encoder)
        self.weak, self.seed, self.hidden, self.max_iter = weak, seed, hidden, max_iter

    def _mlp(self):
        return MLPClassifier(hidden_layer_sizes=(self.hidden,), alpha=1e-4, batch_size=256, learning_rate_init=1e-3,
                             max_iter=self.max_iter, early_stopping=True, n_iter_no_change=5, random_state=self.seed)

    def fit(self, train: list[dict], val: list[dict]) -> None:
        rows, Y = tactic_training_rows(train, weak=self.weak)
        X = self.cache.embed([r["text"] for r in rows])
        self.keep = Y.sum(axis=0) > 0
        # oversample rows that carry rare tactics so the MLP doesn't ignore them
        rng = np.random.default_rng(self.seed)
        pos_rate = Y[:, self.keep].mean(axis=0)
        w = (Y[:, self.keep] / np.maximum(pos_rate, 1e-3)).max(axis=1)
        w = np.clip(w, 1.0, 20.0)
        idx = rng.choice(len(Y), size=len(Y) * 2, replace=True, p=w / w.sum())
        self.clf = self._mlp()
        self.clf.fit(X[idx], Y[idx][:, self.keep])
        Xg = self.cache.embed([r["text"] for r in train])
        self.clf_g = self._mlp()
        self.clf_g.fit(Xg, genre_index(train))

    def predict(self, records: list[dict]) -> tuple[np.ndarray, np.ndarray]:
        X = self.cache.embed([r["text"] for r in records])
        s = np.zeros((len(records), len(TACTICS)))
        p = self.clf.predict_proba(X)
        s[:, self.keep] = p if p.ndim == 2 else p[:, None]
        g = np.zeros((len(records), len(GENRES)))
        g[:, self.clf_g.classes_] = self.clf_g.predict_proba(X)
        return s, g
