"""M0 baseline (FR-MOD-01, FR-FEA-01): TF-IDF word 1-2 grams + char 3-5 grams, logistic regression.

Two heads, trained separately:
  tactics: one-vs-rest logistic regression on turn-labelled turns, plus MentalManip turns with
           their dialogue's labels as weak turn labels (see models/common.py)
  genre:   multinomial logistic regression on every training turn (4 genres)
No context and no role: M0 is the floor every other model must beat.
"""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier

from ..data.schema import GENRES
from .common import TACTICS, genre_index, tactic_training_rows


class TfidfFeatures:
    def __init__(self, max_word: int = 50000, max_char: int = 50000):
        self.word = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=max_word, sublinear_tf=True)
        self.char = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, max_features=max_char, sublinear_tf=True)

    def fit_transform(self, texts):
        try:
            return hstack([self.word.fit_transform(texts), self.char.fit_transform(texts)]).tocsr()
        except ValueError:  # tiny corpora: min_df=2 can leave an empty vocabulary
            self.word.set_params(min_df=1)
            self.char.set_params(min_df=1)
            return hstack([self.word.fit_transform(texts), self.char.fit_transform(texts)]).tocsr()

    def transform(self, texts):
        return hstack([self.word.transform(texts), self.char.transform(texts)]).tocsr()


class M0:
    name = "M0 TF-IDF + logistic regression"

    def __init__(self, weak: bool = True, seed: int = 42):
        self.weak, self.seed = weak, seed

    def fit(self, train: list[dict], val: list[dict]) -> None:
        rows, Y = tactic_training_rows(train, weak=self.weak)
        self.keep = Y.sum(axis=0) > 0
        self.feats = TfidfFeatures()
        F = self.feats.fit_transform([r["text"] for r in rows])
        self.clf = OneVsRestClassifier(LogisticRegression(max_iter=2000, class_weight="balanced", C=4.0, random_state=self.seed))
        self.clf.fit(F, Y[:, self.keep])
        self.feats_g = TfidfFeatures(20000, 20000)
        Fg = self.feats_g.fit_transform([r["text"] for r in train])
        self.clf_g = LogisticRegression(max_iter=2000, class_weight="balanced", C=4.0, random_state=self.seed)
        self.clf_g.fit(Fg, genre_index(train))

    def predict(self, records: list[dict]) -> tuple[np.ndarray, np.ndarray]:
        texts = [r["text"] for r in records]
        s = np.zeros((len(records), len(TACTICS)))
        s[:, self.keep] = self.clf.predict_proba(self.feats.transform(texts))
        g = np.zeros((len(records), len(GENRES)))
        g[:, self.clf_g.classes_] = self.clf_g.predict_proba(self.feats_g.transform(texts))
        return s, g

    def save(self, path: Path) -> None:
        with open(path, "wb") as f:
            pickle.dump(self, f)
