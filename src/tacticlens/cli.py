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


def _model_dir_name(model: str, variant: str, no_weak: bool = False) -> str:
    if model != "m3":
        return f"{model}_strict" if no_weak else model  # strict = no weak MentalManip turn labels
    return "dual_role" if variant == "dual-role" else f"m3_{variant}"


def _m3_dir(args) -> str:
    base = _model_dir_name("m3", args.variant)
    return (base + ("_nolex" if getattr(args, "no_lexical", False) else "")
            + ("_ev" if getattr(args, "evidence_aug", False) else ""))


def _seed_suffix(args) -> str:
    """Runs with --seed go to <name>_s<seed>; the default run (config seed) keeps the plain name."""
    s = getattr(args, "seed", None)
    return f"_s{s}" if s is not None else ""


M3_GRID = {"mil_weight": [0.3, 1.0], "pos_clip": [5.0, 20.0], "dropout": [0.2, 0.4]}
M3_BEST = Path("configs") / "m3_best.json"


def _m3_hparams(root: Path, args) -> dict:
    """configs/m3_best.json (written by sweep-m3) if present, then any --mil-weight/--pos-clip/--dropout flags.
    Every M3 variant and ablation then uses the same settings, chosen on validation data only."""
    hp = {}
    best = root / M3_BEST
    if best.exists():
        hp.update(json.loads(best.read_text(encoding="utf-8"))["params"])
    for k in M3_GRID:
        v = getattr(args, k, None)
        if v is not None:
            hp[k] = v
    if hp:
        print("  M3 settings: " + ", ".join(f"{k}={v}" for k, v in hp.items()))
    return hp


def cmd_sweep_m3(args) -> None:
    """Pick M3 settings on the validation split only (the test split is never touched)."""
    import itertools

    from .models.common import by_split
    from .models.m3 import M3, LexicalSVD
    root, cfg, _ = _paths(args)
    seed = cfg.get("seed", 42)
    sp = by_split(_records(root))
    lex = LexicalSVD(256, seed).fit([r["text"] for r in sp["train"]])  # same for every run, fit once
    keys = list(M3_GRID)
    rows = []
    out_json = root / "models" / "m3_sweep.json"
    done = json.loads(out_json.read_text(encoding="utf-8")) if out_json.exists() and not args.restart else []
    combos = list(itertools.product(*(M3_GRID[k] for k in keys)))
    for i, vals in enumerate(combos, 1):
        params = dict(zip(keys, vals))
        prev = next((r for r in done if r["params"] == params), None)
        if prev is not None:
            print(f"[{i}/{len(combos)}] {params}  val mAP {prev['val_map']:.3f}  (already done)")
            rows.append(prev)
            continue
        print(f"[{i}/{len(combos)}] {params}")
        m = M3(root / "models" / "embeddings", seed=seed, epochs=args.epochs, threads=args.threads,
               lexical_model=lex, log=(print if args.verbose else (lambda *_: None)), **params)
        m.fit(sp["train"], sp["val"])
        best_ep = max(m.history, key=lambda h: h["val_map"])["epoch"]
        rows.append({"params": params, "val_map": round(m.best_val, 4), "best_epoch": best_ep, "epochs_run": len(m.history)})
        print(f"      val mAP {m.best_val:.3f} (best epoch {best_ep} of {len(m.history)})")
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(rows, indent=2), encoding="utf-8")  # resume-safe
    rows.sort(key=lambda r: -r["val_map"])
    out_json.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    lines = ["# M3 settings sweep (validation mAP only, test split untouched)", "",
             "| Rank | MIL weight | pos-weight cap | Dropout | Val mAP | Best epoch |", "|---|---|---|---|---|---|"]
    for k, r in enumerate(rows, 1):
        p = r["params"]
        lines.append(f"| {k} | {p['mil_weight']} | {p['pos_clip']} | {p['dropout']} | {r['val_map']:.3f} | {r['best_epoch']} |")
    md = "\n".join(lines) + "\n"
    (root / "reports").mkdir(exist_ok=True)
    (root / "reports" / "m3_sweep.md").write_text(md, encoding="utf-8")
    (root / M3_BEST).write_text(json.dumps({"params": rows[0]["params"], "val_map": rows[0]["val_map"]}, indent=2),
                                encoding="utf-8")
    print("\n" + md)
    print(f"Best settings saved to {M3_BEST}; `train m3` (and every variant) now uses them.")


