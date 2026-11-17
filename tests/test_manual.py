import json

import pandas as pd
import pytest

from tacticlens.config import load_datasets_config
from tacticlens.data.pipeline import prepare, read_records
from tacticlens.taxonomy.annotation import export_checkset
from tacticlens.taxonomy.manual import agree_checkset, apply_manual, export_batch, load_manual


def _fill(path, marks):
    df = pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
    for (row, col), v in marks.items():
        df.loc[row, col] = v
    df.to_csv(path, index=False, encoding="utf-8-sig")


@pytest.fixture()
def checkset(prepared, project):
    recs, tax = prepared
    d = project / "data" / "annotation"
    export_checkset(recs, tax, d, n=40, seed=42)
    _fill(d / "checkset_A.csv", {(0, "T5"): "1", (0, "T9"): "1", (1, "T8"): "1", (2, "T7"): "1"})
    _fill(d / "checkset_B.csv", {(0, "T5"): "1", (1, "T8"): "1", (3, "T6"): "x"})
    return recs, tax, d


def test_agree_marks_disagreements(checkset, project):
    recs, tax, d = checkset
    c = agree_checkset(d / "checkset_A.csv", d / "checkset_B.csv", d / "checkset_agreed.csv", tax)
    assert c == {"items": 40, "items_with_disagreement": 3, "tactic_disagreements": 3}
    agreed = pd.read_csv(d / "checkset_agreed.csv", dtype=str).fillna("")
    assert agreed.loc[0, "T5"] == "1" and agreed.loc[0, "T9"] == "?" and agreed.loc[1, "T8"] == "1"
    with pytest.raises(ValueError, match="still '\\?'"):
        load_manual(project, tax)
    agreed = agreed.replace("?", "")
    agreed.to_csv(d / "checkset_agreed.csv", index=False, encoding="utf-8-sig")
    manual = load_manual(project, tax)
    key = pd.read_csv(d / "checkset_key.csv", dtype=str)
    k0 = (key.loc[0, "dialogue_id"], int(key.loc[0, "turn_id"]))
    k1 = (key.loc[1, "dialogue_id"], int(key.loc[1, "turn_id"]))
    assert manual[k0]["tactics"] == ["T5"] and manual[k1]["tactics"] == ["T8"]
    assert all(m["set"] == "check" for m in manual.values()) and len(manual) == 40
    # check-set turns are val/test: they never change the training data
    assert apply_manual([dict(r) for r in recs], manual) == 0


def test_batch_labels_reach_training(prepared, project):
    recs, tax = prepared
    p = export_batch(recs, tax, project, n=20, seed=42)
    df = pd.read_csv(p, dtype=str, encoding="utf-8-sig").fillna("")
    assert len(df) > 0 and set(df["dialogue_id"]).issubset({r["dialogue_id"] for r in recs if r["split"] == "train"})
    df.loc[0, "T8"], df.loc[0, "done"] = "1", "1"
    df.loc[1, "done"] = "1"  # labelled "no tactic"
    df.to_csv(p, index=False, encoding="utf-8-sig")
    summary = prepare(load_datasets_config(project), project, tax)
    assert summary["hand_labelled_train_turns"] == 2
    new = {(r["dialogue_id"], r["turn_id"]): r for r in read_records(project / "data" / "processed" / "records.jsonl")}
    r0 = new[(df.loc[0, "dialogue_id"], int(df.loc[0, "turn_id"]))]
    r1 = new[(df.loc[1, "dialogue_id"], int(df.loc[1, "turn_id"]))]
    assert r0["tactics"] == ["T8"] and r0["label_level"] == "turn" and r0["meta"]["manual"]
    assert r1["tactics"] == [] and r1["meta"]["manual"]
    # a second batch never repeats labelled items
    p2 = export_batch(read_records(project / "data" / "processed" / "records.jsonl"), tax, project, n=20, seed=42)
    df2 = pd.read_csv(p2, dtype=str, encoding="utf-8-sig")
    assert not set(zip(df2["dialogue_id"], df2["turn_id"])) & set(zip(df["dialogue_id"], df["turn_id"]))


def test_mil_bag_kept_when_a_turn_is_hand_labelled():
    import numpy as np

    from tacticlens.models.m3_data import build_dialogues
    turns = [{"dialogue_id": "mm1", "turn_id": t, "text": f"t{t}", "role": "unknown", "label_level": "dialogue",
              "tactics": None, "genre": "manipulation", "dataset": "mentalmanip",
              "meta": {"dialogue_tactics": ["T10"]}} for t in range(3)]
    turns[0] = dict(turns[0], label_level="turn", tactics=["T10"],
                    meta={"dialogue_tactics": ["T10"], "manual": True, "source_label_level": "dialogue"})
    item = build_dialogues(turns, lambda t: 0)[0]
    assert item["m_dlg"].sum() > 0 and item["m_turn"].tolist() == [1, 0, 0]
    assert np.isclose(item["y_turn"][0].sum(), 1)


def test_manual_eval_report(checkset, project):
    from test_serve import FakeEngine, bundle

    from tacticlens.analysis.manual_eval import manual_eval
    from tacticlens.serve.predictor import Predictor
    recs, tax, d = checkset
    agree_checkset(d / "checkset_A.csv", d / "checkset_B.csv", d / "checkset_agreed.csv", tax)
    a = pd.read_csv(d / "checkset_agreed.csv", dtype=str).fillna("").replace("?", "1")
    a.to_csv(d / "checkset_agreed.csv", index=False, encoding="utf-8-sig")
    md = manual_eval(recs, load_manual(project, tax), Predictor(FakeEngine(), bundle()), tax)
    assert "## 1." in md and "## 2." in md and "### balanced" in md and "Any tactic in the turn" in md
    assert json.dumps(md)  # plain text
