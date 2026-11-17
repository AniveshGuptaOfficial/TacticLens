import csv
import io
import zipfile

import pytest

from tacticlens.config import load_datasets_config
from tacticlens.data.loaders import dd_detok, load_dailydialog, read_dailydialog
from tacticlens.data.pipeline import prepare, read_records
from tacticlens.taxonomy.mapping import load_taxonomy

LINES = {
    "train": ["Can I borrow your kettle ? __eou__ Sure , take it today . __eou__",
              "I 'm leaving at six . __eou__ OK , have a good trip ! __eou__ Thanks ! __eou__",
              "What time is it ? __eou__ It 's five . __eou__"],
    "validation": ["Do you like tea ? __eou__ I don't drink it . __eou__"],
    "test": ["Happy Diwali ! __eou__ You too ! __eou__"],
}


def _inner(split: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(f"{split}/dialogues_{split}.txt", "\n".join(LINES[split]) + "\n")
        z.writestr(f"{split}/dialogues_act_{split}.txt", "1 2\n")
    return buf.getvalue()


def write_release(d):
    """Same layout as ijcnlp_dailydialog.zip: an outer zip holding train/validation/test zips."""
    d.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(d / "ijcnlp_dailydialog.zip", "w") as z:
        z.writestr("ijcnlp_dailydialog/dialogues_text.txt", "Not split , skipped . __eou__\n")
        for split in LINES:
            z.writestr(f"ijcnlp_dailydialog/{split}.zip", _inner(split))


def test_detok():
    assert dd_detok("I 'm here , are n't you ?") == "I'm here, aren't you?"
    assert dd_detok("It 's ( really ) fine .") == "It's (really) fine."


def test_read_nested_zip(tmp_path):
    write_release(tmp_path / "dd")
    data = read_dailydialog(tmp_path / "dd")
    assert len(data["train"]) == 3 and len(data["val"]) == 1 and len(data["test"]) == 1
    assert data["train"][0] == ["Can I borrow your kettle?", "Sure, take it today."]


def test_load_caps_and_labels(tmp_path):
    write_release(tmp_path / "data" / "raw" / "dd")
    recs = load_dailydialog({"dir": "data/raw/dd", "max_train_dialogues": 2}, tmp_path, None)
    assert {r.dialogue_id.rsplit("_", 1)[0] for r in recs} == {"dd_train", "dd_val"}
    assert len({r.dialogue_id for r in recs if r.meta["fixed_split"] == "train"}) == 2
    assert all(r.tactics == [] and r.label_level == "turn" and r.genre == "neutral" for r in recs)
    assert not any("Diwali" in r.text for r in recs)  # official test dialogues are never loaded


def test_missing_folder_is_reported(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_dailydialog(tmp_path / "nope")


def _splits(project):
    with open(project / "data" / "processed" / "splits.csv", encoding="utf-8") as f:
        return {r["dialogue_id"]: r["split"] for r in csv.DictReader(f)}


def test_adding_dailydialog_leaves_other_splits_unchanged(project):
    cfg = load_datasets_config(project)
    tax = load_taxonomy(project / "configs" / "taxonomy.yaml")
    prepare(cfg, project, tax)
    before = _splits(project)
    write_release(project / "data" / "raw" / "dailydialog")
    summary = prepare(cfg, project, tax)
    after = _splits(project)
    assert summary["datasets"]["dailydialog"].startswith("ok")
    assert {d: s for d, s in after.items() if not d.startswith("dd_")} == before
    recs = read_records(project / "data" / "processed" / "records.jsonl")
    dd = {r["dialogue_id"]: r["split"] for r in recs if r["dataset"] == "dailydialog"}
    assert dd and all(s == d.split("_")[1] for d, s in dd.items())


def test_everyday_report(tmp_path, monkeypatch):
    import shutil
    import types
    from pathlib import Path

    from test_serve import FakeEngine, bundle

    import tacticlens.cli as cli
    from tacticlens.serve.predictor import Predictor

    root = tmp_path / "proj"
    shutil.copytree(Path(__file__).resolve().parents[1] / "configs", root / "configs")
    write_release(root / "data" / "raw" / "dailydialog")
    monkeypatch.setattr(cli, "_predictor", lambda a: Predictor(FakeEngine(), bundle()))
    cli.cmd_everyday(types.SimpleNamespace(root=str(root), limit=10, seed=42, tag="t", engine="onnx",
                                           model="x", bundle=None, fp32=False))
    md = (root / "reports" / "everyday_t.md").read_text(encoding="utf-8")
    assert "## balanced" in md and "## careful" in md and "Turns with any tactic flagged" in md