def _build_model(model: str, root: Path, args, seed: int):
    cache = root / "models" / "embeddings"
    if model == "m0":
        from .models.m0 import M0
        return M0(weak=not args.no_weak, seed=seed)
    if model == "m1":
        from .models.m1 import M1
        return M1(weak=not args.no_weak, seed=seed)
    if model == "m2":
        from .models.m2 import M2
        return M2(cache, weak=not args.no_weak, seed=seed)
    if model == "m3":
        try:
            from .models.m3 import M3
        except ImportError as e:
            raise SystemExit(str(e)) from e
        hp = _m3_hparams(root, args)
        return M3(cache, variant=args.variant, seed=seed, epochs=args.epochs, threads=args.threads,
                  lexical=not args.no_lexical, evidence_aug=getattr(args, "evidence_aug", False), **hp)
    raise SystemExit(f"unknown model {model}")


def cmd_train(args) -> None:
    """Train + evaluate one model the same way as all others (models/common.py)."""
    from .models.common import results_markdown, run_model
    root, cfg, tax = _paths(args)
    seed = args.seed if getattr(args, "seed", None) is not None else cfg.get("seed", 42)
    model = _build_model(args.model, root, args, seed)
    name = _m3_dir(args) if args.model == "m3" else _model_dir_name(args.model, "full", getattr(args, "no_weak", False))
    name += _seed_suffix(args)
    out = root / "models" / name
    res = run_model(model, _records(root), out, n_boot=args.boot, seed=seed)
    md = results_markdown(res, {t: tax.name(t) for t in tax.all_label_ids})
    if args.model == "m1" and hasattr(model, "importances"):
        md += "\n## Top features per tactic\n\n" + "\n".join(
            f"- {t}: " + ", ".join(f"{n} ({v:.2f})" for n, v in feats) for t, feats in model.importances(5).items()) + "\n"
    if hasattr(model, "save"):
        model.save(out if args.model == "m3" else out / f"{name}.pkl")
    (root / "reports").mkdir(exist_ok=True)
    (root / "reports" / f"{name}_results.md").write_text(md, encoding="utf-8")
    print(md)


def cmd_train_m0(args) -> None:  # kept for the phase-1 commands in the README
    args.model, args.no_weak = "m0", False
    cmd_train(args)


def cmd_embed(args) -> None:
    """Pre-compute the MiniLM embeddings for every turn (M2 and M3 reuse them)."""
    from .models.embed import EmbeddingCache
    root, _, _ = _paths(args)
    recs = _records(root)
    cache = EmbeddingCache(root / "models" / "embeddings")
    E = cache.embed([r["text"] for r in recs])
    print(f"{E.shape[0]:,} turns -> {E.shape[1]}-dim embeddings in {cache.vec_path}")


def cmd_compare(args) -> None:
    """Paired bootstrap: is model B better than model A? (FR-EVA-02)"""
    from .eval.compare import paired_bootstrap
    root, _, _ = _paths(args)
    test = [r for r in _records(root) if r["split"] == "test"]
    pa = root / "models" / args.a / "test_predictions.npz"
    pb = root / "models" / args.b / "test_predictions.npz"
    for level in ("turn", "dialogue"):
        r = paired_bootstrap(test, pa, pb, level=level, n_boot=args.boot)
        lo, hi = r["diff_ci95"]
        p = r["p_b_not_better"]
        verdict = (f"{args.b} better (p < 0.05)" if p < 0.05 else
                   f"{args.a} better (p < 0.05)" if p > 0.95 else "no significant difference")
        print(f"{level:9s} n={r['n']:,}  {args.a} {r['macro_f1_a']:.3f}  vs  {args.b} {r['macro_f1_b']:.3f}  "
              f"diff {r['diff']:+.3f} (95% CI {lo:+.3f} to {hi:+.3f}), p={r['p_b_not_better']:.3f}  -> {verdict}")


