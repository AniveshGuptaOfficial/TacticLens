# M3 role-aware GRU-attention (no-role) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.549** (95% CI 0.509 to 0.593), micro-F1 0.656, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.465 | 0.560 | 0.508 | 0.462 | 84 |
| T2 | Emotional appeal (sympathy) | 0.485 | 0.727 | 0.582 | 0.568 | 22 |
| T3 | Credibility / authority | 0.840 | 0.856 | 0.848 | 0.929 | 215 |
| T4 | Personal story / self-modelling | 0.196 | 0.643 | 0.300 | 0.285 | 28 |
| T5 | Urgency / scarcity | 0.868 | 0.968 | 0.915 | 0.882 | 95 |
| T6 | Reward / reciprocity | 0.241 | 0.417 | 0.305 | 0.362 | 48 |
| T7 | Flattery / liking | 0.162 | 0.462 | 0.240 | 0.235 | 13 |
| T9 | Threat / intimidation | 0.574 | 0.871 | 0.692 | 0.759 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.344** (95% CI 0.309 to 0.376), micro-F1 0.322, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.307 | 0.603 | 0.407 | 0.312 | 136 |
| T7 | Flattery / liking | 0.301 | 0.728 | 0.426 | 0.313 | 136 |
| T8 | Guilt / obligation | 0.104 | 0.250 | 0.147 | 0.117 | 20 |
| T9 | Threat / intimidation | 0.143 | 0.803 | 0.243 | 0.183 | 61 |
| T10 | Distortion and blame | 0.415 | 0.614 | 0.495 | 0.488 | 166 |

## Genre (every test turn)

macro-F1 **0.854** (95% CI 0.839 to 0.868), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.991 |
| manipulation | 0.837 |
| scam | 0.960 |
| neutral | 0.627 |
