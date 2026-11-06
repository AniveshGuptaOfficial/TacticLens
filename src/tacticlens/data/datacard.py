"""Data card (FR-DAT-08): counts per dataset, genre, source, split, role and tactic."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pandas as pd

from ..taxonomy.mapping import Taxonomy


def md_table(t: pd.DataFrame) -> str:
    """DataFrame -> markdown table, without needing the `tabulate` package."""
    head = [str(t.index.name or "")] + [str(c) for c in t.columns]
    rows = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for idx, row in t.iterrows():
        rows.append("| " + " | ".join([str(idx)] + [f"{v:,}" if isinstance(v, int) else str(v) for v in row]) + " |")
    return "\n".join(rows)


def build_datacard(records: list[dict], tax: Taxonomy) -> str:
    df = pd.DataFrame(records)
    df["words"] = df["text"].str.split().str.len()
    dlg = df.drop_duplicates("dialogue_id")
    out = ["# Data card", "", f"Turns: {len(df):,} - Dialogues: {dlg.shape[0]:,}", ""]

    def section(title: str, t: pd.DataFrame) -> None:
        out.extend([f"## {title}", "", md_table(t), ""])

    section("Dialogues per dataset and split", pd.crosstab(dlg["dataset"], dlg["split"], margins=True))
    section("Dialogues per genre and source", pd.crosstab(dlg["genre"], dlg["source"], margins=True))
    section("Turns per dataset and role", pd.crosstab(df["dataset"], df["role"], margins=True))
    section("Turn length in words", df.groupby("dataset")["words"].describe()[["mean", "50%", "max"]].round(1))

    turn = Counter(t for ts in df.loc[df["label_level"] == "turn", "tactics"] for t in (ts or []))
    dial = Counter(t for m in dlg.loc[dlg["label_level"] == "dialogue", "meta"] for t in (m.get("dialogue_tactics") or []))
    out += ["## Tactic counts", "", "| Tactic | Name | Group | Turn-level labels | Dialogue-level labels |", "|---|---|---|---|---|"]
    for tid in tax.all_label_ids:
        out.append(f"| {tid} | {tax.name(tid)} | {tax.group(tid) or 'extra'} | {turn.get(tid, 0):,} | {dial.get(tid, 0):,} |")
    lab = df[df["label_level"] == "turn"]
    n_none = int(lab["tactics"].apply(lambda x: not x).sum())
    out += ["", f"Turn-level labelled turns: {len(lab):,} (with no tactic: {n_none:,}).", ""]
    return "\n".join(out)


def write_datacard(records: list[dict], tax: Taxonomy, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_datacard(records, tax), encoding="utf-8")
    return path
