import csv
import json
from collections import defaultdict

from tacticlens.config import load_datasets_config
from tacticlens.data.datacard import build_datacard
from tacticlens.data.dedupe import find_duplicates
from tacticlens.data.pipeline import prepare, read_records
from tacticlens.data.splits import dialogue_splits
from tacticlens.taxonomy.mapping import load_taxonomy


def test_dedupe_exact_and_near():
    texts = {
        "a": "Your account will be blocked today, verify now at <URL>",
        "b": "your account will be BLOCKED today verify now at <URL>!!",  # exact after key
        "c": "Your account will be blocked today, verify now at <URL> pls",  # near
        "d": "Totally different message about dinner plans tonight",
    }
    dropped = find_duplicates(texts, jaccard_threshold=0.8)
    assert dropped["b"] == ("a", "exact")
    assert dropped["c"][0] == "a" and dropped["c"][1] == "near"
    assert "a" not in dropped and "d" not in dropped


def test_disabled_dataset_is_skipped(project):
    from tacticlens.data.pipeline import load_all
    cfg = load_datasets_config(project)
    tax = load_taxonomy(project / "configs" / "taxonomy.yaml")
    recs, status = load_all(cfg, project, tax)
    assert status["sms_munoz"].startswith("disabled") and all(r.dataset != "sms_munoz" for r in recs)
    assert any(r.dataset == "sms_llm" and r.meta.get("model") for r in recs)


def test_splits_ratio_and_determinism():
    dlg = {f"d{i}": ("ds", "scam") for i in range(100)}
    s1 = dialogue_splits(dlg, {"train": 0.7, "val": 0.15, "test": 0.15}, seed=42)
    s2 = dialogue_splits(dlg, {"train": 0.7, "val": 0.15, "test": 0.15}, seed=42)
    assert s1 == s2
    counts = {k: list(s1.values()).count(k) for k in ("train", "val", "test")}
    assert counts == {"train": 70, "val": 15, "test": 15}


def test_prepare_end_to_end(project):
    cfg = load_datasets_config(project)
    tax = load_taxonomy(project / "configs" / "taxonomy.yaml")
    summary = prepare(cfg, project, tax)
    assert summary["datasets"]["sms_munoz"].startswith("disabled")
    assert all(v.startswith("ok") for k, v in summary["datasets"].items() if k != "sms_munoz")
    recs = read_records(project / "data" / "processed" / "records.jsonl")
    # no dialogue in two splits (FR-DAT-06)
    split_of = defaultdict(set)
    for r in recs:
        split_of[r["dialogue_id"]].add(r["split"])
    assert all(len(v) == 1 for v in split_of.values())
    # every genre present, both sources present
    assert {r["genre"] for r in recs} == {"persuasion", "manipulation", "scam", "neutral"}
    assert {r["source"] for r in recs} == {"human", "llm"}
    # duplicates were reported, and the LLM copy of a human SMS was the one dropped
    with open(project / "reports" / "dedupe_removed.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows
    for row in rows:
        if {row["dataset"], row["kept_dataset"]} == {"sms_human", "sms_llm"}:
            assert row["dataset"] == "sms_llm"
    logo = json.loads((project / "data" / "processed" / "logo_splits.json").read_text())
    genre_of = {r["dialogue_id"]: r["genre"] for r in recs}
    for g, parts in logo.items():
        assert all(genre_of[d] == g for d in parts["test"])
        assert all(genre_of[d] != g for d in parts["train"])
    card = build_datacard(recs, tax)
    assert "Tactic counts" in card and "T5" in card
