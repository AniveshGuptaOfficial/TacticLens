"""Dataset loaders: raw files -> unified Records (FR-DAT-01, FR-DAT-03, FR-TAX-03, FR-TAX-04).

Each loader is defensive about file and column names, because the published files differ
in naming. Explicit names in configs/datasets.yaml always win over auto-detection.
"""

from __future__ import annotations

import ast
import json
import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import resolve
from ..taxonomy.mapping import Taxonomy
from ..taxonomy.roles import mentalmanip_role, p4g_role, single_message_role
from .io_utils import find_file, pick_column, read_table, split_label_list
from .normalize import normalize
from .schema import Record, Span

log = logging.getLogger(__name__)


def _isna(v) -> bool:
    try:
        return bool(pd.isna(v))
    except (TypeError, ValueError):
        return False


def _str_id(v) -> str:
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v).strip()


# --------------------------------------------------------------------------- P4G
def load_p4g(cfg: dict[str, Any], root: Path, tax: Taxonomy) -> list[Record]:
    d = resolve(root, cfg["dir"])
    cols = cfg.get("columns", {})
    c_did, c_role, c_text = cols.get("dialogue_id", "B2"), cols.get("role", "B4"), cols.get("text", "Unit")
    c_turn, c_er, c_er2 = cols.get("turn", "Turn"), cols.get("label_er", "er_label_1"), cols.get("label_er_2", "er_label_2")

    ann_path = find_file(d, ["*300_dialog*", "*annotated*dialog*"], cfg.get("annotated_dialog_file"))
    full_path = find_file(d, ["*full_dialog*"], cfg.get("full_dialog_file"))
    info_path = find_file(d, ["*full_info*", "*300_info*", "*info*"], cfg.get("info_file"))
    if not ann_path and not full_path:
        raise FileNotFoundError(f"P4G: no dialog file found in {d}")

    meta_by_dialogue = _p4g_info(info_path, c_did, c_role, cols.get("donation", "B6")) if info_path else {}
    records: list[Record] = []
    annotated_ids: set[str] = set()

    if ann_path:
        df = read_table(ann_path)
        er_cols = [c for c in (pick_column(df, None, [c_er], required=False), pick_column(df, None, [c_er2], required=False)) if c]
        for did, g in df.groupby(c_did, sort=False):
            did = _str_id(did)
            annotated_ids.add(did)
            records.extend(_p4g_dialogue(did, g, c_role, c_text, c_turn, er_cols, tax, meta_by_dialogue))

    if full_path:
        df = read_table(full_path)
        for did, g in df.groupby(c_did, sort=False):
            did = _str_id(did)
            if did in annotated_ids:
                continue
            records.extend(_p4g_dialogue(did, g, c_role, c_text, c_turn, None, tax, meta_by_dialogue))
    return records


def _p4g_info(path: Path, c_did: str, c_role: str, c_don: str) -> dict[str, dict]:
    df = read_table(path)
    out: dict[str, dict] = {}
    numeric = [c for c in df.columns if not str(c).startswith("B") and pd.api.types.is_numeric_dtype(df[c])]
    for _, row in df.iterrows():
        did = _str_id(row[c_did])
        role = p4g_role(row.get(c_role))
        m = out.setdefault(did, {})
        don = row.get(c_don)
        m[f"donation_{'ee' if role == 'target' else 'er'}"] = None if _isna(don) else float(don)
        if role == "target":
            m["persuadee_traits"] = {str(c): float(row[c]) for c in numeric if not _isna(row[c])}
    return out


