import pandas as pd

from tacticlens.config import load_datasets_config
from tacticlens.data.pipeline import prepare, read_records
from tacticlens.eval.metrics import bootstrap_ci, tune_thresholds
from tacticlens.models.common import results_markdown, run_model
from tacticlens.models.m0 import M0
from tacticlens.taxonomy.annotation import export_checkset, kappa_report
from tacticlens.taxonomy.mapping import load_taxonomy


def _prepared(project):
    cfg = load_datasets_config(project)
    tax = load_taxonomy(project / "configs" / "taxonomy.yaml")
    prepare(cfg, project, tax)
    return read_records(project / "data" / "processed" / "records.jsonl"), tax


def test_checkset_and_kappa(project):
    recs, tax = _prepared(project)
    a, b, key = export_checkset(recs, tax, project / "data" / "annotation", n=40)
    da = pd.read_csv(a, encoding="utf-8-sig")
    assert len(da) == 40 and "T1" in da and "evidence" in da
    assert "source_tactics" not in da  # annotators never see source labels
    # A and B agree on T5, disagree once on T9
    da["T5"] = ["1" if i % 4 == 0 else "" for i in range(40)]
    da["T9"] = ["x" if i % 5 == 0 else "" for i in range(40)]
    db = da.copy()
    db.loc[0, "T9"] = ""
    da.to_csv(a, index=False, encoding="utf-8-sig")
    db.to_csv(b, index=False, encoding="utf-8-sig")
    rep = kappa_report(a, b, tax).set_index("tactic")
    assert rep.loc["T5", "kappa"] == 1.0
    assert 0 < rep.loc["T9", "kappa"] < 1
    assert pd.isna(rep.loc["T1", "kappa"])  # never used -> not counted
    assert 0 < rep.loc["overall", "kappa"] < 1


def test_thresholds_and_bootstrap():
    import numpy as np
    y = np.array([[1, 0], [0, 0], [1, 0], [0, 0]])
    s = np.array([[0.9, 0.1], [0.2, 0.3], [0.6, 0.2], [0.4, 0.1]])
    th = tune_thresholds(y, s)
    assert 0.4 < th[0] <= 0.6 and th[1] == 0.5
    lo, hi = bootstrap_ci(lambda idx: float(len(idx)), np.array(["a", "a", "b", "b"]), n_boot=50)
    assert lo <= hi


def test_m0_trains_and_reports(project, tmp_path):
    recs, tax = _prepared(project)
    res = run_model(M0(), recs, tmp_path / "m0", n_boot=50)
    assert "macro_f1" in res["turn"] and "macro_f1_ci95" in res["turn"]
    assert res["turn"]["macro_f1"] > 0.5  # synthetic data is easy; this checks the plumbing
    assert "dialogue" in res and res["dialogue"]["n"] > 0  # MentalManip dialogues, max over turns
    assert "macro_f1" in res["genre"]
    md = results_markdown(res, {t: tax.name(t) for t in tax.all_label_ids})
    assert "M0" in md and "Urgency" in md
    assert (tmp_path / "m0" / "test_predictions.npz").exists()
