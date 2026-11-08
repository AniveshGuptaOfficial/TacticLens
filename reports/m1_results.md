# M1 lexicon + stylometry + XGBoost results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.408** (95% CI 0.373 to 0.445), micro-F1 0.517, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.416 | 0.500 | 0.454 | 0.494 | 84 |
| T2 | Emotional appeal (sympathy) | 0.125 | 0.182 | 0.148 | 0.189 | 22 |
| T3 | Credibility / authority | 0.837 | 0.647 | 0.730 | 0.847 | 215 |
| T4 | Personal story / self-modelling | 0.094 | 0.607 | 0.163 | 0.217 | 28 |
| T5 | Urgency / scarcity | 0.864 | 0.937 | 0.899 | 0.916 | 95 |
| T6 | Reward / reciprocity | 0.500 | 0.104 | 0.172 | 0.181 | 48 |
| T7 | Flattery / liking | 0.018 | 0.077 | 0.029 | 0.031 | 13 |
| T9 | Threat / intimidation | 0.568 | 0.806 | 0.667 | 0.609 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.275** (95% CI 0.248 to 0.301), micro-F1 0.306, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.254 | 0.603 | 0.357 | 0.262 | 136 |
| T7 | Flattery / liking | 0.228 | 1.000 | 0.372 | 0.266 | 136 |
| T8 | Guilt / obligation | 0.043 | 0.050 | 0.047 | 0.058 | 20 |
| T9 | Threat / intimidation | 0.104 | 0.639 | 0.179 | 0.174 | 61 |
| T10 | Distortion and blame | 0.300 | 0.693 | 0.419 | 0.398 | 166 |

## Genre (every test turn)

macro-F1 **0.636** (95% CI 0.622 to 0.648), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.756 |
| manipulation | 0.678 |
| scam | 0.913 |
| neutral | 0.196 |
