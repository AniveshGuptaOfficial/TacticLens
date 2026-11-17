# M3 role-aware GRU-attention (no-context) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.573** (95% CI 0.530 to 0.613), micro-F1 0.683, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.452 | 0.619 | 0.523 | 0.631 | 84 |
| T2 | Emotional appeal (sympathy) | 0.480 | 0.545 | 0.511 | 0.592 | 22 |
| T3 | Credibility / authority | 0.776 | 0.884 | 0.826 | 0.888 | 215 |
| T4 | Personal story / self-modelling | 0.250 | 0.429 | 0.316 | 0.303 | 28 |
| T5 | Urgency / scarcity | 0.879 | 0.842 | 0.860 | 0.890 | 95 |
| T6 | Reward / reciprocity | 0.553 | 0.542 | 0.547 | 0.578 | 48 |
| T7 | Flattery / liking | 0.178 | 0.615 | 0.276 | 0.297 | 13 |
| T9 | Threat / intimidation | 0.634 | 0.839 | 0.722 | 0.821 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.347** (95% CI 0.302 to 0.386), micro-F1 0.388, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.255 | 0.515 | 0.341 | 0.274 | 136 |
| T7 | Flattery / liking | 0.261 | 0.897 | 0.405 | 0.300 | 136 |
| T8 | Guilt / obligation | 0.185 | 0.250 | 0.213 | 0.163 | 20 |
| T9 | Threat / intimidation | 0.225 | 0.377 | 0.282 | 0.271 | 61 |
| T10 | Distortion and blame | 0.398 | 0.657 | 0.495 | 0.435 | 166 |

## Accuracy-style measures

Accuracy counts correct decisions, so it is high whenever most answers are "no". The last column is what a model
that always gives the most common answer scores; read each accuracy against it, and the F1 tables above for the hard task.
Thresholds here are the main ones, tuned on validation for F1.

| Measure | Score (95% CI) | Always-most-common baseline |
|---|---|---|
| Tactic yes/no decisions, single turns (per-label accuracy) | 94.6% (94.0% to 95.1%) | 92.3% |
| All tactics right at once, single turns (exact match) | 68.3% (65.3% to 70.8%) | 61.9% |
| Single turns: uses any tactic (accuracy; F1 82.5%) | 84.7% (82.4% to 87.3%) | 61.9% |
| Tactic yes/no decisions, MentalManip dialogues (per-label accuracy) | 66.5% (64.7% to 68.4%) | 82.7% |
| All tactics right at once, MentalManip dialogues (exact match) | 17.5% (14.7% to 20.5%) | 45.8% |
| MentalManip dialogues: manipulative or not (accuracy; F1 71.8%) | 60.3% (56.3% to 64.2%) | 54.2% |
| Genre, 4 classes (accuracy) | 74.5% (72.5% to 76.3%) | - |
| Influence attempt vs neutral, every turn (accuracy; F1 82.6%) | 74.8% | 79.5% |
| SMS: scam or not (accuracy; F1 95.6%) | 98.0% | 77.3% |

### Same scores, thresholds tuned on validation for accuracy

A second, declared operating point: the cut-offs aim at the most correct yes/no decisions rather than
at F1. It trades recall for precision (turn macro-F1 0.421, dialogue macro-F1 0.084 at these cut-offs).

| Measure | Score (95% CI) | Always-most-common baseline |
|---|---|---|
| Tactic yes/no decisions, single turns (per-label accuracy) | 95.5% (94.9% to 96.1%) | 92.3% |
| All tactics right at once, single turns (exact match) | 73.9% (70.6% to 76.6%) | 61.9% |
| Single turns: uses any tactic (accuracy; F1 76.2%) | 83.6% (81.1% to 85.9%) | 61.9% |
| Tactic yes/no decisions, MentalManip dialogues (per-label accuracy) | 82.5% (81.1% to 83.9%) | 82.7% |
| All tactics right at once, MentalManip dialogues (exact match) | 45.2% (41.3% to 49.0%) | 45.8% |
| MentalManip dialogues: manipulative or not (accuracy; F1 20.6%) | 48.7% (44.8% to 52.7%) | 54.2% |

## Genre (every test turn)

macro-F1 **0.773** (95% CI 0.760 to 0.785), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.964 |
| manipulation | 0.637 |
| scam | 0.943 |
| neutral | 0.547 |
