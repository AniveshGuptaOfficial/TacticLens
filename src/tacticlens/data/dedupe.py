"""Exact and near-duplicate removal at dialogue level (FR-DAT-05).

Near duplicates: MinHash over character shingles + LSH banding, then an exact Jaccard check
(threshold 0.9 by default). The first dialogue seen is kept, so dataset order sets priority:
a Munoz-Islam SMS that copies a Mishra-Soni one is dropped, which is what O5 needs.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict

import numpy as np

from .normalize import dedupe_key

_PRIME = np.uint64(4294967311)  # smallest prime above 2**32; a*x + b stays below 2**64


def shingles(text: str, k: int = 5) -> set[int]:
    t = dedupe_key(text)
    if len(t) <= k:
        return {hash_str(t)} if t else set()
    return {hash_str(t[i:i + k]) for i in range(len(t) - k + 1)}


def hash_str(s: str) -> int:
    """32-bit hash, stable across runs (Python's hash() is not)."""
    return int.from_bytes(hashlib.blake2b(s.encode(), digest_size=4).digest(), "little")


def jaccard(a: set[int], b: set[int]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


class MinHasher:
    def __init__(self, num_perm: int = 64, seed: int = 42):
        rng = np.random.default_rng(seed)
        self.a = rng.integers(1, 2**32 - 1, size=num_perm, dtype=np.uint64)
        self.b = rng.integers(0, 2**32 - 1, size=num_perm, dtype=np.uint64)

    def signature(self, sh: set[int]) -> np.ndarray:
        if not sh:
            return np.zeros(len(self.a), dtype=np.uint64)
        x = np.fromiter(sh, dtype=np.uint64)
        return ((np.outer(self.a, x) + self.b[:, None]) % _PRIME).min(axis=1)


def find_duplicates(
    texts: dict[str, str], jaccard_threshold: float = 0.9, k: int = 5, num_perm: int = 64, bands: int = 16, seed: int = 42
) -> dict[str, tuple[str, str]]:
    """Return {dropped_id: (kept_id, 'exact'|'near')}. `texts` keeps insertion order = priority."""
    dropped: dict[str, tuple[str, str]] = {}
    exact_seen: dict[str, str] = {}
    keep_ids: list[str] = []
    for did, text in texts.items():
        key = dedupe_key(text)
        if key in exact_seen:
            dropped[did] = (exact_seen[key], "exact")
        else:
            exact_seen[key] = did
            keep_ids.append(did)

    mh = MinHasher(num_perm, seed)
    rows = num_perm // bands
    buckets: dict[tuple, list[str]] = defaultdict(list)
    sh_cache: dict[str, set[int]] = {}
    for did in keep_ids:
        sh = shingles(texts[did], k)
        sh_cache[did] = sh
        sig = mh.signature(sh)
        match = None
        cands: set[str] = set()
        for b in range(bands):
            cands.update(buckets.get((b, sig[b * rows:(b + 1) * rows].tobytes()), []))
        for c in cands:
            if jaccard(sh, sh_cache[c]) >= jaccard_threshold:
                match = c
                break
        if match:
            dropped[did] = (match, "near")
            continue
        for b in range(bands):
            buckets[(b, sig[b * rows:(b + 1) * rows].tobytes())].append(did)
    return dropped
