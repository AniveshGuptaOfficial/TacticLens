"""M3 (FR-MOD-04, 05, 08, 09): role-aware, context-aware tactic model. PyTorch, CPU.

Per dialogue, for every turn t:
  x_t  = proj(MiniLM(turn_t)) + role_emb(role_t)               turn + who is speaking
  h_t  = GRU(x_1..x_t)                                          the conversation so far (causal)
  c_t  = attention of x_t over h_{t-8..t-1}                     which earlier turns matter
  z_t  = MLP([x_t; h_t; c_t])
heads on z_t:
  tactics  10 sigmoid  - turn-level BCE where turns are labelled (P4G, PsyScam)
                       - multiple-instance BCE on max over turns where only the dialogue is
                         labelled (MentalManip), for the tactics it labels (T6-T10)
  role     actor/target, where known                (lets M3 label MentalManip roles)
  genre    persuasion / manipulation / scam / neutral
  domain   source dataset, through a gradient-reversal layer, so z_t is pushed to carry
           tactic information that does NOT depend on which dataset a turn came from (O4)

Variants (ablations, FR-MOD-09, and the dual-role baseline, FR-MOD-08):
  full        everything above
  no-role     role embedding removed (every turn "unknown")
  no-context  no GRU, no attention: each turn alone (like M2, but trained jointly)
  no-adv      no domain-adversarial head
  no-mil      MentalManip dialogue labels not used for tactics
  dual-role   after HDRIN (IEEE #9): separate projections for actor and target turns, and
              attention only over the *other* speaker's earlier turns; no role embedding
The turn encoder is frozen MiniLM (embeddings cached on disk), which keeps training to
minutes per epoch on a laptop CPU.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path

import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
except ImportError as e:  # pragma: no cover - checked by the CLI
    raise ImportError("M3 needs PyTorch. See requirements-ml.txt for the CPU install command.") from e

from sklearn.metrics import average_precision_score

from ..data.schema import GENRES
from .common import TACTICS
from .embed import EmbeddingCache
from .m3_data import DOMAINS, batches, build_dialogues, pad_batch, pos_weights


class LexicalSVD:
    """TF-IDF (word 1-2 + char 3-5 grams) compressed to `dim` with truncated SVD, fitted on train.

    Frozen sentence embeddings blur the exact words that strategies like P4G's "logical appeal"
    hinge on; this adds them back as a small dense vector, still cheap on CPU."""

    def __init__(self, dim: int = 256, seed: int = 42):
        self.dim, self.seed = dim, seed

    def fit(self, texts: list[str]) -> "LexicalSVD":
        from sklearn.decomposition import TruncatedSVD

        from .m0 import TfidfFeatures
        self.tfidf = TfidfFeatures(30000, 30000)
        X = self.tfidf.fit_transform(texts)
        k = max(2, min(self.dim, X.shape[1] - 1, X.shape[0] - 1))
        self.svd = TruncatedSVD(n_components=k, random_state=self.seed).fit(X)
        return self

    def transform(self, texts: list[str]) -> np.ndarray:
        Z = self.svd.transform(self.tfidf.transform(texts)).astype(np.float32)
        return Z / (np.linalg.norm(Z, axis=1, keepdims=True) + 1e-8)

VARIANTS = ("full", "no-role", "no-context", "no-adv", "no-mil", "dual-role")


class _GradReverse(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x, lam):
        ctx.lam = lam
        return x.view_as(x)

    @staticmethod
    def backward(ctx, g):
        return -ctx.lam * g, None


class M3Net(nn.Module):
    def __init__(self, in_dim: int, d: int = 256, variant: str = "full", window: int = 8, dropout: float = 0.2,
                 n_tactics: int = len(TACTICS), n_genres: int = len(GENRES), n_domains: int = len(DOMAINS)):
        super().__init__()
        assert variant in VARIANTS, variant
        self.variant, self.window = variant, window
        self.use_role = variant not in ("no-role", "dual-role")
        self.use_context = variant != "no-context"
        self.use_adv = variant != "no-adv"
        self.dual = variant == "dual-role"
        if self.dual:
            self.proj = nn.ModuleList([nn.Linear(in_dim, d) for _ in range(3)])  # actor, target, unknown
        else:
            self.proj = nn.Linear(in_dim, d)
            self.role_emb = nn.Embedding(3, d)
        if self.use_context:
            self.gru = nn.GRU(d, d, batch_first=True)
            self.q, self.k = nn.Linear(d, d, bias=False), nn.Linear(d, d, bias=False)
            self.mix = nn.Linear(3 * d, d)
        else:
            self.mix = nn.Linear(d, d)
        self.drop = nn.Dropout(dropout)
        self.tactic = nn.Linear(d, n_tactics)
        self.role = nn.Linear(d, 2)
        self.genre = nn.Linear(d, n_genres)
        self.domain = nn.Linear(d, n_domains)

    def forward(self, E, role_in, mask, lam: float = 0.0):
        if self.dual:
            x = sum((role_in == r).unsqueeze(-1) * self.proj[r](E) for r in range(3))
        else:
            x = self.proj(E)
            if self.use_role:
                x = x + self.role_emb(role_in)
        x = self.drop(F.gelu(x))
        attn = None
        if self.use_context:
            h, _ = self.gru(x)
            T = x.shape[1]
            t_idx = torch.arange(T, device=x.device)
            allowed = (t_idx[None, :] < t_idx[:, None]) & (t_idx[:, None] - t_idx[None, :] <= self.window)  # [T,T] j<t
            allowed = allowed[None] & mask[:, None, :]
            if self.dual:
                allowed = allowed & (role_in[:, :, None] != role_in[:, None, :])
            scores = torch.einsum("btd,bsd->bts", self.q(x), self.k(h)) / math.sqrt(x.shape[-1])
            # large negative (not -inf) keeps softmax finite; multiplying by `allowed` then zeroes
            # masked turns exactly, and a turn with no earlier turn gets an all-zero row
            attn = torch.softmax(scores.masked_fill(~allowed, -1e9), dim=-1) * allowed
            c = torch.einsum("bts,bsd->btd", attn, h)
            z = self.mix(torch.cat([x, h, c], dim=-1))
        else:
            z = self.mix(x)
        z = self.drop(F.gelu(z))
        out = {"tactic": self.tactic(z), "role": self.role(z), "genre": self.genre(z), "attn": attn}
        out["domain"] = self.domain(_GradReverse.apply(z, lam)) if self.use_adv else None
        return out


def _tensors(batch: dict, E_all: torch.Tensor) -> dict:
    t = {k: torch.as_tensor(v) for k, v in batch.items()}
    t["E"] = E_all[t["emb_idx"]]
    return t


def m3_loss(out: dict, t: dict, pos_w: torch.Tensor, w: dict) -> tuple[torch.Tensor, dict]:
    mask = t["mask"].float()
    parts = {}
    # turn-level tactic BCE
    bce = F.binary_cross_entropy_with_logits(out["tactic"], t["y_turn"], pos_weight=pos_w, reduction="none").mean(-1)
    mt = t["m_turn"] * mask
    parts["turn"] = (bce * mt).sum() / mt.sum().clamp(min=1.0)
    # multiple-instance: dialogue logit = max over real turns
    logits = out["tactic"].masked_fill(~t["mask"][..., None], -1e4)
    dl = logits.max(dim=1).values
    md = t["m_dlg"]
    if md.sum() > 0 and w.get("mil", 0) > 0:
        bd = F.binary_cross_entropy_with_logits(dl, t["y_dlg"], pos_weight=pos_w, reduction="none")
        parts["mil"] = (bd * md).sum() / md.sum()
    else:
        parts["mil"] = torch.zeros(())
    # role (where known)
    ry = t["role_y"]
    known = (ry >= 0) & t["mask"]
    parts["role"] = F.cross_entropy(out["role"][known], ry[known]) if known.any() else torch.zeros(())
    # genre and domain on every real turn
    g = t["genre"][:, None].expand_as(t["role_y"])
    parts["genre"] = F.cross_entropy(out["genre"][t["mask"]], g[t["mask"]])
    if out["domain"] is not None:
        dmn = t["domain"][:, None].expand_as(t["role_y"])
        parts["adv"] = F.cross_entropy(out["domain"][t["mask"]], dmn[t["mask"]])
    else:
        parts["adv"] = torch.zeros(())
    total = parts["turn"] + w["mil"] * parts["mil"] + w["role"] * parts["role"] + w["genre"] * parts["genre"] + w["adv"] * parts["adv"]
    return total, {k: float(v.detach()) for k, v in parts.items()}


class M3:
    """Fits the same fit/predict interface as M0-M2 (models/common.py)."""

    def __init__(self, cache_dir: Path, variant: str = "full", seed: int = 42, encoder=None, d: int = 256,
                 epochs: int = 40, batch_size: int = 32, lr: float = 1e-3, patience: int = 5, lam_max: float = 0.3,
                 weights: dict | None = None, threads: int | None = None, lexical: bool = True, lexical_dim: int = 256,
                 role_dropout: float = 0.3, mil_weight: float | None = None, pos_clip: float = 20.0,
                 dropout: float = 0.2, lexical_model: "LexicalSVD | None" = None, log=print):
        self.cache = EmbeddingCache(cache_dir, encoder=encoder)
        self.variant, self.seed, self.d = variant, seed, d
        self.lexical, self.lexical_dim, self.role_dropout = lexical, lexical_dim, role_dropout
        self.lex = None
        self.pos_clip, self.dropout = pos_clip, dropout
        self._prefit_lex = lexical_model  # a LexicalSVD already fitted on the same training turns (sweeps reuse it)
        self.epochs, self.batch_size, self.lr, self.patience, self.lam_max = epochs, batch_size, lr, patience, lam_max
        self.w = {"mil": 1.0, "role": 0.2, "genre": 0.5, "adv": 0.2, **(weights or {})}
        if mil_weight is not None:
            self.w["mil"] = float(mil_weight)
        if variant == "no-mil":
            self.w["mil"] = 0.0
        self.log = log
        self.name = f"M3 role-aware GRU-attention ({variant})" if variant != "dual-role" else "Dual-role baseline (after HDRIN)"
        if threads:
            torch.set_num_threads(threads)

    # -- helpers
    def _items(self, records: list[dict]) -> tuple[list[dict], torch.Tensor]:
        texts = [r["text"] for r in records]
        E = self.cache.embed(texts, log=self.log)
        if self.lex is not None:
            E = np.hstack([E, self.lex.transform(texts)])
        row = {}
        for i, t in enumerate(texts):
            row.setdefault(t, i)
        items = build_dialogues(records, lambda t: row[t])
        return items, torch.as_tensor(E)

    @torch.no_grad()
    def _forward_all(self, items: list[dict], E: torch.Tensor) -> list[dict]:
        self.net.eval()
        outs = []
        for b in batches(items, 64):
            t = _tensors(pad_batch(b), E)
            o = self.net(t["E"], t["role_in"], t["mask"])
            p = torch.sigmoid(o["tactic"]).numpy()
            g = torch.softmax(o["genre"], -1).numpy()
            r = torch.softmax(o["role"], -1).numpy()
            for k, it in enumerate(b):
                n = len(it["emb_idx"])
                outs.append({"dialogue_id": it["dialogue_id"], "turn_ids": it["turn_ids"],
                             "tactic": p[k, :n], "genre": g[k, :n], "role": r[k, :n]})
        return outs

    def _val_score(self, items: list[dict], E: torch.Tensor) -> float:
        """Threshold-free model selection: mean AUC-PR over tactics, turn level and dialogue level."""
        outs = {o["dialogue_id"]: o for o in self._forward_all(items, E)}
        ys, ss, yd, sd = [], [], [], []
        for it in items:
            o = outs[it["dialogue_id"]]
            m = it["m_turn"] > 0
            if m.any():
                ys.append(it["y_turn"][m])
                ss.append(o["tactic"][m])
            if it["m_dlg"].sum() > 0:
                yd.append(it["y_dlg"])
                sd.append(o["tactic"].max(axis=0))
        aps = []
        pairs = []
        if ys:
            pairs.append((np.concatenate(ys), np.concatenate(ss)))  # turn level: [n_turns, 10]
        if yd:
            pairs.append((np.stack(yd), np.stack(sd)))  # dialogue level: [n_dialogues, 10]
        for Y, S in pairs:
            for j in range(Y.shape[1]):
                if 0 < Y[:, j].sum() < len(Y):
                    aps.append(average_precision_score(Y[:, j], S[:, j]))
        return float(np.mean(aps)) if aps else 0.0

    # -- interface
    def fit(self, train: list[dict], val: list[dict]) -> None:
        torch.manual_seed(self.seed)
        rng = np.random.default_rng(self.seed)
        if self.lexical and self._prefit_lex is not None:
            self.lex = self._prefit_lex
        elif self.lexical:
            self.log(f"  fitting lexical TF-IDF -> SVD({self.lexical_dim}) on {len(train):,} training turns ...")
            self.lex = LexicalSVD(self.lexical_dim, self.seed).fit([r["text"] for r in train])
        tr, Etr = self._items(train)
        va, Eva = self._items(val)
        self.net = M3Net(Etr.shape[1], d=self.d, variant=self.variant, dropout=self.dropout)
        opt = torch.optim.AdamW(self.net.parameters(), lr=self.lr, weight_decay=1e-4)
        pos_w = torch.as_tensor(pos_weights(tr, clip=self.pos_clip))
        best, best_state, bad = -1.0, None, 0
        steps_total = self.epochs * max(1, math.ceil(len(tr) / self.batch_size))
        step = 0
        self.history = []
        for ep in range(1, self.epochs + 1):
            self.net.train()
            t0, agg = time.time(), {}
            for b in batches(tr, self.batch_size, rng):
                p = step / steps_total
                lam = self.lam_max * (2.0 / (1.0 + math.exp(-10 * p)) - 1.0)  # DANN schedule
                t = _tensors(pad_batch(b), Etr)
                role_in = t["role_in"]
                if self.role_dropout > 0:
                    # hide some roles, so the role head must infer the speaker's role from the text
                    # (otherwise it just copies its input) and the tactic heads don't over-rely on it
                    hide = (torch.rand(role_in.shape) < self.role_dropout) & t["mask"]
                    role_in = role_in.masked_fill(hide, 2)
                out = self.net(t["E"], role_in, t["mask"], lam)
                loss, parts = m3_loss(out, t, pos_w, self.w)
                opt.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(self.net.parameters(), 5.0)
                opt.step()
                step += 1
                for k, v in parts.items():
                    agg[k] = agg.get(k, 0.0) + v
            score = self._val_score(va, Eva)
            nb = max(1, math.ceil(len(tr) / self.batch_size))
            self.history.append({"epoch": ep, "val_map": score, **{k: v / nb for k, v in agg.items()}})
            self.log(f"  epoch {ep:2d}  val mAP {score:.3f}  " + "  ".join(f"{k} {v / nb:.3f}" for k, v in agg.items())
                     + f"  ({time.time() - t0:.0f}s)")
            if score > best + 1e-4:
                best, bad = score, 0
                best_state = {k: v.detach().clone() for k, v in self.net.state_dict().items()}
            else:
                bad += 1
                if bad >= self.patience:
                    self.log(f"  early stop at epoch {ep} (best val mAP {best:.3f})")
                    break
        if best_state is not None:
            self.net.load_state_dict(best_state)
        self.best_val = best

    def predict(self, records: list[dict]) -> tuple[np.ndarray, np.ndarray]:
        items, E = self._items(records)
        outs = self._forward_all(items, E)
        pos = {(r["dialogue_id"], r["turn_id"]): i for i, r in enumerate(records)}
        S = np.zeros((len(records), len(TACTICS)))
        G = np.zeros((len(records), len(GENRES)))
        self.last_roles = np.zeros((len(records), 2))
        for o in outs:
            for k, tid in enumerate(o["turn_ids"]):
                i = pos[(o["dialogue_id"], tid)]
                S[i], G[i], self.last_roles[i] = o["tactic"][k], o["genre"][k], o["role"][k]
        return S, G

    def save(self, out_dir: Path) -> None:
        out_dir.mkdir(parents=True, exist_ok=True)
        torch.save(self.net.state_dict(), out_dir / "m3.pt")
        proj = self.net.proj[0] if isinstance(self.net.proj, nn.ModuleList) else self.net.proj
        if self.lex is not None:
            import pickle
            with open(out_dir / "lexical_svd.pkl", "wb") as f:
                pickle.dump(self.lex, f)
        cfg = {"variant": self.variant, "d": self.d, "in_dim": proj.in_features, "lexical": self.lex is not None,
               "role_dropout": self.role_dropout, "pos_clip": self.pos_clip, "dropout": self.dropout,
               "encoder": self.cache.model_name, "weights": self.w, "best_val_map": getattr(self, "best_val", None),
               "history": getattr(self, "history", [])}
        (out_dir / "m3_config.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
