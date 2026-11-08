# M3 role-aware GRU-attention (no-mil) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.467** (95% CI 0.436 to 0.501), micro-F1 0.532, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.376 | 0.452 | 0.411 | 0.435 | 84 |
| T2 | Emotional appeal (sympathy) | 0.149 | 0.636 | 0.241 | 0.251 | 22 |
| T3 | Credibility / authority | 0.722 | 0.786 | 0.753 | 0.858 | 215 |
| T4 | Personal story / self-modelling | 0.104 | 0.821 | 0.185 | 0.128 | 28 |
| T5 | Urgency / scarcity | 0.870 | 0.989 | 0.926 | 0.897 | 95 |
| T6 | Reward / reciprocity | 0.292 | 0.438 | 0.350 | 0.370 | 48 |
| T7 | Flattery / liking | 0.081 | 0.615 | 0.143 | 0.231 | 13 |
| T9 | Threat / intimidation | 0.628 | 0.871 | 0.730 | 0.740 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.278** (95% CI 0.254 to 0.299), micro-F1 0.313, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.253 | 0.743 | 0.377 | 0.275 | 136 |
| T7 | Flattery / liking | 0.233 | 0.919 | 0.371 | 0.250 | 136 |
| T8 | Guilt / obligation | 0.021 | 0.100 | 0.035 | 0.032 | 20 |
| T9 | Threat / intimidation | 0.101 | 0.787 | 0.179 | 0.099 | 61 |
| T10 | Distortion and blame | 0.284 | 0.861 | 0.427 | 0.282 | 166 |

## Genre (every test turn)

macro-F1 **0.860** (95% CI 0.844 to 0.875), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.994 |
| manipulation | 0.833 |
| scam | 0.971 |
| neutral | 0.640 |
