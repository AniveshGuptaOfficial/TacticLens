"""Grounding audit (O5): does a model's tactic score rest on the annotated evidence?

Uses the test turns that carry evidence spans: PsyScam (quotes the annotators gave for each
technique) and annotated P4G (the sentences each strategy label covers). For every
(turn, gold tactic with evidence) the model scores four versions of the turn, each as its
own one-turn dialogue:

  full      the turn as written
  removed   the evidence for that tactic cut out
  only      just the evidence
  random    the same number of words cut out at random, away from the evidence (2 draws)

and we report, after ERASER (DeYoung et al., 2020):
  comprehensiveness   p(full) - p(removed)    high = the score needed the evidence
  sufficiency         p(full) - p(only)       low  = the evidence alone is enough
  random control      p(full) - p(random)     what cutting the same amount of other text does
  evidence effect     comprehensiveness - random control (paired)
A model that keys on shortcuts (dataset style, length) shows comprehensiveness close to the
random control. "detected" restricts to cases the model flagged (p(full) >= its threshold).
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

from ..models.common import TACTICS
from .common import boot_mean, fmt_ci, scores, standalone

_WORD = re.compile(r"\S+")


def evidence_cases(records: list[dict]) -> list[tuple[dict, str, list[tuple[int, int]]]]:
    """(record, tactic, [(start, end), ...]) for each gold tactic that has evidence spans."""
    out = []
    for r in records:
        if r.get("label_level") != "turn" or not r.get("spans"):
            continue
        by_t: dict[str, list[tuple[int, int]]] = {}
        for s in r["spans"]:
            if s["tactic"] in TACTICS and s["tactic"] in (r.get("tactics") or []):
                by_t.setdefault(s["tactic"], []).append((s["start"], s["end"]))
        for t, spans in sorted(by_t.items()):
            out.append((r, t, sorted(set(spans))))
    return out


def _cut(text: str, spans: list[tuple[int, int]]) -> str:
    keep, pos = [], 0
    for s, e in sorted(spans):
        if s > pos:
            keep.append(text[pos:s])
        pos = max(pos, e)
    keep.append(text[pos:])
    return re.sub(r"\s+", " ", " ".join(keep)).strip()


def _only(text: str, spans: list[tuple[int, int]]) -> str:
    return re.sub(r"\s+", " ", " ... ".join(text[s:e] for s, e in sorted(spans))).strip()


def _random_cut(text: str, spans: list[tuple[int, int]], rng: np.random.Generator) -> str | None:
    """Cut a run of words as long as the evidence, overlapping it as little as possible."""
    words = [(m.start(), m.end()) for m in _WORD.finditer(text)]
    in_ev = np.array([any(s < we and ws < e for s, e in spans) for ws, we in words], dtype=bool)
    k = int(in_ev.sum())
    if k == 0 or k >= len(words):
        return None
    starts = np.arange(0, len(words) - k + 1)
    overlap = np.array([in_ev[i:i + k].sum() for i in starts])
    best = starts[overlap == overlap.min()]
    i = int(rng.choice(best))
    return _cut(text, [(words[i][0], words[i + k - 1][1])])


def audit(model, th_turn: np.ndarray, test: list[dict], n_random: int = 2, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    cases = evidence_cases(test)
    base, texts, owner = [], [], []
    for ci, (r, t, spans) in enumerate(cases):
        removed = _cut(r["text"], spans)
        variants = [("full", r["text"]), ("removed", removed or "."), ("only", _only(r["text"], spans) or ".")]
        for k in range(n_random):
            rc = _random_cut(r["text"], spans, rng)
            if rc:
                variants.append((f"random{k}", rc))
        for name, txt in variants:
            base.append(r)
            texts.append(txt)
            owner.append((ci, name))
    S = scores(model, standalone(base, texts, tag="g"))
    rows: dict[int, dict] = {}
    for (ci, name), s in zip(owner, S):
        r, t, spans = cases[ci]
        row = rows.setdefault(ci, {"dataset": r["dataset"], "dialogue_id": r["dialogue_id"], "turn_id": r["turn_id"],
                                   "tactic": t, "ev_chars": sum(e - s_ for s_, e in spans), "chars": len(r["text"])})
        row[f"p_{name}"] = float(s[TACTICS.index(t)])
    df = pd.DataFrame(list(rows.values()))
    if df.empty:
        return df
    rand_cols = [c for c in df.columns if c.startswith("p_random")]
    df["p_random"] = df[rand_cols].mean(axis=1) if rand_cols else np.nan
    df["comprehensiveness"] = df["p_full"] - df["p_removed"]
    df["sufficiency"] = df["p_full"] - df["p_only"]
    df["random_control"] = df["p_full"] - df["p_random"]
    df["evidence_effect"] = df["comprehensiveness"] - df["random_control"]
    df["detected"] = [p >= th_turn[TACTICS.index(t)] for p, t in zip(df["p_full"], df["tactic"])]
    df["flip_removed"] = df["detected"] & np.array(
        [p < th_turn[TACTICS.index(t)] for p, t in zip(df["p_removed"], df["tactic"])])
    df["flip_random"] = df["detected"] & np.array(
        [(p < th_turn[TACTICS.index(t)]) if p == p else False for p, t in zip(df["p_random"], df["tactic"])])
    return df


METRICS = ("comprehensiveness", "random_control", "evidence_effect", "sufficiency")


def summarize(df: pd.DataFrame, model_name: str, n_boot: int = 1000) -> list[dict]:
    out = []
    for subset in ("all", "detected"):
        d0 = df if subset == "all" else df[df["detected"]]
        for ds in ["all", *sorted(d0["dataset"].unique())]:
            d = d0 if ds == "all" else d0[d0["dataset"] == ds]
            d = d.dropna(subset=["p_random"])
            if d.empty:
                continue
            row = {"model": model_name, "cases": subset, "dataset": ds, "n": len(d)}
            g = d["dialogue_id"].to_numpy()
            for m in METRICS:
                row[m] = boot_mean(d[m].to_numpy(), g, n_boot=n_boot)
            det = d[d["detected"]]
            row["flip_removed"] = float(det["flip_removed"].mean()) if len(det) else float("nan")
            row["flip_random"] = float(det["flip_random"].mean()) if len(det) else float("nan")
            out.append(row)
    return out


def report_markdown(rows: list[dict], per_tactic: pd.DataFrame) -> str:
    lines = ["# Grounding audit (evidence spans: PsyScam quotes, P4G strategy sentences; test split)", "",
             "Scores are drops in the model's probability for the gold tactic, mean (95% CI over dialogues).",
             "Comprehensiveness: evidence cut out. Random control: the same number of other words cut out.",
             "Evidence effect = comprehensiveness - random control (> 0 means the evidence matters more than other text).",
             "Sufficiency: evidence alone (lower is better). Flips: share of detected cases that fall below threshold.", ""]
    for subset, title in (("all", "All evidence cases"), ("detected", "Cases the model detected")):
        lines += [f"## {title}", "",
                  "| Model | Dataset | n | Comprehensiveness | Random control | Evidence effect | Sufficiency | Flip (evidence) | Flip (random) |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for r in rows:
            if r["cases"] != subset:
                continue
            lines.append(f"| {r['model']} | {r['dataset']} | {r['n']} | " + " | ".join(fmt_ci(*r[m]) for m in METRICS)
                         + f" | {r['flip_removed']:.2f} | {r['flip_random']:.2f} |")
        lines.append("")
    if not per_tactic.empty:
        cols = list(per_tactic.columns)
        lines += ["## Evidence effect per tactic (all cases, mean)", "",
                  "| Tactic | " + " | ".join(map(str, cols)) + " |", "|---|" + "---|" * len(cols)]
        for t, row in per_tactic.iterrows():
            lines.append(f"| {t} | " + " | ".join("-" if v != v else f"{v:.3f}" for v in row) + " |")
        lines.append("")
    return "\n".join(lines)


def per_tactic_table(dfs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Rows = tactics, columns = models, cells = mean evidence effect (n in brackets in the index)."""
    cols = {}
    for name, df in dfs.items():
        if not df.empty:
            cols[name] = df.dropna(subset=["p_random"]).groupby("tactic")["evidence_effect"].mean()
    if not cols:
        return pd.DataFrame()
    tab = pd.DataFrame(cols)
    return tab.loc[sorted(tab.index, key=lambda t: int(t[1:]))]
