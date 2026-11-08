# M2 frozen MiniLM + MLP results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.472** (95% CI 0.433 to 0.512), micro-F1 0.555, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.446 | 0.440 | 0.443 | 0.521 | 84 |
| T2 | Emotional appeal (sympathy) | 0.312 | 0.455 | 0.370 | 0.376 | 22 |
| T3 | Credibility / authority | 0.831 | 0.707 | 0.764 | 0.848 | 215 |
| T4 | Personal story / self-modelling | 0.171 | 0.500 | 0.255 | 0.263 | 28 |
| T5 | Urgency / scarcity | 0.879 | 0.842 | 0.860 | 0.878 | 95 |
| T6 | Reward / reciprocity | 0.231 | 0.438 | 0.302 | 0.311 | 48 |
| T7 | Flattery / liking | 0.065 | 0.462 | 0.113 | 0.163 | 13 |
| T9 | Threat / intimidation | 0.605 | 0.742 | 0.667 | 0.754 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.288** (95% CI 0.263 to 0.311), micro-F1 0.344, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.232 | 0.919 | 0.371 | 0.263 | 136 |
| T7 | Flattery / liking | 0.230 | 0.934 | 0.369 | 0.272 | 136 |
| T8 | Guilt / obligation | 0.036 | 0.300 | 0.065 | 0.037 | 20 |
| T9 | Threat / intimidation | 0.115 | 0.410 | 0.180 | 0.138 | 61 |
| T10 | Distortion and blame | 0.313 | 0.825 | 0.454 | 0.357 | 166 |

## Accuracy-style measures

Accuracy counts correct decisions, so it is high whenever most answers are "no". The last column is what a model
that always gives the most common answer scores; read each accuracy against it, and the F1 tables above for the hard task.

| Measure | Score (95% CI) | Always-most-common baseline |
|---|---|---|
| Tactic yes/no decisions, single turns (per-label accuracy) | 92.3% (91.6% to 93.0%) | 92.3% |
| All tactics right at once, single turns (exact match) | 55.4% (52.2% to 58.8%) | 61.9% |
| Single turns: uses any tactic (accuracy; F1 66.7%) | 69.9% (66.7% to 73.1%) | 61.9% |
| Tactic yes/no decisions, MentalManip dialogues (per-label accuracy) | 47.0% (45.0% to 48.7%) | 82.7% |
| All tactics right at once, MentalManip dialogues (exact match) | 5.2% (3.5% to 7.0%) | 45.8% |
| MentalManip dialogues: manipulative or not (accuracy; F1 70.3%) | 54.7% (51.0% to 58.7%) | 54.2% |
| Genre, 4 classes (accuracy) | 81.6% (79.5% to 83.4%) | - |
| Influence attempt vs neutral, every turn (accuracy; F1 90.7%) | 84.4% | 79.5% |
| SMS: scam or not (accuracy; F1 94.9%) | 97.7% | 77.3% |

## Genre (every test turn)

macro-F1 **0.802** (95% CI 0.789 to 0.816), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.938 |
| manipulation | 0.809 |
| scam | 0.948 |
| neutral | 0.514 |
