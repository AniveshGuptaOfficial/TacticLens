import json

import numpy as np
import pytest

from tacticlens.models.common import TACTICS
from tacticlens.serve.examples import EXAMPLES
from tacticlens.serve.parse import parse_conversation, roles_for, sentences
from tacticlens.serve.predictor import Predictor
from tacticlens.serve.ui import highlights, log_feedback, summary_markdown, turn_rows

CUES = {"T5": ["urgent", "now", "hours"], "T9": ["or else", "don't bother", "legal action"],
        "T8": ["after everything"], "T1": ["dollars", "vaccine"], "T6": ["gift card", "selected"]}


class FakeEngine:
    """Keyword stand-in for the ONNX/torch engines: same interface, no model files."""

    def __init__(self):
        self.calls = []

    def run(self, texts, roles):
        self.calls.append(list(texts))
        P = np.full((len(texts), len(TACTICS)), 0.05)
        for i, t in enumerate(texts):
            for tac, words in CUES.items():
                if any(w in t.lower() for w in words):
                    P[i, TACTICS.index(tac)] = 0.9
        G = np.tile([0.1, 0.5, 0.3, 0.1], (len(texts), 1))
        R = np.tile([0.7, 0.3], (len(texts), 1))
        return {"tactic": P, "genre": G, "role": R}


def bundle():
    groups = {"T1": "legitimate", "T2": "legitimate", "T3": "legitimate", "T4": "legitimate", "T5": "pressure",
              "T6": "pressure", "T7": "pressure", "T8": "manipulative", "T9": "manipulative", "T10": "manipulative"}
    th = [[0.5] * len(TACTICS), [0.6] * len(TACTICS)]
    return {"model": "fake", "thresholds": {"balanced": th, "careful": [[0.95] * len(TACTICS)] * 2},
            "tactics": [{"id": t, "name": f"name {t}", "group": groups[t]} for t in TACTICS],
            "genres": ["persuasion", "manipulation", "scam", "neutral"]}


def test_parse_single_message_and_conversation():
    one = parse_conversation("URGENT: verify at http://x.example now")  # "URGENT:" is not a speaker line here
    assert len(one) == 1 and one[0].speaker == "Message" and "<URL>" in one[0].text
    assert roles_for(one, None) == ["actor"]
    conv = parse_conversation("Sam: hi there\nRiya: hello\nthis continues Riya\nSam: bye now")
    assert [t.speaker for t in conv] == ["Sam", "Riya", "Sam"] and "continues" in conv[1].raw
    assert roles_for(conv, "sam") == ["actor", "target", "actor"]
    assert roles_for(conv, None) == ["unknown"] * 3
    assert parse_conversation("   ") == []


def test_parse_whatsapp_copy_and_export():
    copied = ("[6:01 PM, 11/2/2026] Unknown \U0001fae5: Bhai kettle la sakta hoon?\n"
              "[6:43 PM, 11/2/2026] Ravi Kumar: Ajj leke jaa\n"
              "mai to bola tha\n"
              "[10:36 PM, 11/3/2026] Unknown \U0001fae5: ohh koi nahi")
    turns = parse_conversation(copied)
    assert [t.speaker for t in turns] == ["Unknown \U0001fae5", "Ravi Kumar", "Unknown \U0001fae5"]
    assert turns[1].raw == "Ajj leke jaa mai to bola tha"
    exported = "11/2/26, 6:01 pm - Asha: see https://x.org now\n11/2/26, 6:02 pm - Ben: ok"
    assert [(t.speaker, t.raw) for t in parse_conversation(exported)] == [("Asha", "see https://x.org now"),
                                                                          ("Ben", "ok")]
    assert len(parse_conversation("URGENT: verify at 10:30 today")) == 1


def test_sentences_cover_text():
    t = "First one. Second one! Third? yes"
    sp = sentences(t)
    assert [t[s:e] for s, e in sp][:2] == ["First one.", "Second one!"]
    assert sentences("no punctuation") == [(0, 14)]


def test_predictor_finds_tactics_evidence_and_verdict():
    p = Predictor(FakeEngine(), bundle())
    res = p.analyze(EXAMPLES[1]["text"], actor="Sam")
    assert res["verdict"] == "Manipulation signals" and "manipulative" in res["groups_found"]
    sam = [t for t in res["turns"] if t["speaker"] == "Sam"]
    assert all(t["role"] == "actor" for t in sam)
    t8 = next(x for t in sam for x in t["tactics"] if x["id"] == "T8")
    assert "after everything" in t8["evidence"]["text"].lower()
    assert {s["id"] for s in res["summary"]} >= {"T8", "T9"}
    assert res["genre"]["label"] == "manipulation"


