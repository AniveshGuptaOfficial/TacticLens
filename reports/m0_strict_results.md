# M0 TF-IDF + logistic regression results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.578** (95% CI 0.526 to 0.623), micro-F1 0.680, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.623 | 0.452 | 0.524 | 0.607 | 84 |
| T2 | Emotional appeal (sympathy) | 0.524 | 0.500 | 0.512 | 0.541 | 22 |
| T3 | Credibility / authority | 0.856 | 0.716 | 0.780 | 0.891 | 215 |
| T4 | Personal story / self-modelling | 0.526 | 0.357 | 0.426 | 0.290 | 28 |
| T5 | Urgency / scarcity | 0.902 | 0.874 | 0.888 | 0.929 | 95 |
| T6 | Reward / reciprocity | 0.473 | 0.542 | 0.505 | 0.498 | 48 |
| T7 | Flattery / liking | 0.170 | 0.615 | 0.267 | 0.352 | 13 |
| T9 | Threat / intimidation | 0.646 | 0.823 | 0.723 | 0.782 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.078** (95% CI 0.054 to 0.103), micro-F1 0.117, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.288 | 0.154 | 0.201 | 0.294 | 136 |
| T7 | Flattery / liking | 0.202 | 0.132 | 0.160 | 0.254 | 136 |
| T8 | Guilt / obligation | 0.000 | 0.000 | 0.000 | 0.033 | 20 |
| T9 | Threat / intimidation | 0.333 | 0.016 | 0.031 | 0.122 | 61 |
| T10 | Distortion and blame | 0.000 | 0.000 | 0.000 | 0.277 | 166 |

## Accuracy-style measures

Accuracy counts correct decisions, so it is high whenever most answers are "no". The last column is what a model
that always gives the most common answer scores; read each accuracy against it, and the F1 tables above for the hard task.
Thresholds here are the main ones, tuned on validation for F1.

| Measure | Score (95% CI) | Always-most-common baseline |
|---|---|---|
| Tactic yes/no decisions, single turns (per-label accuracy) | 95.1% (94.4% to 95.8%) | 92.3% |
| All tactics right at once, single turns (exact match) | 71.2% (67.7% to 74.4%) | 61.9% |
| Single turns: uses any tactic (accuracy; F1 77.4%) | 84.0% (81.7% to 86.3%) | 61.9% |
| Tactic yes/no decisions, MentalManip dialogues (per-label accuracy) | 79.9% (78.4% to 81.4%) | 82.7% |
| All tactics right at once, MentalManip dialogues (exact match) | 38.0% (34.3% to 42.2%) | 45.8% |
| MentalManip dialogues: manipulative or not (accuracy; F1 36.1%) | 51.0% (47.3% to 55.3%) | 54.2% |
| Genre, 4 classes (accuracy) | 76.4% (74.7% to 78.0%) | - |
| Influence attempt vs neutral, every turn (accuracy; F1 85.8%) | 78.0% | 79.5% |
| SMS: scam or not (accuracy; F1 96.6%) | 98.5% | 77.3% |

### Same scores, thresholds tuned on validation for accuracy

A second, declared operating point: the cut-offs aim at the most correct yes/no decisions rather than
at F1. It trades recall for precision (turn macro-F1 0.490, dialogue macro-F1 0.008 at these cut-offs).

| Measure | Score (95% CI) | Always-most-common baseline |
|---|---|---|
| Tactic yes/no decisions, single turns (per-label accuracy) | 95.7% (95.0% to 96.3%) | 92.3% |
| All tactics right at once, single turns (exact match) | 73.3% (69.7% to 76.4%) | 61.9% |
| Single turns: uses any tactic (accuracy; F1 75.3%) | 83.9% (81.1% to 86.7%) | 61.9% |
| Tactic yes/no decisions, MentalManip dialogues (per-label accuracy) | 82.6% (81.2% to 84.0%) | 82.7% |
| All tactics right at once, MentalManip dialogues (exact match) | 45.0% (41.2% to 49.0%) | 45.8% |
| MentalManip dialogues: manipulative or not (accuracy; F1 3.0%) | 45.8% (41.8% to 49.7%) | 54.2% |

## Genre (every test turn)

macro-F1 **0.787** (95% CI 0.777 to 0.796), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.932 |
| manipulation | 0.729 |
| scam | 0.975 |
| neutral | 0.511 |
