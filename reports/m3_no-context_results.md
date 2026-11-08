# M3 role-aware GRU-attention (no-context) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.600** (95% CI 0.558 to 0.643), micro-F1 0.705, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.473 | 0.738 | 0.577 | 0.600 | 84 |
| T2 | Emotional appeal (sympathy) | 0.457 | 0.727 | 0.561 | 0.701 | 22 |
| T3 | Credibility / authority | 0.891 | 0.795 | 0.840 | 0.931 | 215 |
| T4 | Personal story / self-modelling | 0.400 | 0.429 | 0.414 | 0.425 | 28 |
| T5 | Urgency / scarcity | 0.861 | 0.979 | 0.916 | 0.870 | 95 |
| T6 | Reward / reciprocity | 0.400 | 0.542 | 0.460 | 0.477 | 48 |
| T7 | Flattery / liking | 0.200 | 0.615 | 0.302 | 0.453 | 13 |
| T9 | Threat / intimidation | 0.625 | 0.887 | 0.733 | 0.797 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.348** (95% CI 0.300 to 0.396), micro-F1 0.293, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.270 | 0.676 | 0.386 | 0.276 | 136 |
| T7 | Flattery / liking | 0.276 | 0.684 | 0.393 | 0.289 | 136 |
| T8 | Guilt / obligation | 0.333 | 0.150 | 0.207 | 0.200 | 20 |
| T9 | Threat / intimidation | 0.188 | 0.443 | 0.263 | 0.209 | 61 |
| T10 | Distortion and blame | 0.382 | 0.681 | 0.489 | 0.400 | 166 |

## Genre (every test turn)

macro-F1 **0.823** (95% CI 0.812 to 0.834), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.970 |
| manipulation | 0.786 |
| scam | 0.959 |
| neutral | 0.575 |
