"""M1 (FR-MOD-02): cue lexicon + stylometry -> gradient-boosted trees (XGBoost).

Interpretable baseline: every input is a named cue count or style measure, so the
feature importances say which surface cues each tactic leans on. Uses XGBoost when it is
installed; otherwise scikit-learn's HistGradientBoosting (same idea, for environments
without xgboost, e.g. CI).
"""

from __future__ import annotations

import numpy as np

from ..data.schema import GENRES
from ..features.handcrafted import HandcraftedFeatures
from .common import TACTICS, genre_index, tactic_training_rows


def _booster(seed: int, multiclass: bool = False, pos_weight: float = 1.0):
    try:
        from xgboost import XGBClassifier
        kw = dict(n_estimators=300, max_depth=5, learning_rate=0.08, subsample=0.9, colsample_bytree=0.9,
                  tree_method="hist", n_jobs=4, random_state=seed, eval_metric="logloss")
        if not multiclass:
            kw["scale_pos_weight"] = pos_weight
        return XGBClassifier(**kw), "xgboost"
    except ImportError:
        from sklearn.ensemble import HistGradientBoostingClassifier
        return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, max_depth=5,
                                              class_weight="balanced", random_state=seed), "sklearn-hgb"


class M1:
    name = "M1 lexicon + stylometry + XGBoost"

    def __init__(self, weak: bool = True, seed: int = 42):
        self.weak, self.seed = weak, seed
        self.feats = HandcraftedFeatures()

    def fit(self, train: list[dict], val: list[dict]) -> None:
        rows, Y = tactic_training_rows(train, weak=self.weak)
        X = self.feats.transform([r["text"] for r in rows])
        self.models: dict[int, object] = {}
        for j in range(len(TACTICS)):
            pos = int(Y[:, j].sum())
            if pos == 0:
                continue
            m, self.backend = _booster(self.seed, pos_weight=(len(Y) - pos) / pos)
            m.fit(X, Y[:, j])
            self.models[j] = m
        Xg = self.feats.transform([r["text"] for r in train])
        yg = genre_index(train)
        self.genre_classes = np.unique(yg)
        self.genre_model, _ = _booster(self.seed, multiclass=True)
        # xgboost wants labels 0..k-1
        remap = {c: i for i, c in enumerate(self.genre_classes)}
        self.genre_model.fit(Xg, np.array([remap[c] for c in yg]))

    def predict(self, records: list[dict]) -> tuple[np.ndarray, np.ndarray]:
        X = self.feats.transform([r["text"] for r in records])
        s = np.zeros((len(records), len(TACTICS)))
        for j, m in self.models.items():
            s[:, j] = m.predict_proba(X)[:, 1]
        g = np.zeros((len(records), len(GENRES)))
        g[:, self.genre_classes] = self.genre_model.predict_proba(X)
        return s, g

    def importances(self, top: int = 8) -> dict[str, list[tuple[str, float]]]:
        out = {}
        for j, m in self.models.items():
            imp = getattr(m, "feature_importances_", None)
            if imp is None:
                continue
            order = np.argsort(imp)[::-1][:top]
            out[TACTICS[j]] = [(self.feats.names[i], float(imp[i])) for i in order]
        return out
