"""Hand labels: merge the two check-set annotators, load hand-labelled turns, export new batches.

Hand labels never edit the original datasets' files. They are kept in data/annotation/ and joined
to the records by (dialogue_id, turn_id):

  checkset_agreed.csv   made by `cli agree` from checkset_A/B.csv: a tactic is 1 when both
                        annotators marked it, blank when neither did, and "?" when they disagree.
                        Resolve every "?" to 1 or blank (talk it through), then save.
                        These items come from the val/test splits, so they are used ONLY to
                        evaluate (`cli manual-eval`), never to train.
  manual/*.csv          extra batches made by `cli label-batch` (train-split turns, with their
                        dialogue_id and turn_id). Once labelled they replace the source label of
                        that training turn in `cli prepare` (meta["manual"] = True).
"""

from __future__ import annotations

import csv
import random
from collections import defaultdict
from pathlib import Path

import pandas as pd

from .annotation import YES
from .mapping import Taxonomy

ANN_DIR = Path("data") / "annotation"
UNSURE = "?"


def _cell(v) -> str:
    v = "" if pd.isna(v) else str(v).strip().lower()
    return "1" if v in YES else (UNSURE if v == UNSURE else "")


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")


def agree_checkset(path_a: Path, path_b: Path, out: Path, tax: Taxonomy) -> dict:
    """Merge two annotators. Writes `out` (agreed labels, "?" where they disagree) and returns counts."""
    a, b = _read(path_a).set_index("item_id"), _read(path_b).set_index("item_id")
    common = [i for i in a.index if i in b.index]
    labels = [t for t in tax.all_label_ids if t in a.columns and t in b.columns]
    rows, n_dis, items_dis = [], 0, 0
    for i in common:
        ra, rb = a.loc[i], b.loc[i]
        row = {"item_id": i, "dataset": ra.get("dataset", ""), "speaker": ra.get("speaker", ""),
               "context": ra.get("context", ""), "text": ra.get("text", "")}
        dis = 0
        for t in labels:
            va, vb = _cell(ra[t]) == "1", _cell(rb[t]) == "1"
            row[t] = "1" if va and vb else (UNSURE if va != vb else "")
            dis += va != vb
        role_a, role_b = ra.get("role", "").strip().lower(), rb.get("role", "").strip().lower()
        row["role"] = role_a if role_a == role_b else (role_a or role_b if not (role_a and role_b) else UNSURE)
        row["evidence_A"], row["evidence_B"] = ra.get("evidence", ""), rb.get("evidence", "")
        row["notes"] = " | ".join(x for x in (ra.get("notes", ""), rb.get("notes", "")) if x)
        rows.append(row)
        n_dis += dis
        items_dis += dis > 0
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8-sig")
    return {"items": len(rows), "items_with_disagreement": items_dis, "tactic_disagreements": n_dis}


def _labels_of(row: pd.Series, labels: list[str], where: str) -> list[str]:
    out = []
    for t in labels:
        v = _cell(row.get(t, ""))
        if v == UNSURE:
            raise ValueError(f"{where}: {t} is still '?'; resolve it to 1 or blank first")
        if v == "1":
            out.append(t)
    return out


def load_manual(root: Path, tax: Taxonomy) -> dict[tuple[str, int], dict]:
    """{(dialogue_id, turn_id): {"tactics", "role", "set" ("check" | "batch"), "file"}}."""
    d = root / ANN_DIR
    labels = tax.all_label_ids
    out: dict[tuple[str, int], dict] = {}
    agreed, key = d / "checkset_agreed.csv", d / "checkset_key.csv"
    if agreed.exists() and key.exists():
        k = _read(key).set_index("item_id")
        for _, row in _read(agreed).iterrows():
            if row["item_id"] not in k.index:
                continue
            src = k.loc[row["item_id"]]
            out[(src["dialogue_id"], int(src["turn_id"]))] = {
                "tactics": _labels_of(row, labels, f"checkset_agreed.csv {row['item_id']}"),
                "role": row.get("role", "").strip().lower(), "set": "check", "file": agreed.name}
    for p in sorted((d / "manual").glob("*.csv")) if (d / "manual").exists() else []:
        df = _read(p)
        if not {"dialogue_id", "turn_id"} <= set(df.columns):
            raise ValueError(f"{p.name}: needs dialogue_id and turn_id columns (made by `cli label-batch`)")
        for _, row in df.iterrows():
            if str(row.get("done", "")).strip().lower() not in YES:
                continue  # only rows the annotator marked as done
            out[(row["dialogue_id"], int(row["turn_id"]))] = {
                "tactics": _labels_of(row, labels, f"{p.name} {row.get('item_id', '')}"),
                "role": row.get("role", "").strip().lower(), "set": "batch", "file": p.name}
    return out


