"""`prepare`: raw datasets -> data/processed/ (FR-DAT-01 to FR-DAT-07, FR-TAX-03).

Outputs
  data/processed/records.jsonl     one unified record per turn, with its split
  data/processed/splits.csv        dialogue_id, dataset, genre, split
  data/processed/logo_splits.json  leave-one-genre-out splits
  reports/dedupe_removed.csv       which dialogues were dropped as duplicates, and why
  reports/unmapped_labels.csv      source labels that mapped to no tactic
  reports/prepare_summary.json     counts, and which datasets were missing
"""

from __future__ import annotations

import csv
import json
import logging
from collections import Counter, OrderedDict
from pathlib import Path
from typing import Any

from ..config import resolve
from ..taxonomy.mapping import Taxonomy
from .dedupe import find_duplicates
from .loaders import LOADERS
from .schema import Record
from .splits import dialogue_splits, logo_splits

log = logging.getLogger(__name__)

# Dedupe priority: earlier datasets keep their copy.
DATASET_ORDER = ("p4g", "mentalmanip", "psyscam", "sms_human", "sms_llm", "sms_munoz")


def load_all(cfg: dict[str, Any], root: Path, tax: Taxonomy, only: list[str] | None = None) -> tuple[list[Record], dict]:
    records: list[Record] = []
    status: dict[str, str] = {}
    for name in DATASET_ORDER:
        if name not in cfg["datasets"] or (only and name not in only):
            continue
        if cfg["datasets"][name].get("enabled", True) is False:
            status[name] = "disabled in configs/datasets.yaml"
            continue
        try:
            recs = LOADERS[name](cfg["datasets"][name], root, tax)
            for r in recs:
                r.validate()
            records.extend(recs)
            status[name] = f"ok ({len(recs)} turns)"
        except FileNotFoundError as e:
            status[name] = f"missing: {e}"
            log.warning("%s", e)
    return records, status


def prepare(cfg: dict[str, Any], root: Path, tax: Taxonomy, out_dir: Path | None = None, report_dir: Path | None = None) -> dict:
    out_dir = Path(out_dir or resolve(root, "data/processed"))
    report_dir = Path(report_dir or resolve(root, "reports"))
    out_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    records, status = load_all(cfg, root, tax)
    if not records:
        raise RuntimeError(f"no data loaded; status: {status}. Put datasets in data/raw/ (see README).")

    # dialogue texts in dataset priority order
    texts: "OrderedDict[str, str]" = OrderedDict()
    info: dict[str, tuple[str, str]] = {}
    for r in records:
        texts[r.dialogue_id] = (texts.get(r.dialogue_id, "") + " " + r.text).strip()
        info.setdefault(r.dialogue_id, (r.dataset, r.genre))

    dd = cfg.get("dedupe", {})
    dropped = find_duplicates(
        texts, dd.get("jaccard", 0.9), dd.get("shingle", 5), dd.get("num_perm", 64), dd.get("bands", 16), cfg.get("seed", 42)
    )
    with open(report_dir / "dedupe_removed.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["dropped_id", "dataset", "kept_id", "kept_dataset", "kind"])
        for did, (kept, kind) in dropped.items():
            w.writerow([did, info[did][0], kept, info[kept][0], kind])
    records = [r for r in records if r.dialogue_id not in dropped]
    kept_info = {d: v for d, v in info.items() if d not in dropped}

    split = dialogue_splits(kept_info, cfg.get("split", {"train": 0.7, "val": 0.15, "test": 0.15}), cfg.get("seed", 42))
    logo = logo_splits(split, {d: v[1] for d, v in kept_info.items()})

    with open(out_dir / "records.jsonl", "w", encoding="utf-8") as f:
        for r in records:
            d = r.to_dict()
            d["split"] = split[r.dialogue_id]
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    with open(out_dir / "splits.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["dialogue_id", "dataset", "genre", "split"])
        for did, (ds, g) in kept_info.items():
            w.writerow([did, ds, g, split[did]])
    with open(out_dir / "logo_splits.json", "w", encoding="utf-8") as f:
        json.dump(logo, f, indent=1)
    with open(report_dir / "unmapped_labels.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["dataset", "label", "count"])
        w.writeheader()
        w.writerows(tax.unmapped_rows())

    drop_counts = Counter((info[d][0], k) for d, (_, k) in dropped.items())
    summary = {
        "datasets": status,
        "turns": len(records),
        "dialogues": len(kept_info),
        "duplicates_removed": {f"{ds}:{k}": c for (ds, k), c in sorted(drop_counts.items())},
        "split_dialogues": dict(Counter(split.values())),
        "unmapped_label_types": len(tax.unmapped),
    }
    with open(report_dir / "prepare_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    return summary


def read_records(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
