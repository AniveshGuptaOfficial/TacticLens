"""Check set for two annotators (FR-TAX-05) and Cohen's kappa (FR-TAX-06, AC-01).

The check set is 300 turns, stratified so each tactic gets up to 30 items where the data allows,
plus turns with no tactic and turns from every genre. Annotators see the turn and its two
previous turns, never the source labels (those go to a separate key file).
"""

from __future__ import annotations

import csv
import random
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

from .mapping import Taxonomy

YES = {"1", "x", "y", "yes", "true", "t", "✓"}


def _source_tactics(r: dict) -> list[str]:
    if r["label_level"] == "turn":
        return list(r["tactics"] or [])
    if r["label_level"] == "dialogue":
        return list(r["meta"].get("dialogue_tactics") or [])
    return []


def select_checkset(records: list[dict], tax: Taxonomy, n: int = 300, per_tactic: int = 30, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    pool = [r for r in records if r["split"] in ("val", "test")] or records
    by_tactic: dict[str, list[dict]] = defaultdict(list)
    for r in pool:
        for t in _source_tactics(r):
            by_tactic[t].append(r)
    chosen: dict[tuple, dict] = {}
    for t in tax.all_label_ids:
        cands = by_tactic.get(t, [])
        rng.shuffle(cands)
        for r in cands[:per_tactic]:
            chosen[(r["dialogue_id"], r["turn_id"])] = r
    # fill the rest evenly by genre (covers no-tactic turns and unlabelled genres)
    by_genre: dict[str, list[dict]] = defaultdict(list)
    for r in pool:
        if (r["dialogue_id"], r["turn_id"]) not in chosen:
            by_genre[r["genre"]].append(r)
    for g in by_genre:
        rng.shuffle(by_genre[g])
    genres = sorted(by_genre)
    i = 0
    while len(chosen) < n and any(by_genre.values()):
        g = genres[i % len(genres)]
        if by_genre[g]:
            r = by_genre[g].pop()
            chosen[(r["dialogue_id"], r["turn_id"])] = r
        i += 1
    items = list(chosen.values())[:n]
    rng.shuffle(items)
    return items


def export_checkset(records: list[dict], tax: Taxonomy, out_dir: Path, n: int = 300, seed: int = 42) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    items = select_checkset(records, tax, n=n, seed=seed)
    by_dlg: dict[str, dict[int, dict]] = defaultdict(dict)
    for r in records:
        by_dlg[r["dialogue_id"]][r["turn_id"]] = r
    label_cols = tax.all_label_ids
    head = ["item_id", "dataset", "speaker", "context", "text"] + label_cols + ["role", "evidence", "notes"]
    paths = []
    for who in ("A", "B"):
        p = out_dir / f"checkset_{who}.csv"
        with open(p, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(head)
            for k, r in enumerate(items):
                ctx = " | ".join(
                    f"{by_dlg[r['dialogue_id']][t]['speaker']}: {by_dlg[r['dialogue_id']][t]['text']}"
                    for t in range(max(0, r["turn_id"] - 2), r["turn_id"]) if t in by_dlg[r["dialogue_id"]]
                )
                w.writerow([f"c{k:03d}", r["dataset"], r["speaker"], ctx, r["text"]] + [""] * len(label_cols) + ["", "", ""])
        paths.append(p)
    key = out_dir / "checkset_key.csv"
    with open(key, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["item_id", "dialogue_id", "turn_id", "genre", "label_level", "source_tactics", "role"])
        for k, r in enumerate(items):
            w.writerow([f"c{k:03d}", r["dialogue_id"], r["turn_id"], r["genre"], r["label_level"], ";".join(_source_tactics(r)), r["role"]])
    paths.append(key)
    return paths


def _binary(series: pd.Series) -> np.ndarray:
    return series.fillna("").astype(str).str.strip().str.lower().isin(YES).to_numpy().astype(int)


def kappa_report(path_a: Path, path_b: Path, tax: Taxonomy) -> pd.DataFrame:
    a = pd.read_csv(path_a, dtype=str, encoding="utf-8-sig").set_index("item_id")
    b = pd.read_csv(path_b, dtype=str, encoding="utf-8-sig").set_index("item_id")
    common = a.index.intersection(b.index)
    a, b = a.loc[common], b.loc[common]
    rows = []
    for t in tax.all_label_ids:
        if t not in a or t not in b:
            continue
        ya, yb = _binary(a[t]), _binary(b[t])
        both = int(((ya == 1) & (yb == 1)).sum())
        if ya.sum() + yb.sum() == 0:
            k = float("nan")  # tactic never used by either annotator
        elif (ya == yb).all():
            k = 1.0
        else:
            k = float(cohen_kappa_score(ya, yb))
        rows.append({"tactic": t, "name": tax.name(t), "A_yes": int(ya.sum()), "B_yes": int(yb.sum()), "both_yes": both, "kappa": round(k, 3)})
    if "role" in a and "role" in b:
        ra = a["role"].fillna("").str.strip().str.lower()
        rb = b["role"].fillna("").str.strip().str.lower()
        mask = (ra != "") & (rb != "")
        if mask.sum() > 0:
            k = 1.0 if (ra[mask] == rb[mask]).all() else cohen_kappa_score(ra[mask], rb[mask])
            rows.append({"tactic": "role", "name": "Role (actor/target)", "A_yes": int(mask.sum()), "B_yes": int(mask.sum()), "both_yes": int((ra[mask] == rb[mask]).sum()), "kappa": round(float(k), 3)})
    df = pd.DataFrame(rows)
    tac = df[df["tactic"].str.startswith(("T", "X"))]["kappa"].dropna()
    overall = {"tactic": "overall", "name": "Mean over tactics used", "A_yes": None, "B_yes": None, "both_yes": None,
               "kappa": round(float(tac.mean()), 3) if len(tac) else float("nan")}
    return pd.concat([df, pd.DataFrame([overall])], ignore_index=True)