def _p4g_dialogue(did, g, c_role, c_text, c_turn, er_cols, tax, meta_by_dialogue) -> list[Record]:
    """Rows may be sentences (annotated file) or whole turns (full file). Group by (turn, speaker).

    er_cols: the persuader label columns (er_label_1, er_label_2); None = unannotated dialogue.
    """
    labelled = bool(er_cols)
    turns: list[dict] = []
    for _, row in g.iterrows():
        role = p4g_role(row.get(c_role))
        key = (row.get(c_turn), role)
        sent = normalize(row.get(c_text))
        if not sent:
            continue
        if not turns or turns[-1]["key"] != key:
            turns.append({"key": key, "role": role, "sents": [], "labels": []})
        labs: list[str] = []
        if labelled and role == "actor":
            raw = [lab for c in er_cols for lab in split_label_list(row.get(c))]
            labs = tax.map_labels("p4g", raw)
        turns[-1]["sents"].append(sent)
        turns[-1]["labels"].append(labs)

    out = []
    meta = meta_by_dialogue.get(did, {})
    for i, t in enumerate(turns):
        text, spans, pos, tactics = "", [], 0, []
        for sent, labs in zip(t["sents"], t["labels"]):
            if text:
                text += " "
                pos += 1
            start = pos
            text += sent
            pos += len(sent)
            for tac in labs:
                spans.append(Span(tac, start, pos))
                if tac not in tactics:
                    tactics.append(tac)
        out.append(Record(
            dialogue_id=f"p4g_{did}", turn_id=i, speaker="ER" if t["role"] == "actor" else "EE",
            role=t["role"], text=text, genre="persuasion", source="human", dataset="p4g",
            label_level="turn" if labelled else "none",
            tactics=tactics if labelled else None, spans=spans if labelled else [],
            meta=dict(meta),
        ))
    return out


# ------------------------------------------------------------------- MentalManip
_SPEAKER = re.compile(r"(Person\s*\d+|[A-Z][A-Za-z]{0,20})\s*:\s*")


def parse_dialogue(text: str) -> list[tuple[str, str]]:
    """'Person1: hi\nPerson2: hello' -> [('Person1','hi'), ('Person2','hello')]."""
    text = str(text)
    lines = [ln for ln in re.split(r"\r?\n", text) if ln.strip()]
    turns: list[tuple[str, str]] = []
    if len(lines) > 1:
        for ln in lines:
            m = _SPEAKER.match(ln.strip())
            if m:
                turns.append((m.group(1).replace(" ", ""), ln.strip()[m.end():]))
            elif turns:
                turns[-1] = (turns[-1][0], turns[-1][1] + " " + ln.strip())
            else:
                turns.append(("unknown", ln.strip()))
        return turns
    parts = list(re.finditer(r"(Person\s*\d+)\s*:\s*", text))
    if not parts:
        return [("unknown", text)]
    for j, m in enumerate(parts):
        end = parts[j + 1].start() if j + 1 < len(parts) else len(text)
        turns.append((m.group(1).replace(" ", ""), text[m.end():end].strip()))
    return turns


def load_mentalmanip(cfg: dict[str, Any], root: Path, tax: Taxonomy) -> list[Record]:
    d = resolve(root, cfg["dir"])
    path = find_file(d, ["*mentalmanip_maj*", "*maj*", "*.csv"], cfg.get("file"))
    if not path:
        raise FileNotFoundError(f"MentalManip: no file found in {d}")
    df = read_table(path)
    cols = cfg.get("columns", {})
    c_id = pick_column(df, cols.get("id"), ["id", "ID", "dialogue_id"], required=False)
    c_dlg = pick_column(df, cols.get("dialogue"), ["dialogue", "Dialogue", "text", "conversation"])
    c_man = pick_column(df, cols.get("manipulative"), ["manipulative", "Manipulative", "label", "is_manipulative"])
    c_tech = pick_column(df, cols.get("technique"), ["technique", "Technique", "techniques"], required=False)
    c_vul = pick_column(df, cols.get("vulnerability"), ["vulnerability", "Vulnerability", "vulnerabilities"], required=False)

    records = []
    for i, row in df.iterrows():
        did = f"mm_{_str_id(row[c_id]) if c_id else i}"
        manip = str(row[c_man]).strip().lower() in ("1", "1.0", "yes", "true", "manipulative")
        techs = split_label_list(row[c_tech]) if c_tech else []
        dialogue_tactics = tax.map_labels("mentalmanip", techs) if manip else []
        meta = {
            "manipulative": manip,
            "techniques": techs,
            "vulnerabilities": split_label_list(row[c_vul]) if c_vul else [],
            "dialogue_tactics": dialogue_tactics,
        }
        for t, (spk, utt) in enumerate(parse_dialogue(row[c_dlg])):
            records.append(Record(
                dialogue_id=did, turn_id=t, speaker=spk, role=mentalmanip_role(),
                text=normalize(utt), genre="manipulation" if manip else "neutral",
                source="human", dataset="mentalmanip", label_level="dialogue",
                tactics=None, meta=dict(meta),
            ))
    return [r for r in records if r.text]


