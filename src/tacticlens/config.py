"""Config loading. All paths in the YAML files are relative to the project root."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_yaml(path: str | Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_datasets_config(root: Path | None = None, path: str | Path | None = None) -> dict[str, Any]:
    root = Path(root) if root else PROJECT_ROOT
    cfg = load_yaml(path or root / "configs" / "datasets.yaml")
    cfg["_root"] = str(root)
    return cfg


def resolve(root: Path | str, rel: str | Path) -> Path:
    p = Path(rel)
    return p if p.is_absolute() else Path(root) / p
