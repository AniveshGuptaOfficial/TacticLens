# M2 frozen MiniLM + MLP results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.475** (95% CI 0.437 to 0.515), micro-F1 0.560, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.446 | 0.440 | 0.443 | 0.521 | 84 |
| T2 | Emotional appeal (sympathy) | 0.312 | 0.455 | 0.370 | 0.376 | 22 |
| T3 | Credibility / authority | 0.831 | 0.707 | 0.764 | 0.848 | 215 |
| T4 | Personal story / self-modelling | 0.192 | 0.500 | 0.277 | 0.263 | 28 |
| T5 | Urgency / scarcity | 0.879 | 0.842 | 0.860 | 0.878 | 95 |
| T6 | Reward / reciprocity | 0.231 | 0.438 | 0.302 | 0.311 | 48 |
| T7 | Flattery / liking | 0.065 | 0.462 | 0.113 | 0.163 | 13 |
| T9 | Threat / intimidation | 0.605 | 0.742 | 0.667 | 0.754 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.290** (95% CI 0.265 to 0.313), micro-F1 0.337, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.240 | 0.868 | 0.376 | 0.263 | 136 |
| T7 | Flattery / liking | 0.234 | 0.897 | 0.371 | 0.272 | 136 |
| T8 | Guilt / obligation | 0.029 | 0.200 | 0.051 | 0.037 | 20 |
| T9 | Threat / intimidation | 0.113 | 0.820 | 0.199 | 0.138 | 61 |
| T10 | Distortion and blame | 0.313 | 0.825 | 0.454 | 0.357 | 166 |

## Genre (every test turn)

macro-F1 **0.802** (95% CI 0.789 to 0.816), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.938 |
| manipulation | 0.809 |
| scam | 0.948 |
| neutral | 0.514 |
