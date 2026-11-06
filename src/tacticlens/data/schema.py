"""Unified record schema (SRS section 6.3, FR-DAT-03).

One record = one turn. A single SMS or scam report is a dialogue with one turn.

`label_level` says how much tactic supervision a record has:
  "turn"     -> `tactics` holds this turn's labels ([] means no tactic, on purpose)
  "dialogue" -> labels exist only for the whole dialogue, in meta["dialogue_tactics"]; `tactics` is None
  "none"     -> no tactic labels at all; `tactics` is None
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

GENRES = ("persuasion", "manipulation", "scam", "neutral")
ROLES = ("actor", "target", "unknown")
SOURCES = ("human", "llm")
LABEL_LEVELS = ("turn", "dialogue", "none")


@dataclass
class Span:
    tactic: str
    start: int
    end: int


@dataclass
class Record:
    dialogue_id: str
    turn_id: int
    speaker: str
    role: str
    text: str
    genre: str
    source: str
    dataset: str
    label_level: str = "none"
    tactics: list[str] | None = None
    spans: list[Span] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if self.genre not in GENRES:
            raise ValueError(f"bad genre {self.genre!r} in {self.dialogue_id}")
        if self.role not in ROLES:
            raise ValueError(f"bad role {self.role!r} in {self.dialogue_id}")
        if self.source not in SOURCES:
            raise ValueError(f"bad source {self.source!r} in {self.dialogue_id}")
        if self.label_level not in LABEL_LEVELS:
            raise ValueError(f"bad label_level {self.label_level!r}")
        if self.label_level == "turn" and self.tactics is None:
            raise ValueError(f"turn-level record without tactics list: {self.dialogue_id}")
        for s in self.spans:
            if not (0 <= s.start < s.end <= len(self.text)):
                raise ValueError(f"span {s} outside text of {self.dialogue_id}/{self.turn_id}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "Record":
        d = dict(d)
        d["spans"] = [Span(**s) for s in d.get("spans", [])]
        return Record(**d)
