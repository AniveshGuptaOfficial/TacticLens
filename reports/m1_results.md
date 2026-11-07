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

macro-F1 **0.225** (95% CI 0.196 to 0.255), micro-F1 0.294, n = 600

| Tactic | Name | Precision | Recall | F1 | AUC-PR | Support |
|---|---|---|---|---|---|---|
| T6 | Reward / reciprocity | 0.267 | 0.059 | 0.096 | 0.262 | 136 |
| T7 | Flattery / liking | 0.238 | 0.890 | 0.375 | 0.266 | 136 |
| T8 | Guilt / obligation | 0.043 | 0.050 | 0.047 | 0.058 | 20 |
| T9 | Threat / intimidation | 0.176 | 0.197 | 0.186 | 0.174 | 61 |
| T10 | Distortion and blame | 0.300 | 0.693 | 0.419 | 0.398 | 166 |

## Genre (every test turn)

macro-F1 **0.636** (95% CI 0.622 to 0.648), n = 8,331

| Genre | F1 |
|---|---|
| persuasion | 0.756 |
| manipulation | 0.678 |
| scam | 0.913 |
| neutral | 0.196 |

## Top features per tactic

- T1: lex_T2 (0.09), n_chars (0.08), lex_T2_any (0.07), caps_ratio (0.05), lex_T10_any (0.05)
- T2: lex_T2 (0.27), lex_T2_any (0.26), lex_T1_any (0.05), n_words (0.04), caps_ratio (0.03)
- T3: lex_T2 (0.11), n_chars (0.11), lex_T2_any (0.11), flesch (0.09), n_words (0.05)
- T4: lex_T2_any (0.13), lex_T2 (0.08), lex_T4_any (0.08), first_person (0.08), lex_T1_any (0.06)
- T5: n_chars (0.55), n_words (0.16), lex_T2 (0.05), n_phone (0.04), flesch (0.03)
- T6: lex_T2_any (0.13), lex_T2 (0.09), lex_T3_any (0.04), lex_T6_any (0.04), lex_T6 (0.04)
- T7: lex_T2 (0.08), lex_T2_any (0.07), digit_ratio (0.06), n_phone (0.05), lex_T3_any (0.04)
- T8: lex_T2_any (0.10), lex_T2 (0.06), n_phone (0.06), lex_T4_any (0.05), digit_ratio (0.05)
- T9: n_phone (0.19), lex_T2 (0.14), lex_T2_any (0.07), n_url (0.05), lex_T7_any (0.03)
- T10: lex_T2 (0.18), lex_T2_any (0.17), digit_ratio (0.10), n_phone (0.07), lex_T3 (0.03)
