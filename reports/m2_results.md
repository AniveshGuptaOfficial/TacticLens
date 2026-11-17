# M2 frozen MiniLM + MLP results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.494** (95% CI 0.443 to 0.543), micro-F1 0.608, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.547 | 0.417 | 0.473 | 0.517 | 84 |
| T2 | Emotional appeal (sympathy) | 0.476 | 0.455 | 0.465 | 0.374 | 22 |
| T3 | Credibility / authority | 0.852 | 0.670 | 0.750 | 0.832 | 215 |
| T4 | Personal story / self-modelling | 0.204 | 0.357 | 0.260 | 0.170 | 28 |
| T5 | Urgency / scarcity | 0.875 | 0.811 | 0.842 | 0.896 | 95 |
| T6 | Reward / reciprocity | 0.500 | 0.312 | 0.385 | 0.310 | 48 |
| T7 | Flattery / liking | 0.120 | 0.231 | 0.158 | 0.120 | 13 |
| T9 | Threat / intimidation | 0.733 | 0.532 | 0.617 | 0.726 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.297** (95% CI 0.271 to 0.320), micro-F1 0.346, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.234 | 0.949 | 0.376 | 0.263 | 136 |
| T7 | Flattery / liking | 0.233 | 0.904 | 0.370 | 0.258 | 136 |
| T8 | Guilt / obligation | 0.044 | 0.350 | 0.078 | 0.049 | 20 |
| T9 | Threat / intimidation | 0.126 | 0.656 | 0.211 | 0.137 | 61 |
| T10 | Distortion and blame | 0.302 | 0.873 | 0.449 | 0.345 | 166 |

## Accuracy-style measures

Accuracy counts correct decisions, so it is high whenever most answers are "no". The last column is what a model
that always gives the most common answer scores; read each accuracy against it, and the F1 tables above for the hard task.
Thresholds here are the main ones, tuned on validation for F1.

| Measure | Score (95% CI) | Always-most-common baseline |
|---|---|---|
| Tactic yes/no decisions, single turns (per-label accuracy) | 94.5% (93.8% to 95.1%) | 92.3% |
| All tactics right at once, single turns (exact match) | 66.8% (63.6% to 69.8%) | 61.9% |
| Single turns: uses any tactic (accuracy; F1 70.8%) | 78.5% (76.2% to 81.3%) | 61.9% |
| Tactic yes/no decisions, MentalManip dialogues (per-label accuracy) | 44.4% (42.5% to 46.2%) | 82.7% |
| All tactics right at once, MentalManip dialogues (exact match) | 3.3% (2.0% to 4.7%) | 45.8% |
| MentalManip dialogues: manipulative or not (accuracy; F1 70.2%) | 54.5% (50.8% to 58.2%) | 54.2% |
| Genre, 4 classes (accuracy) | 74.8% (72.9% to 76.4%) | - |
| Influence attempt vs neutral, every turn (accuracy; F1 84.0%) | 76.0% | 79.5% |
| SMS: scam or not (accuracy; F1 94.0%) | 97.4% | 77.3% |

### Same scores, thresholds tuned on validation for accuracy

A second, declared operating point: the cut-offs aim at the most correct yes/no decisions rather than
at F1. It trades recall for precision (turn macro-F1 0.315, dialogue macro-F1 0.000 at these cut-offs).

| Measure | Score (95% CI) | Always-most-common baseline |
|---|---|---|
| Tactic yes/no decisions, single turns (per-label accuracy) | 95.0% (94.2% to 95.6%) | 92.3% |
| All tactics right at once, single turns (exact match) | 68.1% (64.3% to 71.4%) | 61.9% |
| Single turns: uses any tactic (accuracy; F1 69.4%) | 80.3% (77.6% to 83.1%) | 61.9% |
| Tactic yes/no decisions, MentalManip dialogues (per-label accuracy) | 82.7% (81.4% to 84.1%) | 82.7% |
| All tactics right at once, MentalManip dialogues (exact match) | 45.8% (42.0% to 49.7%) | 45.8% |
| MentalManip dialogues: manipulative or not (accuracy; F1 0.0%) | 45.8% (42.0% to 49.7%) | 54.2% |

## Genre (every test turn)

macro-F1 **0.774** (95% CI 0.762 to 0.785), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.930 |
| manipulation | 0.701 |
| scam | 0.946 |
| neutral | 0.517 |
