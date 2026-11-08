"""From pasted text to an explained answer: which tactics, in which turn, on what evidence.

For every turn the model gives tactic probabilities; a tactic counts as used when its
probability reaches the validation-tuned threshold of the chosen mode:

  balanced   thresholds tuned for F1 (the main results; catches more, some false alarms)
  careful    thresholds tuned for accuracy (fewer false alarms, misses more)

Evidence: for each tactic found in a turn of more than one sentence, every sentence is scored
on its own and the highest-scoring one is shown. The final model was trained on evidence-only
turns as well, and the grounding audit found its evidence alone is enough for its decision
(sufficiency <= 0), so the sentence that scores highest alone is a fair pointer to why.

Whole-conversation result (2+ turns): max over turns against the dialogue-level thresholds,
tuned on MentalManip conversations.
"""

from __future__ import annotations

import numpy as np

from ..data.normalize import normalize
from .parse import Turn, parse_conversation, roles_for, sentences

GROUP_ORDER = ("manipulative", "pressure", "legitimate")
VERDICTS = {
    "manipulative": "Manipulation signals",
    "pressure": "Pressure tactics",
    "legitimate": "Persuasion with legitimate appeals",
    None: "No influence tactic found",
}
DISCLAIMER = ("TacticLens is a research prototype. It flags patterns a model learned from three research "
              "datasets; it can be wrong and is not proof of intent. Use your own judgement.")


class Predictor:
    def __init__(self, engine, bundle: dict):
        """bundle: thresholds {"balanced": [[turn x10], [dialogue x10]], "careful": ...},
        tactics [{"id", "name", "group"}], genres [...]."""
        self.engine = engine
        self.tactics = bundle["tactics"]
        self.ids = [t["id"] for t in self.tactics]
        self.genres = bundle["genres"]
        self.th = {k: np.asarray(v, dtype=float) for k, v in bundle["thresholds"].items()}
        self.model_name = bundle.get("model", "TacticLens")

    def modes(self) -> list[str]:
        return list(self.th)

    def analyze(self, text: str, actor: str | None = None, mode: str = "balanced", evidence: bool = True) -> dict:
        turns = parse_conversation(text)
        if not turns:
            return {"turns": [], "verdict": VERDICTS[None], "summary": [], "genre": None, "disclaimer": DISCLAIMER,
                    "mode": mode}
        th_t, th_d = self.th.get(mode, self.th["balanced"])
        roles = roles_for(turns, actor)
        out = self.engine.run([t.text for t in turns], roles)
        P = np.asarray(out["tactic"], dtype=float)
        G = np.asarray(out["genre"], dtype=float)
        R = np.asarray(out["role"], dtype=float)

        hits = [[j for j in range(len(self.ids)) if P[i, j] >= th_t[j]] for i in range(len(turns))]
        ev = self._evidence(turns, roles, hits) if evidence else {}
        res_turns = []
        for i, (t, role) in enumerate(zip(turns, roles)):
            found = []
            for j in sorted(hits[i], key=lambda j: -P[i, j]):
                tac = self.tactics[j]
                found.append({"id": tac["id"], "name": tac["name"], "group": tac["group"],
                              "score": round(float(P[i, j]), 3), "threshold": round(float(th_t[j]), 3),
                              "evidence": ev.get((i, j))})
            res_turns.append({"index": i, "speaker": t.speaker, "role": role, "text": t.raw,
                              "model_text": t.text, "tactics": found,
                              "predicted_role": {"actor": round(float(R[i, 0]), 3), "target": round(float(R[i, 1]), 3)}
                              if R.ndim == 2 and R.shape[1] == 2 else None})

        # conversation level
        if len(turns) > 1:
            focus = [i for i, r in enumerate(roles) if r == "actor"] or list(range(len(turns)))
            pooled = P[focus].max(axis=0)
            conv = [j for j in range(len(self.ids)) if pooled[j] >= th_d[j]]
            conv = sorted(set(conv) | {j for i in focus for j in hits[i]}, key=lambda j: -pooled[j])
            summary = [{"id": self.ids[j], "name": self.tactics[j]["name"], "group": self.tactics[j]["group"],
                        "score": round(float(pooled[j]), 3),
                        "turns": [i for i in focus if j in hits[i]]} for j in conv]
        else:
            summary = [{"id": d["id"], "name": d["name"], "group": d["group"], "score": d["score"], "turns": [0]}
                       for d in res_turns[0]["tactics"]]
        g = G.mean(axis=0)
        groups = {s["group"] for s in summary}
        top = next((grp for grp in GROUP_ORDER if grp in groups), None)
        return {
            "verdict": VERDICTS[top],
            "groups_found": [grp for grp in GROUP_ORDER if grp in groups],
            "summary": summary,
            "genre": {"label": self.genres[int(g.argmax())], "probs": dict(zip(self.genres, np.round(g, 3).tolist()))},
            "turns": res_turns,
            "mode": mode,
            "checked_speaker": actor or None,
            "disclaimer": DISCLAIMER,
        }

    def _evidence(self, turns: list[Turn], roles: list[str], hits: list[list[int]]) -> dict:
        """(turn, tactic) -> {"text", "start", "end", "score"}: the sentence that alone scores highest."""
        jobs, texts, rl = [], [], []
        for i, t in enumerate(turns):
            if not hits[i]:
                continue
            spans = sentences(t.raw)
            if len(spans) < 2:
                continue
            for s, e in spans:
                jobs.append((i, s, e))
                texts.append(normalize(t.raw[s:e]))
                rl.append(roles[i])
        ev: dict = {}
        if jobs:
            P = np.asarray(self.engine.run(texts, rl)["tactic"], dtype=float)
            for i in {j[0] for j in jobs}:
                rows = [k for k, job in enumerate(jobs) if job[0] == i]
                for j in hits[i]:
                    k = max(rows, key=lambda k: P[k, j])
                    _, s, e = jobs[k]
                    ev[(i, j)] = {"text": turns[i].raw[s:e], "start": s, "end": e, "score": round(float(P[k, j]), 3)}
        for i, t in enumerate(turns):  # one-sentence turns: the whole turn is the evidence
            for j in hits[i]:
                ev.setdefault((i, j), {"text": t.raw, "start": 0, "end": len(t.raw), "score": None})
        return ev
