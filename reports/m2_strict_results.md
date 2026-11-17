# M2 frozen MiniLM + MLP results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.536** (95% CI 0.484 to 0.587), micro-F1 0.647, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.529 | 0.440 | 0.481 | 0.540 | 84 |
| T2 | Emotional appeal (sympathy) | 0.529 | 0.409 | 0.462 | 0.372 | 22 |
| T3 | Credibility / authority | 0.832 | 0.740 | 0.783 | 0.860 | 215 |
| T4 | Personal story / self-modelling | 0.191 | 0.321 | 0.240 | 0.191 | 28 |
| T5 | Urgency / scarcity | 0.897 | 0.821 | 0.857 | 0.900 | 95 |
| T6 | Reward / reciprocity | 0.361 | 0.458 | 0.404 | 0.396 | 48 |
| T7 | Flattery / liking | 0.250 | 0.538 | 0.341 | 0.359 | 13 |
| T9 | Threat / intimidation | 0.667 | 0.774 | 0.716 | 0.774 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.037** (95% CI 0.016 to 0.060), micro-F1 0.038, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.400 | 0.015 | 0.028 | 0.270 | 136 |
| T7 | Flattery / liking | 0.467 | 0.051 | 0.093 | 0.270 | 136 |
| T8 | Guilt / obligation | 0.000 | 0.000 | 0.000 | 0.033 | 20 |
| T9 | Threat / intimidation | 1.000 | 0.033 | 0.063 | 0.158 | 61 |
| T10 | Distortion and blame | 0.000 | 0.000 | 0.000 | 0.277 | 166 |

## Accuracy-style measures

Accuracy counts correct decisions, so it is high whenever most answers are "no". The last column is what a model
that always gives the most common answer scores; read each accuracy against it, and the F1 tables above for the hard task.
Thresholds here are the main ones, tuned on validation for F1.

| Measure | Score (95% CI) | Always-most-common baseline |
|---|---|---|
| Tactic yes/no decisions, single turns (per-label accuracy) | 94.6% (93.8% to 95.2%) | 92.3% |
| All tactics right at once, single turns (exact match) | 66.5% (63.2% to 69.9%) | 61.9% |
| Single turns: uses any tactic (accuracy; F1 71.4%) | 77.9% (75.2% to 80.9%) | 61.9% |
| Tactic yes/no decisions, MentalManip dialogues (per-label accuracy) | 82.7% (81.4% to 84.1%) | 82.7% |
| All tactics right at once, MentalManip dialogues (exact match) | 44.8% (41.0% to 48.7%) | 45.8% |
| MentalManip dialogues: manipulative or not (accuracy; F1 8.7%) | 47.3% (43.3% to 51.3%) | 54.2% |
| Genre, 4 classes (accuracy) | 74.8% (72.9% to 76.4%) | - |
| Influence attempt vs neutral, every turn (accuracy; F1 84.0%) | 76.0% | 79.5% |
| SMS: scam or not (accuracy; F1 94.0%) | 97.4% | 77.3% |

### Same scores, thresholds tuned on validation for accuracy

A second, declared operating point: the cut-offs aim at the most correct yes/no decisions rather than
at F1. It trades recall for precision (turn macro-F1 0.401, dialogue macro-F1 0.013 at these cut-offs).

| Measure | Score (95% CI) | Always-most-common baseline |
|---|---|---|
| Tactic yes/no decisions, single turns (per-label accuracy) | 95.5% (94.9% to 96.1%) | 92.3% |
| All tactics right at once, single turns (exact match) | 70.9% (67.4% to 74.0%) | 61.9% |
| Single turns: uses any tactic (accuracy; F1 67.8%) | 79.6% (76.9% to 82.7%) | 61.9% |
| Tactic yes/no decisions, MentalManip dialogues (per-label accuracy) | 82.8% (81.5% to 84.2%) | 82.7% |
| All tactics right at once, MentalManip dialogues (exact match) | 45.8% (42.0% to 49.7%) | 45.8% |
| MentalManip dialogues: manipulative or not (accuracy; F1 1.2%) | 46.2% (42.2% to 50.0%) | 54.2% |

## Genre (every test turn)

macro-F1 **0.774** (95% CI 0.762 to 0.785), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.930 |
| manipulation | 0.701 |
| scam | 0.946 |
| neutral | 0.517 |
