"""Do persuasion tactics go with donations? (O7, PersuasionForGood)

Per P4G dialogue: how often the persuader used each tactic (share of persuader turns), from
  gold   the annotated dialogues' labels (about 300 dialogues), and
  model  the final model's detections on every dialogue (about 1,000)
and the persuadee's actual donation (0 to 2 dollars, from the info file).

Two models, tactic shares standardised, controlled for the persuadee's Big Five traits and
the number of persuader turns:
  donated (yes/no)  logistic regression, odds ratios
  amount ($)        linear mixed model with a random intercept per persuader (worker ID B3),
                    because many persuaders ran several dialogues; falls back to OLS with
                    persuader-clustered standard errors if the mixed model does not converge.
p-values are Holm-corrected across tactics. This is observational: an association, not proof
that a tactic causes donations.
"""

from __future__ import annotations

import warnings
from collections import defaultdict

import numpy as np
import pandas as pd

from ..models.common import TACTICS, turn_labels
from .common import holm, scores

BIG_FIVE = ["extrovert", "agreeable", "conscientious", "neurotic", "open"]


def persuader_ids(info: pd.DataFrame | None) -> dict[str, str]:
    if info is None or "B3" not in info.columns:
        return {}
    out = {}
    for _, row in info.iterrows():
        if str(row.get("B4")).strip() in ("0", "0.0"):
            did, pid = str(row["B2"]).strip(), str(row["B3"]).strip()
            out[did] = out[f"p4g_{did}"] = pid  # records carry the "p4g_" prefix
    return out


def dialogue_table(records: list[dict], source: str, model=None, th_turn=None, pids: dict | None = None) -> pd.DataFrame:
    """One row per P4G dialogue: tactic shares over persuader turns, donation, traits."""
    p4g = [r for r in records if r["dataset"] == "p4g"]
    if source == "gold":
        dlg_ok = {r["dialogue_id"] for r in p4g if r["label_level"] == "turn"}
        p4g = [r for r in p4g if r["dialogue_id"] in dlg_ok]
    actors = [r for r in p4g if r["role"] == "actor"]
    if source == "gold":
        L = np.stack([turn_labels(r) for r in actors]) if actors else np.zeros((0, len(TACTICS)))
    else:
        L = (scores(model, actors) >= th_turn).astype(int)
    by = defaultdict(list)
    for r, lab in zip(actors, L):
        by[r["dialogue_id"]].append(lab)
    meta = {r["dialogue_id"]: r.get("meta") or {} for r in p4g}
    rows = []
    for did, labs in by.items():
        m = meta[did]
        don = m.get("donation_ee")
        if don is None or don != don:
            continue
        row = {"dialogue_id": did, "persuader": (pids or {}).get(did, did), "donation": float(don),
               "donated": int(float(don) > 0), "n_turns": len(labs)}
        share = np.mean(labs, axis=0)
        row.update({t: float(v) for t, v in zip(TACTICS, share)})
        traits = m.get("persuadee_traits") or {}
        for b in BIG_FIVE:
            v = next((traits[k] for k in traits if k.split(".")[0].lower() == b), np.nan)
            row[b] = v
        rows.append(row)
    return pd.DataFrame(rows)


MAX_DONATION = 2.0  # persuadees could give part of their $2 task payment; larger entries are not valid amounts


def fit(df: pd.DataFrame, min_share: float = 0.02) -> dict:
    import statsmodels.api as sm
    import statsmodels.formula.api as smf

    tactics = [t for t in TACTICS if t in df and df[t].mean() >= min_share and df[t].std() > 0]
    controls = [b for b in BIG_FIVE if b in df and df[b].notna().mean() > 0.9]
    d = df.dropna(subset=controls).copy()
    z = {}
    for c in tactics + controls:
        d[c + "_z"] = (d[c] - d[c].mean()) / (d[c].std() or 1.0)
        z[c] = c + "_z"
    d["log_turns"] = np.log(d["n_turns"])
    X = sm.add_constant(d[[z[c] for c in tactics + controls] + ["log_turns"]])
    out = {"n": len(d), "n_persuaders": int(d["persuader"].nunique()), "tactics": tactics, "controls": controls,
           "donated_rate": float(d["donated"].mean()),
           "mean_donation": float(d.loc[d["donation"] <= MAX_DONATION, "donation"].mean())}

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        logit = sm.Logit(d["donated"], X).fit(disp=0)
    ci = logit.conf_int()
    out["logit"] = [{"tactic": t, "or": float(np.exp(logit.params[z[t]])), "lo": float(np.exp(ci.loc[z[t], 0])),
                     "hi": float(np.exp(ci.loc[z[t], 1])), "p": float(logit.pvalues[z[t]])} for t in tactics]

    n_bad = int((d["donation"] > MAX_DONATION).sum())
    da = d[d["donation"] <= MAX_DONATION]
    out["amount_excluded"] = n_bad
    formula = "donation ~ " + " + ".join([z[c] for c in tactics + controls] + ["log_turns"])
    method = "mixed (random intercept per persuader)"
    res = None
    if da["persuader"].nunique() < len(da):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                res = smf.mixedlm(formula, da, groups=da["persuader"]).fit(reml=True)
            if not res.converged:
                res = None
        except Exception:  # noqa: BLE001 - singular fits etc.; fall back below
            res = None
    if res is None:
        method = "OLS, persuader-clustered SE"
        res = smf.ols(formula, da).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(da["persuader"])[0]})
    ci = res.conf_int()
    out["amount_method"] = method
    out["amount"] = [{"tactic": t, "b": float(res.params[z[t]]), "lo": float(ci.loc[z[t], 0]),
                      "hi": float(ci.loc[z[t], 1]), "p": float(res.pvalues[z[t]])} for t in tactics]
    for key in ("logit", "amount"):
        for r, ph in zip(out[key], holm([r["p"] for r in out[key]])):
            r["p_holm"] = ph
    return out


def report_markdown(results: dict[str, dict], names: dict[str, str]) -> str:
    lines = ["# Tactics and donations (PersuasionForGood)", "",
             "Tactic use = share of the persuader's turns with that tactic, standardised (1 SD).",
             "Controls: persuadee Big Five traits and log number of persuader turns. p-values Holm-corrected across tactics.",
             "Observational association, not a causal effect.", ""]
    for src, r in results.items():
        lines += [f"## Tactics from {src}", "",
                  f"Dialogues {r['n']:,} (persuaders {r['n_persuaders']:,}); donated {r['donated_rate']:.0%}, "
                  f"mean donation ${r['mean_donation']:.2f}. Amount model: {r['amount_method']}"
                  + (f"; {r['amount_excluded']} entries above $2 left out of it (not valid amounts)." if r.get("amount_excluded") else ".")
                  , "",
                  "| Tactic | Name | Odds of donating (95% CI) | p (Holm) | Change in $ (95% CI) | p (Holm) |",
                  "|---|---|---|---|---|---|"]
        amt = {a["tactic"]: a for a in r["amount"]}
        for lg in r["logit"]:
            a = amt[lg["tactic"]]
            lines.append(f"| {lg['tactic']} | {names.get(lg['tactic'], '')} | {lg['or']:.2f} ({lg['lo']:.2f} to {lg['hi']:.2f}) | "
                         f"{lg['p_holm']:.3g}{' *' if lg['p_holm'] < 0.05 else ''} | {a['b']:+.3f} ({a['lo']:+.3f} to {a['hi']:+.3f}) | "
                         f"{a['p_holm']:.3g}{' *' if a['p_holm'] < 0.05 else ''} |")
        lines.append("")
    return "\n".join(lines)
