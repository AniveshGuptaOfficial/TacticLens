# M2 frozen MiniLM + MLP results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.519** (95% CI 0.478 to 0.563), micro-F1 0.618, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.493 | 0.429 | 0.459 | 0.510 | 84 |
| T2 | Emotional appeal (sympathy) | 0.364 | 0.545 | 0.436 | 0.365 | 22 |
| T3 | Credibility / authority | 0.855 | 0.740 | 0.793 | 0.863 | 215 |
| T4 | Personal story / self-modelling | 0.125 | 0.536 | 0.203 | 0.191 | 28 |
| T5 | Urgency / scarcity | 0.874 | 0.947 | 0.909 | 0.875 | 95 |
| T6 | Reward / reciprocity | 0.333 | 0.479 | 0.393 | 0.384 | 48 |
| T7 | Flattery / liking | 0.182 | 0.462 | 0.261 | 0.324 | 13 |
| T9 | Threat / intimidation | 0.617 | 0.806 | 0.699 | 0.762 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.156** (95% CI 0.131 to 0.178), micro-F1 0.157, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.249 | 0.566 | 0.346 | 0.258 | 136 |
| T7 | Flattery / liking | 0.290 | 0.346 | 0.315 | 0.278 | 136 |
| T8 | Guilt / obligation | 0.000 | 0.000 | 0.000 | 0.033 | 20 |
| T9 | Threat / intimidation | 0.081 | 0.213 | 0.118 | 0.129 | 61 |
| T10 | Distortion and blame | 0.000 | 0.000 | 0.000 | 0.277 | 166 |

## Genre (every test turn)

macro-F1 **0.802** (95% CI 0.789 to 0.816), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.938 |
| manipulation | 0.809 |
| scam | 0.948 |
| neutral | 0.514 |