# ------------------------------------------------------------------------ SMS
def _sms_label(v) -> str:
    s = str(v).strip().lower()
    if s in ("ham", "legit", "legitimate", "0", "normal"):
        return "ham"
    if s in ("smishing", "phishing", "smish", "fraud", "scam"):
        return "smishing"
    if s in ("spam", "1"):
        return "spam"
    return s


def load_sms(name: str, cfg: dict[str, Any], root: Path, tax: Taxonomy) -> list[Record]:
    d = resolve(root, cfg["dir"])
    path = find_file(d, ["*.csv", "*.xlsx", "*.tsv", "*.json*"], cfg.get("file"))
    if not path:
        raise FileNotFoundError(f"{name}: no file found in {d}")
    df = read_table(path)
    cols = cfg.get("columns", {})
    c_lab = pick_column(df, cols.get("label"), ["label", "class", "category", "type", "v1", "target"])
    c_txt = pick_column(df, cols.get("text"), ["text", "message", "sms", "content", "msg", "v2", "body"])
    c_model = pick_column(df, None, ["model"], required=False)
    c_topic = pick_column(df, None, ["topic"], required=False)
    cleaner = None
    if cfg.get("clean_generated"):
        from .generate_llm_sms import clean as cleaner  # same cleaning as at generation time
        from .generate_llm_sms import is_leak
    records = []
    for i, row in df.iterrows():
        raw = row[c_txt]
        if cleaner and isinstance(raw, str):
            raw = cleaner(raw)
            if is_leak(raw):
                continue
        text = normalize(raw)
        if not text:
            continue
        lab = _sms_label(row[c_lab])
        records.append(Record(
            dialogue_id=f"{name}_{i}", turn_id=0, speaker="sender", role=single_message_role(),
            text=text, genre="neutral" if lab == "ham" else "scam", source=cfg.get("source", "human"),
            dataset=name, label_level="none", tactics=None,
            meta={"sms_label": lab, **({"model": str(row[c_model])} if c_model else {}),
                  **({"topic": str(row[c_topic])} if c_topic else {})},
        ))
    return records


# --------------------------------------------------------------------- PsyScam
def parse_structured(value):
    """A dict/list given as JSON or as a Python literal (PsyScam's PTs column uses single quotes)."""
    if not isinstance(value, str):
        return value
    s = value.strip()
    if not s or s[0] not in "[{":
        return value
    for parse in (json.loads, ast.literal_eval):
        try:
            return parse(s)
        except (ValueError, SyntaxError):
            continue
    return value


def _evidence_items(ev) -> list[tuple[str, str]]:
    """Accept {tech: quote}, {tech: [quotes]}, [{technique, quote}], or a string of these."""
    if ev is None or (isinstance(ev, float) and pd.isna(ev)):
        return []
    ev = parse_structured(ev)
    if isinstance(ev, str):
        return []
    items: list[tuple[str, str]] = []
    if isinstance(ev, dict):
        for k, v in ev.items():
            for q in v if isinstance(v, list) else [v]:
                items.append((str(k), str(q)))
    elif isinstance(ev, list):
        for e in ev:
            if isinstance(e, dict):
                tech = e.get("technique") or e.get("label") or e.get("type") or ""
                quote = e.get("quote") or e.get("evidence") or e.get("text") or ""
                items.append((str(tech), str(quote)))
    return items


def _alnum_index(text: str) -> tuple[str, list[int]]:
    """Lower-case letters/digits only, plus the position of each kept char in `text`."""
    keep, pos = [], []
    for i, ch in enumerate(text):
        if ch.isalnum():
            keep.append(ch.lower())
            pos.append(i)
    return "".join(keep), pos


