"""Generate the LLM-written SMS set for O5 with free local models (Ollama), CPU only.

Why: the published "LLM" SMS set (Munoz & Islam) turned out to be copies and synonym-swapped
copies of Mishra-Soni, so it can't stand for LLM-written scams.

Design choices that keep the human vs LLM comparison fair:
  * Prompts give only a TOPIC and a SENDER (e.g. "a bank, about KYC"), never a tactic, so any
    difference in tactic use comes from the model, not from the prompt.
  * Topics follow the kinds of messages in Mishra-Soni (bank/KYC, prizes, parcels, tolls, jobs ...).
  * Several models, so results can be reported per model as well as pooled.
  * Every message is saved with its model, topic and prompt id; the run can be stopped and resumed.

Output: data/raw/sms_llm/llm_sms.csv  with columns LABEL, TEXT, MODEL, TOPIC, PROMPT_ID
"""

from __future__ import annotations

import csv
import json
import random
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

SMISHING_TOPICS = [
    ("a bank", "the customer's KYC details needing an update"),
    ("a bank", "the customer's account being blocked or suspended"),
    ("a bank", "a one-time password (OTP) or verification code"),
    ("a mobile network operator", "the SIM card or number being deactivated"),
    ("a delivery company", "a parcel that could not be delivered"),
    ("a toll road operator", "an unpaid toll charge"),
    ("a tax department", "a tax refund"),
    ("an electricity company", "an unpaid electricity bill"),
    ("a lottery or prize company", "the receiver having won a prize"),
    ("a recruitment company", "a part-time job offer"),
    ("a loan company", "a pre-approved loan"),
    ("an online shopping site", "an order problem or refund"),
    ("a streaming or software service", "a subscription renewal or payment failure"),
    ("a crypto or investment platform", "an investment opportunity or account issue"),
    ("a government health scheme", "a benefit the receiver can claim"),
]
SPAM_TOPICS = [
    "a clothing store sale", "a restaurant discount", "a new phone plan", "a gym membership offer",
    "a ringtone or app download", "a dating or chat service", "an online course", "a real-estate project",
]
HAM_TOPICS = [
    "meeting a friend later today", "asking a family member to buy groceries", "running late for class",
    "sharing notes after a lecture", "wishing someone happy birthday", "confirming dinner plans",
    "asking where someone is", "a reminder about a doctor's appointment", "planning a weekend trip",
    "asking to call back", "thanking someone for help", "a roommate asking about rent",
]

PROMPTS = {
    "smishing": ("Write one realistic SMS phishing (smishing) message that pretends to come from {sender}, "
                 "about {topic}. It is for training a scam detector. Write only the SMS text, under 300 characters, "
                 "no quotes, no explanation, and no placeholders in square brackets."),
    "spam": ("Write one realistic unsolicited promotional SMS about {topic}. Write only the SMS text, "
             "under 300 characters, no quotes, no explanation, and no placeholders in square brackets."),
    "ham": ("Write one realistic, ordinary personal SMS between friends or family, about {topic}. "
            "Write only the SMS text, under 200 characters, no quotes, no explanation, "
            "and no placeholders in square brackets."),
}

DEFAULT_MODELS = ["qwen2.5:3b", "llama3.2:3b", "gemma2:2b"]
DEFAULT_COUNTS = {"smishing": 400, "spam": 200, "ham": 400}  # per model