FINAL_MODEL = "m3_no-context_ev"  # M3 without context window, trained with evidence augmentation


def _names(tax) -> dict[str, str]:
    return {t: tax.name(t) for t in tax.all_label_ids}


def _write_report(root: Path, name: str, md: str) -> None:
    (root / "reports").mkdir(exist_ok=True)
    (root / "reports" / name).write_text(md, encoding="utf-8")
    print(md)


def cmd_grounding(args) -> None:
    """O5: does each model's tactic score depend on the annotated evidence?"""
    import pandas as pd

    from .analysis.common import load_model
    from .analysis.grounding import audit, per_tactic_table, report_markdown, summarize
    root, _, tax = _paths(args)
    test = [r for r in _records(root) if r["split"] == "test"]
    rows, dfs = [], {}
    for name in args.models:
        print(f"[{name}] scoring evidence-removed / evidence-only / random-cut versions ...")
        model, (th_t, _) = load_model(root, name, log=lambda *_: None)
        df = audit(model, th_t, test)
        df.insert(0, "model", name)
        dfs[name] = df
        rows += summarize(df, name, n_boot=args.boot)
    (root / "reports").mkdir(exist_ok=True)
    pd.concat(dfs.values()).to_csv(root / "reports" / "grounding_cases.csv", index=False)
    _write_report(root, "grounding.md", report_markdown(rows, per_tactic_table(dfs)))


def cmd_human_vs_llm(args) -> None:
    """O6: tactic profile of human- vs LLM-written SMS."""
    import numpy as np

    from .analysis.common import load_model
    from .analysis.human_vs_llm import (
        compare,
        lexicon_matrix,
        per_generator,
        report_markdown,
        select,
        tactic_matrix,
    )
    root, _, tax = _paths(args)
    sel = select(_records(root), args.label)
    if not sel["human"] or not sel["llm"]:
        raise SystemExit(f"need both human and LLM {args.label} messages; found {len(sel['human'])} and {len(sel['llm'])}")
    model, (th_t, _) = load_model(root, args.model, log=lambda *_: None)
    A, B = tactic_matrix(model, th_t, sel["human"]), tactic_matrix(model, th_t, sel["llm"])
    LA, LB = lexicon_matrix(sel["human"]), lexicon_matrix(sel["llm"])
    words = {k: np.median([len(r["text"].split()) for r in v]) for k, v in sel.items()}
    extra = {"tpm_human": A.sum(1).mean(), "tpm_llm": B.sum(1).mean(), "len_human": words["human"], "len_llm": words["llm"]}
    gens = {"human (Mishra-Soni)": A.mean(0), **per_generator(sel["llm"], B)}
    md = report_markdown(args.label, {k: len(v) for k, v in sel.items()}, args.model, compare(A, B), compare(LA, LB),
                         gens, _names(tax), extra)
    _write_report(root, f"human_vs_llm_{args.label}.md", md)


