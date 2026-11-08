# M3 role-aware GRU-attention (no-mil) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.491** (95% CI 0.458 to 0.524), micro-F1 0.634, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.429 | 0.643 | 0.514 | 0.547 | 84 |
| T2 | Emotional appeal (sympathy) | 0.281 | 0.727 | 0.405 | 0.528 | 22 |
| T3 | Credibility / authority | 0.884 | 0.814 | 0.847 | 0.933 | 215 |
| T4 | Personal story / self-modelling | 0.000 | 0.000 | 0.000 | 0.119 | 28 |
| T5 | Urgency / scarcity | 0.872 | 1.000 | 0.931 | 0.873 | 95 |
| T6 | Reward / reciprocity | 0.348 | 0.333 | 0.340 | 0.369 | 48 |
| T7 | Flattery / liking | 0.087 | 0.846 | 0.157 | 0.181 | 13 |
| T9 | Threat / intimidation | 0.606 | 0.919 | 0.731 | 0.656 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.275** (95% CI 0.253 to 0.295), micro-F1 0.226, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.254 | 0.640 | 0.363 | 0.250 | 136 |
| T7 | Flattery / liking | 0.235 | 0.985 | 0.379 | 0.232 | 136 |
| T8 | Guilt / obligation | 0.013 | 0.050 | 0.021 | 0.029 | 20 |
| T9 | Threat / intimidation | 0.102 | 1.000 | 0.185 | 0.095 | 61 |
| T10 | Distortion and blame | 0.276 | 0.928 | 0.425 | 0.274 | 166 |

## Genre (every test turn)

macro-F1 **0.845** (95% CI 0.829 to 0.861), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.997 |
| manipulation | 0.828 |
| scam | 0.951 |
| neutral | 0.605 |
