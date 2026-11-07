"""Builds a tiny fake project (configs + all five raw datasets) in a temp folder.

The fixtures copy the real formats (column names, label strings) closely enough to exercise
every loader, but every row is synthetic.
"""

from __future__ import annotations

import random
import shutil
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]

ER_SENTS = {
    "logical-appeal": ["Every two dollars buys a vaccine for a child.", "Ninety percent of funds go to programs."],
    "emotion-appeal": ["Imagine a child going to bed hungry tonight.", "These families have lost everything."],
    "credibility-appeal": ["Save the Children is rated four stars by Charity Navigator.", "They have worked for a hundred years."],
    "personal-story": ["When my mother was ill a charity helped us.", "My cousin was helped by them once."],
    "foot-in-the-door": ["Could you give just one dollar today?", "Even a small amount like fifty cents helps."],
    "greeting": ["Hello, how are you today?", "Hi there, nice to meet you."],
}
EE_SENTS = ["I am not sure about donating.", "That sounds good to me.", "How much do they spend on admin?", "Okay I will think about it."]

MM_TECH = ["Denial", "Playing the Victim Role", "Intimidation", "Shaming or Belittlement", "Persuasion or Seduction"]
MM_LINES = {
    "Denial": "That never happened, you're imagining it again.",
    "Playing the Victim Role": "After everything I've done for you, this is how you treat me?",
    "Intimidation": "Don't you dare walk away from me or you'll regret it.",
    "Shaming or Belittlement": "You're so stupid, you can't do anything right.",
    "Persuasion or Seduction": "Come on, you know you want to, I'll make it worth your while.",
}
SMS = {
    "ham": ["Are we still meeting at 6?", "Call me when you reach home.", "Mom says dinner is ready.", "Can you send the notes from class?"],
    "smishing": ["URGENT: your SBI account will be blocked today. Verify at http://sbi-kyc.xyz/login now",
                 "Dear customer, your KYC expired. Update now at bit.ly/kyc-upd or call +91 98765 43210",
                 "You have won Rs 10,000! Claim your prize at www.prize-now.top before midnight",
                 "Your parcel is held. Pay the fee at http://ind-post.info/pay to release it today"],
    "spam": ["50% off all shoes this weekend only at our store!", "Get a free trial of our new app today, reply YES"],
}
PSY = {
    "Urgency and Scarcity": "You must pay within one hour or the offer expires.",
    "Authority and Impersonation": "This is officer Sharma from the cyber police department.",
    "Fear and Intimidation": "If you don't pay, a warrant will be issued for your arrest.",
    "Phantom Riches": "You have been selected to receive a cash reward of five lakh rupees.",
    "Liking": "You seem like such a kind and smart person, I trust you.",
}


def _write_p4g(d: Path, rng: random.Random) -> None:
    d.mkdir(parents=True)
    ann, full, info = [], [], []
    labels = list(ER_SENTS)
    for k in range(40):
        did = f"20180{k:03d}-ann"
        for turn in range(5):
            for _ in range(2):
                lab = rng.choice(labels)
                ann.append({"Unit": rng.choice(ER_SENTS[lab]), "Turn": turn, "B4": 0, "B2": did, "er_label_1": lab, "ee_label_1": None,
                            "er_label_2": "emotion-appeal" if lab == "personal-story" else None})
            ann.append({"Unit": rng.choice(EE_SENTS), "Turn": turn, "B4": 1, "B2": did, "er_label_1": None, "ee_label_1": "positive-reaction", "er_label_2": None})
        info += [{"B2": did, "B4": 0, "B6": 0.0, "extrovert": 3.0}, {"B2": did, "B4": 1, "B6": float(rng.choice([0, 0.5, 1, 2])), "extrovert": rng.uniform(1, 5)}]
    for k in range(20):
        did = f"20181{k:03d}-full"
        for turn in range(4):
            full.append({"Unit": rng.choice(ER_SENTS[rng.choice(labels)]) + f" Turn {turn}.", "Turn": turn, "B4": 0, "B2": did})
            full.append({"Unit": rng.choice(EE_SENTS) + f" Reply {turn}.", "Turn": turn, "B4": 1, "B2": did})
        info += [{"B2": did, "B4": 1, "B6": 1.0, "extrovert": 2.0}]
    pd.DataFrame(ann).to_excel(d / "300_dialog.xlsx", index=False)
    pd.DataFrame(full).to_csv(d / "full_dialog.csv", index=False)
    pd.DataFrame(info).to_csv(d / "full_info.csv", index=False)


