"""Two ways to run the final model on new text, with the same interface:

  OnnxEngine   the deployed path: MiniLM and the M3 head as ONNX (int8 by default), tokenizers,
               and the TF-IDF->SVD features as plain scikit-learn objects. No PyTorch needed.
  TorchEngine  the research path: the trained M3 loaded with M3.load (any variant).

run(texts, roles) treats every text as a turn of its own (the final model has no context
window) and returns tactic probabilities [n, 10], genre probabilities [n, 4] and role
probabilities [n, 2] (actor, target).
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np

from ..models.embed import chunks

ROLE_IN = {"actor": 0, "target": 1, "unknown": 2}
MAX_TOKENS = 256  # all-MiniLM-L6-v2 max_seq_length


def lexical_features(lex: dict, texts: list[str]) -> np.ndarray:
    from scipy.sparse import hstack
    X = hstack([lex["word"].transform(texts), lex["char"].transform(texts)]).tocsr()
    Z = lex["svd"].transform(X).astype(np.float32)
    return Z / (np.linalg.norm(Z, axis=1, keepdims=True) + 1e-8)


def mean_pool(hidden: np.ndarray, mask: np.ndarray) -> np.ndarray:
    m = mask[..., None].astype(np.float32)
    v = (hidden * m).sum(axis=1) / np.clip(m.sum(axis=1), 1e-9, None)
    return v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-12)


class OnnxEngine:
    def __init__(self, bundle_dir: Path, int8: bool = True, threads: int | None = None):
        import onnxruntime as ort
        from tokenizers import Tokenizer

        self.dir = Path(bundle_dir)
        self.cfg = json.loads((self.dir / "bundle.json").read_text(encoding="utf-8"))
        so = ort.SessionOptions()
        if threads:
            so.intra_op_num_threads = threads
        suffix = "int8" if int8 else "fp32"
        prov = ["CPUExecutionProvider"]
        self.enc = ort.InferenceSession(str(self.dir / f"encoder_{suffix}.onnx"), so, providers=prov)
        self.head = ort.InferenceSession(str(self.dir / f"m3_{suffix}.onnx"), so, providers=prov)
        self.enc_inputs = {i.name for i in self.enc.get_inputs()}
        self.tok = Tokenizer.from_file(str(self.dir / "tokenizer" / "tokenizer.json"))
        self.tok.enable_truncation(MAX_TOKENS)
        self.tok.enable_padding(pad_id=0, pad_token="[PAD]")
        self.lex = None
        if self.cfg.get("lexical"):
            with open(self.dir / "lexical.pkl", "rb") as f:
                self.lex = pickle.load(f)

    def _encode(self, pieces: list[str], batch: int = 32) -> np.ndarray:
        out = np.zeros((len(pieces), self.cfg["embed_dim"]), dtype=np.float32)
        order = np.argsort([len(p) for p in pieces])  # similar lengths together = less padding
        for s in range(0, len(order), batch):
            idx = order[s:s + batch]
            enc = self.tok.encode_batch([pieces[i] for i in idx])
            ids = np.array([e.ids for e in enc], dtype=np.int64)
            mask = np.array([e.attention_mask for e in enc], dtype=np.int64)
            feeds = {"input_ids": ids, "attention_mask": mask}
            if "token_type_ids" in self.enc_inputs:
                feeds["token_type_ids"] = np.zeros_like(ids)
            hidden = self.enc.run(None, feeds)[0]
            out[idx] = mean_pool(hidden, mask)
        return out

    def embed(self, texts: list[str]) -> np.ndarray:
        """Same recipe as training (models/embed.py): long texts in overlapping word chunks, averaged."""
        pieces, owner = [], []
        for j, t in enumerate(texts):
            for c in chunks(t):
                pieces.append(c)
                owner.append(j)
        E = self._encode(pieces)
        owner = np.array(owner)
        V = np.stack([E[owner == j].mean(axis=0) for j in range(len(texts))]).astype(np.float32)
        return V / (np.linalg.norm(V, axis=1, keepdims=True) + 1e-8)

    def features(self, texts: list[str]) -> np.ndarray:
        E = self.embed(texts)
        if self.lex is not None:
            E = np.hstack([E, lexical_features(self.lex, texts)])
        return E.astype(np.float32)

    def run(self, texts: list[str], roles: list[str]) -> dict[str, np.ndarray]:
        if not texts:
            z = np.zeros((0, 1), dtype=np.float32)
            return {"tactic": z, "genre": z, "role": z}
        X = self.features(texts)
        r = np.array([ROLE_IN.get(x, 2) for x in roles], dtype=np.int64)
        tactic, genre, role = self.head.run(None, {"emb": X, "role": r})
        return {"tactic": tactic, "genre": genre, "role": role}


class TorchEngine:
    def __init__(self, root: Path, model_name: str):
        from ..models.m3 import M3
        self.m = M3.load(root / "models" / model_name, root / "models" / "embeddings", log=lambda *_: None)

    def run(self, texts: list[str], roles: list[str]) -> dict[str, np.ndarray]:
        recs = [{"dialogue_id": f"q{i}", "turn_id": 0, "text": t, "role": r, "label_level": "none",
                 "tactics": [], "spans": [], "genre": "neutral", "dataset": "app", "meta": {}}
                for i, (t, r) in enumerate(zip(texts, roles))]
        S, G = self.m.predict(recs)
        return {"tactic": S, "genre": G, "role": self.m.last_roles}
