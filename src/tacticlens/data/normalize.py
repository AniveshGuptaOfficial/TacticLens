"""Text normalisation (FR-DAT-04).

Unicode NFC, HTML stripped, URLs / e-mails / phone numbers masked with tokens,
whitespace collapsed. Case and punctuation are kept: they carry tactic cues ("URGENT!!!").
"""

from __future__ import annotations

import html
import re
import unicodedata

URL_TOKEN, EMAIL_TOKEN, PHONE_TOKEN = "<URL>", "<EMAIL>", "<PHONE>"

_TAG = re.compile(r"<(?!/?(?:URL|EMAIL|PHONE)>)[^<>]{1,200}>")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")
_URL = re.compile(
    r"(?:(?:https?://|www\.)[^\s<>\"']+)"
    r"|(?:\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|net|org|in|co|info|io|ly|me|biz|xyz|top|uk|us)"
    r"(?:/[^\s<>\"']*)?)",
    re.IGNORECASE,
)
# 7+ digits, optionally with +, spaces, dots, dashes or brackets between them.
_PHONE = re.compile(r"(?<![\w<])\+?\d(?:[\s().-]?\d){6,}(?![\w>])")
_WS = re.compile(r"\s+")


def normalize(text: str | None) -> str:
    if text is None:
        return ""
    t = str(text)
    t = unicodedata.normalize("NFC", t)
    t = html.unescape(t)
    t = _TAG.sub(" ", t)
    t = _EMAIL.sub(EMAIL_TOKEN, t)
    t = _URL.sub(URL_TOKEN, t)
    t = _PHONE.sub(PHONE_TOKEN, t)
    t = _WS.sub(" ", t).strip()
    return t


def dedupe_key(text: str) -> str:
    """Key for exact-duplicate detection: lower-case letters and digits only."""
    return re.sub(r"[^a-z0-9]+", "", text.lower())
