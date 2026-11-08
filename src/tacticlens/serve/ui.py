"""Web UI (Gradio). Paste a message or a conversation, see the tactics, the evidence and a verdict.

Run:  python -m tacticlens.cli ui                (opens http://127.0.0.1:7860)
For the user study add  --feedback-log reports/study_feedback.csv  (stores ratings and a hash of
the input, never the text itself).
"""

from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from .examples import EXAMPLES
from .predictor import Predictor

GROUP_COLOURS = {"manipulative": "#e5484d", "pressure": "#f5a524", "legitimate": "#30a46c"}
GROUP_LABEL = {"manipulative": "manipulative", "pressure": "pressure", "legitimate": "legitimate appeal"}
MODE_LABELS = {"balanced": "Balanced (catches more)", "careful": "Careful (fewer false alarms)"}


def highlights(result: dict) -> list[tuple[str, str | None]]:
    """[(text piece, label or None)] for gr.HighlightedText: evidence spans labelled with their tactics."""
    out: list[tuple[str, str | None]] = []
    for k, t in enumerate(result["turns"]):
        if k:
            out.append(("\n", None))
        if t["speaker"] != "Message":
            out.append((f"{t['speaker']}: ", None))
        text = t["text"]
        spans: dict[tuple[int, int], list[str]] = {}
        for tac in t["tactics"]:
            ev = tac.get("evidence") or {"start": 0, "end": len(text)}
            spans.setdefault((ev["start"], ev["end"]), []).append(tac["name"])
        pos = 0
        for (s, e), labs in sorted(spans.items()):
            if s < pos:  # overlaps an earlier highlighted span: fold into it
                continue
            if s > pos:
                out.append((text[pos:s], None))
            out.append((text[s:e], " + ".join(labs)))
            pos = e
        if pos < len(text):
            out.append((text[pos:], None))
    return out


def summary_markdown(result: dict) -> str:
    if not result["turns"]:
        return "Paste a message or a conversation first."
    lines = [f"## {result['verdict']}"]
    if result.get("checked_speaker"):
        lines.append(f"Checked speaker: **{result['checked_speaker']}**")
    g = result["genre"]
    lines.append(f"Looks most like: **{g['label']}** ({g['probs'][g['label']]:.0%})")
    if result["summary"]:
        lines += ["", "| Tactic | Type | Score | Turns |", "|---|---|---|---|"]
        for s in result["summary"]:
            turns = ", ".join(str(i + 1) for i in s["turns"]) or "whole conversation"
            lines.append(f"| {s['name']} | {GROUP_LABEL.get(s['group'], s['group'])} | {s['score']:.2f} | {turns} |")
    lines += ["", f"*{result['disclaimer']}*"]
    return "\n".join(lines)


def turn_rows(result: dict) -> list[list[str]]:
    rows = []
    for t in result["turns"]:
        tacs = "; ".join(f"{x['name']} ({x['score']:.2f})" for x in t["tactics"]) or "-"
        ev = "; ".join(x["evidence"]["text"] for x in t["tactics"] if x.get("evidence") and x["evidence"].get("score"))
        rows.append([str(t["index"] + 1), t["speaker"], t["role"], tacs, ev or "-"])
    return rows


def log_feedback(path: Path, text: str, result: dict | None, rating: str, comment: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time_utc", "input_sha256", "n_turns", "mode", "verdict", "rating", "comment"])
        w.writerow([datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:16],
                    len((result or {}).get("turns", [])), (result or {}).get("mode", ""),
                    (result or {}).get("verdict", ""), rating, (comment or "").replace("\n", " ")[:500]])


def build_ui(predictor: Predictor, feedback_log: Path | None = None):
    import gradio as gr

    colour_map = {t["name"]: GROUP_COLOURS.get(t["group"], "#888888") for t in predictor.tactics}
    modes = [m for m in ("balanced", "careful") if m in predictor.modes()]

    def run(text, actor, mode_label):
        mode = next((m for m in modes if MODE_LABELS[m] == mode_label), "balanced")
        res = predictor.analyze(text or "", actor=(actor or "").strip() or None, mode=mode)
        return summary_markdown(res), highlights(res), turn_rows(res), res

    def send(text, rating, comment, last):
        if feedback_log is None:
            return "Feedback logging is off in this deployment."
        if not rating:
            return "Pick Helpful or Not helpful first."
        log_feedback(feedback_log, text, last, rating, comment)
        return "Thanks, recorded."

    with gr.Blocks(title="TacticLens") as demo:
        gr.Markdown("# TacticLens\nFinds influence tactics in a message or a conversation: legitimate appeals, "
                    "pressure tactics and manipulation, across persuasion, interpersonal manipulation and scams.\n\n"
                    "Write a conversation as one line per turn: `Name: what they said`.")
        with gr.Row(equal_height=False):
            with gr.Column(scale=3):
                text = gr.Textbox(label="Message or conversation", lines=7,
                                  placeholder="Riya: I'll be late tonight.\nSam: After everything I've done for you...")
                go = gr.Button("Analyse", variant="primary")
                with gr.Row():
                    actor = gr.Textbox(label="Speaker to check (optional)", placeholder="e.g. Sam")
                    mode = gr.Radio([MODE_LABELS[m] for m in modes], value=MODE_LABELS[modes[0]], label="Mode")
                ex = [[e["text"], e["actor"], MODE_LABELS[modes[0]]] for e in EXAMPLES]
                try:
                    gr.Examples(ex, inputs=[text, actor, mode], example_labels=[e["title"] for e in EXAMPLES],
                                label="Examples (click one, then Analyse)")
                except TypeError:  # older Gradio without example_labels
                    gr.Examples(ex, inputs=[text, actor, mode], label="Examples (click one, then Analyse)")
            with gr.Column(scale=2):
                verdict = gr.Markdown("### Result\nPaste a message or pick an example, then press **Analyse**. "
                                      "The verdict, the tactics found and their evidence appear here and below.")
        marked = gr.HighlightedText(label="Evidence (highlighted by tactic)", color_map=colour_map,
                                    combine_adjacent=False, show_legend=True)
        table = gr.Dataframe(headers=["Turn", "Speaker", "Role", "Tactics (score)", "Evidence sentence"],
                             label="Turn by turn", wrap=True)
        state = gr.State(None)
        go.click(run, [text, actor, mode], [verdict, marked, table, state])
        with gr.Accordion("Was this useful? (feedback)", open=False):
            rating = gr.Radio(["Helpful", "Not helpful"], label="Rating")
            comment = gr.Textbox(label="Comment (optional)", lines=2)
            fb = gr.Button("Send feedback")
            fb_out = gr.Markdown()
            fb.click(send, [text, rating, comment, state], fb_out)
    return demo