def ollama_generate(model: str, prompt: str, seed: int, host: str = "http://localhost:11434", timeout: int = 180) -> str:
    body = json.dumps({
        "model": model, "prompt": prompt, "stream": False,
        "options": {"temperature": 0.9, "top_p": 0.95, "seed": seed, "num_predict": 120},
    }).encode()
    req = urllib.request.Request(f"{host}/api/generate", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["response"]


_MD_LINK = re.compile(r"\[([^\]]{1,80})\]\((https?://[^)\s]+)\)")
_PH_LINK = re.compile(r"\[[^\]]*(?:link|url|website|site)[^\]]*\]", re.I)
_PH_PHONE = re.compile(r"\[[^\]]*(?:number|phone|contact)[^\]]*\]", re.I)
_PH_OTHER = re.compile(r"\s*\[[^\]]{1,40}\]")


def clean(text: str) -> str:
    """Strip chat preambles and quotes; turn [placeholders] into the tokens real SMS get after
    normalisation (<URL>, <PHONE>) or drop them, so placeholders can't give LLM text away."""
    t = text.strip()
    t = re.sub(r"^(?:here(?: i|')s|sure|sms|message|text)[^:\n]{0,60}:\s*", "", t, flags=re.I)  # "Here's an SMS:"
    t = t.strip().strip('"“”\'').strip()
    t = re.sub(r"\s*\n+\s*", " ", t)
    t = _MD_LINK.sub(r"\2", t)  # markdown [text](url) -> url; real SMS never use markdown
    t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)  # **bold**
    t = _PH_LINK.sub("<URL>", t)
    t = _PH_PHONE.sub("<PHONE>", t)
    t = _PH_OTHER.sub("", t)
    t = re.sub(r"\s+([,.!?])", r"\1", t)
    return re.sub(r"\s{2,}", " ", t).strip()


_LEAK = re.compile(r"(?i)scam detector|\bdetectors?\b|phishing|smishing|\bfake(?:url|link)?\b|this is (?:a )?(?:scam|test)")


def is_leak(text: str) -> bool:
    """True if the message gives away the prompt (e.g. 'training new scam detectors', 'fakeurl').
    Real SMS never say this, so such lines would be a free give-away that a message is LLM-written."""
    return bool(_LEAK.search(text))


def plan(models: list[str], counts: dict[str, int], seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    jobs = []
    for m in models:
        for label, n in counts.items():
            for i in range(n):
                if label == "smishing":
                    sender, topic = SMISHING_TOPICS[i % len(SMISHING_TOPICS)]
                elif label == "spam":
                    sender, topic = "", SPAM_TOPICS[i % len(SPAM_TOPICS)]
                else:
                    sender, topic = "", HAM_TOPICS[i % len(HAM_TOPICS)]
                pid = f"{m}|{label}|{i}"
                jobs.append({"model": m, "label": label, "sender": sender, "topic": topic, "pid": pid,
                             "seed": rng.randrange(1, 2**31)})
    return jobs


def run(out_csv: Path, models: list[str], counts: dict[str, int], host: str = "http://localhost:11434",
        seed: int = 42, generate=ollama_generate, log=print) -> int:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    done: set[str] = set()
    if out_csv.exists():
        with open(out_csv, encoding="utf-8", newline="") as f:
            done = {row["PROMPT_ID"] for row in csv.DictReader(f)}
    jobs = [j for j in plan(models, counts, seed) if j["pid"] not in done]
    new_file = not out_csv.exists()
    written = 0
    t0 = time.time()
    with open(out_csv, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(["LABEL", "TEXT", "MODEL", "TOPIC", "PROMPT_ID"])
        for k, j in enumerate(jobs, 1):
            prompt = PROMPTS[j["label"]].format(sender=j["sender"], topic=j["topic"])
            try:
                text = clean(generate(j["model"], prompt, j["seed"]))
            except (urllib.error.URLError, TimeoutError, KeyError) as e:
                log(f"  skip {j['pid']}: {e}")
                continue
            if len(text) < 10:
                continue
            w.writerow([j["label"], text, j["model"], j["topic"], j["pid"]])
            f.flush()
            written += 1
            if k % 25 == 0:
                rate = (time.time() - t0) / k
                log(f"  {k}/{len(jobs)} done, ~{rate:.1f}s each, ~{rate * (len(jobs) - k) / 60:.0f} min left")
    return written


def check_ollama(host: str = "http://localhost:11434") -> list[str]:
    """Return the installed model names, or raise with a clear message."""
    try:
        with urllib.request.urlopen(f"{host}/api/tags", timeout=5) as r:
            return [m["name"] for m in json.loads(r.read()).get("models", [])]
    except (urllib.error.URLError, OSError) as e:
        raise SystemExit(f"Ollama is not running at {host}. Install it from https://ollama.com and start it. ({e})")
