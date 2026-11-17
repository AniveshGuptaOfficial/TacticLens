"""Dialogue tensors for M3 (NumPy only, so it can be tested without PyTorch).

One item per dialogue:
  emb_idx       [T]     row of each turn in the embedding matrix
  role_in       [T]     0 actor, 1 target, 2 unknown  (input to the model)
  role_y        [T]     0 actor, 1 target, -1 unknown (target for the role head)
  y_turn        [T,10]  turn-level tactic labels
  m_turn        [T]     1 where the turn carries turn-level labels
  y_dlg         [10]    dialogue-level tactic labels (MentalManip)
  m_dlg         [10]    1 for tactics the dialogue label speaks about (MIL_TACTICS), else 0
  genre         int     the dialogue's genre
  domain        int     the source dataset (target of the adversarial head)
"""

from __future__ import annotations

from collections import OrderedDict

import numpy as np

from .common import GENRE_INDEX, TACTICS, dialogue_labels, turn_labels

ROLE_IN = {"actor": 0, "target": 1, "unknown": 2}
ROLE_Y = {"actor": 0, "target": 1, "unknown": -1}
DOMAINS = ["p4g", "mentalmanip", "psyscam", "sms_human", "sms_llm"]
# tactics that MentalManip's dialogue labels can speak about (see configs/taxonomy.yaml)
MIL_TACTICS = ["T6", "T7", "T8", "T9", "T10"]


def build_dialogues(records: list[dict], row_of_text) -> list[dict]:
    """records -> dialogue items (turn order kept). row_of_text(text) gives the embedding row."""
    groups: "OrderedDict[str, list[dict]]" = OrderedDict()
    for r in records:
        groups.setdefault(r["dialogue_id"], []).append(r)
    mil = np.array([1 if t in MIL_TACTICS else 0 for t in TACTICS], dtype=np.float32)
    items = []
    for did, turns in groups.items():
        turns = sorted(turns, key=lambda r: r["turn_id"])
        first = turns[0]
        m_turn = np.array([1 if r["label_level"] == "turn" else 0 for r in turns], dtype=np.float32)
        # a MentalManip dialogue keeps its MIL label when some of its turns got hand labels
        is_dlg = any(r["label_level"] == "dialogue" or (r.get("meta") or {}).get("source_label_level") == "dialogue"
                     for r in turns)
        items.append({
            "dialogue_id": did,
            "turn_ids": [r["turn_id"] for r in turns],
            "emb_idx": np.array([row_of_text(r["text"]) for r in turns], dtype=np.int64),
            "role_in": np.array([ROLE_IN[r["role"]] for r in turns], dtype=np.int64),
            "role_y": np.array([ROLE_Y[r["role"]] for r in turns], dtype=np.int64),
            "y_turn": np.stack([turn_labels(r) for r in turns]).astype(np.float32),
            "m_turn": m_turn,
            "y_dlg": dialogue_labels(first).astype(np.float32) if is_dlg else np.zeros(len(TACTICS), np.float32),
            "m_dlg": mil if is_dlg else np.zeros(len(TACTICS), np.float32),
            "genre": GENRE_INDEX[first["genre"]],
            "domain": DOMAINS.index(first["dataset"]) if first["dataset"] in DOMAINS else len(DOMAINS) - 1,
        })
    return items


def evidence_records(records: list[dict], min_words: int = 3) -> list[dict]:
    """Extra training turns made of annotated evidence alone (the "evidence-span" signal).

    M3 sees a turn only through one frozen sentence embedding, so it cannot be told directly
    which words matter. Instead every evidence span of a labelled training turn (a PsyScam
    quote fragment, a P4G strategy sentence) becomes its own one-turn example labelled with the
    tactics that span is evidence for. The model then has to recognise each tactic from its
    evidence without the rest of the turn around it.
    """
    out = []
    for r in records:
        if r.get("label_level") != "turn" or not r.get("spans"):
            continue
        by_span: dict[tuple[int, int], set[str]] = {}
        for s in r["spans"]:
            if s["tactic"] in TACTICS:  # skip flagged extras such as X_SOCIAL_PROOF
                by_span.setdefault((s["start"], s["end"]), set()).add(s["tactic"])
        for k, ((a, b), tacs) in enumerate(sorted(by_span.items())):
            text = " ".join(r["text"][a:b].split())
            if len(text.split()) < min_words:
                continue
            out.append({**r, "dialogue_id": f"{r['dialogue_id']}#ev{r['turn_id']}.{k}", "turn_id": 0, "text": text,
                        "tactics": sorted(tacs, key=lambda t: int(t[1:])), "spans": [],
                        "meta": {**(r.get("meta") or {}), "evidence_of": r["dialogue_id"]}})
    return out


def pad_batch(items: list[dict]) -> dict[str, np.ndarray]:
    """Right-pad a list of dialogues to the longest one. `mask` marks real turns."""
    B, T, K = len(items), max(len(it["emb_idx"]) for it in items), len(TACTICS)
    out = {
        "emb_idx": np.zeros((B, T), np.int64), "role_in": np.full((B, T), 2, np.int64),
        "role_y": np.full((B, T), -1, np.int64), "y_turn": np.zeros((B, T, K), np.float32),
        "m_turn": np.zeros((B, T), np.float32), "mask": np.zeros((B, T), bool),
        "y_dlg": np.stack([it["y_dlg"] for it in items]), "m_dlg": np.stack([it["m_dlg"] for it in items]),
        "genre": np.array([it["genre"] for it in items], np.int64),
        "domain": np.array([it["domain"] for it in items], np.int64),
    }
    for b, it in enumerate(items):
        n = len(it["emb_idx"])
        for k in ("emb_idx", "role_in", "role_y", "m_turn"):
            out[k][b, :n] = it[k]
        out["y_turn"][b, :n] = it["y_turn"]
        out["mask"][b, :n] = True
    return out


def batches(items: list[dict], batch_size: int, rng: np.random.Generator | None = None):
    """Length-bucketed batches: sort by length inside shuffled chunks, so padding stays small."""
    order = np.arange(len(items))
    if rng is not None:
        rng.shuffle(order)
    chunk = batch_size * 20
    out = []
    for s in range(0, len(order), chunk):
        part = sorted(order[s:s + chunk], key=lambda i: len(items[i]["emb_idx"]))
        out.extend(part[k:k + batch_size] for k in range(0, len(part), batch_size))
    if rng is not None:
        rng.shuffle(out)
    return [[items[i] for i in b] for b in out]


def pos_weights(items: list[dict], clip: float = 20.0) -> np.ndarray:
    """Per-tactic positive weight for the BCE loss, from turn- and dialogue-level labels."""
    pos = np.zeros(len(TACTICS))
    tot = np.zeros(len(TACTICS))
    for it in items:
        m = it["m_turn"][:, None]
        pos += (it["y_turn"] * m).sum(axis=0) + it["y_dlg"] * it["m_dlg"]
        tot += m.sum() + it["m_dlg"]
    w = (tot - pos) / np.maximum(pos, 1.0)
    return np.clip(w, 1.0, clip).astype(np.float32)
