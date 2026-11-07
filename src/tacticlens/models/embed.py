"""Frozen sentence embeddings with a disk cache (FR-FEA-03). Shared by M2 and M3.

Model: sentence-transformers/all-MiniLM-L6-v2 (22M parameters, 384-dim, fast on CPU).
Long texts (PsyScam reports average 133 words, up to 1,337) are split into overlapping
word chunks and their embeddings averaged, so nothing past the model's window is lost.
Identical texts are embedded once. The cache maps a text hash -> row, so re-running only
embeds new texts.

Files: models/embeddings/<model-name>.npy and .keys.json
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_WORDS, OVERLAP_WORDS = 160, 40


def text_key(text: str) -> str:
    return hashlib.blake2b(text.encode("utf-8"), digest_size=12).hexdigest()


def chunks(text: str, size: int = CHUNK_WORDS, overlap: int = OVERLAP_WORDS) -> list[str]:
    words = text.split()
    if len(words) <= size:
        return [text]
    out, step = [], size - overlap
    for start in range(0, len(words), step):
        out.append(" ".join(words[start:start + size]))
        if start + size >= len(words):
            break
    return out


class EmbeddingCache:
    def __init__(self, cache_dir: Path, model_name: str = DEFAULT_MODEL, encoder=None):
        self.dir = Path(cache_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.model_name = model_name
        stem = model_name.replace("/", "__")
        self.vec_path, self.key_path = self.dir / f"{stem}.npy", self.dir / f"{stem}.keys.json"
        self._encoder = encoder  # tests pass a fake: callable(list[str]) -> np.ndarray
        if self.vec_path.exists() and self.key_path.exists():
            self.vecs = np.load(self.vec_path)
            self.keys = json.loads(self.key_path.read_text(encoding="utf-8"))
        else:
            self.vecs, self.keys = None, {}

    def _encode(self, texts: list[str], batch_size: int = 64) -> np.ndarray:
        if self._encoder is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as e:
                raise SystemExit("M2/M3 need sentence-transformers: pip install -r requirements-ml.txt") from e
            self._encoder = SentenceTransformer(self.model_name, device="cpu")
        if callable(self._encoder) and not hasattr(self._encoder, "encode"):
            return np.asarray(self._encoder(texts), dtype=np.float32)
        return np.asarray(self._encoder.encode(texts, batch_size=batch_size, show_progress_bar=len(texts) > 2000,
                                               normalize_embeddings=True, convert_to_numpy=True), dtype=np.float32)

    def embed(self, texts: list[str], log=print) -> np.ndarray:
        new = {}
        for t in texts:
            k = text_key(t)
            if k not in self.keys and k not in new:
                new[k] = t
        if new:
            log(f"Embedding {len(new):,} new texts with {self.model_name} (cached afterwards) ...")
            pieces, owner = [], []
            for j, (k, t) in enumerate(new.items()):
                for c in chunks(t):
                    pieces.append(c)
                    owner.append(j)
            E = self._encode(pieces)
            owner = np.array(owner)
            V = np.stack([E[owner == j].mean(axis=0) for j in range(len(new))]).astype(np.float32)
            V /= np.linalg.norm(V, axis=1, keepdims=True) + 1e-8
            base = 0 if self.vecs is None else len(self.vecs)
            for j, k in enumerate(new):
                self.keys[k] = base + j
            self.vecs = V if self.vecs is None else np.vstack([self.vecs, V])
            np.save(self.vec_path, self.vecs)
            self.key_path.write_text(json.dumps(self.keys), encoding="utf-8")
        return self.vecs[[self.keys[text_key(t)] for t in texts]]
