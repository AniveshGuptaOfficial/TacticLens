"""ONNX export of the final model (FR-DEP: CPU, small, fast) and a check that it still scores the same.

export_onnx writes models/onnx/:
  encoder_fp32.onnx, encoder_int8.onnx   MiniLM (all-MiniLM-L6-v2) -> token states; pooling in numpy
  m3_fp32.onnx, m3_int8.onnx             M3 head: features + role -> tactic / genre / role probabilities
  tokenizer/                             the MiniLM tokenizer (tokenizer.json)
  lexical.pkl                            TF-IDF (word, char) + SVD as plain scikit-learn objects
  bundle.json                            thresholds (balanced = F1, careful = accuracy, both tuned on
                                         validation), taxonomy names/groups, versions
int8 = dynamic quantisation of the weights (onnxruntime.quantization.quantize_dynamic).

eval_onnx re-runs the test split through the ONNX engine and compares macro-F1, size and speed
with the PyTorch model, so the report can say what quantisation costs.
"""

from __future__ import annotations

import json
import pickle
import shutil
import time
from pathlib import Path

import numpy as np

from ..data.schema import GENRES
from ..models.common import TACTICS


def _torch_export(module, args, path: Path, input_names, output_names, dynamic_axes) -> None:
    import torch
    kw = dict(input_names=input_names, output_names=output_names, dynamic_axes=dynamic_axes, opset_version=17)
    try:
        torch.onnx.export(module, args, str(path), dynamo=False, **kw)  # classic exporter, no onnxscript needed
    except TypeError:  # older torch without the `dynamo` argument
        torch.onnx.export(module, args, str(path), **kw)


def _head_module(net):
    """The no-context M3 path as a plain module (no gradient-reversal Function, no dropout)."""
    import torch
    import torch.nn.functional as F

    class Head(torch.nn.Module):
        def __init__(self, net):
            super().__init__()
            self.net = net

        def forward(self, emb, role):
            n = self.net
            x = n.proj(emb)
            if n.use_role:
                x = x + n.role_emb(role)
            z = F.gelu(n.mix(F.gelu(x)))
            return torch.sigmoid(n.tactic(z)), torch.softmax(n.genre(z), -1), torch.softmax(n.role(z), -1)

    return Head(net).eval()


def _quantize(src: Path, dst: Path) -> None:
    from onnxruntime.quantization import QuantType, quantize_dynamic
    quantize_dynamic(str(src), str(dst), weight_type=QuantType.QInt8)


def export_onnx(root: Path, model_name: str, out: Path, records: list[dict], names: dict[str, str],
                groups: dict[str, str], log=print) -> dict:
    import sklearn
    import torch
    from transformers import AutoModel, AutoTokenizer

    from ..models.common import by_split, load_predictions, threshold_pair, tune_all_thresholds
    from ..models.m3 import M3

    mdir = root / "models" / model_name
    cfg = json.loads((mdir / "m3_config.json").read_text(encoding="utf-8"))
    if cfg["variant"] != "no-context":
        raise SystemExit(f"ONNX export supports the no-context model (the final one); {model_name} is {cfg['variant']}")
    out.mkdir(parents=True, exist_ok=True)
    m3 = M3.load(mdir, root / "models" / "embeddings", log=lambda *_: None)

    # 1. M3 head
    log("exporting the M3 head ...")
    head = _head_module(m3.net)
    in_dim = cfg["in_dim"]
    ex = (torch.randn(4, in_dim), torch.zeros(4, dtype=torch.long))
    _torch_export(head, ex, out / "m3_fp32.onnx", ["emb", "role"], ["tactic", "genre", "role_prob"],
                  {"emb": {0: "n"}, "role": {0: "n"}, "tactic": {0: "n"}, "genre": {0: "n"}, "role_prob": {0: "n"}})
    _quantize(out / "m3_fp32.onnx", out / "m3_int8.onnx")

    # 2. MiniLM encoder
    enc_name = cfg.get("encoder", "sentence-transformers/all-MiniLM-L6-v2")
    log(f"exporting the encoder {enc_name} ...")
    tok = AutoTokenizer.from_pretrained(enc_name)
    bert = AutoModel.from_pretrained(enc_name).eval()

    class Enc(torch.nn.Module):
        def __init__(self, m):
            super().__init__()
            self.m = m

        def forward(self, input_ids, attention_mask, token_type_ids):
            return self.m(input_ids=input_ids, attention_mask=attention_mask, token_type_ids=token_type_ids).last_hidden_state

    sample = tok(["a short example", "another example sentence here"], padding=True, return_tensors="pt")
    dyn = {"input_ids": {0: "b", 1: "s"}, "attention_mask": {0: "b", 1: "s"}, "token_type_ids": {0: "b", 1: "s"},
           "hidden": {0: "b", 1: "s"}}
    _torch_export(Enc(bert), (sample["input_ids"], sample["attention_mask"], sample["token_type_ids"]),
                  out / "encoder_fp32.onnx", ["input_ids", "attention_mask", "token_type_ids"], ["hidden"], dyn)
    _quantize(out / "encoder_fp32.onnx", out / "encoder_int8.onnx")
    if (out / "tokenizer").exists():
        shutil.rmtree(out / "tokenizer")
    tok.save_pretrained(str(out / "tokenizer"))

    # 3. lexical features as plain scikit-learn objects (no tacticlens/torch classes in the pickle)
    if m3.lex is not None:
        with open(out / "lexical.pkl", "wb") as f:
            pickle.dump({"word": m3.lex.tfidf.word, "char": m3.lex.tfidf.char, "svd": m3.lex.svd}, f)

    # 4. thresholds: balanced = the F1 ones used in every report; careful = tuned for accuracy
    th_f1 = np.asarray(np.load(mdir / "test_predictions.npz")["thresholds"])
    val = by_split(records)["val"]
    sv, _ = load_predictions(mdir / "val_predictions.npz", val)
    th_acc = tune_all_thresholds(val, sv, objective="accuracy")
    t1, d1 = threshold_pair(th_f1)
    bundle = {
        "model": model_name,
        "variant": cfg["variant"],
        "in_dim": in_dim,
        "embed_dim": int(bert.config.hidden_size),
        "lexical": m3.lex is not None,
        "encoder": enc_name,
        "thresholds": {"balanced": [t1.tolist(), d1.tolist()], "careful": [r.tolist() for r in th_acc]},
        "tactics": [{"id": t, "name": names.get(t, t), "group": groups.get(t)} for t in TACTICS],
        "genres": list(GENRES),
        "versions": {"scikit-learn": sklearn.__version__, "torch": torch.__version__},
    }
    (out / "bundle.json").write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    sizes = {p.name: round(p.stat().st_size / 1e6, 1) for p in sorted(out.glob("*.onnx"))}
    log("sizes (MB): " + ", ".join(f"{k} {v}" for k, v in sizes.items()))
    return {"sizes_mb": sizes}


