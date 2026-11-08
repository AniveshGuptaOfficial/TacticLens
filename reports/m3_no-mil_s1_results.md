# M3 role-aware GRU-attention (no-mil) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.531** (95% CI 0.491 to 0.570), micro-F1 0.655, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.500 | 0.607 | 0.548 | 0.564 | 84 |
| T2 | Emotional appeal (sympathy) | 0.415 | 0.773 | 0.540 | 0.653 | 22 |
| T3 | Credibility / authority | 0.877 | 0.860 | 0.869 | 0.928 | 215 |
| T4 | Personal story / self-modelling | 0.167 | 0.143 | 0.154 | 0.131 | 28 |
| T5 | Urgency / scarcity | 0.869 | 0.979 | 0.921 | 0.857 | 95 |
| T6 | Reward / reciprocity | 0.308 | 0.333 | 0.320 | 0.375 | 48 |
| T7 | Flattery / liking | 0.085 | 0.846 | 0.154 | 0.236 | 13 |
| T9 | Threat / intimidation | 0.617 | 0.935 | 0.744 | 0.739 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.254** (95% CI 0.231 to 0.274), micro-F1 0.218, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.246 | 0.838 | 0.380 | 0.243 | 136 |
| T7 | Flattery / liking | 0.239 | 0.934 | 0.381 | 0.224 | 136 |
| T8 | Guilt / obligation | 0.000 | 0.000 | 0.000 | 0.027 | 20 |
| T9 | Threat / intimidation | 0.105 | 0.984 | 0.189 | 0.095 | 61 |
| T10 | Distortion and blame | 0.238 | 0.488 | 0.320 | 0.254 | 166 |

## Genre (every test turn)

macro-F1 **0.839** (95% CI 0.822 to 0.855), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.996 |
| manipulation | 0.805 |
| scam | 0.959 |
| neutral | 0.595 |
