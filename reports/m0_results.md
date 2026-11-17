# M0 TF-IDF + logistic regression results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.529** (95% CI 0.487 to 0.565), micro-F1 0.697, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.597 | 0.476 | 0.530 | 0.607 | 84 |
| T2 | Emotional appeal (sympathy) | 0.524 | 0.500 | 0.512 | 0.538 | 22 |
| T3 | Credibility / authority | 0.813 | 0.791 | 0.802 | 0.889 | 215 |
| T4 | Personal story / self-modelling | 0.435 | 0.357 | 0.392 | 0.275 | 28 |
| T5 | Urgency / scarcity | 0.872 | 1.000 | 0.931 | 0.926 | 95 |
| T6 | Reward / reciprocity | 0.415 | 0.354 | 0.382 | 0.341 | 48 |
| T7 | Flattery / liking | 0.000 | 0.000 | 0.000 | 0.069 | 13 |
| T9 | Threat / intimidation | 0.672 | 0.694 | 0.683 | 0.773 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.295** (95% CI 0.271 to 0.319), micro-F1 0.378, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.238 | 0.993 | 0.384 | 0.312 | 136 |
| T7 | Flattery / liking | 0.241 | 0.978 | 0.387 | 0.311 | 136 |
| T8 | Guilt / obligation | 0.000 | 0.000 | 0.000 | 0.037 | 20 |
| T9 | Threat / intimidation | 0.179 | 0.557 | 0.271 | 0.186 | 61 |
| T10 | Distortion and blame | 0.332 | 0.633 | 0.436 | 0.365 | 166 |

## Accuracy-style measures

Accuracy counts correct decisions, so it is high whenever most answers are "no". The last column is what a model
that always gives the most common answer scores; read each accuracy against it, and the F1 tables above for the hard task.
Thresholds here are the main ones, tuned on validation for F1.

| Measure | Score (95% CI) | Always-most-common baseline |
|---|---|---|
| Tactic yes/no decisions, single turns (per-label accuracy) | 95.5% (94.8% to 96.0%) | 92.3% |
| All tactics right at once, single turns (exact match) | 71.5% (67.9% to 74.8%) | 61.9% |
| Single turns: uses any tactic (accuracy; F1 77.8%) | 84.0% (81.2% to 86.7%) | 61.9% |
| Tactic yes/no decisions, MentalManip dialogues (per-label accuracy) | 55.4% (53.6% to 57.2%) | 82.7% |
| All tactics right at once, MentalManip dialogues (exact match) | 10.5% (8.0% to 13.0%) | 45.8% |
| MentalManip dialogues: manipulative or not (accuracy; F1 70.4%) | 55.3% (51.5% to 59.0%) | 54.2% |
| Genre, 4 classes (accuracy) | 76.4% (74.7% to 78.0%) | - |
| Influence attempt vs neutral, every turn (accuracy; F1 85.8%) | 78.0% | 79.5% |
| SMS: scam or not (accuracy; F1 96.6%) | 98.5% | 77.3% |

### Same scores, thresholds tuned on validation for accuracy

A second, declared operating point: the cut-offs aim at the most correct yes/no decisions rather than
at F1. It trades recall for precision (turn macro-F1 0.420, dialogue macro-F1 0.000 at these cut-offs).

| Measure | Score (95% CI) | Always-most-common baseline |
|---|---|---|
| Tactic yes/no decisions, single turns (per-label accuracy) | 95.7% (95.1% to 96.3%) | 92.3% |
| All tactics right at once, single turns (exact match) | 73.9% (70.4% to 77.0%) | 61.9% |
| Single turns: uses any tactic (accuracy; F1 74.2%) | 83.6% (80.9% to 86.3%) | 61.9% |
| Tactic yes/no decisions, MentalManip dialogues (per-label accuracy) | 82.7% (81.4% to 84.1%) | 82.7% |
| All tactics right at once, MentalManip dialogues (exact match) | 45.8% (42.0% to 49.7%) | 45.8% |
| MentalManip dialogues: manipulative or not (accuracy; F1 0.0%) | 45.8% (42.0% to 49.7%) | 54.2% |

## Genre (every test turn)

macro-F1 **0.787** (95% CI 0.777 to 0.796), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.932 |
| manipulation | 0.729 |
| scam | 0.975 |
| neutral | 0.511 |
