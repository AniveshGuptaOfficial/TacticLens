"""Role per turn (FR-TAX-04).

P4G: persuader (B4 = 0) = actor, persuadee (B4 = 1) = target.
SMS and PsyScam: the sender / scammer = actor.
MentalManip: the files don't mark who manipulates, so roles stay "unknown" until the
check set is annotated; M3's role head predicts them elsewhere.
"""

from __future__ import annotations


def p4g_role(b4) -> str:
    try:
        v = int(float(b4))
    except (TypeError, ValueError):
        s = str(b4).strip().upper()
        return {"ER": "actor", "EE": "target", "PERSUADER": "actor", "PERSUADEE": "target"}.get(s, "unknown")
    return {0: "actor", 1: "target"}.get(v, "unknown")


def single_message_role() -> str:
    return "actor"


def mentalmanip_role() -> str:
    return "unknown"
