# Dual-role baseline (after HDRIN) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.575** (95% CI 0.524 to 0.620), micro-F1 0.689, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.426 | 0.619 | 0.505 | 0.432 | 84 |
| T2 | Emotional appeal (sympathy) | 0.457 | 0.727 | 0.561 | 0.601 | 22 |
| T3 | Credibility / authority | 0.873 | 0.860 | 0.867 | 0.928 | 215 |
| T4 | Personal story / self-modelling | 0.293 | 0.429 | 0.348 | 0.212 | 28 |
| T5 | Urgency / scarcity | 0.872 | 1.000 | 0.931 | 0.871 | 95 |
| T6 | Reward / reciprocity | 0.250 | 0.604 | 0.354 | 0.387 | 48 |
| T7 | Flattery / liking | 0.429 | 0.231 | 0.300 | 0.185 | 13 |
| T9 | Threat / intimidation | 0.615 | 0.903 | 0.732 | 0.759 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.333** (95% CI 0.293 to 0.366), micro-F1 0.303, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.283 | 0.662 | 0.396 | 0.296 | 136 |
| T7 | Flattery / liking | 0.283 | 0.647 | 0.394 | 0.309 | 136 |
| T8 | Guilt / obligation | 0.119 | 0.250 | 0.161 | 0.103 | 20 |
| T9 | Threat / intimidation | 0.172 | 0.328 | 0.226 | 0.200 | 61 |
| T10 | Distortion and blame | 0.358 | 0.753 | 0.485 | 0.467 | 166 |

## Genre (every test turn)

macro-F1 **0.835** (95% CI 0.820 to 0.849), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.994 |
| manipulation | 0.791 |
| scam | 0.950 |
| neutral | 0.604 |
