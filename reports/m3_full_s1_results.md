# M3 role-aware GRU-attention (full) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.534** (95% CI 0.496 to 0.572), micro-F1 0.639, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.490 | 0.560 | 0.522 | 0.524 | 84 |
| T2 | Emotional appeal (sympathy) | 0.500 | 0.500 | 0.500 | 0.596 | 22 |
| T3 | Credibility / authority | 0.812 | 0.865 | 0.838 | 0.917 | 215 |
| T4 | Personal story / self-modelling | 0.200 | 0.500 | 0.286 | 0.206 | 28 |
| T5 | Urgency / scarcity | 0.869 | 0.905 | 0.887 | 0.856 | 95 |
| T6 | Reward / reciprocity | 0.288 | 0.354 | 0.318 | 0.336 | 48 |
| T7 | Flattery / liking | 0.101 | 0.846 | 0.180 | 0.301 | 13 |
| T9 | Threat / intimidation | 0.620 | 0.919 | 0.740 | 0.762 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.308** (95% CI 0.270 to 0.346), micro-F1 0.287, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.302 | 0.375 | 0.334 | 0.290 | 136 |
| T7 | Flattery / liking | 0.309 | 0.434 | 0.361 | 0.291 | 136 |
| T8 | Guilt / obligation | 0.087 | 0.100 | 0.093 | 0.081 | 20 |
| T9 | Threat / intimidation | 0.178 | 0.623 | 0.277 | 0.180 | 61 |
| T10 | Distortion and blame | 0.339 | 0.795 | 0.476 | 0.445 | 166 |

## Genre (every test turn)

macro-F1 **0.818** (95% CI 0.801 to 0.834), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.996 |
| manipulation | 0.722 |
| scam | 0.965 |
| neutral | 0.591 |
