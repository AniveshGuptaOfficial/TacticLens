# M0 TF-IDF + logistic regression results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.585** (95% CI 0.533 to 0.629), micro-F1 0.693, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.527 | 0.571 | 0.549 | 0.623 | 84 |
| T2 | Emotional appeal (sympathy) | 0.500 | 0.545 | 0.522 | 0.579 | 22 |
| T3 | Credibility / authority | 0.848 | 0.753 | 0.798 | 0.900 | 215 |
| T4 | Personal story / self-modelling | 0.409 | 0.321 | 0.360 | 0.263 | 28 |
| T5 | Urgency / scarcity | 0.900 | 0.853 | 0.876 | 0.932 | 95 |
| T6 | Reward / reciprocity | 0.469 | 0.479 | 0.474 | 0.507 | 48 |
| T7 | Flattery / liking | 0.269 | 0.538 | 0.359 | 0.362 | 13 |
| T9 | Threat / intimidation | 0.617 | 0.935 | 0.744 | 0.775 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.184** (95% CI 0.161 to 0.204), micro-F1 0.280, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.263 | 0.846 | 0.401 | 0.300 | 136 |
| T7 | Flattery / liking | 0.255 | 0.544 | 0.347 | 0.255 | 136 |
| T8 | Guilt / obligation | 0.000 | 0.000 | 0.000 | 0.033 | 20 |
| T9 | Threat / intimidation | 0.112 | 0.361 | 0.171 | 0.120 | 61 |
| T10 | Distortion and blame | 0.000 | 0.000 | 0.000 | 0.277 | 166 |

## Genre (every test turn)

macro-F1 **0.800** (95% CI 0.791 to 0.809), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.939 |
| manipulation | 0.741 |
| scam | 0.978 |
| neutral | 0.541 |
