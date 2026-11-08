"""Human- vs LLM-written scam SMS (O6): which tactics does each use, and how often?

Messages: Mishra-Soni smishing SMS (human) vs the locally generated set (qwen2.5:3b,
llama3.2:3b, gemma2:2b), same label (smishing by default). For every message the final model
says which tactics it uses (score >= its turn threshold). We compare the share of messages
using each tactic, with a 95% bootstrap CI on the difference, Fisher's exact test and Holm
correction across tactics, and repeat it per generator model.

A model-free check runs alongside: the share of messages with at least one cue word from
configs/lexicon.yaml for each tactic. Agreement between the two makes the result less likely
to be an artefact of the model.

Caveat to report: no SMS carries tactic labels, so the model's tactic heads are used out of
domain here (they learned tactics from P4G, MentalManip and PsyScam).
"""

from __future__ import annotations

import numpy as np
from scipy.stats import fisher_exact

from ..models.common import TACTICS
from .common import holm, scores

DATASETS = {"human": "sms_human", "llm": "sms_llm"}


def select(records: list[dict], label: str = "smishing") -> dict[str, list[dict]]:
    out = {k: [] for k in DATASETS}
    for r in records:
        for k, ds in DATASETS.items():
            if r["dataset"] == ds and (r.get("meta") or {}).get("sms_label") == label:
                out[k].append(r)
    return out


def tactic_matrix(model, th_turn: np.ndarray, recs: list[dict]) -> np.ndarray:
    return (scores(model, recs) >= th_turn).astype(int)


def lexicon_matrix(recs: list[dict]) -> np.ndarray:
    from ..features.handcrafted import Lexicon
    lex = Lexicon()
    M = np.zeros((len(recs), len(TACTICS)), dtype=int)
    for i, r in enumerate(recs):
        c = lex.counts(r["text"])
        for t, v in zip(lex.tactics, c):
            M[i, TACTICS.index(t)] = int(v > 0)
    return M


def compare(A: np.ndarray, B: np.ndarray, n_boot: int = 2000, seed: int = 42) -> list[dict]:
    """A = human [n, 10] 0/1, B = LLM. Share using each tactic and the difference (B - A)."""
    rng = np.random.default_rng(seed)
    ia = rng.integers(0, len(A), size=(n_boot, len(A)))
    ib = rng.integers(0, len(B), size=(n_boot, len(B)))
    rows = []
    for j, t in enumerate(TACTICS):
        a, b = A[:, j], B[:, j]
        diffs = b[ib].mean(axis=1) - a[ia].mean(axis=1)
        lo, hi = np.quantile(diffs, [0.025, 0.975])
        _, p = fisher_exact([[int(b.sum()), int(len(b) - b.sum())], [int(a.sum()), int(len(a) - a.sum())]])
        rows.append({"tactic": t, "human": float(a.mean()), "llm": float(b.mean()), "diff": float(b.mean() - a.mean()),
                     "ci": (float(lo), float(hi)), "p": float(p)})
    for r, ph in zip(rows, holm([r["p"] for r in rows])):
        r["p_holm"] = ph
    return rows


def per_generator(recs: list[dict], M: np.ndarray) -> dict[str, np.ndarray]:
    out: dict[str, list[int]] = {}
    for i, r in enumerate(recs):
        out.setdefault((r.get("meta") or {}).get("model", "unknown"), []).append(i)
    return {k: M[v].mean(axis=0) for k, v in sorted(out.items())}


def report_markdown(label: str, n: dict, model_name: str, rows: list[dict], lex_rows: list[dict],
                    gens: dict[str, np.ndarray], names: dict[str, str], extra: dict) -> str:
    def table(rs, title):
        out = [f"## {title}", "", "| Tactic | Name | Human | LLM | LLM - human (95% CI) | p (Holm) |",
               "|---|---|---|---|---|---|"]
        for r in rs:
            if r["human"] == 0 and r["llm"] == 0:
                continue
            star = " *" if r["p_holm"] < 0.05 else ""
            out.append(f"| {r['tactic']} | {names.get(r['tactic'], '')} | {r['human']:.1%} | {r['llm']:.1%} | "
                       f"{r['diff']:+.1%} ({r['ci'][0]:+.1%} to {r['ci'][1]:+.1%}) | {r['p_holm']:.3g}{star} |")
        return out + [""]

    lines = [f"# Human vs LLM-written SMS ({label})", "",
             f"Messages: human {n['human']:,}, LLM {n['llm']:,}. Tactic model: {model_name} (turn thresholds).",
             "Share of messages that use each tactic. * = significant after Holm correction across tactics.",
             f"Tactics per message (mean): human {extra['tpm_human']:.2f}, LLM {extra['tpm_llm']:.2f}. "
             f"Words per message (median): human {extra['len_human']:.0f}, LLM {extra['len_llm']:.0f}.", ""]
    lines += table(rows, f"Model-detected tactics ({model_name})")
    lines += table(lex_rows, "Model-free check: at least one lexicon cue")
    if gens:
        keys = [t for t in TACTICS if any(v[TACTICS.index(t)] > 0 for v in gens.values())]
        lines += ["## Per generator (model-detected share)", "",
                  "| Source | " + " | ".join(keys) + " |", "|---|" + "---|" * len(keys)]
        for g, v in gens.items():
            lines.append(f"| {g} | " + " | ".join(f"{v[TACTICS.index(t)]:.0%}" for t in keys) + " |")
        lines.append("")
    lines += ["Caveat: SMS have no tactic labels, so the tactic heads are applied out of domain here.", ""]
    return "\n".join(lines)
