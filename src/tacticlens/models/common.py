"""Shared training data, evaluation and prediction files for every model (M0-M3, dual-role).

Every model implements the same two calls:
    fit(train: list[dict], val: list[dict])
    predict(records: list[dict]) -> (tactic_scores [N, 10], genre_probs [N, 4])
and `run_model` does the rest the same way for all of them, so the numbers are comparable:

  thresholds   per tactic AND per level, tuned on validation (FR-MOD-07), shape [2, 10]:
                 row 0 (turn)      on turn-level val rows (P4G, PsyScam)
                 row 1 (dialogue)  on max-pooled val MentalManip dialogues
                 A max over many turns needs a higher cut-off than one turn, so T6/T7/T9 (which
                 occur at both levels) get a separate threshold for each. F1 is averaged over
                 bootstrap resamples of the validation rows, so rare tactics get stable thresholds.
  turn eval    tactic P/R/F1/AUC-PR on test turns that carry turn-level labels (FR-EVA-01)
  dialogue     tactic F1 on test MentalManip dialogues, dialogue score = max over its turns
  genre        macro-F1 over the 4 genres on every test turn
  CIs          95% cluster bootstrap over dialogues
  saved        models/<name>/{val,test}_predictions.npz + metrics.json, for `compare` (FR-EVA-02)
               and `rescore` (re-scores without retraining)

Weak labels: baselines that only see single turns can't learn from MentalManip's per-dialogue
labels directly, so by default every turn of a manipulative dialogue gets the dialogue's
tactics as noisy turn labels (`weak_turn_labels`). M3 instead learns them with a
multiple-instance loss over the dialogue.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Protocol

import numpy as np
from sklearn.metrics import f1_score

from ..data.schema import GENRES
from ..eval.metrics import bootstrap_ci, multilabel_report, tune_thresholds

TACTICS = [f"T{i}" for i in range(1, 11)]
GENRE_INDEX = {g: i for i, g in enumerate(GENRES)}


class Model(Protocol):
    name: str

    def fit(self, train: list[dict], val: list[dict]) -> None: ...

    def predict(self, records: list[dict]) -> tuple[np.ndarray, np.ndarray]: ...


# --------------------------------------------------------------------------- labels
def turn_labels(r: dict, labels: list[str] = TACTICS) -> np.ndarray:
    ts = r.get("tactics") or []
    return np.array([1 if t in ts else 0 for t in labels], dtype=np.int8)


def dialogue_labels(r: dict, labels: list[str] = TACTICS) -> np.ndarray:
    ts = (r.get("meta") or {}).get("dialogue_tactics") or []
    return np.array([1 if t in ts else 0 for t in labels], dtype=np.int8)


def weak_turn_labels(r: dict, labels: list[str] = TACTICS) -> np.ndarray | None:
    """Turn labels for training single-turn models: real ones, or the dialogue's (noisy), or None."""
    if r["label_level"] == "turn":
        return turn_labels(r, labels)
    if r["label_level"] == "dialogue":
        return dialogue_labels(r, labels)
    return None


def genre_index(records: list[dict]) -> np.ndarray:
    return np.array([GENRE_INDEX[r["genre"]] for r in records], dtype=np.int64)


