"""M0 baseline (FR-MOD-01, FR-FEA-01): TF-IDF word 1-2 grams + char 3-5 grams.

Two heads, trained separately:
  tactics: one-vs-rest logistic regression on turn-level labelled turns (P4G annotated, PsyScam),
           per-tactic thresholds tuned on validation (FR-MOD-07)
  genre:   multinomial logistic regression on every turn (4 genres)
No context and no role: M0 is the floor every other model must beat.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.multiclass import OneVsRestClassifier

from ..data.schema import GENRES
from ..eval.metrics import bootstrap_ci, multilabel_report, tune_thresholds


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


def _xy_tactics(rows: list[dict], labels: list[str]):
    X = [r["text"] for r in rows]
    Y = np.array([[1 if t in (r["tactics"] or []) else 0 for t in labels] for r in rows], dtype=int)
    G = np.array([r["dialogue_id"] for r in rows])
    return X, Y, G


def train_m0(records: list[dict], labels: list[str], out_dir: Path, n_boot: int = 1000, seed: int = 42) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    results: dict = {"model": "M0 TF-IDF + logistic regression", "labels": labels}

    # ---- tactic head
    lab = [r for r in records if r["label_level"] == "turn"]
    tr = [r for r in lab if r["split"] == "train"]
    va = [r for r in lab if r["split"] == "val"]
    te = [r for r in lab if r["split"] == "test"]
    if tr and te:
        Xtr, Ytr, _ = _xy_tactics(tr, labels)
        Xva, Yva, _ = _xy_tactics(va or tr, labels)
        Xte, Yte, Gte = _xy_tactics(te, labels)
        keep = Ytr.sum(axis=0) > 0  # tactics with no training positives can't be learned
        feats = TfidfFeatures()
        Ftr = feats.fit_transform(Xtr)
        clf = OneVsRestClassifier(LogisticRegression(max_iter=2000, class_weight="balanced", C=4.0, random_state=seed))
        clf.fit(Ftr, Ytr[:, keep])
        def scores(F):
            s = np.zeros((F.shape[0], len(labels)))
            s[:, keep] = clf.predict_proba(F)
            return s
        Sva, Ste = scores(feats.transform(Xva)), scores(feats.transform(Xte))
        th = tune_thresholds(Yva, Sva)
        th[~keep] = 1.01
        Pte = (Ste >= th).astype(int)
        rep = multilabel_report(Yte, Pte, Ste, labels)
        present = [labels.index(t) for t in rep["labels_with_support"]]
        if present:
            lo, hi = bootstrap_ci(
                lambda idx: f1_score(Yte[idx][:, present], Pte[idx][:, present], average="macro", zero_division=0),
                Gte, n_boot=n_boot, seed=seed)
            rep["macro_f1_ci95"] = [lo, hi]
        rep.update({"n_train": len(tr), "n_val": len(va), "n_test": len(te), "thresholds": dict(zip(labels, th.round(2).tolist()))})
        results["tactics"] = rep
        with open(out_dir / "m0_tactics.pkl", "wb") as f:
            pickle.dump({"features": feats, "clf": clf, "keep": keep, "thresholds": th, "labels": labels}, f)
    else:
        results["tactics"] = {"skipped": "no turn-level labelled train/test data"}

    # ---- genre head
    tr = [r for r in records if r["split"] == "train"]
    te = [r for r in records if r["split"] == "test"]
    if tr and te and len({r["genre"] for r in tr}) > 1:
        feats_g = TfidfFeatures(20000, 20000)
        Ftr = feats_g.fit_transform([r["text"] for r in tr])
        clf_g = LogisticRegression(max_iter=2000, class_weight="balanced", C=4.0, random_state=seed)
        clf_g.fit(Ftr, [r["genre"] for r in tr])
        yte = np.array([r["genre"] for r in te])
        pte = clf_g.predict(feats_g.transform([r["text"] for r in te]))
        g = np.array([r["dialogue_id"] for r in te])
        present = sorted(set(yte))
        mf1 = float(f1_score(yte, pte, labels=present, average="macro", zero_division=0))
        lo, hi = bootstrap_ci(lambda idx: f1_score(yte[idx], pte[idx], labels=present, average="macro", zero_division=0), g, n_boot=n_boot, seed=seed)
        per = f1_score(yte, pte, labels=list(GENRES), average=None, zero_division=0)
        results["genre"] = {"macro_f1": mf1, "macro_f1_ci95": [lo, hi], "per_genre_f1": dict(zip(GENRES, map(float, per))), "n_test": len(te)}
        with open(out_dir / "m0_genre.pkl", "wb") as f:
            pickle.dump({"features": feats_g, "clf": clf_g}, f)
    else:
        results["genre"] = {"skipped": "need train/test turns from 2+ genres"}

    with open(out_dir / "m0_metrics.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    return results


def metrics_markdown(res: dict, names: dict[str, str]) -> str:
    out = ["# M0 baseline results", ""]
    t = res.get("tactics", {})
    if "macro_f1" in t:
        ci = t.get("macro_f1_ci95", [float("nan")] * 2)
        out += [f"Tactics (turn level): macro-F1 **{t['macro_f1']:.3f}** (95% CI {ci[0]:.3f} to {ci[1]:.3f}), micro-F1 {t['micro_f1']:.3f}. "
                f"Train {t['n_train']:,}, val {t['n_val']:,}, test {t['n_test']:,} turns.", "",
                "| Tactic | Name | Precision | Recall | F1 | AUC-PR | Test support |", "|---|---|---|---|---|---|---|"]
        for lab, m in t["per_label"].items():
            ap = "" if m["auc_pr"] is None else f"{m['auc_pr']:.3f}"
            out.append(f"| {lab} | {names.get(lab, lab)} | {m['precision']:.3f} | {m['recall']:.3f} | {m['f1']:.3f} | {ap} | {m['support']} |")
        out.append("")
    else:
        out += [f"Tactics: {t.get('skipped', 'not run')}", ""]
    g = res.get("genre", {})
    if "macro_f1" in g:
        ci = g["macro_f1_ci95"]
        out += [f"Genre: macro-F1 **{g['macro_f1']:.3f}** (95% CI {ci[0]:.3f} to {ci[1]:.3f}) on {g['n_test']:,} test turns.", "",
                "| Genre | F1 |", "|---|---|"] + [f"| {k} | {v:.3f} |" for k, v in g["per_genre_f1"].items()] + [""]
    else:
        out += [f"Genre: {g.get('skipped', 'not run')}", ""]
    return "\n".join(out)
