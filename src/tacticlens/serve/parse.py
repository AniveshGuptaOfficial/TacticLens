"""Turn what a user pastes into turns: one message, or a conversation written as "Name: text" lines."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..data.normalize import normalize

MAX_TURNS = 60
MAX_CHARS = 6000
# A speaker name: up to 40 characters with no colon (emoji allowed, e.g. a saved contact "Unknown 🫥").
_SPEAKER = re.compile(r"^\s*([^\s:\[\]][^:\n]{0,39}?)\s*:\s+(.+)$")
# WhatsApp timestamps in front of a line: "[6:01 PM, 11/2/2026] " (copied) or "11/2/26, 6:01 pm - " (exported).
_TIME = r"\d{1,2}[:.]\d{2}(?:[:.]\d{2})?(?:\s*[AaPp]\.?[Mm]\.?)?"
_DATE = r"\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}"
_STAMP = re.compile(rf"^\s*\[?\s*(?:{_TIME},\s*{_DATE}|{_DATE},?\s*{_TIME})\s*\]?\s*(?:-\s*)?")
_SENT = re.compile(r"(?<=[.!?])\s+(?=[\"'A-Z0-9<(])|\n+")


@dataclass
class Turn:
    speaker: str
    text: str  # normalised, as the model sees it
    raw: str   # as pasted, shown back to the user


def parse_conversation(text: str) -> list[Turn]:
    """Lines starting with "Name:" open a new turn; other lines continue the current one.
    WhatsApp timestamps in front of a line are removed first.
    With fewer than two such lines the whole input is one message (an SMS, an email, a post)."""
    text = (text or "")[:MAX_CHARS]
    lines = [_STAMP.sub("", ln, count=1) for ln in text.splitlines()]
    lines = [ln for ln in lines if ln.strip()]
    if not lines:
        return []
    if sum(bool(_SPEAKER.match(ln)) for ln in lines) < 2:  # "URGENT: ..." alone is a message, not a speaker
        raw = " ".join(ln.strip() for ln in lines)
        return [Turn("Message", normalize(raw), raw)]
    turns: list[list[str]] = []
    for ln in lines:
        m = _SPEAKER.match(ln)
        if m:
            turns.append([m.group(1).strip(), m.group(2).strip()])
        elif turns:
            turns[-1][1] += " " + ln.strip()
        else:
            turns.append(["Unknown", ln.strip()])
    return [Turn(s, normalize(t), t) for s, t in turns[:MAX_TURNS] if normalize(t)]


def roles_for(turns: list[Turn], actor: str | None) -> list[str]:
    """actor = the speaker the user wants checked (suspected persuader/manipulator/scammer).
    A single message is from its sender, so it counts as the actor."""
    if len(turns) == 1 and turns[0].speaker == "Message":
        return ["actor"]
    if actor:
        a = actor.strip().lower()
        return ["actor" if t.speaker.lower() == a else "target" for t in turns]
    return ["unknown"] * len(turns)


def sentences(text: str) -> list[tuple[int, int]]:
    """(start, end) character spans of the sentences in `text`."""
    spans, pos = [], 0
    for m in _SENT.finditer(text):
        if text[pos:m.start()].strip():
            spans.append((pos, m.start()))
        pos = m.end()
    if text[pos:].strip():
        spans.append((pos, len(text)))
    return spans or [(0, len(text))]
