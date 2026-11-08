# M3 role-aware GRU-attention (no-context) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.566** (95% CI 0.526 to 0.604), micro-F1 0.681, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.470 | 0.655 | 0.547 | 0.653 | 84 |
| T2 | Emotional appeal (sympathy) | 0.409 | 0.818 | 0.545 | 0.673 | 22 |
| T3 | Credibility / authority | 0.879 | 0.842 | 0.860 | 0.927 | 215 |
| T4 | Personal story / self-modelling | 0.227 | 0.357 | 0.278 | 0.283 | 28 |
| T5 | Urgency / scarcity | 0.864 | 1.000 | 0.927 | 0.873 | 95 |
| T6 | Reward / reciprocity | 0.348 | 0.500 | 0.410 | 0.378 | 48 |
| T7 | Flattery / liking | 0.129 | 0.692 | 0.217 | 0.350 | 13 |
| T9 | Threat / intimidation | 0.620 | 0.919 | 0.740 | 0.748 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.350** (95% CI 0.302 to 0.397), micro-F1 0.290, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.267 | 0.860 | 0.407 | 0.301 | 136 |
| T7 | Flattery / liking | 0.265 | 0.897 | 0.409 | 0.294 | 136 |
| T8 | Guilt / obligation | 0.333 | 0.100 | 0.154 | 0.230 | 20 |
| T9 | Threat / intimidation | 0.213 | 0.426 | 0.284 | 0.240 | 61 |
| T10 | Distortion and blame | 0.416 | 0.608 | 0.494 | 0.450 | 166 |

## Genre (every test turn)

macro-F1 **0.817** (95% CI 0.805 to 0.829), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.963 |
| manipulation | 0.799 |
| scam | 0.940 |
| neutral | 0.565 |