def _write_mm(d: Path, rng: random.Random) -> None:
    d.mkdir(parents=True)
    rows = []
    for k in range(60):
        manip = k % 3 != 0
        techs = rng.sample(MM_TECH, 2) if manip else []
        lines = [f"Person1: Hey, can we talk about yesterday number {k}?"]
        for t in techs:
            lines.append(f"Person2: {MM_LINES[t]}")
            lines.append("Person1: I just want to understand what happened.")
        if not manip:
            lines.append("Person2: Sure, let's grab coffee and talk it through.")
        rows.append({"id": k, "dialogue": "\n".join(lines), "manipulative": int(manip),
                     "technique": ",".join(techs) if techs else None, "vulnerability": "Naivety" if manip else None})
    pd.DataFrame(rows).to_csv(d / "mentalmanip_maj.csv", index=False)


def _write_sms(d: Path, rng: random.Random, n: int, llm: bool) -> None:
    d.mkdir(parents=True)
    rows = []
    for i in range(n):
        lab = rng.choice(["ham", "ham", "smishing", "spam"])
        text = rng.choice(SMS[lab]) + (f" (ref {i * 7 + 3} {'AI' if llm else 'H'})")
        rows.append({"LABEL": lab.capitalize() if lab == "smishing" else lab, "TEXT": text})
    if not llm:
        pd.DataFrame(rows).to_csv(d / "Dataset_5971.csv", index=False)
    else:
        rows.append({"LABEL": "ham", "TEXT": "Are we still meeting at 6? (ref 3 H)"})  # an exact copy of a human one, maybe
        df = pd.DataFrame(rows)
        df["MODEL"] = ["qwen2.5:3b" if i % 2 else "llama3.2:3b" for i in range(len(df))]
        df["TOPIC"] = "test topic"
        df["PROMPT_ID"] = [f"m|x|{i}" for i in range(len(df))]
        df.to_csv(d / "llm_sms.csv", index=False)


def _write_psyscam(d: Path, rng: random.Random) -> None:
    """Same shape as the public D2.csv: PTs is a Python-literal dict {technique: quote}."""
    d.mkdir(parents=True)
    rows = []
    for k in range(60):
        techs = rng.sample(list(PSY), 2)
        text = f"Report {k}: The caller said hello.\n" + " ".join(PSY[t] for t in techs) + "\nThen they hung up."
        pts = {t: PSY[t] for t in techs}
        # one quote made of two fragments joined by " ... ", as in the real file
        first = techs[0]
        pts[first] = f"The caller said hello ... {PSY[first]}"
        rows.append({"scam_id": 900000 + k, "description": text, "dollars_lost": "", "scam_type": "Phishing", "PTs": repr(pts)})
    pd.DataFrame(rows).to_csv(d / "D2.csv", index=False)


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    root = tmp_path / "proj"
    shutil.copytree(REPO / "configs", root / "configs")
    rng = random.Random(0)
    raw = root / "data" / "raw"
    _write_p4g(raw / "p4g", rng)
    _write_mm(raw / "mentalmanip", rng)
    _write_sms(raw / "sms_human", rng, 80, llm=False)
    _write_sms(raw / "sms_llm_gen", rng, 80, llm=True)
    _write_psyscam(raw / "psyscam", rng)
    return root


def fake_encoder(dim: int = 64):
    """Deterministic stand-in for MiniLM: hashed bag of words, L2-normalised. No downloads."""
    import hashlib

    import numpy as np

    def enc(texts):
        out = np.zeros((len(texts), dim), dtype=np.float32)
        for i, t in enumerate(texts):
            for w in t.lower().split():
                h = int.from_bytes(hashlib.md5(w.encode()).digest()[:4], "little")
                out[i, h % dim] += 1.0 if (h >> 8) % 2 else -1.0
        n = np.linalg.norm(out, axis=1, keepdims=True)
        return out / np.maximum(n, 1e-8)

    return enc


@pytest.fixture()
def prepared(project):
    from tacticlens.config import load_datasets_config
    from tacticlens.data.pipeline import prepare, read_records
    from tacticlens.taxonomy.mapping import load_taxonomy

    cfg = load_datasets_config(project)
    tax = load_taxonomy(project / "configs" / "taxonomy.yaml")
    prepare(cfg, project, tax)
    return read_records(project / "data" / "processed" / "records.jsonl"), tax
