"""Cross-genre transfer (O4): train without one genre, test on it.

For each influence genre G (persuasion = P4G, manipulation = MentalManip, scam = PsyScam +
scam SMS) the leave-one-genre-out split from `prepare` trains and tunes on the other genres
(plus neutral) and tests on G's test dialogues. A tactic can only transfer if the training
genres label it, so scores are macro-F1 over the *shared* tactics: those with positives in
G's test set at the level G is scored on (turn for P4G/PsyScam, dialogue for MentalManip)
and with labels somewhere in the training genres.

The in-domain reference is the main model (trained on all genres) scored on the same test
dialogues and the same shared tactics, from its saved predictions. The gap between the two is
the transfer cost.

clean_sources (default): the split from `prepare` keeps every dataset's *neutral* dialogues in
training, so e.g. MentalManip's non-manipulative conversations stay in when manipulation is
held out, and the model learns "MentalManip-style talk has no tactics". With clean_sources every
record from a dataset that appears in the held-out test set is dropped from train/val too.

Two scores per run: macro-F1 at the tuned thresholds, and macro AUC-PR (threshold-free). A big
F1 drop with a small AUC-PR drop means the model still ranks the turns right but its thresholds,
tuned on the other genres, do not fit the new genre (calibration), not that it cannot see the
tactic at all.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import average_precision_score, f1_score

from ..eval.metrics import bootstrap_ci
from ..models.common import TACTICS, dialogue_labels, dialogue_pool, threshold_pair, turn_labels

LEVEL = {"persuasion": "turn", "scam": "turn", "manipulation": "dialogue"}


def logo_records(records: list[dict], logo: dict, genre: str, clean_sources: bool = True) -> list[dict]:
    split_of = {}
    for s in ("train", "val", "test"):
        for did in logo[genre][s]:
            split_of[did] = s
    out = [{**r, "split": split_of[r["dialogue_id"]]} for r in records if r["dialogue_id"] in split_of]
    if clean_sources:
        held = {r["dataset"] for r in out if r["split"] == "test" and r["label_level"] != "none"}
        out = [r for r in out if r["split"] == "test" or r["dataset"] not in held]
    return out


def trained_tactics(train: list[dict]) -> set[str]:
    have = np.zeros(len(TACTICS), dtype=int)
    for r in train:
        if r["label_level"] == "turn":
            have |= turn_labels(r)
        elif r["label_level"] == "dialogue":
            have |= dialogue_labels(r)
    return {t for t, h in zip(TACTICS, have) if h}


def level_arrays(test: list[dict], S: np.ndarray, th, level: str):
    """(Y, P, scores, groups) at one level: turn rows with turn labels, or max-pooled dialogues."""
    th_t, th_d = threshold_pair(th)
    if level == "turn":
        m = np.array([r["label_level"] == "turn" for r in test])
        if not m.any():
            z = np.zeros((0, len(TACTICS)))
            return z, z, z, np.array([])
        Y = np.stack([turn_labels(r) for r, k in zip(test, m) if k])
        return Y, (S[m] >= th_t).astype(int), S[m], np.array([r["dialogue_id"] for r, k in zip(test, m) if k])
    dids, pooled, Y = dialogue_pool(test, S)
    return Y, (pooled >= th_d).astype(int), pooled, np.array(dids)


def shared_macro(Y, P, Sc, groups, tactics: list[str], n_boot: int = 1000, seed: int = 42) -> dict:
    cols = [TACTICS.index(t) for t in tactics]
    if not cols or len(Y) == 0:
        return {"macro_f1": float("nan"), "ci": (float("nan"), float("nan")), "per_tactic": {},
                "auc_pr": float("nan"), "per_tactic_ap": {}}

    def f(idx):
        return f1_score(Y[idx][:, cols], P[idx][:, cols], average="macro", zero_division=0)

    full = np.arange(len(Y))
    per = f1_score(Y[:, cols], P[:, cols], average=None, zero_division=0)
    aps = [float(average_precision_score(Y[:, c], Sc[:, c])) for c in cols]
    return {"macro_f1": float(f(full)), "ci": bootstrap_ci(f, groups, n_boot=n_boot, seed=seed),
            "per_tactic": dict(zip(tactics, map(float, per))),
            "auc_pr": float(np.mean(aps)), "per_tactic_ap": dict(zip(tactics, aps))}


def evaluate_genre(genre: str, test: list[dict], S: np.ndarray, th, train_tactics: set[str], n_boot: int = 1000) -> dict:
    level = LEVEL[genre]
    Y, P, Sc, g = level_arrays(test, S, th, level)
    present = {TACTICS[j] for j in range(len(TACTICS)) if len(Y) and Y[:, j].sum() > 0}
    shared = sorted(present & train_tactics, key=lambda t: int(t[1:]))
    res = shared_macro(Y, P, Sc, g, shared, n_boot=n_boot)
    res.update({"level": level, "shared": shared, "not_in_training": sorted(present - train_tactics)})
    return res


def report_markdown(rows: list[dict], names: dict[str, str], clean_sources: bool = True) -> str:
    lines = ["# Cross-genre transfer (leave one genre out)", "",
             "Macro-F1 over the tactics the held-out genre shares with the training genres, 95% CI over dialogues;",
             "AUC-PR = threshold-free macro average precision over the same tactics.",
             "In-domain = the main model (trained on all genres) on the same test dialogues and tactics.",
             ("Training excludes every dataset that appears in the held-out test set (also its neutral dialogues)."
              if clean_sources else "Training keeps the held-out datasets' neutral dialogues (split as made by `prepare`)."), "",
             "| Held-out genre | Level | Model | Shared tactics | F1 in-domain | F1 transfer | AUC-PR in-domain | AUC-PR transfer |",
             "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        i, o = r["in_domain"], r["transfer"]
        lines.append(f"| {r['genre']} | {o['level']} | {r['model']} | {', '.join(o['shared']) or '-'} | "
                     f"{i['macro_f1']:.3f} ({i['ci'][0]:.3f} to {i['ci'][1]:.3f}) | "
                     f"{o['macro_f1']:.3f} ({o['ci'][0]:.3f} to {o['ci'][1]:.3f}) | "
                     f"{i['auc_pr']:.3f} | {o['auc_pr']:.3f} |")
    lines += ["", "## Per tactic (F1 in-domain -> transfer; AUC-PR in-domain -> transfer)", ""]
    for r in rows:
        i, o = r["in_domain"], r["transfer"]
        parts = [f"{t} {names.get(t, '')}: F1 {i['per_tactic'].get(t, float('nan')):.2f} -> {o['per_tactic'].get(t, float('nan')):.2f}, "
                 f"AP {i['per_tactic_ap'].get(t, float('nan')):.2f} -> {o['per_tactic_ap'].get(t, float('nan')):.2f}"
                 for t in o["shared"]]
        miss = f" (not labelled in training: {', '.join(o['not_in_training'])})" if o["not_in_training"] else ""
        lines.append(f"- **{r['genre']}, {r['model']}**: " + ("; ".join(parts) or "-") + miss)
    return "\n".join(lines) + "\n"
