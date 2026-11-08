# M3 role-aware GRU-attention (no-context) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.538** (95% CI 0.498 to 0.578), micro-F1 0.689, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.500 | 0.548 | 0.523 | 0.641 | 84 |
| T2 | Emotional appeal (sympathy) | 0.531 | 0.773 | 0.630 | 0.704 | 22 |
| T3 | Credibility / authority | 0.875 | 0.814 | 0.843 | 0.929 | 215 |
| T4 | Personal story / self-modelling | 0.000 | 0.000 | 0.000 | 0.201 | 28 |
| T5 | Urgency / scarcity | 0.879 | 0.916 | 0.897 | 0.867 | 95 |
| T6 | Reward / reciprocity | 0.323 | 0.438 | 0.372 | 0.400 | 48 |
| T7 | Flattery / liking | 0.200 | 0.538 | 0.292 | 0.372 | 13 |
| T9 | Threat / intimidation | 0.647 | 0.887 | 0.748 | 0.789 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.349** (95% CI 0.306 to 0.387), micro-F1 0.362, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.303 | 0.632 | 0.410 | 0.325 | 136 |
| T7 | Flattery / liking | 0.269 | 0.801 | 0.403 | 0.332 | 136 |
| T8 | Guilt / obligation | 0.138 | 0.200 | 0.163 | 0.191 | 20 |
| T9 | Threat / intimidation | 0.222 | 0.459 | 0.299 | 0.237 | 61 |
| T10 | Distortion and blame | 0.330 | 0.813 | 0.470 | 0.430 | 166 |

## Genre (every test turn)

macro-F1 **0.829** (95% CI 0.815 to 0.842), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.961 |
| manipulation | 0.835 |
| scam | 0.956 |
| neutral | 0.562 |