def apply_manual(records: list[dict], manual: dict[tuple[str, int], dict]) -> int:
    """Replace the labels of TRAIN-split turns that have hand labels. Val/test turns are left alone,
    so hand labels there stay a clean test. Returns how many turns changed."""
    n = 0
    for r in records:
        m = manual.get((r["dialogue_id"], r["turn_id"]))
        if m is None or r.get("split") != "train":
            continue
        r["meta"] = dict(r.get("meta") or {}, manual=True, source_tactics=r.get("tactics"),
                         source_label_level=r["label_level"])
        r["tactics"], r["label_level"] = list(m["tactics"]), "turn"
        n += 1
    return n


def select_batch(records: list[dict], tax: Taxonomy, n: int = 200, exclude: set | None = None,
                 seed: int = 42) -> list[dict]:
    """Train-split turns where hand labels help most:
      1/2  MentalManip turns from conversations labelled with guilt, distortion, threat or flattery
           (the dialogue label says the tactic is there, not which turn)
      1/4  SMS (smishing and spam, human and LLM): no tactic labels at all
      1/4  persuader turns from the PersuasionForGood dialogues without strategy labels
    """
    rng = random.Random(seed)
    exclude = exclude or set()
    pool = [r for r in records if r["split"] == "train" and (r["dialogue_id"], r["turn_id"]) not in exclude
            and len(r["text"].split()) >= 3]
    want_mm = {"T8", "T10", "T9", "T7"}
    mm = [r for r in pool if r["dataset"] == "mentalmanip"
          and want_mm & set((r.get("meta") or {}).get("dialogue_tactics") or [])]
    sms = [r for r in pool if r["dataset"].startswith("sms") and (r.get("meta") or {}).get("sms_label") in ("smishing", "spam")]
    p4g = [r for r in pool if r["dataset"] == "p4g" and r["label_level"] == "none" and r["role"] == "actor"]
    picked: list[dict] = []
    for part, q in ((mm, n // 2), (sms, n // 4), (p4g, n - n // 2 - n // 4)):
        rng.shuffle(part)
        if part is mm:  # spread over conversations: at most 2 turns per dialogue
            per: dict[str, int] = defaultdict(int)
            got = 0
            for r in part:
                if got >= q:
                    break
                if per[r["dialogue_id"]] < 2:
                    picked.append(r)
                    per[r["dialogue_id"]] += 1
                    got += 1
        else:
            picked += part[:q]
    rng.shuffle(picked)
    return picked


def export_batch(records: list[dict], tax: Taxonomy, root: Path, n: int = 200, seed: int = 42) -> Path:
    d = root / ANN_DIR / "manual"
    d.mkdir(parents=True, exist_ok=True)
    have = set(load_manual(root, tax)) | {(r["dialogue_id"], r["turn_id"]) for p in d.glob("*.csv")
                                          for r in _read(p)[["dialogue_id", "turn_id"]].astype({"turn_id": int}).to_dict("records")}
    items = select_batch(records, tax, n=n, exclude=have, seed=seed + len(list(d.glob("*.csv"))))
    by_dlg: dict[str, dict[int, dict]] = defaultdict(dict)
    for r in records:
        by_dlg[r["dialogue_id"]][r["turn_id"]] = r
    k = len(list(d.glob("batch_*.csv"))) + 1
    path = d / f"batch_{k:02d}.csv"
    labels = tax.all_label_ids
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["item_id", "dataset", "speaker", "context", "text"] + labels
                   + ["role", "evidence", "notes", "done", "dialogue_id", "turn_id"])
        for i, r in enumerate(items):
            dl = by_dlg[r["dialogue_id"]]
            ctx = " | ".join(f"{dl[t]['speaker']}: {dl[t]['text']}" for t in range(max(0, r["turn_id"] - 2), r["turn_id"]) if t in dl)
            w.writerow([f"b{k:02d}_{i:03d}", r["dataset"], r["speaker"], ctx, r["text"]] + [""] * len(labels)
                       + ["", "", "", "", r["dialogue_id"], r["turn_id"]])
    return path