def find_quote(text: str, quote: str) -> tuple[int, int] | None:
    """Find `quote` in `text`, ignoring case, spaces, punctuation and line breaks. Returns char span."""
    q, _ = _alnum_index(normalize(quote))
    if len(q) < 8:
        return None
    t, pos = _alnum_index(text)
    i = t.find(q)
    if i < 0:
        return None
    return pos[i], pos[i + len(q) - 1] + 1


def load_psyscam(cfg: dict[str, Any], root: Path, tax: Taxonomy, stats: dict | None = None) -> list[Record]:
    d = resolve(root, cfg["dir"])
    path = find_file(d, ["*.jsonl", "*.json", "*.csv", "*.xlsx"], cfg.get("file"))
    if not path:
        raise FileNotFoundError(f"PsyScam: no file found in {d}")
    df = read_table(path)
    cols = cfg.get("columns", {})
    c_id = pick_column(df, cols.get("id"), ["scam_id", "id", "report_id", "post_id"], required=False)
    c_txt = pick_column(df, cols.get("text"), ["scammer_text", "scammer_words", "text", "description", "content", "report", "post", "body"])
    c_tec = pick_column(df, cols.get("techniques"), ["PTs", "techniques", "psychological_techniques", "labels", "technique", "label"])
    c_ev = pick_column(df, cols.get("evidence"), ["evidence", "evidences", "rationale", "quotes", "PTs"], required=False)
    stats = stats if stats is not None else {}
    stats.setdefault("evidence_found", 0)
    stats.setdefault("evidence_missing", 0)

    records = []
    for i, row in df.iterrows():
        text = normalize(row[c_txt])
        if not text:
            continue
        tactics = tax.map_labels("psyscam", split_label_list(parse_structured(row[c_tec])))
        spans: list[Span] = []
        for tech, quote in _evidence_items(row[c_ev]) if c_ev else []:
            mapped = tax.map_labels("psyscam", [tech])
            # quotes may be several fragments joined by "..." -> one span per fragment found
            found = False
            for frag in re.split(r"\s*(?:\.\.\.|…)\s*", quote):
                hit = find_quote(text, frag)
                if not hit:
                    continue
                found = True
                for t in mapped:
                    spans.append(Span(t, hit[0], hit[1]))
            stats["evidence_found" if found else "evidence_missing"] += 1
        records.append(Record(
            dialogue_id=f"psyscam_{_str_id(row[c_id]) if c_id else i}", turn_id=0, speaker="scammer",
            role=single_message_role(), text=text, genre="scam", source="human", dataset="psyscam",
            label_level="turn", tactics=tactics, spans=spans, meta={},
        ))
    return records


# ----------------------------------------------------------------- DailyDialog
# Everyday English conversations (Li et al., IJCNLP 2017; CC BY-NC-SA 4.0), used as neutral turns
# with no tactic, so the model sees ordinary chat ("can I borrow your kettle?") as a negative.
# Only the official train and validation dialogues enter the pipeline, each keeping its own split
# (meta["fixed_split"]); the official test dialogues are kept out for `cli everyday`.
_DD_SPLITS = (("validation", "val"), ("valid", "val"), ("train", "train"), ("test", "test"))
_DD_DETOK = [(re.compile(r"\s+([,.!?;:%)\]])"), r"\1"), (re.compile(r"([(\[$])\s+"), r"\1"),
             (re.compile(r"\s*([\u2019'])\s*(s|m|re|ve|ll|d|t)\b", re.I), r"\1\2"),
             (re.compile(r"\s+(n[\u2019']t)\b", re.I), r"\1")]


def _dd_split_of(name: str) -> str | None:
    name = name.lower()
    return next((v for k, v in _DD_SPLITS if k in name), None)


def dd_detok(u: str) -> str:
    u = " ".join(u.split())
    for pat, rep in _DD_DETOK:
        u = pat.sub(rep, u)
    return u


def _dd_parse_text(raw: str) -> list[list[str]]:
    out = []
    for line in raw.splitlines():
        utts = [dd_detok(u) for u in line.split("__eou__")]
        utts = [u for u in utts if u]
        if utts:
            out.append(utts)
    return out


