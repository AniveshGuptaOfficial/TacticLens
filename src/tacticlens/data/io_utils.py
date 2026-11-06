"""Finding files and columns in downloaded datasets, whatever their exact names."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import pandas as pd

TABLE_EXT = (".csv", ".tsv", ".xlsx", ".xls", ".json", ".jsonl")


def find_file(directory: Path, patterns: Iterable[str] = ("*",), explicit: str | None = None) -> Path | None:
    """Return the explicit file if given, else the first file matching any pattern (in order)."""
    directory = Path(directory)
    if explicit:
        p = Path(explicit)
        p = p if p.is_absolute() else directory / p
        return p if p.exists() else None
    if not directory.exists():
        return None
    for pat in patterns:
        hits = sorted(
            p for p in directory.rglob(pat) if p.is_file() and p.suffix.lower() in TABLE_EXT
        )
        if hits:
            return hits[0]
    return None


def read_table(path: Path) -> pd.DataFrame:
    suf = path.suffix.lower()
    if suf == ".csv":
        for enc in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                return pd.read_csv(path, encoding=enc)
            except UnicodeDecodeError:
                continue
    if suf == ".tsv":
        return pd.read_csv(path, sep="\t")
    if suf in (".xlsx", ".xls"):
        return pd.read_excel(path)
    if suf == ".jsonl":
        with open(path, encoding="utf-8") as f:
            return pd.DataFrame([json.loads(line) for line in f if line.strip()])
    if suf == ".json":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            # {"data": [...]} or {id: {...}}
            for v in data.values():
                if isinstance(v, list):
                    return pd.DataFrame(v)
            return pd.DataFrame.from_dict(data, orient="index").reset_index(names="id")
        return pd.DataFrame(data)
    raise ValueError(f"unsupported file type: {path}")


def pick_column(df: pd.DataFrame, explicit: str | None, candidates: Iterable[str], required: bool = True) -> str | None:
    """Explicit name wins; else first candidate that matches a column, ignoring case and spaces."""
    if explicit:
        if explicit not in df.columns:
            raise KeyError(f"column {explicit!r} not found; columns are {list(df.columns)}")
        return explicit
    norm = {str(c).strip().lower().replace(" ", "_"): c for c in df.columns}
    for cand in candidates:
        key = cand.strip().lower().replace(" ", "_")
        if key in norm:
            return norm[key]
    if required:
        raise KeyError(f"none of {list(candidates)} found; columns are {list(df.columns)}")
    return None


def split_label_list(value) -> list[str]:
    """'Denial, Evasion' / ['Denial'] / NaN -> list of clean strings."""
    if value is None:
        return []
    if isinstance(value, float) and pd.isna(value):
        return []
    if isinstance(value, (list, tuple, set)):
        items = list(value)
    elif isinstance(value, dict):
        items = list(value.keys())
    else:
        s = str(value).strip()
        if s.startswith("[") and s.endswith("]"):
            try:
                items = json.loads(s.replace("'", '"'))
            except json.JSONDecodeError:
                items = s.strip("[]").split(",")
        else:
            items = s.replace(";", ",").split(",")
    out = []
    for it in items:
        t = str(it).strip().strip("'\"")
        if t and t.lower() not in ("nan", "none", "null", ""):
            out.append(t)
    return out
