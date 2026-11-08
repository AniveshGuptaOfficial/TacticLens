import numpy as np
import pytest

from tacticlens.analysis.common import boot_mean, holm, load_model
from tacticlens.analysis.grounding import (
    _cut,
    _random_cut,
    audit,
    evidence_cases,
    per_tactic_table,
    report_markdown,
    summarize,
)
from tacticlens.analysis.human_vs_llm import compare, lexicon_matrix, select, tactic_matrix
from tacticlens.analysis.transfer import evaluate_genre, logo_records, trained_tactics
from tacticlens.models.common import TACTICS, by_split, run_model
from tacticlens.models.m0 import M0
from tacticlens.models.m3_data import evidence_records


@pytest.fixture()
def m0_project(prepared, project):
    recs, tax = prepared
    out = project / "models" / "m0"
    m = M0()
    run_model(m, recs, out, n_boot=20)
    m.save(out / "m0.pkl")
    return project, recs, tax


def test_helpers():
    m, lo, hi = boot_mean(np.array([1.0, 2.0, 3.0, 4.0]), np.array(["a", "a", "b", "b"]), n_boot=200)
    assert m == 2.5 and lo <= m <= hi
    assert holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])


def test_cut_and_random_cut():
    text = "one two three four five six seven eight"
    assert _cut(text, [(4, 13)]) == "one four five six seven eight"
    rc = _random_cut(text, [(4, 13)], np.random.default_rng(0))
    assert rc is not None and len(rc.split()) == 6 and "two three" in rc  # cut elsewhere, same length


def test_grounding_audit_runs_on_m0(m0_project):
    root, recs, _ = m0_project
    model, (th_t, _) = load_model(root, "m0")
    test = [r for r in recs if r["split"] == "test"]
    assert evidence_cases(test)  # PsyScam fixture quotes are found as spans
    df = audit(model, th_t, test)
    assert {"comprehensiveness", "sufficiency", "random_control", "evidence_effect"} <= set(df.columns)
    assert set(df["dataset"]) <= {"psyscam", "p4g"}
    rows = summarize(df, "m0", n_boot=50)
    md = report_markdown(rows, per_tactic_table({"m0": df}))
    assert "Comprehensiveness" in md and "| m0 |" in md


def test_human_vs_llm_on_m0(m0_project):
    root, recs, _ = m0_project
    model, (th_t, _) = load_model(root, "m0")
    sel = select(recs, "smishing")
    assert sel["human"] and sel["llm"]
    A, B = tactic_matrix(model, th_t, sel["human"]), tactic_matrix(model, th_t, sel["llm"])
    rows = compare(A, B, n_boot=100)
    assert len(rows) == len(TACTICS) and all(0 <= r["p_holm"] <= 1 for r in rows)
    L = lexicon_matrix(sel["human"])
    assert L.shape == (len(sel["human"]), len(TACTICS)) and L[:, TACTICS.index("T5")].sum() > 0  # "urgent", "now"


def test_transfer_helpers(prepared, project, tmp_path):
    import json
    recs, _ = prepared
    logo = json.loads((project / "data" / "processed" / "logo_splits.json").read_text())
    sub = logo_records(recs, logo, "scam")
    sp = by_split(sub)
    assert sp["test"] and all(r["genre"] == "scam" for r in sp["test"])
    assert not any(r["genre"] == "scam" for r in sp["train"] + sp["val"])
    tt = trained_tactics(sp["train"])
    assert "T9" in tt  # MentalManip intimidation (dialogue level) is in training
    m = M0()
    run_model(m, sub, tmp_path / "logo", n_boot=20)
    S, _ = m.predict(sp["test"])
    res = evaluate_genre("scam", sp["test"], S, np.full((2, len(TACTICS)), 0.5), tt, n_boot=20)
    assert res["level"] == "turn" and set(res["shared"]) <= tt and res["shared"]


def test_evidence_records(prepared):
    recs, _ = prepared
    train = [r for r in recs if r["split"] == "train"]
    ev = evidence_records(train)
    assert ev and all(r["label_level"] == "turn" and r["tactics"] and "#ev" in r["dialogue_id"] for r in ev)
    assert len({r["dialogue_id"] for r in ev}) == len(ev)
    texts: dict[str, str] = {}
    for r in train:
        texts[r["dialogue_id"]] = texts.get(r["dialogue_id"], "") + " " + " ".join(r["text"].split())
    for r in ev[:20]:
        assert r["text"] in texts[r["meta"]["evidence_of"]]


def test_donation_table_and_fit(m0_project):
    root, recs, _ = m0_project
    from tacticlens.analysis.donation import dialogue_table
    model, (th_t, _) = load_model(root, "m0")
    gold = dialogue_table(recs, "gold")
    pred = dialogue_table(recs, "model", model=model, th_turn=th_t)
    assert len(pred) >= len(gold) > 0 and {"donation", "donated", "T1", "extrovert"} <= set(pred.columns)
    pytest.importorskip("statsmodels")
    from tacticlens.analysis.donation import fit
    res = fit(pred)
    assert res["n"] > 0 and res["logit"] and res["amount"]


def test_logo_clean_sources(prepared, project):
    import json
    recs, _ = prepared
    logo = json.loads((project / "data" / "processed" / "logo_splits.json").read_text())
    clean = by_split(logo_records(recs, logo, "manipulation"))
    kept = by_split(logo_records(recs, logo, "manipulation", clean_sources=False))
    assert any(r["dataset"] == "mentalmanip" for r in kept["train"])  # its neutral dialogues
    assert not any(r["dataset"] == "mentalmanip" for r in clean["train"] + clean["val"])
    assert {r["dialogue_id"] for r in clean["test"]} == {r["dialogue_id"] for r in kept["test"]}


def test_evidence_skips_flagged_extras():
    r = {"dialogue_id": "d", "turn_id": 0, "label_level": "turn", "text": "Everyone in town already joined us today",
         "tactics": ["T3"], "spans": [{"tactic": "X_SOCIAL_PROOF", "start": 0, "end": 40}], "meta": {}}
    assert evidence_records([r]) == []
    assert evidence_cases([r]) == []
