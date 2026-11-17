# TacticLens

Capstone project: **Where Persuasion Ends and Manipulation Begins: A Unified, Role-Aware Model of
Influence Tactics Across Persuasive Dialogue, Interpersonal Manipulation and Human- vs LLM-Written Scams.**

TacticLens labels influence tactics turn by turn, using who is speaking (actor or target), across
persuasion, interpersonal manipulation and scam messages. It runs on CPU only, at zero cost.

This repository follows the SRS (TacticLens SRS v1.0). Requirement IDs (FR-DAT-01 and so on) appear in
the code comments so each piece can be traced back.

## Status

| Phase | Months | What | Status |
|---|---|---|---|
| 1 | 1-2 | Project setup, taxonomy, data pipeline, check set, kappa, M0 baseline | **Done** |
| 2 | 3-4 | M1 (XGBoost + lexicon), M2 (MiniLM + MLP), M3 (role-aware GRU-attention), dual-role baseline, ablations | **Done** |
| 3 | 4-5 | Grounding audit, cross-genre transfer, human vs LLM, donation model | **Implemented** |
| 4 | 5-6 | ONNX int8, FastAPI, Gradio, Docker, Hugging Face Space, user study | **Implemented** |

## Folder layout

```
TacticLens/
  configs/            taxonomy.yaml (10 tactics + label mappings), datasets.yaml (paths, columns)
  data/
    raw/              put the downloaded datasets here (not committed to Git)
    processed/        unified records and splits (created by the pipeline)
    annotation/       check-set CSVs for the two annotators
  reports/            data card, metrics, figures
  models/             trained models
  src/tacticlens/
    data/             loaders, normaliser, dedupe, splits, data card
    taxonomy/         taxonomy loading, label mapping, roles, kappa
    models/           baselines (M0 now; M1-M3 next)
    eval/             metrics with bootstrap confidence intervals
    cli.py            one entry point for every step
  tests/              unit tests with small synthetic fixtures
  run.ps1             Windows commands (.\run.ps1 setup, test, prepare, ...)
  .github/workflows/  CI: lint + tests on every push
```

## Setup (Windows, once)

1. Install Python 3.11 from python.org (tick "Add to PATH").
2. Open PowerShell in this folder and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
pytest
```

All tests should pass before you add any real data.

## Step 1: download the five datasets

Put each one in its own folder under `data/raw/`. Exact file names don't matter: the loaders find the
right file and columns, and `configs/datasets.yaml` lets you override them.

| Dataset | Folder | Where to get it |
|---|---|---|
| PersuasionForGood | `data/raw/p4g/` | https://gitlab.com/ucdavisnlp/persuasionforgood (files `full_dialog.csv`, `full_info.csv`, `300_dialog.xlsx`, `300_info.xlsx`) |
| MentalManip | `data/raw/mentalmanip/` | https://github.com/audreycs/MentalManip (`mentalmanip_maj.csv`, `mentalmanip_con.csv`) |
| Mishra-Soni SMS Phishing | `data/raw/sms_human/` | https://data.mendeley.com/datasets/f45bkkt8pr/1 (CC BY 4.0) |
| Munoz & Islam LLM SMS | `data/raw/sms_llm/` | https://data.mendeley.com/datasets/vmg875v4xs/1 (CC BY 4.0) |
| PsyScam | `data/raw/psyscam/` | Link in the paper: https://arxiv.org/abs/2505.15017 (research use only) |

Then check what was found:

```powershell
python -m tacticlens.cli inspect
```

## Step 2: run the pipeline

```powershell
python -m tacticlens.cli prepare      # load, normalise, map labels, roles, dedupe, split (FR-DAT, FR-TAX)
python -m tacticlens.cli datacard     # reports/data_card.md (FR-DAT-08)
python -m tacticlens.cli checkset     # data/annotation/checkset_A.csv and _B.csv (FR-TAX-05)
python -m tacticlens.cli train-m0     # M0 baseline + metrics with 95% CIs (FR-MOD-01, FR-EVA-01)
```

After both annotators fill in their check-set CSVs (rules and practice items: `docs/annotation_guide.md`):

```powershell
python -m tacticlens.cli kappa        # Cohen's kappa per tactic (FR-TAX-06, AC-01)
```

## Phase 2: models

Install the model libraries once (about 1 GB with PyTorch CPU):

```cmd
pip install -r requirements-ml.txt
pytest -q
```

Train and evaluate. Every model is scored the same way (`models/common.py`), and results go to
`reports/<model>_results.md` and `models/<model>/`:

```cmd
python -m tacticlens.cli train m0
python -m tacticlens.cli train m1
python -m tacticlens.cli embed                      :: MiniLM embeddings, cached, ~10-20 min once
python -m tacticlens.cli train m2
python -m tacticlens.cli sweep-m3                   :: pick M3 settings on validation only (8 runs, ~40 min, resumable)
python -m tacticlens.cli train m3                   :: the proposed model (uses configs/m3_best.json)
python -m tacticlens.cli train m3 --variant dual-role
python -m tacticlens.cli train m3 --variant no-role       :: ablations (FR-MOD-09)
python -m tacticlens.cli train m3 --variant no-context
python -m tacticlens.cli train m3 --variant no-adv
python -m tacticlens.cli train m3 --variant no-mil
```

Repeat key runs with other seeds (`--seed 1`, `--seed 2`; saved as `<model>_s1` ...) and get one table
of mean ± SD over seeds in `reports/summary.md`:

```cmd
python -m tacticlens.cli summarize
python -m tacticlens.cli rescore            :: re-tune thresholds + re-score saved models, no retraining
```

**Final model:** `m3_no-context_ev`: M3 without the context window (keeps the role head), trained
with evidence augmentation (`--variant no-context --evidence-aug`). Over 3 seeds it is at least as good
as full M3, 3x faster, and the best grounded in the annotated evidence (phase 2 and 3 results docs).

Is M3 better? Paired bootstrap over dialogues (FR-EVA-02):

```cmd
python -m tacticlens.cli compare m2 m3_full
python -m tacticlens.cli compare dual_role m3_full
python -m tacticlens.cli compare m3_no-role m3_full       :: AC-03: does role help?
```

## Phase 3: analyses

All use the final model (`m3_no-context_ev`) unless you name another trained model. Reports go to `reports/`.

```cmd
:: evidence-span training: M3 also learns from evidence-only turns (saved as m3_no-context_ev)
python -m tacticlens.cli train m3 --variant no-context --evidence-aug

