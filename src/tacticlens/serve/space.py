"""Package the ONNX app as a Hugging Face Space (free CPU tier) and, if asked, upload it.

bundle_space writes space/:
  app.py              starts the Gradio UI on the ONNX engine
  api_server.py       the same model as an HTTP API (used by the Dockerfile's API mode)
  requirements.txt    onnxruntime, tokenizers, gradio, numpy, scipy, scikit-learn==<training version>
  README.md           Space card (sdk: gradio) with the limits and dataset licences
  model/              the ONNX bundle (int8 only, to keep it small)
  tacticlens/         the parts of this package the app needs (no PyTorch, no data)
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

PKG_FILES = ["__init__.py", "data/__init__.py", "data/normalize.py", "data/schema.py", "models/__init__.py",
             "models/embed.py", "serve/__init__.py", "serve/parse.py", "serve/engines.py", "serve/predictor.py",
             "serve/ui.py", "serve/examples.py", "serve/api.py"]

APP = '''"""TacticLens Hugging Face Space: Gradio UI on the int8 ONNX model."""
import json
from pathlib import Path

from tacticlens.serve.engines import OnnxEngine
from tacticlens.serve.predictor import Predictor
from tacticlens.serve.ui import build_ui

HERE = Path(__file__).parent / "model"
predictor = Predictor(OnnxEngine(HERE, int8=True), json.loads((HERE / "bundle.json").read_text(encoding="utf-8")))
demo = build_ui(predictor)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0")
'''

API_SERVER = '''"""TacticLens HTTP API on the int8 ONNX model:  python api_server.py  (port 8000, docs at /docs)."""
import json
from pathlib import Path

import uvicorn

from tacticlens.serve.api import create_app
from tacticlens.serve.engines import OnnxEngine
from tacticlens.serve.predictor import Predictor

HERE = Path(__file__).parent / "model"
predictor = Predictor(OnnxEngine(HERE, int8=True), json.loads((HERE / "bundle.json").read_text(encoding="utf-8")))

if __name__ == "__main__":
    uvicorn.run(create_app(predictor), host="0.0.0.0", port=8000)
'''

README = """---
title: TacticLens
emoji: 🔎
colorFrom: indigo
colorTo: red
sdk: gradio
app_file: app.py
pinned: false
license: cc-by-nc-4.0
---

# TacticLens

Finds influence tactics (legitimate appeals, pressure tactics, manipulation) in a message or a
conversation, turn by turn, and shows the sentence each decision rests on.

Final-year capstone project (VIT Vellore). Model: frozen all-MiniLM-L6-v2 + TF-IDF features +
a small multi-task head, exported to int8 ONNX; CPU only.

**Limits.** Research prototype trained on PersuasionForGood, MentalManip (CC BY-NC 4.0) and
PsyScam. Test-set macro-F1 for naming the tactic is about 0.59 on single turns and 0.36 on whole
conversations, so it misses tactics and raises false alarms. It is not proof of anyone's intent.
Non-commercial research use only (MentalManip licence). Inputs are not stored.
"""


def bundle_space(bundle_dir: Path, src_pkg: Path, out: Path) -> Path:
    bundle = json.loads((bundle_dir / "bundle.json").read_text(encoding="utf-8"))
    if out.exists():
        shutil.rmtree(out)
    (out / "model").mkdir(parents=True)
    for name in ["bundle.json", "encoder_int8.onnx", "m3_int8.onnx", "lexical.pkl"]:
        if (bundle_dir / name).exists():
            shutil.copy2(bundle_dir / name, out / "model" / name)
    shutil.copytree(bundle_dir / "tokenizer", out / "model" / "tokenizer")
    for rel in PKG_FILES:
        dst = out / "tacticlens" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_pkg / rel, dst)
    sk = bundle.get("versions", {}).get("scikit-learn")
    reqs = ["numpy", "scipy", f"scikit-learn=={sk}" if sk else "scikit-learn", "onnxruntime", "tokenizers"]
    (out / "requirements.txt").write_text("\n".join(reqs) + "\n", encoding="utf-8")
    (out / "app.py").write_text(APP, encoding="utf-8")
    (out / "api_server.py").write_text(API_SERVER, encoding="utf-8")
    (out / "README.md").write_text(README, encoding="utf-8")
    return out


def deploy_space(space_dir: Path, repo_id: str, private: bool = False) -> str:
    """Create (if needed) and upload the Space. Needs `huggingface-cli login` first."""
    from huggingface_hub import HfApi
    api = HfApi()
    api.create_repo(repo_id, repo_type="space", space_sdk="gradio", private=private, exist_ok=True)
    api.upload_folder(folder_path=str(space_dir), repo_id=repo_id, repo_type="space",
                      commit_message="Deploy TacticLens")
    return f"https://huggingface.co/spaces/{repo_id}"
