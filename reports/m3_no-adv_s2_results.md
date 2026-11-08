# M3 role-aware GRU-attention (no-adv) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.536** (95% CI 0.496 to 0.576), micro-F1 0.629, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.491 | 0.655 | 0.561 | 0.508 | 84 |
| T2 | Emotional appeal (sympathy) | 0.407 | 0.500 | 0.449 | 0.534 | 22 |
| T3 | Credibility / authority | 0.875 | 0.847 | 0.861 | 0.928 | 215 |
| T4 | Personal story / self-modelling | 0.132 | 0.821 | 0.228 | 0.168 | 28 |
| T5 | Urgency / scarcity | 0.869 | 0.979 | 0.921 | 0.879 | 95 |
| T6 | Reward / reciprocity | 0.275 | 0.458 | 0.344 | 0.379 | 48 |
| T7 | Flattery / liking | 0.111 | 0.538 | 0.184 | 0.288 | 13 |
| T9 | Threat / intimidation | 0.622 | 0.903 | 0.737 | 0.754 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.311** (95% CI 0.280 to 0.339), micro-F1 0.280, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.253 | 0.743 | 0.377 | 0.326 | 136 |
| T7 | Flattery / liking | 0.256 | 0.743 | 0.381 | 0.327 | 136 |
| T8 | Guilt / obligation | 0.037 | 0.100 | 0.054 | 0.082 | 20 |
| T9 | Threat / intimidation | 0.197 | 0.492 | 0.282 | 0.181 | 61 |
| T10 | Distortion and blame | 0.381 | 0.578 | 0.459 | 0.426 | 166 |

## Genre (every test turn)

macro-F1 **0.842** (95% CI 0.827 to 0.856), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.997 |
| manipulation | 0.782 |
| scam | 0.973 |
| neutral | 0.617 |
