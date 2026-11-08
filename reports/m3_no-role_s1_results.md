# M3 role-aware GRU-attention (no-role) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.545** (95% CI 0.501 to 0.584), micro-F1 0.677, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.452 | 0.679 | 0.543 | 0.509 | 84 |
| T2 | Emotional appeal (sympathy) | 0.395 | 0.773 | 0.523 | 0.580 | 22 |
| T3 | Credibility / authority | 0.827 | 0.870 | 0.848 | 0.918 | 215 |
| T4 | Personal story / self-modelling | 0.200 | 0.286 | 0.235 | 0.220 | 28 |
| T5 | Urgency / scarcity | 0.872 | 1.000 | 0.931 | 0.868 | 95 |
| T6 | Reward / reciprocity | 0.266 | 0.521 | 0.352 | 0.329 | 48 |
| T7 | Flattery / liking | 0.154 | 0.308 | 0.205 | 0.281 | 13 |
| T9 | Threat / intimidation | 0.614 | 0.871 | 0.720 | 0.753 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.318** (95% CI 0.280 to 0.355), micro-F1 0.271, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.292 | 0.721 | 0.415 | 0.298 | 136 |
| T7 | Flattery / liking | 0.299 | 0.699 | 0.419 | 0.295 | 136 |
| T8 | Guilt / obligation | 0.091 | 0.050 | 0.065 | 0.101 | 20 |
| T9 | Threat / intimidation | 0.162 | 0.344 | 0.220 | 0.152 | 61 |
| T10 | Distortion and blame | 0.339 | 0.783 | 0.473 | 0.413 | 166 |

## Genre (every test turn)

macro-F1 **0.835** (95% CI 0.820 to 0.849), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.993 |
| manipulation | 0.801 |
| scam | 0.948 |
| neutral | 0.599 |
