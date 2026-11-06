# M0 baseline results

Tactics (turn level): macro-F1 **0.585** (95% CI 0.533 to 0.629), micro-F1 0.693. Train 4,891, val 1,058, test 923 turns.

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Test support |
|---|---|---|---|---|---|---|
| T1 | Rational appeal | 0.527 | 0.571 | 0.549 | 0.623 | 84 |
| T2 | Emotional appeal (sympathy) | 0.500 | 0.545 | 0.522 | 0.579 | 22 |
| T3 | Credibility / authority | 0.848 | 0.753 | 0.798 | 0.900 | 215 |
| T4 | Personal story / self-modelling | 0.409 | 0.321 | 0.360 | 0.263 | 28 |
| T5 | Urgency / scarcity | 0.900 | 0.853 | 0.876 | 0.932 | 95 |
| T6 | Reward / reciprocity | 0.469 | 0.479 | 0.474 | 0.507 | 48 |
| T7 | Flattery / liking | 0.269 | 0.538 | 0.359 | 0.362 | 13 |
| T8 | Guilt / obligation | 0.000 | 0.000 | 0.000 |  | 0 |
| T9 | Threat / intimidation | 0.617 | 0.935 | 0.744 | 0.775 | 62 |
| T10 | Distortion and blame | 0.000 | 0.000 | 0.000 |  | 0 |

Genre: macro-F1 **0.800** (95% CI 0.790 to 0.810) on 8,331 test turns.

| Genre | F1 |
|---|---|
| persuasion | 0.939 |
| manipulation | 0.739 |
| scam | 0.979 |
| neutral | 0.542 |
