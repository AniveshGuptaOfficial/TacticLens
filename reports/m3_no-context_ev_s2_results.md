# M3 role-aware GRU-attention (no-context) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.593** (95% CI 0.554 to 0.636), micro-F1 0.693, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.436 | 0.726 | 0.545 | 0.652 | 84 |
| T2 | Emotional appeal (sympathy) | 0.415 | 0.773 | 0.540 | 0.583 | 22 |
| T3 | Credibility / authority | 0.802 | 0.828 | 0.815 | 0.888 | 215 |
| T4 | Personal story / self-modelling | 0.333 | 0.536 | 0.411 | 0.286 | 28 |
| T5 | Urgency / scarcity | 0.874 | 0.947 | 0.909 | 0.916 | 95 |
| T6 | Reward / reciprocity | 0.446 | 0.521 | 0.481 | 0.568 | 48 |
| T7 | Flattery / liking | 0.219 | 0.538 | 0.311 | 0.384 | 13 |
| T9 | Threat / intimidation | 0.587 | 0.984 | 0.735 | 0.771 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.337** (95% CI 0.296 to 0.382), micro-F1 0.311, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.256 | 0.875 | 0.397 | 0.341 | 136 |
| T7 | Flattery / liking | 0.262 | 0.912 | 0.407 | 0.341 | 136 |
| T8 | Guilt / obligation | 1.000 | 0.050 | 0.095 | 0.286 | 20 |
| T9 | Threat / intimidation | 0.189 | 0.541 | 0.280 | 0.245 | 61 |
| T10 | Distortion and blame | 0.366 | 0.813 | 0.505 | 0.490 | 166 |

## Genre (every test turn)

macro-F1 **0.817** (95% CI 0.802 to 0.830), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.960 |
| manipulation | 0.837 |
| scam | 0.914 |
| neutral | 0.559 |
