# Dual-role baseline (after HDRIN) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.540** (95% CI 0.495 to 0.583), micro-F1 0.659, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.506 | 0.476 | 0.491 | 0.496 | 84 |
| T2 | Emotional appeal (sympathy) | 0.310 | 0.818 | 0.450 | 0.614 | 22 |
| T3 | Credibility / authority | 0.877 | 0.833 | 0.854 | 0.924 | 215 |
| T4 | Personal story / self-modelling | 0.167 | 0.571 | 0.258 | 0.187 | 28 |
| T5 | Urgency / scarcity | 0.872 | 1.000 | 0.931 | 0.879 | 95 |
| T6 | Reward / reciprocity | 0.269 | 0.292 | 0.280 | 0.343 | 48 |
| T7 | Flattery / liking | 0.229 | 0.615 | 0.333 | 0.301 | 13 |
| T9 | Threat / intimidation | 0.621 | 0.871 | 0.725 | 0.771 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.326** (95% CI 0.292 to 0.363), micro-F1 0.265, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.242 | 0.890 | 0.381 | 0.294 | 136 |
| T7 | Flattery / liking | 0.300 | 0.478 | 0.368 | 0.296 | 136 |
| T8 | Guilt / obligation | 0.125 | 0.050 | 0.071 | 0.152 | 20 |
| T9 | Threat / intimidation | 0.222 | 0.607 | 0.325 | 0.233 | 61 |
| T10 | Distortion and blame | 0.355 | 0.765 | 0.485 | 0.435 | 166 |

## Genre (every test turn)

macro-F1 **0.854** (95% CI 0.838 to 0.869), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.996 |
| manipulation | 0.840 |
| scam | 0.965 |
| neutral | 0.616 |
