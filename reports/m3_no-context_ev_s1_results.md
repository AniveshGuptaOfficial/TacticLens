# M3 role-aware GRU-attention (no-context) results

## Tactics, turn level (P4G + PsyScam test turns)

macro-F1 **0.579** (95% CI 0.521 to 0.618), micro-F1 0.685, n = 923

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.500 | 0.631 | 0.558 | 0.638 | 84 |
| T2 | Emotional appeal (sympathy) | 0.464 | 0.591 | 0.520 | 0.545 | 22 |
| T3 | Credibility / authority | 0.796 | 0.837 | 0.816 | 0.907 | 215 |
| T4 | Personal story / self-modelling | 0.255 | 0.429 | 0.320 | 0.281 | 28 |
| T5 | Urgency / scarcity | 0.861 | 0.916 | 0.888 | 0.922 | 95 |
| T6 | Reward / reciprocity | 0.433 | 0.542 | 0.481 | 0.555 | 48 |
| T7 | Flattery / liking | 0.200 | 0.769 | 0.317 | 0.391 | 13 |
| T9 | Threat / intimidation | 0.606 | 0.919 | 0.731 | 0.822 | 62 |

## Tactics, dialogue level (MentalManip test dialogues, max over turns)

macro-F1 **0.362** (95% CI 0.317 to 0.407), micro-F1 0.335, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.279 | 0.801 | 0.414 | 0.316 | 136 |
| T7 | Flattery / liking | 0.278 | 0.809 | 0.414 | 0.318 | 136 |
| T8 | Guilt / obligation | 0.250 | 0.150 | 0.188 | 0.236 | 20 |
| T9 | Threat / intimidation | 0.210 | 0.557 | 0.305 | 0.270 | 61 |
| T10 | Distortion and blame | 0.390 | 0.663 | 0.491 | 0.442 | 166 |

## Genre (every test turn)

macro-F1 **0.783** (95% CI 0.769 to 0.795), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.946 |
| manipulation | 0.725 |
| scam | 0.903 |
| neutral | 0.558 |
