# M3 role-aware GRU-attention (full) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.520** (95% CI 0.491 to 0.549), micro-F1 0.590, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.434 | 0.738 | 0.546 | 0.572 | 84 |
| T2 | Emotional appeal (sympathy) | 0.309 | 0.773 | 0.442 | 0.525 | 22 |
| T3 | Credibility / authority | 0.858 | 0.902 | 0.880 | 0.938 | 215 |
| T4 | Personal story / self-modelling | 0.126 | 0.857 | 0.220 | 0.203 | 28 |
| T5 | Urgency / scarcity | 0.864 | 1.000 | 0.927 | 0.896 | 95 |
| T6 | Reward / reciprocity | 0.235 | 0.500 | 0.320 | 0.334 | 48 |
| T7 | Flattery / liking | 0.064 | 0.692 | 0.117 | 0.267 | 13 |
| T9 | Threat / intimidation | 0.609 | 0.855 | 0.711 | 0.784 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.327** (95% CI 0.289 to 0.362), micro-F1 0.209, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.320 | 0.485 | 0.386 | 0.349 | 136 |
| T7 | Flattery / liking | 0.273 | 0.794 | 0.406 | 0.368 | 136 |
| T8 | Guilt / obligation | 0.115 | 0.300 | 0.167 | 0.098 | 20 |
| T9 | Threat / intimidation | 0.167 | 0.443 | 0.242 | 0.168 | 61 |
| T10 | Distortion and blame | 0.405 | 0.464 | 0.433 | 0.478 | 166 |

## Genre (every test turn)

macro-F1 **0.842** (95% CI 0.827 to 0.856), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.995 |
| manipulation | 0.813 |
| scam | 0.947 |
| neutral | 0.612 |
