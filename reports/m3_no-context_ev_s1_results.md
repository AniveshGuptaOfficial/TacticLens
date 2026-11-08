# M3 role-aware GRU-attention (no-context) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.579** (95% CI 0.533 to 0.625), micro-F1 0.685, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.500 | 0.631 | 0.558 | 0.638 | 84 |
| T2 | Emotional appeal (sympathy) | 0.464 | 0.591 | 0.520 | 0.545 | 22 |
| T3 | Credibility / authority | 0.796 | 0.837 | 0.816 | 0.907 | 215 |
| T4 | Personal story / self-modelling | 0.255 | 0.429 | 0.320 | 0.281 | 28 |
| T5 | Urgency / scarcity | 0.861 | 0.916 | 0.888 | 0.922 | 95 |
| T6 | Reward / reciprocity | 0.433 | 0.542 | 0.481 | 0.555 | 48 |
| T7 | Flattery / liking | 0.200 | 0.769 | 0.317 | 0.391 | 13 |
| T9 | Threat / intimidation | 0.606 | 0.919 | 0.731 | 0.822 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.362** (95% CI 0.316 to 0.407), micro-F1 0.335, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.279 | 0.801 | 0.414 | 0.316 | 136 |
| T7 | Flattery / liking | 0.278 | 0.809 | 0.414 | 0.318 | 136 |
| T8 | Guilt / obligation | 0.250 | 0.150 | 0.188 | 0.236 | 20 |
| T9 | Threat / intimidation | 0.210 | 0.557 | 0.305 | 0.270 | 61 |
| T10 | Distortion and blame | 0.390 | 0.663 | 0.491 | 0.442 | 166 |

## Accuracy-style measures

Accuracy counts correct decisions, so it is high whenever most answers are "no". The last column is what a model
that always gives the most common answer scores; read each accuracy against it, and the F1 tables above for the hard task.
Thresholds here are the main ones, tuned on validation for F1.

| Measure | Score (95% CI) | Always-most-common baseline |
|---|---|---|
| Tactic yes/no decisions, single turns (per-label accuracy) | 94.5% (93.9% to 95.1%) | 92.3% |
| All tactics right at once, single turns (exact match) | 69.1% (66.1% to 71.8%) | 61.9% |
| Single turns: uses any tactic (accuracy; F1 83.2%) | 85.5% (83.2% to 87.8%) | 61.9% |
| Tactic yes/no decisions, MentalManip dialogues (per-label accuracy) | 65.7% (63.7% to 67.7%) | 82.7% |
| All tactics right at once, MentalManip dialogues (exact match) | 21.3% (18.0% to 24.7%) | 45.8% |
| MentalManip dialogues: manipulative or not (accuracy; F1 70.9%) | 59.2% (55.3% to 63.0%) | 54.2% |
| Genre, 4 classes (accuracy) | 77.8% (76.0% to 79.5%) | - |
| Influence attempt vs neutral, every turn (accuracy; F1 87.0%) | 79.9% | 79.5% |
| SMS: scam or not (accuracy; F1 94.0%) | 97.2% | 77.3% |

### Same scores, thresholds tuned on validation for accuracy

A second, declared operating point: the cut-offs aim at the most correct yes/no decisions rather than
at F1. It trades recall for precision (turn macro-F1 0.491, dialogue macro-F1 0.045 at these cut-offs).

| Measure | Score (95% CI) | Always-most-common baseline |
|---|---|---|
| Tactic yes/no decisions, single turns (per-label accuracy) | 95.7% (95.0% to 96.2%) | 92.3% |
| All tactics right at once, single turns (exact match) | 74.3% (71.0% to 77.2%) | 61.9% |
| Single turns: uses any tactic (accuracy; F1 78.2%) | 84.8% (82.2% to 87.4%) | 61.9% |
| Tactic yes/no decisions, MentalManip dialogues (per-label accuracy) | 82.9% (81.6% to 84.4%) | 82.7% |
| All tactics right at once, MentalManip dialogues (exact match) | 46.7% (42.8% to 50.5%) | 45.8% |
| MentalManip dialogues: manipulative or not (accuracy; F1 9.3%) | 48.2% (44.3% to 52.0%) | 54.2% |

## Genre (every test turn)

macro-F1 **0.783** (95% CI 0.770 to 0.795), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.946 |
| manipulation | 0.725 |
| scam | 0.903 |
| neutral | 0.558 |