def cmd_transfer(args) -> None:
    """O4: leave one genre out - train on the others, test on it."""
    import numpy as np

    from .analysis.transfer import evaluate_genre, logo_records, report_markdown, trained_tactics
    from .models.common import by_split, load_predictions, run_model
    root, cfg, tax = _paths(args)
    seed = cfg.get("seed", 42)
    recs = _records(root)
    logo = json.loads((root / "data" / "processed" / "logo_splits.json").read_text(encoding="utf-8"))
    main_test = by_split(recs)["test"]
    rows = []
    for genre in args.genres:
        sub = logo_records(recs, logo, genre, clean_sources=not args.keep_neutral)
        sp = by_split(sub)
        tt = trained_tactics(sp["train"])
        for mname in args.models:
            out = root / "models" / f"logo_{genre}_{mname}" if not args.keep_neutral else root / "models" / f"logo_{genre}_{mname}_kn"
            print(f"[{genre} held out] training {mname} on {len(sp['train']):,} turns ...")
            if mname == "m3":
                args.model, args.variant, args.epochs, args.no_lexical = "m3", "no-context", args.epochs, False
                args.evidence_aug = True  # same recipe as the final model
            else:
                args.model, args.no_weak = mname, False
            model = _build_model(mname, root, args, seed)
            run_model(model, sub, out, n_boot=args.boot, seed=seed)
            St, _ = load_predictions(out / "test_predictions.npz", sp["test"])
            th = np.load(out / "test_predictions.npz")["thresholds"]
            transfer = evaluate_genre(genre, sp["test"], St, th, tt, n_boot=args.boot)
            ref_name = FINAL_MODEL if mname == "m3" else mname
            ref_dir = root / "models" / ref_name
            ids = {r["dialogue_id"] for r in sp["test"]}
            ref_test = [r for r in main_test if r["dialogue_id"] in ids]
            Sr, _ = load_predictions(ref_dir / "test_predictions.npz", ref_test)
            thr = np.load(ref_dir / "test_predictions.npz")["thresholds"]
            ind = evaluate_genre(genre, ref_test, Sr, thr, set(transfer["shared"]), n_boot=args.boot)
            rows.append({"genre": genre, "model": ref_name, "in_domain": ind, "transfer": transfer})
    _write_report(root, "transfer.md" if not args.keep_neutral else "transfer_keep_neutral.md",
                  report_markdown(rows, _names(tax), clean_sources=not args.keep_neutral))


def cmd_donation(args) -> None:
    """O7: persuader tactic use vs the persuadee's donation (P4G)."""
    from .analysis.common import load_model
    from .analysis.donation import dialogue_table, fit, persuader_ids, report_markdown
    from .data.io_utils import find_file, read_table
    root, cfg, tax = _paths(args)
    recs = _records(root)
    pcfg = cfg["datasets"]["p4g"]
    info_path = find_file(resolve(root, pcfg["dir"]), ["*full_info*", "*300_info*", "*info*"], pcfg.get("info_file"))
    pids = persuader_ids(read_table(info_path) if info_path else None)
    results = {}
    gold = dialogue_table(recs, "gold", pids=pids)
    if len(gold) >= 30:
        results["gold labels (annotated dialogues)"] = fit(gold)
    model, (th_t, _) = load_model(root, args.model, log=lambda *_: None)
    pred = dialogue_table(recs, "model", model=model, th_turn=th_t, pids=pids)
    results[f"{args.model} detections (all dialogues)"] = fit(pred)
    (root / "reports").mkdir(exist_ok=True)
    pred.to_csv(root / "reports" / "donation_dialogues.csv", index=False)
    _write_report(root, "donation.md", report_markdown(results, _names(tax)))


ONNX_DIR = Path("models") / "onnx"


def _bundle_from_torch(root: Path, model_name: str, tax) -> dict:
    """Same bundle.json content as export-onnx writes, for running the PyTorch model in the app."""
    import numpy as np

    from .data.schema import GENRES
    from .models.common import (
        TACTICS,
        by_split,
        load_predictions,
        threshold_pair,
        tune_all_thresholds,
    )
    mdir = root / "models" / model_name
    t1, d1 = threshold_pair(np.load(mdir / "test_predictions.npz")["thresholds"])
    val = by_split(_records(root))["val"]
    sv, _ = load_predictions(mdir / "val_predictions.npz", val)
    th_acc = tune_all_thresholds(val, sv, objective="accuracy")
    return {"model": model_name, "thresholds": {"balanced": [t1.tolist(), d1.tolist()], "careful": th_acc.tolist()},
            "tactics": [{"id": t, "name": tax.name(t), "group": tax.group(t)} for t in TACTICS], "genres": list(GENRES)}


