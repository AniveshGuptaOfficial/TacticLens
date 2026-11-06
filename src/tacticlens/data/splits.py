"""Dialogue-level splits (FR-DAT-06) and leave-one-genre-out splits (FR-DAT-07).

Splits are made per dialogue, never per turn, so no conversation leaks across splits.
Stratified by (dataset, genre), seed 42.
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np

INFLUENCE_GENRES = ("persuasion", "manipulation", "scam")


def dialogue_splits(
    dialogues: dict[str, tuple[str, str]], ratios: dict[str, float], seed: int = 42
) -> dict[str, str]:
    """dialogues: {dialogue_id: (dataset, genre)} -> {dialogue_id: 'train'|'val'|'test'}."""
    strata: dict[tuple[str, str], list[str]] = defaultdict(list)
    for did, key in dialogues.items():
        strata[key].append(did)
    rng = np.random.default_rng(seed)
    out: dict[str, str] = {}
    tr, va = ratios["train"], ratios["val"]
    for key in sorted(strata):
        ids = sorted(strata[key])
        rng.shuffle(ids)
        n = len(ids)
        n_tr = int(round(n * tr))
        n_va = int(round(n * va))
        if n >= 3:
            n_tr = min(max(n_tr, 1), n - 2)
            n_va = max(n_va, 1)
        for i, did in enumerate(ids):
            out[did] = "train" if i < n_tr else ("val" if i < n_tr + n_va else "test")
    return out


def logo_splits(split: dict[str, str], genre_of: dict[str, str]) -> dict[str, dict[str, list[str]]]:
    """For each influence genre G: train/val = other genres' train/val (+ neutral), test = G's test.

    Returns {G: {'train': [...], 'val': [...], 'test': [...]}}.
    """
    out = {}
    for g in INFLUENCE_GENRES:
        parts = {"train": [], "val": [], "test": []}
        for did, s in split.items():
            dg = genre_of[did]
            if dg == g:
                if s == "test":
                    parts["test"].append(did)
            elif s in ("train", "val"):
                parts[s].append(did)
        out[g] = {k: sorted(v) for k, v in parts.items()}
    return out
