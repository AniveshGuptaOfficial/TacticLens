import numpy as np
import pytest
from conftest import fake_encoder

from tacticlens.models.common import TACTICS

torch = pytest.importorskip("torch")  # the rest needs PyTorch (installed from requirements-ml.txt)


@pytest.mark.parametrize("variant", ["full", "no-role", "no-context", "no-adv", "dual-role"])
def test_m3net_shapes_and_causal_attention(variant):
    from tacticlens.models.m3 import M3Net
    net = M3Net(16, d=32, variant=variant)
    E = torch.randn(2, 5, 16)
    roles = torch.tensor([[0, 1, 0, 1, 0], [0, 1, 2, 2, 2]])
    mask = torch.tensor([[True] * 5, [True, True, True, False, False]])
    out = net(E, roles, mask, lam=0.1)
    assert out["tactic"].shape == (2, 5, len(TACTICS)) and out["genre"].shape == (2, 5, 4)
    if out["attn"] is not None:
        a = out["attn"]
        assert torch.allclose(torch.triu(a[0], diagonal=0), torch.zeros_like(a[0]))  # only earlier turns
        assert a[1, :, 3:].abs().sum() == 0  # never attends to padding
        if variant == "dual-role":
            assert a[0, 2, 0] == 0  # actor turn 2 ignores earlier actor turn 0


def test_gradient_reversal_flips_sign():
    from tacticlens.models.m3 import _GradReverse
    x = torch.ones(3, requires_grad=True)
    _GradReverse.apply(x, 0.5).sum().backward()
    assert torch.allclose(x.grad, torch.full((3,), -0.5))


def test_m3_trains_end_to_end(prepared, tmp_path):
    from tacticlens.models.common import run_model
    from tacticlens.models.m3 import M3
    recs, _ = prepared
    m = M3(tmp_path / "emb", encoder=fake_encoder(64), epochs=4, d=32, lexical_dim=16, log=lambda *_: None)
    res = run_model(m, recs, tmp_path / "m3", n_boot=20)
    assert res["turn"]["macro_f1"] > 0.2 and "dialogue" in res
    m.save(tmp_path / "m3")
    assert (tmp_path / "m3" / "m3.pt").exists() and len(m.history) >= 1
    assert (tmp_path / "m3" / "lexical_svd.pkl").exists()
    assert m.last_roles.shape[1] == 2  # role probabilities are kept for every predicted turn


def test_lexical_svd_shapes():
    from tacticlens.models.m3 import LexicalSVD
    texts = [f"urgent verify account {i}" if i % 2 else f"donate to children charity {i}" for i in range(40)]
    lex = LexicalSVD(dim=8).fit(texts)
    Z = lex.transform(texts[:5])
    assert Z.shape == (5, 8) and np.allclose(np.linalg.norm(Z, axis=1), 1, atol=1e-3)


def test_m3_sweep_settings_reach_the_model(prepared, tmp_path):
    from tacticlens.models.m3 import M3, LexicalSVD
    from tacticlens.models.m3_data import pos_weights
    recs, _ = prepared
    train = [r for r in recs if r["split"] == "train"]
    lex = LexicalSVD(dim=16).fit([r["text"] for r in train])
    m = M3(tmp_path / "emb", encoder=fake_encoder(64), epochs=1, d=32, mil_weight=0.3, pos_clip=5.0, dropout=0.4,
           lexical_model=lex, log=lambda *_: None)
    m.fit(train, [r for r in recs if r["split"] == "val"])
    assert m.w["mil"] == 0.3 and m.net.drop.p == 0.4 and m.lex is lex  # prefit lexical model reused, not refit
    items, _ = m._items(train)
    assert pos_weights(items, clip=5.0).max() <= 5.0


def test_m3_hparams_from_best_file_and_flags(tmp_path):
    import json
    from types import SimpleNamespace

    from tacticlens.cli import M3_BEST, _m3_hparams
    args = SimpleNamespace(mil_weight=None, pos_clip=None, dropout=0.3)
    assert _m3_hparams(tmp_path, args) == {"dropout": 0.3}
    (tmp_path / M3_BEST).parent.mkdir(parents=True)
    (tmp_path / M3_BEST).write_text(json.dumps({"params": {"mil_weight": 0.3, "pos_clip": 5.0, "dropout": 0.2}}))
    assert _m3_hparams(tmp_path, args) == {"mil_weight": 0.3, "pos_clip": 5.0, "dropout": 0.3}  # flag wins