def _predictor(args):
    from .serve.predictor import Predictor
    root, _, tax = _paths(args)
    if args.engine == "onnx":
        from .serve.engines import OnnxEngine
        bdir = root / (args.bundle or ONNX_DIR)
        if not (bdir / "bundle.json").exists():
            raise SystemExit(f"{bdir} has no bundle.json: run `python -m tacticlens.cli export-onnx` first")
        bundle = json.loads((bdir / "bundle.json").read_text(encoding="utf-8"))
        return Predictor(OnnxEngine(bdir, int8=not args.fp32), bundle)
    from .serve.engines import TorchEngine
    return Predictor(TorchEngine(root, args.model), _bundle_from_torch(root, args.model, tax))


def cmd_export_onnx(args) -> None:
    from .serve.export import export_onnx
    root, _, tax = _paths(args)
    names = {t: tax.name(t) for t in tax.all_label_ids}
    groups = {t: tax.group(t) for t in tax.all_label_ids}
    out = root / (args.out or ONNX_DIR)
    export_onnx(root, args.model, out, _records(root), names, groups)
    print(f"ONNX bundle written to {out}")


def cmd_eval_onnx(args) -> None:
    from .serve.export import eval_onnx
    root, _, _ = _paths(args)
    _write_report(root, "onnx.md", eval_onnx(root, root / (args.bundle or ONNX_DIR), _records(root), n_boot=args.boot))


def cmd_analyze(args) -> None:
    text = Path(args.file).read_text(encoding="utf-8") if args.file else args.text
    res = _predictor(args).analyze(text or "", actor=args.actor, mode=args.mode)
    print(json.dumps(res, indent=2, ensure_ascii=False))


def cmd_serve(args) -> None:
    import uvicorn

    from .serve.api import create_app
    uvicorn.run(create_app(_predictor(args)), host=args.host, port=args.port)


def cmd_ui(args) -> None:
    from .serve.ui import build_ui
    root, _, _ = _paths(args)
    log = root / args.feedback_log if args.feedback_log else None
    build_ui(_predictor(args), feedback_log=log).launch(server_name=args.host, server_port=args.port, share=args.share)


def cmd_bundle_space(args) -> None:
    from .serve.space import bundle_space
    root, _, _ = _paths(args)
    out = bundle_space(root / (args.bundle or ONNX_DIR), Path(__file__).resolve().parent, root / args.out)
    print(f"Space folder ready: {out}  (test it: cd {args.out} && python app.py)")


def cmd_deploy_space(args) -> None:
    from .serve.space import deploy_space
    root, _, _ = _paths(args)
    print("Deployed:", deploy_space(root / args.dir, args.repo, private=args.private))


def cmd_rescore(args) -> None:
    """Re-tune thresholds and re-score every saved model (or the ones named) without retraining."""
    from .models.common import results_markdown, score_saved
    root, _, tax = _paths(args)
    recs = _records(root)
    dirs = [root / "models" / n for n in args.models] if args.models else sorted(
        p.parent for p in (root / "models").glob("*/val_predictions.npz") if not p.parent.name.startswith("logo_"))
    for d in dirs:
        if not (d / "val_predictions.npz").exists():
            print(f"{d.name}: no val_predictions.npz (trained before rescore existed) - retrain it once")
            continue
        old = json.loads((d / "metrics.json").read_text(encoding="utf-8")).get("model", d.name)
        res = score_saved(old, d, recs, n_boot=args.boot)
        md = results_markdown(res, {t: tax.name(t) for t in tax.all_label_ids})
        (root / "reports" / f"{d.name}_results.md").write_text(md, encoding="utf-8")
        t, g = res.get("turn", {}).get("macro_f1"), res.get("dialogue", {}).get("macro_f1")
        print(f"{d.name:22s} turn {t if t is None else round(t, 3)}  dialogue {g if g is None else round(g, 3)}")


