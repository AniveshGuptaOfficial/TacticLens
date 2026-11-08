# M3 role-aware GRU-attention (no-context) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.593** (95% CI 0.553 to 0.635), micro-F1 0.693, n = 923

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

macro-F1 **0.337** (95% CI 0.296 to 0.379), micro-F1 0.311, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.256 | 0.875 | 0.397 | 0.341 | 136 |
| T7 | Flattery / liking | 0.262 | 0.912 | 0.407 | 0.341 | 136 |
| T8 | Guilt / obligation | 1.000 | 0.050 | 0.095 | 0.286 | 20 |
| T9 | Threat / intimidation | 0.189 | 0.541 | 0.280 | 0.245 | 61 |
| T10 | Distortion and blame | 0.366 | 0.813 | 0.505 | 0.490 | 166 |

## Accuracy-style measures

Accuracy counts correct decisions, so it is high whenever most answers are "no". The last column is what a model
that always gives the most common answer scores; read each accuracy against it, and the F1 tables above for the hard task.
Thresholds here are the main ones, tuned on validation for F1.

| Measure | Score (95% CI) | Always-most-common baseline |
|---|---|---|
| Tactic yes/no decisions, single turns (per-label accuracy) | 94.6% (93.9% to 95.1%) | 92.3% |
| All tactics right at once, single turns (exact match) | 67.8% (64.6% to 70.5%) | 61.9% |
| Single turns: uses any tactic (accuracy; F1 83.0%) | 85.2% (83.1% to 87.3%) | 61.9% |
| Tactic yes/no decisions, MentalManip dialogues (per-label accuracy) | 60.7% (59.0% to 62.6%) | 82.7% |
| All tactics right at once, MentalManip dialogues (exact match) | 14.3% (11.5% to 17.2%) | 45.8% |
| MentalManip dialogues: manipulative or not (accuracy; F1 70.7%) | 56.7% (52.7% to 60.3%) | 54.2% |
| Genre, 4 classes (accuracy) | 84.0% (81.9% to 85.7%) | - |
| Influence attempt vs neutral, every turn (accuracy; F1 91.1%) | 85.2% | 79.5% |
| SMS: scam or not (accuracy; F1 93.6%) | 97.0% | 77.3% |

### Same scores, thresholds tuned on validation for accuracy

A second, declared operating point: the cut-offs aim at the most correct yes/no decisions rather than
at F1. It trades recall for precision (turn macro-F1 0.485, dialogue macro-F1 0.057 at these cut-offs).

| Measure | Score (95% CI) | Always-most-common baseline |
|---|---|---|
| Tactic yes/no decisions, single turns (per-label accuracy) | 95.8% (95.2% to 96.3%) | 92.3% |
| All tactics right at once, single turns (exact match) | 74.1% (70.9% to 76.8%) | 61.9% |
| Single turns: uses any tactic (accuracy; F1 76.7%) | 84.0% (81.5% to 86.5%) | 61.9% |
| Tactic yes/no decisions, MentalManip dialogues (per-label accuracy) | 82.8% (81.4% to 84.2%) | 82.7% |
| All tactics right at once, MentalManip dialogues (exact match) | 46.3% (42.7% to 50.2%) | 45.8% |
| MentalManip dialogues: manipulative or not (accuracy; F1 9.4%) | 48.5% (44.7% to 52.3%) | 54.2% |

## Genre (every test turn)

macro-F1 **0.817** (95% CI 0.802 to 0.833), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.960 |
| manipulation | 0.837 |
| scam | 0.914 |
| neutral | 0.559 |
