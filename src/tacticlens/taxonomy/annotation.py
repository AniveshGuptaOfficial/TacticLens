"""Check set for two annotators (FR-TAX-05) and Cohen's kappa (FR-TAX-06, AC-01).

The check set is 300 turns: up to 16 per tactic, 60 SMS (human and LLM-written), 30 turns with
no source tactic, the rest spread over genres (see select_checkset). Annotators see the turn and its two
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


def select_checkset(records: list[dict], tax: Taxonomy, n: int = 300, per_tactic: int = 16, n_sms: int = 60,
                    n_none: int = 30, seed: int = 42) -> list[dict]:
    """Val/test turns in three parts, so the check set tests what the thesis claims:

      tactics  up to `per_tactic` turns per source tactic (rare tactics still get items)
      SMS      `n_sms` messages, half Mishra-Soni (human) and half LLM-generated, mostly smishing
               plus some spam and ham; they have no source labels and are what settles the
               human-vs-LLM tactic profiles
      none     `n_none` turns with no source tactic (neutral talk, persuadee replies), so
               annotators also see turns where the right answer is "nothing"
    and the rest filled evenly by genre.
    """
    rng = random.Random(seed)
    pool = [r for r in records if r["split"] in ("val", "test")] or records
    n_sms, n_none = min(n_sms, n // 5), min(n_none, n // 10)  # keep the parts in proportion for small n
    per_tactic = min(per_tactic, max(1, (n - n_sms - n_none) // max(1, len(tax.all_label_ids))))
    chosen: dict[tuple, dict] = {}

    def take(r):
        chosen[(r["dialogue_id"], r["turn_id"])] = r

    def free(rs):
        return [r for r in rs if (r["dialogue_id"], r["turn_id"]) not in chosen]

    # 1. SMS, human and LLM, by label: 1/2 smishing, 1/4 spam, 1/4 ham
    for ds in ("sms_human", "sms_llm"):
        want = n_sms // 2
        by_lab: dict[str, list[dict]] = defaultdict(list)
        for r in pool:
            if r["dataset"] == ds:
                by_lab[(r.get("meta") or {}).get("sms_label", "")].append(r)
        for lab in by_lab:
            rng.shuffle(by_lab[lab])
        quota = {"smishing": want // 2, "spam": want // 4}
        quota["ham"] = want - sum(quota.values())
        for lab, q in quota.items():
            for r in by_lab.get(lab, [])[:q]:
                take(r)
        rest = [r for lab in by_lab for r in by_lab[lab]]
        rng.shuffle(rest)
        got = sum(1 for r in chosen.values() if r["dataset"] == ds)
        for r in free(rest)[:max(0, want - got)]:
            take(r)
    # 2. per tactic (labelled datasets)
    by_tactic: dict[str, list[dict]] = defaultdict(list)
    for r in pool:
        for t in _source_tactics(r):
            by_tactic[t].append(r)
    for t in tax.all_label_ids:
        cands = by_tactic.get(t, [])
        rng.shuffle(cands)
        for r in free(cands)[:per_tactic]:
            take(r)
    # 3. labelled turns with no tactic
    none = [r for r in pool if r["label_level"] in ("turn", "dialogue") and not _source_tactics(r)
            and not r["dataset"].startswith("sms")]
    rng.shuffle(none)
    for r in free(none)[:n_none]:
        take(r)
    # 4. fill the rest evenly by genre
    by_genre: dict[str, list[dict]] = defaultdict(list)
    for r in free(pool):
        by_genre[r["genre"]].append(r)
    for g in by_genre:
        rng.shuffle(by_genre[g])
    genres = sorted(by_genre)
    i = 0
    while len(chosen) < n and any(by_genre.values()):
        g = genres[i % len(genres)]
        if by_genre[g]:
            take(by_genre[g].pop())
        i += 1
    items = list(chosen.values())
    rng.shuffle(items)
    return items[:n]


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
