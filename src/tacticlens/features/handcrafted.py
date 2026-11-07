"""Cue-lexicon and stylometric features for M1 (FR-FEA-02).

Per turn, a small dense vector:
  lexicon      count of cue hits per tactic (T1-T10), and whether any hit (10 + 10)
  stylometry   length in words and chars, mean word length, share of capitals, digits,
               exclamation and question marks, <URL>/<PHONE>/<EMAIL> tokens, 2nd-person
               pronouns, 1st-person pronouns, Flesch reading ease (approx.)  (13)
The stylometry set follows the cue types used by CuePhish (IEEE #16) to separate
LLM-written from human-written phishing.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np

from ..config import PROJECT_ROOT, load_yaml

STYLO_NAMES = [
    "n_words", "n_chars", "mean_word_len", "caps_ratio", "digit_ratio", "excl_per_word",
    "quest_per_word", "n_url", "n_phone", "n_email", "second_person", "first_person", "flesch",
]
_WORD = re.compile(r"[A-Za-z']+")
_VOWELS = re.compile(r"[aeiouy]+", re.I)


class Lexicon:
    def __init__(self, path: str | Path | None = None):
        cfg = load_yaml(path or PROJECT_ROOT / "configs" / "lexicon.yaml")
        self.tactics = sorted(cfg, key=lambda t: int(t[1:]))
        self.patterns = {}
        for t in self.tactics:
            alts = []
            for cue in cfg[t]:
                c = re.escape(str(cue).lower())
                # whole word/phrase where the cue starts/ends with a letter, plain substring for symbols
                left = r"\b" if re.match(r"\w", str(cue)) else ""
                right = r"\b" if re.search(r"\w$", str(cue)) else ""
                alts.append(f"{left}{c}{right}")
            self.patterns[t] = re.compile("|".join(alts))

    def counts(self, text: str) -> np.ndarray:
        low = text.lower()
        return np.array([len(self.patterns[t].findall(low)) for t in self.tactics], dtype=np.float32)

    @property
    def names(self) -> list[str]:
        return [f"lex_{t}" for t in self.tactics] + [f"lex_{t}_any" for t in self.tactics]


def _syllables(word: str) -> int:
    return max(1, len(_VOWELS.findall(word)))


def stylometry(text: str) -> np.ndarray:
    words = _WORD.findall(text)
    nw = max(len(words), 1)
    nc = max(len(text), 1)
    sentences = max(len(re.findall(r"[.!?]+", text)), 1)
    syl = sum(_syllables(w) for w in words)
    flesch = 206.835 - 1.015 * (nw / sentences) - 84.6 * (syl / nw)
    low = [w.lower() for w in words]
    return np.array([
        len(words), len(text), sum(len(w) for w in words) / nw,
        sum(ch.isupper() for ch in text) / nc, sum(ch.isdigit() for ch in text) / nc,
        text.count("!") / nw, text.count("?") / nw,
        text.count("<URL>"), text.count("<PHONE>"), text.count("<EMAIL>"),
        sum(w in ("you", "your", "you're", "yours", "u", "ur") for w in low) / nw,
        sum(w in ("i", "me", "my", "i'm", "mine", "we", "our") for w in low) / nw,
        max(min(flesch, 120.0), -50.0),
    ], dtype=np.float32)


class HandcraftedFeatures:
    def __init__(self, lexicon_path: str | Path | None = None):
        self.lex = Lexicon(lexicon_path)
        self.names = self.lex.names + STYLO_NAMES

    def transform(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), len(self.names)), dtype=np.float32)
        k = len(self.lex.tactics)
        for i, t in enumerate(texts):
            c = self.lex.counts(t)
            out[i, :k] = c
            out[i, k:2 * k] = c > 0
            out[i, 2 * k:] = stylometry(t)
        return out
