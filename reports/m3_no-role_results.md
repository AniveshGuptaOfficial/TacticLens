# M3 role-aware GRU-attention (no-role) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.552** (95% CI 0.512 to 0.594), micro-F1 0.675, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.486 | 0.619 | 0.545 | 0.491 | 84 |
| T2 | Emotional appeal (sympathy) | 0.552 | 0.727 | 0.627 | 0.587 | 22 |
| T3 | Credibility / authority | 0.865 | 0.833 | 0.848 | 0.915 | 215 |
| T4 | Personal story / self-modelling | 0.203 | 0.571 | 0.299 | 0.222 | 28 |
| T5 | Urgency / scarcity | 0.853 | 0.979 | 0.912 | 0.868 | 95 |
| T6 | Reward / reciprocity | 0.341 | 0.292 | 0.315 | 0.340 | 48 |
| T7 | Flattery / liking | 0.105 | 0.308 | 0.157 | 0.244 | 13 |
| T9 | Threat / intimidation | 0.609 | 0.855 | 0.711 | 0.717 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.348** (95% CI 0.317 to 0.375), micro-F1 0.317, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.282 | 0.860 | 0.425 | 0.320 | 136 |
| T7 | Flattery / liking | 0.293 | 0.853 | 0.436 | 0.332 | 136 |
| T8 | Guilt / obligation | 0.065 | 0.400 | 0.112 | 0.128 | 20 |
| T9 | Threat / intimidation | 0.156 | 0.754 | 0.258 | 0.155 | 61 |
| T10 | Distortion and blame | 0.396 | 0.711 | 0.509 | 0.464 | 166 |

## Genre (every test turn)

macro-F1 **0.839** (95% CI 0.822 to 0.854), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.990 |
| manipulation | 0.799 |
| scam | 0.955 |
| neutral | 0.611 |