def eval_onnx(root: Path, bundle_dir: Path, records: list[dict], n_boot: int = 200, log=print) -> str:
    """Test-split macro-F1 of the ONNX engine (int8 and fp32) next to the PyTorch model, plus speed."""
    from ..models.common import by_split, evaluate
    from .engines import OnnxEngine

    bundle = json.loads((bundle_dir / "bundle.json").read_text(encoding="utf-8"))
    test = by_split(records)["test"]
    ref = json.loads((root / "models" / bundle["model"] / "metrics.json").read_text(encoding="utf-8"))
    th = np.array(bundle["thresholds"]["balanced"])
    rows = [("PyTorch (reference)", ref["turn"]["macro_f1"], ref["dialogue"]["macro_f1"], ref["genre"]["macro_f1"],
             None, None)]
    probe = [r["text"] for r in test[:300]]
    S_by = {}
    for int8 in (True, False):
        name = "ONNX int8" if int8 else "ONNX fp32"
        eng = OnnxEngine(bundle_dir, int8=int8)
        log(f"{name}: scoring {len(test):,} test turns ...")
        out = eng.run([r["text"] for r in test], [r["role"] for r in test])
        S_by[name] = out["tactic"]
        res = evaluate(test, out["tactic"], out["genre"], th, n_boot=n_boot)
        t0 = time.perf_counter()
        for k in range(0, len(probe), 1):  # one turn at a time, like the app
            eng.run([probe[k]], ["unknown"])
        ms = 1000 * (time.perf_counter() - t0) / len(probe)
        size = sum((bundle_dir / f).stat().st_size for f in (f"encoder_{'int8' if int8 else 'fp32'}.onnx",
                                                             f"m3_{'int8' if int8 else 'fp32'}.onnx")) / 1e6
        rows.append((name, res["turn"]["macro_f1"], res["dialogue"]["macro_f1"], res["genre"]["macro_f1"], ms, size))
    agree = float(((S_by["ONNX int8"] >= th[0]) == (S_by["ONNX fp32"] >= th[0])).mean())
    lines = ["# ONNX export check (final model, test split)", "",
             f"Model: `{bundle['model']}`. Thresholds: the validation-tuned F1 ones (balanced mode).", "",
             "| Runtime | Turn macro-F1 | Dialogue macro-F1 | Genre macro-F1 | ms per turn (CPU, 1 at a time) | Model size (MB) |",
             "|---|---|---|---|---|---|"]
    for name, t, d, g, ms, size in rows:
        lines.append(f"| {name} | {t:.3f} | {d:.3f} | {g:.3f} | {'-' if ms is None else f'{ms:.1f}'} | "
                     f"{'-' if size is None else f'{size:.1f}'} |")
    lines += ["", f"int8 and fp32 agree on {agree:.1%} of the turn-level tactic decisions.",
              "The PyTorch row uses the cached sentence-transformers embeddings; small differences come from",
              "re-tokenising and from int8 weights.", ""]
    return "\n".join(lines)