def summarize_runs(models_dir: Path) -> list[dict]:
    """Every models/<name>/metrics.json, grouped over seeds (<name>, <name>_s1, <name>_s2 ...)."""
    import re
    import statistics
    groups: dict[str, list[dict]] = {}
    for f in sorted(models_dir.glob("*/metrics.json")):
        if f.parent.name.startswith("logo_"):  # transfer runs have their own test sets
            continue
        base = re.sub(r"_s\d+$", "", f.parent.name)
        groups.setdefault(base, []).append(json.loads(f.read_text(encoding="utf-8")))
    rows = []
    for name, runs in groups.items():
        row = {"model": name, "seeds": len(runs)}
        for level in ("turn", "dialogue", "genre"):
            v = [r[level]["macro_f1"] for r in runs if r.get(level)]
            if v:
                row[level] = statistics.mean(v)
                row[level + "_sd"] = statistics.stdev(v) if len(v) > 1 else None
        rows.append(row)
    return rows


def cmd_summarize(args) -> None:
    root, _, _ = _paths(args)
    rows = summarize_runs(root / "models")

    def cell(r, k):
        if k not in r:
            return "-"
        sd = r.get(k + "_sd")
        return f"{r[k]:.3f}" + (f" ± {sd:.3f}" if sd is not None else "")

    lines = ["# All runs (macro-F1, mean ± SD over seeds)", "",
             "| Model | Seeds | Turn | Dialogue | Genre |", "|---|---|---|---|---|"]
    lines += [f"| {r['model']} | {r['seeds']} | {cell(r, 'turn')} | {cell(r, 'dialogue')} | {cell(r, 'genre')} |"
              for r in rows]
    md = "\n".join(lines) + "\n"
    (root / "reports").mkdir(exist_ok=True)
    (root / "reports" / "summary.md").write_text(md, encoding="utf-8")
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
    p = sub.add_parser("train", help="train + evaluate m0, m1, m2 or m3")
    p.add_argument("model", choices=["m0", "m1", "m2", "m3"])
    p.add_argument("--variant", default="full", help="m3 only: full, no-role, no-context, no-adv, no-mil, dual-role")
    p.add_argument("--epochs", type=int, default=40, help="m3: max epochs (early stopping after 5 without gain)")
    p.add_argument("--no-lexical", action="store_true", help="m3: MiniLM embedding only, no TF-IDF-SVD features")
    p.add_argument("--evidence-aug", action="store_true", help="m3: add evidence-only training turns (saved as <name>_ev)")
    p.add_argument("--threads", type=int, default=None, help="CPU threads for PyTorch (default: all)")
    p.add_argument("--mil-weight", type=float, default=None, help="m3: weight of the MentalManip MIL loss")
    p.add_argument("--pos-clip", type=float, default=None, help="m3: cap on the rare-class positive weight")
    p.add_argument("--dropout", type=float, default=None, help="m3: dropout")
    p.add_argument("--seed", type=int, default=None, help="training seed; results go to <model>_s<seed>")
    p.add_argument("--no-weak", action="store_true", help="m0-m2: don't use MentalManip dialogue labels as weak turn labels")
    p.add_argument("--boot", type=int, default=1000)
    p.set_defaults(fn=cmd_train)
    p = sub.add_parser("sweep-m3", help="choose M3 settings on validation data (8 runs, resumable)")
    p.add_argument("--epochs", type=int, default=40)
    p.add_argument("--threads", type=int, default=None)
    p.add_argument("--restart", action="store_true", help="ignore earlier sweep results")
    p.set_defaults(fn=cmd_sweep_m3)
    sub.add_parser("embed").set_defaults(fn=cmd_embed)
    sub.add_parser("summarize", help="table of every trained model, mean ± SD over seeds").set_defaults(fn=cmd_summarize)
    p = sub.add_parser("grounding", help="phase 3: does the tactic score depend on the annotated evidence?")
    p.add_argument("models", nargs="*", default=["m0", FINAL_MODEL], help="folders under models/ (M0 or M3 runs)")
    p.add_argument("--boot", type=int, default=1000)
    p.set_defaults(fn=cmd_grounding)
    p = sub.add_parser("human-vs-llm", help="phase 3: tactic profile of human vs LLM-written SMS")
    p.add_argument("--model", default=FINAL_MODEL)
    p.add_argument("--label", default="smishing", choices=["smishing", "spam"])
    p.set_defaults(fn=cmd_human_vs_llm)
    p = sub.add_parser("transfer", help="phase 3: leave one genre out (trains 1 model per genre and model)")
    p.add_argument("--genres", nargs="*", default=["persuasion", "manipulation", "scam"])
    p.add_argument("--models", nargs="*", default=["m0", "m3"], choices=["m0", "m3"])
    p.add_argument("--keep-neutral", action="store_true", help="keep held-out datasets' neutral dialogues in training")
    p.add_argument("--epochs", type=int, default=40)
    p.add_argument("--threads", type=int, default=None)
    p.add_argument("--boot", type=int, default=1000)
    p.set_defaults(fn=cmd_transfer)
    p = sub.add_parser("donation", help="phase 3: persuader tactics vs donations (P4G)")
    p.add_argument("--model", default=FINAL_MODEL)
    p.set_defaults(fn=cmd_donation)
    def engine_args(p, port):
        p.add_argument("--engine", choices=["onnx", "torch"], default="onnx")
        p.add_argument("--bundle", help="ONNX bundle folder (default models/onnx)")
        p.add_argument("--fp32", action="store_true", help="use the fp32 ONNX files instead of int8")
        p.add_argument("--model", default=FINAL_MODEL, help="torch engine: which trained model")
        if port:
            p.add_argument("--host", default="127.0.0.1")
            p.add_argument("--port", type=int, default=port)

    p = sub.add_parser("export-onnx", help="phase 4: export the final model to ONNX (fp32 + int8)")
    p.add_argument("--model", default=FINAL_MODEL)
    p.add_argument("--out", help="output folder (default models/onnx)")
    p.set_defaults(fn=cmd_export_onnx)
    p = sub.add_parser("eval-onnx", help="phase 4: test-split F1, size and speed of the ONNX model")
    p.add_argument("--bundle")
    p.add_argument("--boot", type=int, default=200)
    p.set_defaults(fn=cmd_eval_onnx)
    p = sub.add_parser("analyze", help="phase 4: analyse one text from the command line (JSON out)")
    p.add_argument("text", nargs="?", default="")
    p.add_argument("--file", help="read the text from a file")
    p.add_argument("--actor")
    p.add_argument("--mode", default="balanced", choices=["balanced", "careful"])
    engine_args(p, None)
    p.set_defaults(fn=cmd_analyze)
    p = sub.add_parser("serve", help="phase 4: FastAPI server (POST /analyze; docs at /docs)")
    engine_args(p, 8000)
    p.set_defaults(fn=cmd_serve)
    p = sub.add_parser("ui", help="phase 4: Gradio web UI")
    engine_args(p, 7860)
    p.add_argument("--share", action="store_true", help="temporary public gradio.live link")
    p.add_argument("--feedback-log", help="CSV for user-study feedback, e.g. reports/study_feedback.csv")
    p.set_defaults(fn=cmd_ui)
    p = sub.add_parser("bundle-space", help="phase 4: make the Hugging Face Space folder")
    p.add_argument("--bundle")
    p.add_argument("--out", default="space")
    p.set_defaults(fn=cmd_bundle_space)
    p = sub.add_parser("deploy-space", help="phase 4: upload the Space folder (needs huggingface-cli login)")
    p.add_argument("--repo", required=True, help="your-username/tacticlens")
    p.add_argument("--dir", default="space")
    p.add_argument("--private", action="store_true")
    p.set_defaults(fn=cmd_deploy_space)
    p = sub.add_parser("rescore", help="re-tune thresholds + re-score saved models without retraining")
    p.add_argument("models", nargs="*", help="folders under models/ (default: all that have val predictions)")
    p.add_argument("--boot", type=int, default=1000)
    p.set_defaults(fn=cmd_rescore)
    p = sub.add_parser("compare", help="paired bootstrap between two trained models")
    p.add_argument("a", help="baseline folder under models/, e.g. m2")
    p.add_argument("b", help="new model folder under models/, e.g. m3_full")
    p.add_argument("--boot", type=int, default=2000)
    p.set_defaults(fn=cmd_compare)
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
