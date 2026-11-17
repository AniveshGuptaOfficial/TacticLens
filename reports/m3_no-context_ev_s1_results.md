# M3 role-aware GRU-attention (no-context) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.577** (95% CI 0.525 to 0.627), micro-F1 0.709, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.479 | 0.833 | 0.609 | 0.652 | 84 |
| T2 | Emotional appeal (sympathy) | 0.458 | 0.500 | 0.478 | 0.543 | 22 |
| T3 | Credibility / authority | 0.829 | 0.809 | 0.819 | 0.894 | 215 |
| T4 | Personal story / self-modelling | 0.286 | 0.214 | 0.245 | 0.261 | 28 |
| T5 | Urgency / scarcity | 0.874 | 0.947 | 0.909 | 0.916 | 95 |
| T6 | Reward / reciprocity | 0.533 | 0.500 | 0.516 | 0.566 | 48 |
| T7 | Flattery / liking | 0.231 | 0.462 | 0.308 | 0.388 | 13 |
| T9 | Threat / intimidation | 0.696 | 0.774 | 0.733 | 0.790 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.357** (95% CI 0.313 to 0.397), micro-F1 0.388, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.247 | 0.860 | 0.384 | 0.282 | 136 |
| T7 | Flattery / liking | 0.254 | 0.846 | 0.390 | 0.307 | 136 |
| T8 | Guilt / obligation | 0.227 | 0.250 | 0.238 | 0.209 | 20 |
| T9 | Threat / intimidation | 0.217 | 0.492 | 0.302 | 0.284 | 61 |
| T10 | Distortion and blame | 0.369 | 0.645 | 0.469 | 0.382 | 166 |

## Accuracy-style measures

Accuracy counts correct decisions, so it is high whenever most answers are "no". The last column is what a model
that always gives the most common answer scores; read each accuracy against it, and the F1 tables above for the hard task.
Thresholds here are the main ones, tuned on validation for F1.

| Measure | Score (95% CI) | Always-most-common baseline |
|---|---|---|
| Tactic yes/no decisions, single turns (per-label accuracy) | 95.2% (94.6% to 95.8%) | 92.3% |
| All tactics right at once, single turns (exact match) | 71.3% (68.1% to 74.3%) | 61.9% |
| Single turns: uses any tactic (accuracy; F1 82.5%) | 85.5% (82.9% to 88.1%) | 61.9% |
| Tactic yes/no decisions, MentalManip dialogues (per-label accuracy) | 61.8% (59.7% to 63.8%) | 82.7% |
| All tactics right at once, MentalManip dialogues (exact match) | 17.3% (14.5% to 20.3%) | 45.8% |
| MentalManip dialogues: manipulative or not (accuracy; F1 70.3%) | 57.8% (54.0% to 61.7%) | 54.2% |
| Genre, 4 classes (accuracy) | 75.5% (73.4% to 77.4%) | - |
| Influence attempt vs neutral, every turn (accuracy; F1 83.9%) | 76.1% | 79.5% |
| SMS: scam or not (accuracy; F1 92.7%) | 96.5% | 77.3% |

### Same scores, thresholds tuned on validation for accuracy

A second, declared operating point: the cut-offs aim at the most correct yes/no decisions rather than
at F1. It trades recall for precision (turn macro-F1 0.439, dialogue macro-F1 0.014 at these cut-offs).

| Measure | Score (95% CI) | Always-most-common baseline |
|---|---|---|
| Tactic yes/no decisions, single turns (per-label accuracy) | 95.6% (95.0% to 96.2%) | 92.3% |
| All tactics right at once, single turns (exact match) | 73.8% (70.9% to 76.6%) | 61.9% |
| Single turns: uses any tactic (accuracy; F1 79.4%) | 84.8% (82.7% to 87.4%) | 61.9% |
| Tactic yes/no decisions, MentalManip dialogues (per-label accuracy) | 82.6% (81.2% to 84.0%) | 82.7% |
| All tactics right at once, MentalManip dialogues (exact match) | 44.8% (40.8% to 48.7%) | 45.8% |
| MentalManip dialogues: manipulative or not (accuracy; F1 3.6%) | 45.8% (42.0% to 49.7%) | 54.2% |

## Genre (every test turn)

macro-F1 **0.771** (95% CI 0.758 to 0.784), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.963 |
| manipulation | 0.672 |
| scam | 0.909 |
| neutral | 0.539 |