def by_split(records: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {"train": [], "val": [], "test": []}
    for r in records:
        out[r["split"]].append(r)
    return out


def tactic_training_rows(records: list[dict], weak: bool = True) -> tuple[list[dict], np.ndarray]:
    rows, ys = [], []
    for r in records:
        y = weak_turn_labels(r) if weak else (turn_labels(r) if r["label_level"] == "turn" else None)
        if y is not None:
            rows.append(r)
            ys.append(y)
    return rows, (np.stack(ys) if ys else np.zeros((0, len(TACTICS)), dtype=np.int8))


# ------------------------------------------------------------------ dialogue pooling
def dialogue_pool(records: list[dict], scores: np.ndarray, only_level: str = "dialogue"):
    """Max-pool turn scores per dialogue. Returns (dialogue_ids, pooled [D,10], labels [D,10])."""
    idx: dict[str, list[int]] = defaultdict(list)
    for i, r in enumerate(records):
        if r["label_level"] == only_level:
            idx[r["dialogue_id"]].append(i)
    dids = sorted(idx)
    if not dids:
        return [], np.zeros((0, scores.shape[1])), np.zeros((0, scores.shape[1]), dtype=np.int8)
    pooled = np.stack([scores[idx[d]].max(axis=0) for d in dids])
    labs = np.stack([dialogue_labels(records[idx[d][0]]) for d in dids])
    return dids, pooled, labs


# ----------------------------------------------------------------------- evaluation
THRESH_BOOT = 200  # bootstrap resamples used to smooth the threshold choice


def threshold_pair(th: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(turn, dialogue) thresholds. Old prediction files hold one row used for both levels."""
    th = np.asarray(th, dtype=float)
    return (th[0], th[1]) if th.ndim == 2 else (th, th)


def tune_all_thresholds(val: list[dict], val_scores: np.ndarray, n_boot: int = THRESH_BOOT) -> np.ndarray:
    """[2, 10]: row 0 tuned on turn-level val rows, row 1 on max-pooled val dialogues.
    A tactic with no positives at a level borrows the other level's threshold (else 0.5)."""
    th_t = np.full(len(TACTICS), 0.5)
    th_d = np.full(len(TACTICS), 0.5)
    has_t = np.zeros(len(TACTICS), dtype=bool)
    has_d = np.zeros(len(TACTICS), dtype=bool)
    tmask = np.array([r["label_level"] == "turn" for r in val])
    if tmask.any():
        yv = np.stack([turn_labels(r) for r, m in zip(val, tmask) if m])
        th_t = tune_thresholds(yv, val_scores[tmask], n_boot=n_boot)
        has_t = yv.sum(axis=0) > 0
    _, pooled, dl = dialogue_pool(val, val_scores)
    if len(pooled):
        th_d = tune_thresholds(dl, pooled, n_boot=n_boot)
        has_d = dl.sum(axis=0) > 0
    th_t = np.where(has_t, th_t, np.where(has_d, th_d, 0.5))
    th_d = np.where(has_d, th_d, np.where(has_t, th_t, 0.5))
    return np.stack([th_t, th_d])


def evaluate(test: list[dict], tactic_scores: np.ndarray, genre_probs: np.ndarray, th: np.ndarray,
             n_boot: int = 1000, seed: int = 42) -> dict:
    th_t, th_d = threshold_pair(th)
    res: dict = {"thresholds": {"turn": dict(zip(TACTICS, np.round(th_t, 3).tolist())),
                                "dialogue": dict(zip(TACTICS, np.round(th_d, 3).tolist()))}}

    # turn level
    tm = np.array([r["label_level"] == "turn" for r in test])
    if tm.any():
        rows = [r for r, m in zip(test, tm) if m]
        Y = np.stack([turn_labels(r) for r in rows])
        S = tactic_scores[tm]
        P = (S >= th_t).astype(int)
        rep = multilabel_report(Y, P, S, TACTICS)
        present = [TACTICS.index(t) for t in rep["labels_with_support"]]
        G = np.array([r["dialogue_id"] for r in rows])
        rep["macro_f1_ci95"] = list(bootstrap_ci(
            lambda i: f1_score(Y[i][:, present], P[i][:, present], average="macro", zero_division=0),
            G, n_boot=n_boot, seed=seed))
        rep["n"] = int(tm.sum())
        res["turn"] = rep

    # dialogue level (MentalManip)
    dids, pooled, DL = dialogue_pool(test, tactic_scores)
    if len(dids):
        DP = (pooled >= th_d).astype(int)
        rep = multilabel_report(DL, DP, pooled, TACTICS)
        present = [TACTICS.index(t) for t in rep["labels_with_support"]]
        D = np.array(dids)
        rep["macro_f1_ci95"] = list(bootstrap_ci(
            lambda i: f1_score(DL[i][:, present], DP[i][:, present], average="macro", zero_division=0),
            D, n_boot=n_boot, seed=seed))
        rep["n"] = len(dids)
        res["dialogue"] = rep

    # genre
    yg = genre_index(test)
    pg = genre_probs.argmax(axis=1)
    present = sorted(set(yg.tolist()))
    G = np.array([r["dialogue_id"] for r in test])
    res["genre"] = {
        "macro_f1": float(f1_score(yg, pg, labels=present, average="macro", zero_division=0)),
        "macro_f1_ci95": list(bootstrap_ci(
            lambda i: f1_score(yg[i], pg[i], labels=present, average="macro", zero_division=0),
            G, n_boot=n_boot, seed=seed)),
        "per_genre_f1": dict(zip(GENRES, map(float, f1_score(yg, pg, labels=list(range(len(GENRES))),
                                                             average=None, zero_division=0)))),
        "n": len(test),
    }
    return res


def save_predictions(path: Path, records: list[dict], tactic_scores: np.ndarray, genre_probs: np.ndarray | None,
                     th: np.ndarray) -> None:
    np.savez_compressed(
        path,
        dialogue_id=np.array([r["dialogue_id"] for r in records]),
        turn_id=np.array([r["turn_id"] for r in records]),
        tactic_scores=tactic_scores.astype(np.float32),
        genre_probs=(genre_probs if genre_probs is not None else np.zeros((len(records), len(GENRES)))).astype(np.float32),
        thresholds=np.asarray(th),
    )


def load_predictions(path: Path, records: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    """Scores saved by save_predictions, put back in the order of `records`."""
    z = np.load(path, allow_pickle=False)
    pos = {(d, int(t)): i for i, (d, t) in enumerate(zip(z["dialogue_id"], z["turn_id"]))}
    idx = np.array([pos[(r["dialogue_id"], int(r["turn_id"]))] for r in records])
    return z["tactic_scores"][idx], z["genre_probs"][idx]


def score_saved(name: str, out_dir: Path, records: list[dict], n_boot: int = 1000, seed: int = 42) -> dict:
    """Re-tune thresholds and re-evaluate from saved val/test predictions, without retraining."""
    sp = by_split(records)
    sv, gv = load_predictions(out_dir / "val_predictions.npz", sp["val"])
    st, gt = load_predictions(out_dir / "test_predictions.npz", sp["test"])
    return _finish(name, out_dir, sp, sv, gv, st, gt, n_boot, seed)


def _finish(name, out_dir, sp, sv, gv, st, gt, n_boot, seed) -> dict:
    th = tune_all_thresholds(sp["val"], sv)
    res = {"model": name, **evaluate(sp["test"], st, gt, th, n_boot=n_boot, seed=seed)}
    save_predictions(out_dir / "val_predictions.npz", sp["val"], sv, gv, th)
    save_predictions(out_dir / "test_predictions.npz", sp["test"], st, gt, th)
    with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    return res


def run_model(model: Model, records: list[dict], out_dir: Path, n_boot: int = 1000, seed: int = 42) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    sp = by_split(records)
    model.fit(sp["train"], sp["val"])
    sv, gv = model.predict(sp["val"])
    st, gt = model.predict(sp["test"])
    return _finish(model.name, out_dir, sp, sv, gv, st, gt, n_boot, seed)


# ------------------------------------------------------------------------- reports
def results_markdown(res: dict, names: dict[str, str]) -> str:
    out = [f"# {res['model']} results", ""]
    for level, title in (("turn", "Tactics, turn level (P4G + PsyScam test turns)"),
                         ("dialogue", "Tactics, dialogue level (MentalManip test dialogues, max over turns)")):
        t = res.get(level)
        if not t:
            continue
        lo, hi = t["macro_f1_ci95"]
        out += [f"## {title}", "",
                f"macro-F1 **{t['macro_f1']:.3f}** (95% CI {lo:.3f} to {hi:.3f}), micro-F1 {t['micro_f1']:.3f}, n = {t['n']:,}", "",
                "| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |", "|---|---|---|---|---|---|---|"]
        for lab, m in t["per_label"].items():
            if m["support"] == 0:
                continue
            ap = "" if m["auc_pr"] is None else f"{m['auc_pr']:.3f}"
            out.append(f"| {lab} | {names.get(lab, lab)} | {m['precision']:.3f} | {m['recall']:.3f} | {m['f1']:.3f} | {ap} | {m['support']} |")
        out.append("")
    g = res["genre"]
    lo, hi = g["macro_f1_ci95"]
    out += ["## Genre (every test turn)", "", f"macro-F1 **{g['macro_f1']:.3f}** (95% CI {lo:.3f} to {hi:.3f}), n = {g['n']:,}", "",
            "| Genre | F1 |", "|---|---|"] + [f"| {k} | {v:.3f} |" for k, v in g["per_genre_f1"].items()] + [""]
    return "\n".join(out)
