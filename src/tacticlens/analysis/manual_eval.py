"""Check the datasets' own labels and the model against the hand labels of the check set.

Uses only hand-labelled turns from the val/test splits (checkset_agreed.csv), never train turns.
Three questions:
  1. How accurate are the source datasets' labels? (source label vs human label, per tactic)
  2. How accurate is the model on single turns, judged by people? (incl. T8/T10, which have no
     turn-level source labels)
  3. Human vs LLM SMS: what do the human labels say about the tactic shares? (settles O6 where
     the model and the lexicon disagree)
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np

SMS_TACTICS = ["T3", "T5", "T6", "T7", "T9"]


def _prf(y: np.ndarray, p: np.ndarray) -> tuple[float, float, float]:
    tp = int((y & p).sum())
    prec = tp / p.sum() if p.sum() else float("nan")
    rec = tp / y.sum() if y.sum() else float("nan")
    f1 = 2 * tp / (y.sum() + p.sum()) if (y.sum() + p.sum()) else float("nan")
    return prec, rec, f1


def _f(x: float) -> str:
    return "–" if x != x else f"{x:.2f}"


def manual_eval(records: list[dict], manual: dict, pred, tax, min_pos: int = 3) -> str:
    by_key = {(r["dialogue_id"], r["turn_id"]): r for r in records}
    items = [(by_key[k], m) for k, m in manual.items()
             if m["set"] == "check" and k in by_key and by_key[k]["split"] in ("val", "test")]
    if not items:
        return "No hand-labelled check-set items found. Run `cli agree`, resolve every '?', then rerun."
    ids = pred.ids
    names = {t["id"]: t["name"] for t in pred.tactics}
    H = np.array([[t in m["tactics"] for t in ids] for _, m in items], dtype=bool)
    split = np.array([r["split"] for r, _ in items])
    ds = [r["dataset"] for r, _ in items]
    roles = [r.get("role") or "unknown" for r, _ in items]
    S = np.asarray(pred.engine.run([r["text"] for r, _ in items], roles)["tactic"], dtype=float)

    count = defaultdict(int)
    for d, s in zip(ds, split):
        count[(d, s)] += 1
    lines = [f"# Hand-label check ({len(items)} turns, val/test only)", "",
             "| Dataset | Val | Test |", "|---|---|---|"]
    lines += [f"| {d} | {count[(d, 'val')]} | {count[(d, 'test')]} |" for d in sorted({d for d, _ in count})]

    # 1. source labels vs human labels
    lines += ["", "## 1. Are the datasets' own labels right?", "",
              "Turns whose dataset has turn-level labels (PersuasionForGood, PsyScam). Precision = share of "
              "source labels that people confirm; recall = share of human labels the source also has.", "",
              "| Tactic | Source yes | Human yes | Both | Precision | Recall |", "|---|---|---|---|---|---|"]
    turn_idx = [i for i, (r, _) in enumerate(items) if r["label_level"] == "turn" and r["dataset"] not in ("dailydialog",)]
    if turn_idx:
        src = np.array([[t in (items[i][0]["tactics"] or []) for t in ids] for i in turn_idx], dtype=bool)
        hum = H[turn_idx]
        for j, t in enumerate(ids):
            if src[:, j].sum() + hum[:, j].sum() == 0:
                continue
            p, r_, _ = _prf(hum[:, j], src[:, j])
            lines.append(f"| {names[t]} | {int(src[:, j].sum())} | {int(hum[:, j].sum())} | "
                         f"{int((src[:, j] & hum[:, j]).sum())} | {_f(p)} | {_f(r_)} |")
    mm = [(i, set((items[i][0].get("meta") or {}).get("dialogue_tactics") or [])) for i in range(len(items))
          if items[i][0]["dataset"] == "mentalmanip"]
    if mm:
        lines += ["", "MentalManip labels whole conversations. Share of hand-labelled turns from conversations "
                  "labelled with a tactic in which people found that tactic in the turn itself:", "",
                  "| Tactic | Turns from labelled conversations | Tactic found in the turn |", "|---|---|---|"]
        for j, t in enumerate(ids):
            sel = [i for i, tags in mm if t in tags]
            if sel:
                k = int(H[sel, j].sum())
                lines.append(f"| {names[t]} | {len(sel)} | {k} ({k / len(sel):.0%}) |")

    # 2. model vs human labels
    lines += ["", "## 2. Is the model right, by people's labels?", ""]
    for mode in pred.modes():
        th = pred.th[mode][0]
        P = S >= th
        lines += [f"### {mode}", "", "| Tactic | Human yes | Model yes | Precision | Recall | F1 |", "|---|---|---|---|---|---|"]
        f1s, f1s_test = [], []
        for j, t in enumerate(ids):
            p, r_, f = _prf(H[:, j], P[:, j])
            lines.append(f"| {names[t]} | {int(H[:, j].sum())} | {int(P[:, j].sum())} | {_f(p)} | {_f(r_)} | {_f(f)} |")
            if H[:, j].sum() >= min_pos:
                f1s.append(f)
                te = split == "test"
                if H[te, j].sum() >= min_pos:
                    f1s_test.append(_prf(H[te, j], P[te, j])[2])
        any_h, any_p = H.any(1), P.any(1)
        lines += ["", f"- Macro-F1 over tactics with at least {min_pos} human positives: "
                  f"{(np.nanmean(f1s) if f1s else float('nan')):.3f} ({len(f1s)} tactics); test items only: "
                  f"{(np.nanmean(f1s_test) if f1s_test else float('nan')):.3f}",
                  f"- Any tactic in the turn: accuracy {(any_h == any_p).mean():.1%} "
                  f"(always 'no tactic' would get {(~any_h).mean():.1%})", ""]

    # 3. SMS: human vs LLM by human labels
    sms = [i for i in range(len(items)) if items[i][0]["dataset"] in ("sms_human", "sms_llm")
           and (items[i][0].get("meta") or {}).get("sms_label") in ("smishing", "spam")]
    if sms:
        P = S >= pred.th["balanced"][0]
        lines += ["## 3. Human vs LLM scam SMS, by human labels", "",
                  "Share of smishing/spam messages with each tactic. Small samples: read as a check on the "
                  "direction of the model and lexicon results, not as new estimates.", "",
                  "| Tactic | Human-written: people | LLM: people | Human-written: model | LLM: model |",
                  "|---|---|---|---|---|"]
        hum_i = [i for i in sms if items[i][0]["dataset"] == "sms_human"]
        llm_i = [i for i in sms if items[i][0]["dataset"] == "sms_llm"]
        for t in SMS_TACTICS:
            if t not in ids:
                continue
            j = ids.index(t)

            def share(idx, M, j=j):
                return f"{M[idx, j].mean():.0%} ({int(M[idx, j].sum())}/{len(idx)})" if idx else "–"
            lines.append(f"| {names[t]} | {share(hum_i, H)} | {share(llm_i, H)} | {share(hum_i, P)} | {share(llm_i, P)} |")
    return "\n".join(lines) + "\n"
