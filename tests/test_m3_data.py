import numpy as np

from tacticlens.models.common import TACTICS
from tacticlens.models.m3_data import MIL_TACTICS, batches, build_dialogues, pad_batch, pos_weights


def _items(recs):
    rows = {}
    for i, r in enumerate(recs):
        rows.setdefault(r["text"], i)
    return build_dialogues(recs, lambda t: rows[t])


def test_dialogue_items_and_padding(prepared):
    recs, _ = prepared
    items = _items(recs)
    mm = [it for it in items if it["dialogue_id"].startswith("mm_")]
    p4 = [it for it in items if it["dialogue_id"].startswith("p4g_")]
    assert mm and p4
    assert all(it["m_turn"].sum() == 0 and it["m_dlg"].sum() == len(MIL_TACTICS) for it in mm)
    assert all((it["role_y"] == -1).all() for it in mm)  # MentalManip roles unknown
    assert any(it["m_turn"].sum() > 0 for it in p4)
    b = pad_batch(items[:5])
    T = max(len(it["emb_idx"]) for it in items[:5])
    assert b["y_turn"].shape == (5, T, len(TACTICS)) and b["mask"].sum() == sum(len(it["emb_idx"]) for it in items[:5])
    bs = batches(items, 8, np.random.default_rng(0))
    assert sum(len(x) for x in bs) == len(items)
    w = pos_weights(items)
    assert w.shape == (len(TACTICS),) and (w >= 1).all()
