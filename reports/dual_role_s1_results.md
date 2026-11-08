# Dual-role baseline (after HDRIN) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.536** (95% CI 0.503 to 0.569), micro-F1 0.640, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.432 | 0.714 | 0.538 | 0.422 | 84 |
| T2 | Emotional appeal (sympathy) | 0.436 | 0.773 | 0.557 | 0.545 | 22 |
| T3 | Credibility / authority | 0.819 | 0.865 | 0.842 | 0.918 | 215 |
| T4 | Personal story / self-modelling | 0.125 | 0.429 | 0.194 | 0.142 | 28 |
| T5 | Urgency / scarcity | 0.864 | 1.000 | 0.927 | 0.882 | 95 |
| T6 | Reward / reciprocity | 0.239 | 0.458 | 0.314 | 0.362 | 48 |
| T7 | Flattery / liking | 0.119 | 0.538 | 0.194 | 0.282 | 13 |
| T9 | Threat / intimidation | 0.611 | 0.887 | 0.724 | 0.766 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.331** (95% CI 0.298 to 0.360), micro-F1 0.247, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.315 | 0.588 | 0.410 | 0.293 | 136 |
| T7 | Flattery / liking | 0.308 | 0.559 | 0.397 | 0.306 | 136 |
| T8 | Guilt / obligation | 0.051 | 0.350 | 0.090 | 0.101 | 20 |
| T9 | Threat / intimidation | 0.197 | 0.475 | 0.279 | 0.219 | 61 |
| T10 | Distortion and blame | 0.337 | 0.825 | 0.478 | 0.450 | 166 |

## Genre (every test turn)

macro-F1 **0.842** (95% CI 0.826 to 0.857), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.995 |
| manipulation | 0.803 |
| scam | 0.965 |
| neutral | 0.606 |
