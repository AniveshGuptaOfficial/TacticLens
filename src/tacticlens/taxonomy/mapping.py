"""Shared taxonomy and source-label mapping (FR-TAX-01 to FR-TAX-03)."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from ..config import PROJECT_ROOT, load_yaml


def _key(label: str) -> str:
    """lower-case, hyphens/underscores/spaces unified, a trailing '(continued)'-style note dropped."""
    k = re.sub(r"[\s_\-]+", " ", str(label).strip().lower())
    return re.sub(r"\s*\([^)]*\)\s*$", "", k).strip()


@dataclass
class Taxonomy:
    tactics: dict[str, dict]
    extra: dict[str, dict]
    mappings: dict[str, dict[str, list[str]]]
    unmapped: Counter = field(default_factory=Counter)

    @property
    def tactic_ids(self) -> list[str]:
        """T1..T10 in numeric order (the labels models predict)."""
        return sorted(self.tactics, key=lambda t: int(t[1:]))

    @property
    def all_label_ids(self) -> list[str]:
        return self.tactic_ids + list(self.extra)

    def name(self, tid: str) -> str:
        return (self.tactics.get(tid) or self.extra.get(tid) or {}).get("name", tid)

    def group(self, tid: str) -> str | None:
        return self.tactics.get(tid, {}).get("group")

    def map_labels(self, dataset: str, labels: list[str]) -> list[str]:
        """Map source labels to shared tactic ids. Unknown labels are counted, not dropped silently."""
        table = self.mappings.get(dataset, {})
        out: list[str] = []
        for lab in labels:
            k = _key(lab)
            if k in table:
                out.extend(table[k])
            else:
                self.unmapped[(dataset, k)] += 1
        # keep order, drop repeats
        seen: set[str] = set()
        return [t for t in out if not (t in seen or seen.add(t))]

    def unmapped_rows(self) -> list[dict]:
        return [
            {"dataset": d, "label": lab, "count": c}
            for (d, lab), c in self.unmapped.most_common()
        ]


def load_taxonomy(path: str | Path | None = None) -> Taxonomy:
    cfg = load_yaml(path or PROJECT_ROOT / "configs" / "taxonomy.yaml")
    mappings = {
        ds: {_key(k): list(v or []) for k, v in table.items()}
        for ds, table in (cfg.get("mappings") or {}).items()
    }
    tax = Taxonomy(cfg["tactics"], cfg.get("extra_labels") or {}, mappings)
    known = set(tax.all_label_ids)
    for ds, table in mappings.items():
        for k, v in table.items():
            bad = [t for t in v if t not in known]
            if bad:
                raise ValueError(f"mapping {ds}:{k} points to unknown tactic(s) {bad}")
    return tax
