# M3 role-aware GRU-attention (no-adv) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.548** (95% CI 0.503 to 0.592), micro-F1 0.666, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.461 | 0.631 | 0.533 | 0.582 | 84 |
| T2 | Emotional appeal (sympathy) | 0.478 | 0.500 | 0.489 | 0.584 | 22 |
| T3 | Credibility / authority | 0.858 | 0.842 | 0.850 | 0.929 | 215 |
| T4 | Personal story / self-modelling | 0.164 | 0.393 | 0.232 | 0.174 | 28 |
| T5 | Urgency / scarcity | 0.869 | 0.979 | 0.921 | 0.849 | 95 |
| T6 | Reward / reciprocity | 0.294 | 0.417 | 0.345 | 0.376 | 48 |
| T7 | Flattery / liking | 0.169 | 0.769 | 0.278 | 0.213 | 13 |
| T9 | Threat / intimidation | 0.620 | 0.919 | 0.740 | 0.778 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.336** (95% CI 0.294 to 0.376), micro-F1 0.297, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.276 | 0.706 | 0.397 | 0.290 | 136 |
| T7 | Flattery / liking | 0.300 | 0.544 | 0.386 | 0.304 | 136 |
| T8 | Guilt / obligation | 0.154 | 0.100 | 0.121 | 0.101 | 20 |
| T9 | Threat / intimidation | 0.202 | 0.590 | 0.301 | 0.254 | 61 |
| T10 | Distortion and blame | 0.389 | 0.614 | 0.477 | 0.435 | 166 |

## Genre (every test turn)

macro-F1 **0.829** (95% CI 0.814 to 0.843), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.997 |
| manipulation | 0.770 |
| scam | 0.963 |
| neutral | 0.586 |
