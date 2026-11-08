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

macro-F1 **0.304** (95% CI 0.281 to 0.325), micro-F1 0.391, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.274 | 0.728 | 0.398 | 0.316 | 136 |
| T7 | Flattery / liking | 0.268 | 0.882 | 0.412 | 0.327 | 136 |
| T8 | Guilt / obligation | 0.000 | 0.000 | 0.000 | 0.037 | 20 |
| T9 | Threat / intimidation | 0.149 | 0.656 | 0.243 | 0.205 | 61 |
| T10 | Distortion and blame | 0.327 | 0.807 | 0.465 | 0.363 | 166 |

## Accuracy-style measures

Accuracy counts correct decisions, so it is high whenever most answers are "no". The last column is what a model
that always gives the most common answer scores; read each accuracy against it, and the F1 tables above for the hard task.

| Measure | Score (95% CI) | Always-most-common baseline |
|---|---|---|
| Tactic yes/no decisions, single turns (per-label accuracy) | 94.4% (93.6% to 95.1%) | 92.3% |
| All tactics right at once, single turns (exact match) | 65.5% (61.0% to 69.9%) | 61.9% |
| Single turns: uses any tactic (accuracy; F1 73.1%) | 79.2% (76.0% to 82.3%) | 61.9% |
| Tactic yes/no decisions, MentalManip dialogues (per-label accuracy) | 59.2% (57.3% to 61.1%) | 82.7% |
| All tactics right at once, MentalManip dialogues (exact match) | 10.8% (8.3% to 13.3%) | 45.8% |
| MentalManip dialogues: manipulative or not (accuracy; F1 70.1%) | 56.2% (52.0% to 60.2%) | 54.2% |
| Genre, 4 classes (accuracy) | 78.3% (76.6% to 79.9%) | - |
| Influence attempt vs neutral, every turn (accuracy; F1 87.8%) | 80.7% | 79.5% |
| SMS: scam or not (accuracy; F1 97.3%) | 98.8% | 77.3% |

## Genre (every test turn)

macro-F1 **0.800** (95% CI 0.791 to 0.809), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.939 |
| manipulation | 0.741 |
| scam | 0.978 |
| neutral | 0.541 |