def test_predictor_single_message_and_modes():
    p = Predictor(FakeEngine(), bundle())
    sms = p.analyze(EXAMPLES[2]["text"])
    assert {s["id"] for s in sms["summary"]} >= {"T5", "T9"} and sms["verdict"] == "Manipulation signals"
    multi = [x for x in sms["turns"][0]["tactics"] if x["evidence"]["score"] is not None]
    assert multi and all(sms["turns"][0]["text"][x["evidence"]["start"]:x["evidence"]["end"]] == x["evidence"]["text"]
                         for x in multi)
    careful = p.analyze(EXAMPLES[2]["text"], mode="careful")
    assert careful["summary"] == []  # 0.9 < 0.95
    assert {s["id"] for s in careful["possible"]} >= {"T5", "T9"}  # 0.9 >= balanced 0.5
    assert careful["verdict"] == "No clear tactic, but possible signals"
    assert "Possible signals" in summary_markdown(careful) and "possible:" in turn_rows(careful)[0][3]
    assert sms["possible"] == []  # balanced mode lists no possible signals
    conv = p.analyze(EXAMPLES[1]["text"], actor="Sam", mode="careful")
    assert conv["summary"] == [] and "T8" in {s["id"] for s in conv["possible"]}
    assert p.analyze(EXAMPLES[4]["text"])["verdict"] == "No influence tactic found"
    assert p.analyze("")["turns"] == []


def test_weak_conversation_only_tactic_is_a_possible_signal():
    class Flat(FakeEngine):
        def run(self, texts, roles):
            out = super().run(texts, roles)
            out["tactic"][:, TACTICS.index("T6")] = 0.3  # below the turn cutoff 0.5, above dialogue 0.2
            return out
    b = bundle()
    b["thresholds"]["balanced"] = [[0.5] * len(TACTICS), [0.2] * len(TACTICS)]
    res = Predictor(Flat(), b).analyze("Asha: hi there\nBen: see you tomorrow")
    assert res["summary"] == [] and [s["id"] for s in res["possible"]] == ["T6"]
    assert res["verdict"] == "No clear tactic, but possible signals"


def test_ui_helpers(tmp_path):
    p = Predictor(FakeEngine(), bundle())
    res = p.analyze(EXAMPLES[1]["text"], actor="Sam")
    pieces = highlights(res)
    assert "".join(s for s, _ in pieces).count("\n") == len(res["turns"]) - 1
    assert any(lab and "name T8" in lab for _, lab in pieces)
    assert "Manipulation signals" in summary_markdown(res)
    rows = turn_rows(res)
    assert len(rows) == len(res["turns"])
    sam = next(r for r, t in zip(rows, res["turns"]) if t["tactics"])
    assert sam[4] != "-"  # evidence shown even for one-sentence turns
    log = tmp_path / "fb.csv"
    log_feedback(log, "secret text", res, "Helpful", "nice")
    content = log.read_text()
    assert "Helpful" in content and "secret text" not in content


def test_api_endpoints():
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from tacticlens.serve.api import create_app
    c = TestClient(create_app(Predictor(FakeEngine(), bundle())))
    assert c.get("/health").json()["status"] == "ok"
    assert len(c.get("/taxonomy").json()["tactics"]) == len(TACTICS)
    r = c.post("/analyze", json={"text": EXAMPLES[2]["text"]})
    assert r.status_code == 200 and r.json()["summary"]
    assert c.post("/analyze", json={"text": "hi", "mode": "nope"}).status_code == 422


def test_ui_builds():
    pytest.importorskip("gradio")
    from tacticlens.serve.ui import build_ui
    assert build_ui(Predictor(FakeEngine(), bundle())) is not None


def test_onnx_head_export_matches_torch(tmp_path):
    torch = pytest.importorskip("torch")
    pytest.importorskip("onnx")
    ort = pytest.importorskip("onnxruntime")
    from tacticlens.models.m3 import M3Net
    from tacticlens.serve.export import _head_module, _quantize, _torch_export
    net = M3Net(40, d=16, variant="no-context").eval()
    head = _head_module(net)
    E, r = torch.randn(5, 40), torch.tensor([0, 1, 2, 0, 1])
    _torch_export(head, (E, r), tmp_path / "h.onnx", ["emb", "role"], ["tactic", "genre", "role_prob"],
                  {"emb": {0: "n"}, "role": {0: "n"}})
    _quantize(tmp_path / "h.onnx", tmp_path / "h8.onnx")
    s = ort.InferenceSession(str(tmp_path / "h.onnx"), providers=["CPUExecutionProvider"])
    got = s.run(None, {"emb": E.numpy(), "role": r.numpy()})
    with torch.no_grad():
        ref = net(E[:, None, :], r[:, None], torch.ones(5, 1, dtype=torch.bool))
    assert np.allclose(got[0], torch.sigmoid(ref["tactic"][:, 0]).numpy(), atol=1e-5)
    assert (tmp_path / "h8.onnx").exists()


def test_space_bundle(tmp_path):
    from pathlib import Path

    from tacticlens.serve.space import bundle_space
    b = tmp_path / "onnx"
    (b / "tokenizer").mkdir(parents=True)
    (b / "tokenizer" / "tokenizer.json").write_text("{}")
    for f in ["encoder_int8.onnx", "m3_int8.onnx", "lexical.pkl"]:
        (b / f).write_bytes(b"x")
    (b / "bundle.json").write_text(json.dumps({**bundle(), "versions": {"scikit-learn": "1.5.2"}}))
    pkg = Path(__import__("tacticlens").__file__).parent
    out = bundle_space(b, pkg, tmp_path / "space")
    assert (out / "app.py").exists() and (out / "tacticlens" / "serve" / "engines.py").exists()
    assert "scikit-learn==1.5.2" in (out / "requirements.txt").read_text()
    assert not list((out / "tacticlens").rglob("m3.py"))  # no torch code in the Space
