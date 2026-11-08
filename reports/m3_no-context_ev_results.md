# M3 role-aware GRU-attention (no-context) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.585** (95% CI 0.546 to 0.627), micro-F1 0.693, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.495 | 0.619 | 0.550 | 0.610 | 84 |
| T2 | Emotional appeal (sympathy) | 0.458 | 0.500 | 0.478 | 0.528 | 22 |
| T3 | Credibility / authority | 0.838 | 0.795 | 0.816 | 0.907 | 215 |
| T4 | Personal story / self-modelling | 0.271 | 0.464 | 0.342 | 0.281 | 28 |
| T5 | Urgency / scarcity | 0.867 | 0.958 | 0.910 | 0.926 | 95 |
| T6 | Reward / reciprocity | 0.519 | 0.583 | 0.549 | 0.589 | 48 |
| T7 | Flattery / liking | 0.184 | 0.692 | 0.290 | 0.437 | 13 |
| T9 | Threat / intimidation | 0.626 | 0.919 | 0.745 | 0.811 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.368** (95% CI 0.312 to 0.411), micro-F1 0.345, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.255 | 0.949 | 0.402 | 0.304 | 136 |
| T7 | Flattery / liking | 0.266 | 0.868 | 0.408 | 0.332 | 136 |
| T8 | Guilt / obligation | 0.500 | 0.150 | 0.231 | 0.246 | 20 |
| T9 | Threat / intimidation | 0.185 | 0.541 | 0.276 | 0.240 | 61 |
| T10 | Distortion and blame | 0.438 | 0.657 | 0.525 | 0.450 | 166 |

## Genre (every test turn)

macro-F1 **0.799** (95% CI 0.787 to 0.812), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.959 |
| manipulation | 0.774 |
| scam | 0.903 |
| neutral | 0.560 |