python -m tacticlens.cli grounding m0 m3_full m3_no-context m3_no-context_ev   :: O5 grounding audit
python -m tacticlens.cli transfer                                              :: O4 leave one genre out (~15 min)
python -m tacticlens.cli human-vs-llm                                          :: O6 human vs LLM smishing
python -m tacticlens.cli human-vs-llm --label spam
python -m tacticlens.cli donation                                              :: O7 tactics vs donations
```

## Phase 4: the app

Install the app libraries once: `pip install -r requirements-app.txt`

```cmd
python -m tacticlens.cli export-onnx          :: final model -> models/onnx (fp32 + int8, tokenizer, thresholds)
python -m tacticlens.cli eval-onnx            :: reports/onnx.md: F1, size and speed, int8 vs PyTorch
python -m tacticlens.cli analyze "URGENT: your account is locked, verify now at http://x.example"
python -m tacticlens.cli ui                   :: web UI at http://127.0.0.1:7860
python -m tacticlens.cli serve                :: HTTP API at http://127.0.0.1:8000/docs
python -m tacticlens.cli bundle-space         :: space/ folder for Hugging Face (int8 ONNX, no PyTorch)
huggingface-cli login
python -m tacticlens.cli deploy-space --repo YOUR-HF-NAME/tacticlens
```

Two modes, both with thresholds tuned on validation data: **balanced** (F1, the reported results)
and **careful** (accuracy, fewer false alarms). For each tactic the app shows the sentence that
scores highest on its own as evidence. Conversations are pasted as `Name: text` lines; give the
speaker to check to get role-aware results. User-study protocol: `docs/user_study.md`
(run the UI with `--feedback-log reports/study_feedback.csv`). Docker: see the `Dockerfile`.

## First checks to do (from the SRS)

1. `python -m tacticlens.cli llm-overlap`: how many Munoz & Islam messages are exact copies of
   Mishra-Soni ones. If most are copies, generate LLM SMS locally instead (see SRS section 6.1).
2. After `prepare`, open `reports/unmapped_labels.csv`. Any source label that maps to no tactic is
   listed there.
3. MentalManip has no per-turn manipulator label, so its roles are `unknown` until the check set is
   annotated.

## Licences

Code: MIT. Data is **not** included. MentalManip is CC BY-NC 4.0 (non-commercial). PsyScam states no
licence and is used for research evaluation only.
