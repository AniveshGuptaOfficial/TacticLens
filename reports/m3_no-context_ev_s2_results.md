# M3 role-aware GRU-attention (no-context) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.565** (95% CI 0.522 to 0.606), micro-F1 0.680, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.465 | 0.631 | 0.535 | 0.626 | 84 |
| T2 | Emotional appeal (sympathy) | 0.438 | 0.636 | 0.519 | 0.508 | 22 |
| T3 | Credibility / authority | 0.836 | 0.805 | 0.820 | 0.903 | 215 |
| T4 | Personal story / self-modelling | 0.204 | 0.393 | 0.268 | 0.265 | 28 |
| T5 | Urgency / scarcity | 0.874 | 0.874 | 0.874 | 0.920 | 95 |
| T6 | Reward / reciprocity | 0.511 | 0.500 | 0.505 | 0.596 | 48 |
| T7 | Flattery / liking | 0.179 | 0.385 | 0.244 | 0.370 | 13 |
| T9 | Threat / intimidation | 0.684 | 0.839 | 0.754 | 0.801 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.340** (95% CI 0.295 to 0.381), micro-F1 0.392, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.249 | 0.824 | 0.383 | 0.275 | 136 |
| T7 | Flattery / liking | 0.255 | 0.831 | 0.390 | 0.305 | 136 |
| T8 | Guilt / obligation | 0.200 | 0.150 | 0.171 | 0.230 | 20 |
| T9 | Threat / intimidation | 0.217 | 0.377 | 0.275 | 0.260 | 61 |
| T10 | Distortion and blame | 0.371 | 0.687 | 0.482 | 0.398 | 166 |

## Accuracy-style measures

Accuracy counts correct decisions, so it is high whenever most answers are "no". The last column is what a model
that always gives the most common answer scores; read each accuracy against it, and the F1 tables above for the hard task.
Thresholds here are the main ones, tuned on validation for F1.

| Measure | Score (95% CI) | Always-most-common baseline |
|---|---|---|
| Tactic yes/no decisions, single turns (per-label accuracy) | 94.7% (94.1% to 95.2%) | 92.3% |
| All tactics right at once, single turns (exact match) | 69.0% (66.1% to 71.7%) | 61.9% |
| Single turns: uses any tactic (accuracy; F1 83.0%) | 85.5% (82.8% to 88.1%) | 61.9% |
| Tactic yes/no decisions, MentalManip dialogues (per-label accuracy) | 63.0% (61.0% to 65.1%) | 82.7% |
| All tactics right at once, MentalManip dialogues (exact match) | 17.7% (14.5% to 20.7%) | 45.8% |
| MentalManip dialogues: manipulative or not (accuracy; F1 70.2%) | 57.5% (53.5% to 61.3%) | 54.2% |
| Genre, 4 classes (accuracy) | 77.4% (75.7% to 79.1%) | - |
| Influence attempt vs neutral, every turn (accuracy; F1 85.4%) | 78.0% | 79.5% |
| SMS: scam or not (accuracy; F1 93.9%) | 97.2% | 77.3% |

### Same scores, thresholds tuned on validation for accuracy

A second, declared operating point: the cut-offs aim at the most correct yes/no decisions rather than
at F1. It trades recall for precision (turn macro-F1 0.412, dialogue macro-F1 0.000 at these cut-offs).

| Measure | Score (95% CI) | Always-most-common baseline |
|---|---|---|
| Tactic yes/no decisions, single turns (per-label accuracy) | 95.5% (94.9% to 96.0%) | 92.3% |
| All tactics right at once, single turns (exact match) | 72.0% (68.5% to 75.2%) | 61.9% |
| Single turns: uses any tactic (accuracy; F1 68.6%) | 80.4% (77.6% to 83.4%) | 61.9% |
| Tactic yes/no decisions, MentalManip dialogues (per-label accuracy) | 82.7% (81.2% to 84.2%) | 82.7% |
| All tactics right at once, MentalManip dialogues (exact match) | 45.8% (42.2% to 50.0%) | 45.8% |
| MentalManip dialogues: manipulative or not (accuracy; F1 0.0%) | 45.8% (42.2% to 50.0%) | 54.2% |

## Genre (every test turn)

macro-F1 **0.786** (95% CI 0.774 to 0.798), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.959 |
| manipulation | 0.719 |
| scam | 0.913 |
| neutral | 0.552 |
