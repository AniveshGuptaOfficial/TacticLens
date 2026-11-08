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


def tune_all_thresholds(val: list[dict], val_scores: np.ndarray, n_boot: int = THRESH_BOOT,
                        objective: str = "f1") -> np.ndarray:
    """[2, 10]: row 0 tuned on turn-level val rows, row 1 on max-pooled val dialogues.
    A tactic with no positives at a level borrows the other level's threshold (else 0.5)."""
    th_t = np.full(len(TACTICS), 0.5)
    th_d = np.full(len(TACTICS), 0.5)
    has_t = np.zeros(len(TACTICS), dtype=bool)
    has_d = np.zeros(len(TACTICS), dtype=bool)
    tmask = np.array([r["label_level"] == "turn" for r in val])
    if tmask.any():
        yv = np.stack([turn_labels(r) for r, m in zip(val, tmask) if m])
        th_t = tune_thresholds(yv, val_scores[tmask], n_boot=n_boot, objective=objective)
        has_t = yv.sum(axis=0) > 0
    _, pooled, dl = dialogue_pool(val, val_scores)
    if len(pooled):
        th_d = tune_thresholds(dl, pooled, n_boot=n_boot, objective=objective)
        has_d = dl.sum(axis=0) > 0
    th_t = np.where(has_t, th_t, np.where(has_d, th_d, 0.5))
    th_d = np.where(has_d, th_d, np.where(has_t, th_t, 0.5))
    return np.stack([th_t, th_d])


def _binary(y: np.ndarray, p: np.ndarray) -> dict:
    tp = int(((y == 1) & (p == 1)).sum())
    prec = tp / max(int(p.sum()), 1)
    rec = tp / max(int(y.sum()), 1)
    return {"accuracy": float((y == p).mean()), "precision": prec, "recall": rec,
            "f1": 2 * prec * rec / (prec + rec) if prec + rec else 0.0,
            "majority_baseline": float(max(y.mean(), 1 - y.mean())), "positive_rate": float(y.mean()), "n": int(len(y))}


def accuracy_measures(Y: np.ndarray, P: np.ndarray, groups: np.ndarray, cols: list[int],
                      n_boot: int = 1000, seed: int = 42) -> dict:
    """Accuracy-style measures over the tactics with test support (cols), each with a 95% CI and the
    score of a model that always says "no tactic", so the high numbers can be read honestly.

      label_accuracy   share of correct yes/no decisions over every (turn, tactic) pair
      exact_match      share of turns where every tactic decision is right
      any_tactic       does the turn use any influence tactic at all? (binary detection)
    """
    Y, P = Y[:, cols], P[:, cols]
    ya, pa = Y.max(axis=1), P.max(axis=1)
    out = {
        "label_accuracy": float((Y == P).mean()),
        "label_accuracy_ci95": list(bootstrap_ci(lambda i: float((Y[i] == P[i]).mean()), groups, n_boot=n_boot, seed=seed)),
        "label_accuracy_always_no": float((Y == 0).mean()),
        "exact_match": float((Y == P).all(axis=1).mean()),
        "exact_match_ci95": list(bootstrap_ci(lambda i: float((Y[i] == P[i]).all(axis=1).mean()), groups,
                                              n_boot=n_boot, seed=seed)),
        "exact_match_always_no": float((Y == 0).all(axis=1).mean()),
        "any_tactic": _binary(ya, pa),
    }
    out["any_tactic"]["accuracy_ci95"] = list(bootstrap_ci(lambda i: float((ya[i] == pa[i]).mean()), groups,
                                                           n_boot=n_boot, seed=seed))
    return out