def read_dailydialog(d: Path) -> dict[str, list[list[str]]]:
    """{'train'|'val'|'test': [dialogue = list of utterances]} from what is in `d`:
    the original release (dialogues_<split>.txt, utterances ending in __eou__; folders or the
    release's zip files, nested zips too), or tables with a `dialog` column whose path names the
    split (e.g. the Hugging Face parquet export: train/0000.parquet)."""
    import io
    import zipfile

    d = Path(d)
    if not d.exists():
        raise FileNotFoundError(f"DailyDialog: folder {d} not found")
    found: dict[str, list[list[str]]] = {}

    def take(name: str, raw: bytes) -> None:
        base = Path(name).name.lower()
        if not (base.startswith("dialogues_") and base.endswith(".txt")) or "_act" in base or "_emotion" in base:
            return
        split = _dd_split_of(base)
        if split and split not in found:
            found[split] = _dd_parse_text(raw.decode("utf-8", errors="replace"))

    def walk_zip(zf: zipfile.ZipFile) -> None:
        for info in zf.infolist():
            if info.filename.lower().endswith(".zip"):
                walk_zip(zipfile.ZipFile(io.BytesIO(zf.read(info))))
            elif info.filename.lower().endswith(".txt"):
                take(info.filename, zf.read(info))

    for p in sorted(d.rglob("*")):
        if not p.is_file():
            continue
        suf = p.suffix.lower()
        if suf == ".txt":
            take(p.name, p.read_bytes())
        elif suf == ".zip":
            walk_zip(zipfile.ZipFile(p))
        elif suf in (".parquet", ".csv", ".jsonl", ".json"):
            split = _dd_split_of(str(p.relative_to(d)))
            if not split or split in found:
                continue
            df = pd.read_parquet(p) if suf == ".parquet" else read_table(p)
            col = next((c for c in df.columns if str(c).lower() in ("dialog", "dialogue", "utterances")), None)
            if col is None:
                continue
            dialogs = []
            for v in df[col]:
                utts = list(v) if not isinstance(v, str) else parse_structured(v) or v.split("__eou__")
                utts = [dd_detok(str(u)) for u in utts if str(u).strip()]
                if utts:
                    dialogs.append(utts)
            found[split] = dialogs
    if not found.get("train"):
        raise FileNotFoundError(f"DailyDialog: no train dialogues found in {d} (see configs/datasets.yaml)")
    return found


def load_dailydialog(cfg: dict[str, Any], root: Path, tax: Taxonomy) -> list[Record]:
    import numpy as np

    data = read_dailydialog(resolve(root, cfg["dir"]))
    caps = {"train": cfg.get("max_train_dialogues", 2500), "val": cfg.get("max_val_dialogues", 500)}
    rng = np.random.default_rng(cfg.get("seed", 42))
    records = []
    for split in ("train", "val"):
        dialogs = data.get(split, [])
        idx = np.arange(len(dialogs))
        if caps[split] and len(idx) > caps[split]:
            idx = np.sort(rng.choice(idx, size=caps[split], replace=False))
        for i in idx:
            for t, utt in enumerate(dialogs[i]):
                text = normalize(utt)
                if not text:
                    continue
                records.append(Record(
                    dialogue_id=f"dd_{split}_{i}", turn_id=t, speaker="AB"[t % 2], role="unknown",
                    text=text, genre="neutral", source="human", dataset="dailydialog",
                    label_level="turn", tactics=[], meta={"fixed_split": split},
                ))
    return records


LOADERS = {
    "p4g": lambda c, r, t: load_p4g(c, r, t),
    "mentalmanip": lambda c, r, t: load_mentalmanip(c, r, t),
    "sms_human": lambda c, r, t: load_sms("sms_human", c, r, t),
    "sms_llm": lambda c, r, t: load_sms("sms_llm", c, r, t),
    "sms_munoz": lambda c, r, t: load_sms("sms_munoz", c, r, t),
    "psyscam": lambda c, r, t: load_psyscam(c, r, t),
    "dailydialog": lambda c, r, t: load_dailydialog(c, r, t),
}
