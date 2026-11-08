# M3 role-aware GRU-attention (no-context) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.585** (95% CI 0.543 to 0.631), micro-F1 0.693, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.495 | 0.619 | 0.550 | 0.610 | 84 |
| T2 | Emotional appeal (sympathy) | 0.458 | 0.500 | 0.478 | 0.528 | 22 |
| T3 | Credibility / authority | 0.838 | 0.795 | 0.816 | 0.907 | 215 |
| T4 | Personal story / self-modelling | 0.271 | 0.464 | 0.342 | 0.281 | 28 |
| T5 | Urgency / scarcity | 0.867 | 0.958 | 0.910 | 0.926 | 95 |
| T6 | Reward / reciprocity | 0.519 | 0.583 | 0.549 | 0.589 | 48 |
| T7 | Flattery / liking | 0.184 | 0.692 | 0.290 | 0.437 | 13 |
| T9 | Threat / intimidation | 0.626 | 0.919 | 0.745 | 0.811 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.368** (95% CI 0.316 to 0.416), micro-F1 0.345, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.255 | 0.949 | 0.402 | 0.304 | 136 |
| T7 | Flattery / liking | 0.266 | 0.868 | 0.408 | 0.332 | 136 |
| T8 | Guilt / obligation | 0.500 | 0.150 | 0.231 | 0.246 | 20 |
| T9 | Threat / intimidation | 0.185 | 0.541 | 0.276 | 0.240 | 61 |
| T10 | Distortion and blame | 0.438 | 0.657 | 0.525 | 0.450 | 166 |

## Accuracy-style measures

Accuracy counts correct decisions, so it is high whenever most answers are "no". The last column is what a model
that always gives the most common answer scores; read each accuracy against it, and the F1 tables above for the hard task.
Thresholds here are the main ones, tuned on validation for F1.

| Measure | Score (95% CI) | Always-most-common baseline |
|---|---|---|
| Tactic yes/no decisions, single turns (per-label accuracy) | 94.8% (94.2% to 95.4%) | 92.3% |
| All tactics right at once, single turns (exact match) | 69.9% (66.9% to 72.5%) | 61.9% |
| Single turns: uses any tactic (accuracy; F1 82.7%) | 85.3% (83.1% to 87.6%) | 61.9% |
| Tactic yes/no decisions, MentalManip dialogues (per-label accuracy) | 62.8% (61.0% to 64.6%) | 82.7% |
| All tactics right at once, MentalManip dialogues (exact match) | 16.7% (13.8% to 19.7%) | 45.8% |
| MentalManip dialogues: manipulative or not (accuracy; F1 71.2%) | 57.5% (53.5% to 61.3%) | 54.2% |
| Genre, 4 classes (accuracy) | 80.3% (78.6% to 81.9%) | - |
| Influence attempt vs neutral, every turn (accuracy; F1 88.2%) | 81.4% | 79.5% |
| SMS: scam or not (accuracy; F1 93.8%) | 97.1% | 77.3% |

### Same scores, thresholds tuned on validation for accuracy

A second, declared operating point: the cut-offs aim at the most correct yes/no decisions rather than
at F1. It trades recall for precision (turn macro-F1 0.489, dialogue macro-F1 0.070 at these cut-offs).

| Measure | Score (95% CI) | Always-most-common baseline |
|---|---|---|
| Tactic yes/no decisions, single turns (per-label accuracy) | 95.7% (95.1% to 96.2%) | 92.3% |
| All tactics right at once, single turns (exact match) | 73.8% (70.8% to 76.5%) | 61.9% |
| Single turns: uses any tactic (accuracy; F1 79.0%) | 84.9% (82.5% to 87.3%) | 61.9% |
| Tactic yes/no decisions, MentalManip dialogues (per-label accuracy) | 82.8% (81.5% to 84.2%) | 82.7% |
| All tactics right at once, MentalManip dialogues (exact match) | 45.5% (41.8% to 49.5%) | 45.8% |
| MentalManip dialogues: manipulative or not (accuracy; F1 9.2%) | 47.2% (43.3% to 51.2%) | 54.2% |

## Genre (every test turn)

macro-F1 **0.799** (95% CI 0.787 to 0.812), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.959 |
| manipulation | 0.774 |
| scam | 0.903 |
| neutral | 0.560 |
