# M0 TF-IDF + logistic regression results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.502** (95% CI 0.461 to 0.534), micro-F1 0.641, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.733 | 0.393 | 0.512 | 0.612 | 84 |
| T2 | Emotional appeal (sympathy) | 0.478 | 0.500 | 0.489 | 0.536 | 22 |
| T3 | Credibility / authority | 0.838 | 0.772 | 0.804 | 0.894 | 215 |
| T4 | Personal story / self-modelling | 0.345 | 0.357 | 0.351 | 0.259 | 28 |
| T5 | Urgency / scarcity | 0.909 | 0.842 | 0.874 | 0.928 | 95 |
| T6 | Reward / reciprocity | 0.202 | 0.479 | 0.284 | 0.267 | 48 |
| T7 | Flattery / liking | 0.000 | 0.000 | 0.000 | 0.052 | 13 |
| T9 | Threat / intimidation | 0.564 | 0.919 | 0.699 | 0.794 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.293** (95% CI 0.271 to 0.314), micro-F1 0.375, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.253 | 0.993 | 0.403 | 0.316 | 136 |
| T7 | Flattery / liking | 0.273 | 0.544 | 0.364 | 0.327 | 136 |
| T8 | Guilt / obligation | 0.000 | 0.000 | 0.000 | 0.037 | 20 |
| T9 | Threat / intimidation | 0.138 | 0.787 | 0.235 | 0.205 | 61 |
| T10 | Distortion and blame | 0.327 | 0.807 | 0.465 | 0.363 | 166 |

## Genre (every test turn)

macro-F1 **0.800** (95% CI 0.791 to 0.809), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.939 |
| manipulation | 0.741 |
| scam | 0.978 |
| neutral | 0.541 |
