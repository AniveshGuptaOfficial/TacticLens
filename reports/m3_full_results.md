# M3 role-aware GRU-attention (full) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.547** (95% CI 0.507 to 0.586), micro-F1 0.649, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.403 | 0.643 | 0.495 | 0.517 | 84 |
| T2 | Emotional appeal (sympathy) | 0.395 | 0.773 | 0.523 | 0.563 | 22 |
| T3 | Credibility / authority | 0.814 | 0.893 | 0.851 | 0.932 | 215 |
| T4 | Personal story / self-modelling | 0.172 | 0.607 | 0.268 | 0.194 | 28 |
| T5 | Urgency / scarcity | 0.862 | 0.989 | 0.922 | 0.887 | 95 |
| T6 | Reward / reciprocity | 0.323 | 0.438 | 0.372 | 0.383 | 48 |
| T7 | Flattery / liking | 0.143 | 0.769 | 0.241 | 0.246 | 13 |
| T9 | Threat / intimidation | 0.577 | 0.903 | 0.704 | 0.753 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.351** (95% CI 0.319 to 0.384), micro-F1 0.246, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.274 | 0.757 | 0.402 | 0.303 | 136 |
| T7 | Flattery / liking | 0.276 | 0.794 | 0.409 | 0.316 | 136 |
| T8 | Guilt / obligation | 0.091 | 0.400 | 0.148 | 0.130 | 20 |
| T9 | Threat / intimidation | 0.218 | 0.475 | 0.299 | 0.228 | 61 |
| T10 | Distortion and blame | 0.411 | 0.627 | 0.496 | 0.449 | 166 |

## Genre (every test turn)

macro-F1 **0.845** (95% CI 0.828 to 0.859), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.994 |
| manipulation | 0.818 |
| scam | 0.960 |
| neutral | 0.607 |
