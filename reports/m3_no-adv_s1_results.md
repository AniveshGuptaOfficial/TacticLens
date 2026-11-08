# M3 role-aware GRU-attention (no-adv) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.530** (95% CI 0.488 to 0.572), micro-F1 0.639, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.420 | 0.595 | 0.493 | 0.495 | 84 |
| T2 | Emotional appeal (sympathy) | 0.462 | 0.545 | 0.500 | 0.516 | 22 |
| T3 | Credibility / authority | 0.859 | 0.823 | 0.841 | 0.914 | 215 |
| T4 | Personal story / self-modelling | 0.167 | 0.321 | 0.220 | 0.164 | 28 |
| T5 | Urgency / scarcity | 0.869 | 0.979 | 0.921 | 0.847 | 95 |
| T6 | Reward / reciprocity | 0.256 | 0.458 | 0.328 | 0.344 | 48 |
| T7 | Flattery / liking | 0.124 | 0.846 | 0.216 | 0.268 | 13 |
| T9 | Threat / intimidation | 0.578 | 0.952 | 0.720 | 0.776 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.348** (95% CI 0.315 to 0.380), micro-F1 0.295, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.270 | 0.757 | 0.398 | 0.291 | 136 |
| T7 | Flattery / liking | 0.270 | 0.735 | 0.395 | 0.300 | 136 |
| T8 | Guilt / obligation | 0.107 | 0.400 | 0.168 | 0.134 | 20 |
| T9 | Threat / intimidation | 0.190 | 0.574 | 0.286 | 0.198 | 61 |
| T10 | Distortion and blame | 0.348 | 0.843 | 0.493 | 0.444 | 166 |

## Genre (every test turn)

macro-F1 **0.844** (95% CI 0.829 to 0.859), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.997 |
| manipulation | 0.809 |
| scam | 0.968 |
| neutral | 0.602 |
