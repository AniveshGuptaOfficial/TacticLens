import numpy as np
from conftest import fake_encoder

from tacticlens.eval.compare import paired_bootstrap
from tacticlens.features.handcrafted import HandcraftedFeatures, Lexicon, stylometry
from tacticlens.models.common import (
    TACTICS,
    by_split,
    dialogue_pool,
    run_model,
    tactic_training_rows,
)
from tacticlens.models.embed import EmbeddingCache, chunks
from tacticlens.models.m0 import M0
from tacticlens.models.m1 import M1
from tacticlens.models.m2 import M2


def test_lexicon_and_stylometry():
    lex = Lexicon()
    c = dict(zip(lex.tactics, lex.counts("URGENT: your account will be blocked today, act now!")))
    assert c["T5"] >= 2 and c["T9"] >= 1 and c["T4"] == 0
    s = stylometry("Hello THERE!! Call <PHONE> or visit <URL>")
    assert s[7] == 1 and s[8] == 1 and s[5] > 0  # url, phone, exclamations
    X = HandcraftedFeatures().transform(["a", "b c"])
    assert X.shape == (2, 33)


def test_weak_rows_and_dialogue_pool(prepared):
    recs, _ = prepared
    rows, Y = tactic_training_rows(recs, weak=True)
    strict, _ = tactic_training_rows(recs, weak=False)
    assert len(rows) > len(strict)  # MentalManip turns added as weak rows
    assert Y.shape[1] == len(TACTICS)
    test = by_split(recs)["test"]
    S = np.random.default_rng(0).random((len(test), len(TACTICS)))
    dids, pooled, DL = dialogue_pool(test, S)
    assert len(dids) == len(pooled) == len(DL) and all(d.startswith("mm_") for d in dids)


def test_m1_runs(prepared, tmp_path):
    recs, _ = prepared
    res = run_model(M1(), recs, tmp_path / "m1", n_boot=30)
    assert res["turn"]["macro_f1"] > 0.3 and "dialogue" in res


def test_embedding_cache_chunks_and_reuse(tmp_path):
    long = " ".join(f"w{i}" for i in range(400))
    assert len(chunks(long)) >= 3 and chunks("short text") == ["short text"]
    calls = []
    enc = fake_encoder(16)

    def counting(texts):
        calls.append(len(texts))
        return enc(texts)

    c = EmbeddingCache(tmp_path, encoder=counting)
    a = c.embed(["hello world", long, "hello world"], log=lambda *_: None)
    assert a.shape == (3, 16) and np.allclose(a[0], a[2])
    c2 = EmbeddingCache(tmp_path, encoder=counting)
    c2.embed(["hello world"], log=lambda *_: None)
    assert len(calls) == 1  # second time came from disk


def test_m2_and_compare(prepared, tmp_path):
    recs, _ = prepared
    run_model(M0(), recs, tmp_path / "m0", n_boot=20)
    res = run_model(M2(tmp_path / "emb", encoder=fake_encoder(64), max_iter=30), recs, tmp_path / "m2", n_boot=20)
    assert "turn" in res and "genre" in res
    test = by_split(recs)["test"]
    r = paired_bootstrap(test, tmp_path / "m0" / "test_predictions.npz", tmp_path / "m2" / "test_predictions.npz", n_boot=50)
    assert set(r) >= {"diff", "diff_ci95", "p_b_not_better"} and 0 <= r["p_b_not_better"] <= 1


def test_summarize_groups_seeds(tmp_path):
    import json

    from tacticlens.cli import summarize_runs
    for name, f1 in (("m3_full", 0.50), ("m3_full_s1", 0.54), ("m0", 0.40)):
        (tmp_path / name).mkdir()
        (tmp_path / name / "metrics.json").write_text(json.dumps({"turn": {"macro_f1": f1}, "genre": {"macro_f1": 0.8}}))
    rows = {r["model"]: r for r in summarize_runs(tmp_path)}
    assert rows["m3_full"]["seeds"] == 2 and abs(rows["m3_full"]["turn"] - 0.52) < 1e-9
    assert rows["m3_full"]["turn_sd"] > 0 and rows["m0"]["turn_sd"] is None and "dialogue" not in rows["m0"]


def test_thresholds_per_level_and_rescore(prepared, tmp_path):
    import json

    import numpy as np

    from tacticlens.eval.metrics import tune_thresholds
    from tacticlens.models.common import TACTICS, run_model, score_saved
    from tacticlens.models.m0 import M0
    recs, _ = prepared
    res = run_model(M0(), recs, tmp_path / "m0", n_boot=20)
    th = np.load(tmp_path / "m0" / "test_predictions.npz")["thresholds"]
    assert th.shape == (2, len(TACTICS)) and set(res["thresholds"]) == {"turn", "dialogue"}
    again = score_saved("M0", tmp_path / "m0", recs, n_boot=20)  # from saved files, no retraining
    assert abs(again["turn"]["macro_f1"] - res["turn"]["macro_f1"]) < 1e-9
    assert json.loads((tmp_path / "m0" / "metrics.json").read_text())["model"] == "M0"
    # smoothed thresholds stay inside the grid and need no positives at every level
    y = np.array([[1], [0], [0], [0], [1], [0]])
    s = np.array([[0.9], [0.2], [0.6], [0.1], [0.7], [0.3]])
    t = tune_thresholds(y, s, n_boot=100)
    assert 0.3 < t[0] <= 0.7