def accuracy_operating_point(test: list[dict], tactic_scores: np.ndarray, th: np.ndarray,
                             n_boot: int = 1000, seed: int = 42) -> dict:
    """Accuracy-style measures with thresholds tuned on validation for accuracy, not F1.

    The main thresholds maximise F1, which favours catching tactics (recall); on MentalManip that
    flags reward/flattery in most dialogues and scores below "always no" on accuracy. This second,
    declared operating point shows what the same scores give when the cut-offs aim at correct
    decisions instead. Both come from validation data only.
    """
    th_t, th_d = threshold_pair(th)
    out: dict = {"thresholds": {"turn": dict(zip(TACTICS, np.round(th_t, 3).tolist())),
                                "dialogue": dict(zip(TACTICS, np.round(th_d, 3).tolist()))}}
    tm = np.array([r["label_level"] == "turn" for r in test])
    if tm.any():
        rows = [r for r, m in zip(test, tm) if m]
        Y = np.stack([turn_labels(r) for r in rows])
        P = (tactic_scores[tm] >= th_t).astype(int)
        cols = [j for j in range(len(TACTICS)) if Y[:, j].sum() > 0]
        out["turn"] = accuracy_measures(Y, P, np.array([r["dialogue_id"] for r in rows]), cols, n_boot=n_boot, seed=seed)
        out["turn"]["macro_f1"] = float(f1_score(Y[:, cols], P[:, cols], average="macro", zero_division=0))
    dids, pooled, DL = dialogue_pool(test, tactic_scores)
    if len(dids):
        DP = (pooled >= th_d).astype(int)
        cols = [j for j in range(len(TACTICS)) if DL[:, j].sum() > 0]
        out["dialogue"] = accuracy_measures(DL, DP, np.array(dids), cols, n_boot=n_boot, seed=seed)
        out["dialogue"]["macro_f1"] = float(f1_score(DL[:, cols], DP[:, cols], average="macro", zero_division=0))
    return out


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
        rep["accuracy"] = accuracy_measures(Y, P, G, present, n_boot=n_boot, seed=seed)
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
        rep["accuracy"] = accuracy_measures(DL, DP, D, present, n_boot=n_boot, seed=seed)
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
        "accuracy": float((yg == pg).mean()),
        "accuracy_ci95": list(bootstrap_ci(lambda i: float((yg[i] == pg[i]).mean()), G, n_boot=n_boot, seed=seed)),
    }
    neutral = GENRES.index("neutral")
    res["genre"]["influence_vs_neutral"] = _binary((yg != neutral).astype(int), (pg != neutral).astype(int))
    sms = np.array([r["dataset"] in ("sms_human", "sms_llm") for r in test])
    if sms.any():
        scam = GENRES.index("scam")
        res["genre"]["sms_scam_detection"] = _binary((yg[sms] == scam).astype(int), (pg[sms] == scam).astype(int))
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
    th_acc = tune_all_thresholds(sp["val"], sv, objective="accuracy")
    res["accuracy_operating_point"] = accuracy_operating_point(sp["test"], st, th_acc, n_boot=n_boot, seed=seed)
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
def _ci(c):
    return f" ({c[0]:.1%} to {c[1]:.1%})" if c else ""


def _level_rows(get) -> list[str]:
    rows = []
    ci = _ci
    for level, name in (("turn", "single turns"), ("dialogue", "MentalManip dialogues")):
        a = get(level)
        if not a:
            continue
        rows.append(f"| Tactic yes/no decisions, {name} (per-label accuracy) | {a['label_accuracy']:.1%}{ci(a['label_accuracy_ci95'])} "
                    f"| {a['label_accuracy_always_no']:.1%} |")
        rows.append(f"| All tactics right at once, {name} (exact match) | {a['exact_match']:.1%}{ci(a['exact_match_ci95'])} "
                    f"| {a['exact_match_always_no']:.1%} |")
        b = a["any_tactic"]
        what = "manipulative or not" if level == "dialogue" else "uses any tactic"
        rows.append(f"| {name[0].upper() + name[1:]}: {what} (accuracy; F1 {b['f1']:.1%}) | {b['accuracy']:.1%}{ci(b.get('accuracy_ci95'))} "
                    f"| {b['majority_baseline']:.1%} |")
    return rows


def _accuracy_markdown(res: dict) -> list[str]:
    ci = _ci
    rows = _level_rows(lambda level: (res.get(level) or {}).get("accuracy"))
    g = res.get("genre") or {}
    if "accuracy" in g:
        rows.append(f"| Genre, 4 classes (accuracy) | {g['accuracy']:.1%}{ci(g.get('accuracy_ci95'))} | - |")
    for key, label in (("influence_vs_neutral", "Influence attempt vs neutral, every turn"),
                       ("sms_scam_detection", "SMS: scam or not")):
        b = g.get(key)
        if b:
            rows.append(f"| {label} (accuracy; F1 {b['f1']:.1%}) | {b['accuracy']:.1%} | {b['majority_baseline']:.1%} |")
    if not rows:
        return []
    out = ["## Accuracy-style measures", "",
           "Accuracy counts correct decisions, so it is high whenever most answers are \"no\". The last column is what a model",
           "that always gives the most common answer scores; read each accuracy against it, and the F1 tables above for the hard task.",
           "Thresholds here are the main ones, tuned on validation for F1.", "",
           "| Measure | Score (95% CI) | Always-most-common baseline |", "|---|---|---|", *rows, ""]
    op = res.get("accuracy_operating_point")
    if op:
        rows2 = _level_rows(lambda level: op.get(level))
        f1s = ", ".join(f"{lvl} macro-F1 {op[lvl]['macro_f1']:.3f}" for lvl in ("turn", "dialogue") if op.get(lvl))
        out += ["### Same scores, thresholds tuned on validation for accuracy", "",
                "A second, declared operating point: the cut-offs aim at the most correct yes/no decisions rather than",
                f"at F1. It trades recall for precision ({f1s} at these cut-offs).", "",
                "| Measure | Score (95% CI) | Always-most-common baseline |", "|---|---|---|", *rows2, ""]
    return out


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
    out += _accuracy_markdown(res)
    g = res["genre"]
    lo, hi = g["macro_f1_ci95"]
    out += ["## Genre (every test turn)", "", f"macro-F1 **{g['macro_f1']:.3f}** (95% CI {lo:.3f} to {hi:.3f}), n = {g['n']:,}", "",
            "| Genre | F1 |", "|---|---|"] + [f"| {k} | {v:.3f} |" for k, v in g["per_genre_f1"].items()] + [""]
    return "\n".join(out)
