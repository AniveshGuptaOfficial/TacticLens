"""One entry point for every step: `python -m tacticlens.cli <command>`."""

from __future__ import annotations

import argparse
import json
import logging
import random
from pathlib import Path

from .config import PROJECT_ROOT, load_datasets_config, resolve
from .taxonomy.mapping import load_taxonomy


def _paths(args):
    root = Path(args.root).resolve() if args.root else PROJECT_ROOT
    cfg = load_datasets_config(root)
    tax = load_taxonomy(root / "configs" / "taxonomy.yaml")
    return root, cfg, tax


def cmd_inspect(args) -> None:
    """Show which file and columns each loader would use (run after downloading)."""
    from .data.io_utils import TABLE_EXT, read_table
    root, cfg, _ = _paths(args)
    for name, c in cfg["datasets"].items():
        d = resolve(root, c["dir"])
        files = sorted(p for p in d.rglob("*") if p.is_file() and p.suffix.lower() in TABLE_EXT) if d.exists() else []
        print(f"\n== {name}  ({d})")
        if not files:
            print("   MISSING: no data files. See README step 1.")
            continue
        for p in files[:6]:
            try:
                df = read_table(p)
                print(f"   {p.name}: {len(df):,} rows; columns: {list(df.columns)[:12]}")
            except Exception as e:  # noqa: BLE001 - show any read problem to the user
                print(f"   {p.name}: could not read ({e})")


def cmd_prepare(args) -> None:
    from .data.pipeline import prepare
    root, cfg, tax = _paths(args)
    print(json.dumps(prepare(cfg, root, tax), indent=2))


def _records(root: Path) -> list[dict]:
    from .data.pipeline import read_records
    p = root / "data" / "processed" / "records.jsonl"
    if not p.exists():
        raise SystemExit("Run `python -m tacticlens.cli prepare` first.")
    return read_records(p)


def cmd_datacard(args) -> None:
    from .data.datacard import write_datacard
    root, _, tax = _paths(args)
    print("wrote", write_datacard(_records(root), tax, root / "reports" / "data_card.md"))


def cmd_checkset(args) -> None:
    from .taxonomy.annotation import export_checkset
    root, cfg, tax = _paths(args)
    for p in export_checkset(_records(root), tax, root / "data" / "annotation", n=args.n, seed=cfg.get("seed", 42)):
        print("wrote", p)


def cmd_kappa(args) -> None:
    from .taxonomy.annotation import kappa_report
    root, _, tax = _paths(args)
    a = root / "data" / "annotation" / "checkset_A.csv"
    b = root / "data" / "annotation" / "checkset_B.csv"
    rep = kappa_report(a, b, tax)
    out = root / "reports" / "kappa.csv"
    out.parent.mkdir(exist_ok=True)
    rep.to_csv(out, index=False)
    print(rep.to_string(index=False))
    overall = rep.loc[rep["tactic"] == "overall", "kappa"].iloc[0]
    print(f"\nOverall kappa {overall} -> AC-01 {'MET' if overall >= 0.60 else 'NOT met'} (target 0.60)")


def cmd_train_m0(args) -> None:
    from .models.m0 import metrics_markdown, train_m0
    root, cfg, tax = _paths(args)
    res = train_m0(_records(root), tax.tactic_ids, root / "models" / "m0", n_boot=args.boot, seed=cfg.get("seed", 42))
    md = metrics_markdown(res, {t: tax.name(t) for t in tax.all_label_ids})
    (root / "reports").mkdir(exist_ok=True)
    (root / "reports" / "m0_results.md").write_text(md, encoding="utf-8")
    print(md)


def cmd_llm_overlap(args) -> None:
    """First check from the SRS: are the LLM-set messages copies of Mishra-Soni ones?"""
    from .data.dedupe import jaccard, shingles
    from .data.loaders import load_sms
    from .data.normalize import dedupe_key
    root, cfg, tax = _paths(args)
    human = load_sms("sms_human", cfg["datasets"]["sms_human"], root, tax)
    llm = load_sms("sms_llm", cfg["datasets"]["sms_llm"], root, tax)
    hkeys = {dedupe_key(r.text) for r in human}
    exact = sum(dedupe_key(r.text) in hkeys for r in llm)
    rng = random.Random(42)
    sample = rng.sample(llm, min(args.n, len(llm)))
    hsh = [shingles(r.text) for r in human]
    near = sum(max((jaccard(shingles(r.text), h) for h in hsh), default=0) >= 0.9 for r in sample)
    print(f"LLM set messages: {len(llm):,}; exact copies of Mishra-Soni: {exact:,} ({exact / max(len(llm), 1):.1%})")
    print(f"Near copies (Jaccard >= 0.9) in a random sample of {len(sample)}: {near} ({near / max(len(sample), 1):.1%})")
    if exact / max(len(llm), 1) > 0.5:
        print("WARNING: most messages are copies of human SMS, so the LLM set is not usable for O5.")


def cmd_gen_llm_sms(args) -> None:
    """Write the LLM SMS set with local Ollama models (replaces the unusable Munoz-Islam set)."""
    from .data import generate_llm_sms as g
    root, cfg, _ = _paths(args)
    installed = g.check_ollama(args.host)
    models = args.models.split(",") if args.models else g.DEFAULT_MODELS
    missing = [m for m in models if not any(i == m or i.startswith(m + ":") or i.split(":")[0] == m for i in installed)]
    if missing:
        raise SystemExit(f"Model(s) not installed: {missing}. Run: " + " && ".join(f"ollama pull {m}" for m in missing))
    counts = {"smishing": args.smishing, "spam": args.spam, "ham": args.ham}
    out = resolve(root, cfg["datasets"]["sms_llm"]["dir"]) / "llm_sms.csv"
    total = sum(counts.values()) * len(models)
    print(f"Generating up to {total} messages with {models} -> {out}  (safe to stop with Ctrl+C and re-run to resume)")
    n = g.run(out, models, counts, host=args.host, seed=cfg.get("seed", 42))
    print(f"Wrote {n} new messages.")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="tacticlens")
    ap.add_argument("--root", help="project folder (default: this repository)")
    ap.add_argument("-v", "--verbose", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("inspect").set_defaults(fn=cmd_inspect)
    sub.add_parser("prepare").set_defaults(fn=cmd_prepare)
    sub.add_parser("datacard").set_defaults(fn=cmd_datacard)
    p = sub.add_parser("checkset")
    p.add_argument("--n", type=int, default=300)
    p.set_defaults(fn=cmd_checkset)
    sub.add_parser("kappa").set_defaults(fn=cmd_kappa)
    p = sub.add_parser("train-m0")
    p.add_argument("--boot", type=int, default=1000)
    p.set_defaults(fn=cmd_train_m0)
    p = sub.add_parser("gen-llm-sms")
    p.add_argument("--models", help="comma-separated Ollama models (default: qwen2.5:3b,llama3.2:3b,gemma2:2b)")
    p.add_argument("--smishing", type=int, default=400)
    p.add_argument("--spam", type=int, default=200)
    p.add_argument("--ham", type=int, default=400)
    p.add_argument("--host", default="http://localhost:11434")
    p.set_defaults(fn=cmd_gen_llm_sms)
    p = sub.add_parser("llm-overlap")
    p.add_argument("--n", type=int, default=100)
    p.set_defaults(fn=cmd_llm_overlap)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING, format="%(levelname)s %(message)s")
    args.fn(args)


if __name__ == "__main__":
    main()
