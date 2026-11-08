# M3 role-aware GRU-attention (full) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.532** (95% CI 0.499 to 0.563), micro-F1 0.667, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.474 | 0.643 | 0.545 | 0.575 | 84 |
| T2 | Emotional appeal (sympathy) | 0.386 | 0.773 | 0.515 | 0.612 | 22 |
| T3 | Credibility / authority | 0.905 | 0.842 | 0.872 | 0.932 | 215 |
| T4 | Personal story / self-modelling | 0.143 | 0.071 | 0.095 | 0.198 | 28 |
| T5 | Urgency / scarcity | 0.856 | 0.937 | 0.894 | 0.836 | 95 |
| T6 | Reward / reciprocity | 0.308 | 0.500 | 0.381 | 0.395 | 48 |
| T7 | Flattery / liking | 0.120 | 0.846 | 0.210 | 0.275 | 13 |
| T9 | Threat / intimidation | 0.640 | 0.887 | 0.743 | 0.716 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.316** (95% CI 0.279 to 0.352), micro-F1 0.254, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.320 | 0.419 | 0.363 | 0.316 | 136 |
| T7 | Flattery / liking | 0.322 | 0.500 | 0.392 | 0.347 | 136 |
| T8 | Guilt / obligation | 0.088 | 0.150 | 0.111 | 0.058 | 20 |
| T9 | Threat / intimidation | 0.177 | 0.475 | 0.258 | 0.191 | 61 |
| T10 | Distortion and blame | 0.327 | 0.765 | 0.458 | 0.394 | 166 |

## Genre (every test turn)

macro-F1 **0.827** (95% CI 0.812 to 0.841), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.996 |
| manipulation | 0.749 |
| scam | 0.976 |
| neutral | 0.587 |
