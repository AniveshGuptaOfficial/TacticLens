# Data card

Turns: 54,383 - Dialogues: 12,411

## Dialogues per dataset and split

| dataset | test | train | val | All |
|---|---|---|---|---|
| mentalmanip | 600 | 2,799 | 600 | 3,999 |
| p4g | 152 | 712 | 153 | 1,017 |
| psyscam | 109 | 511 | 110 | 730 |
| sms_human | 852 | 3,973 | 851 | 5,676 |
| sms_llm | 149 | 692 | 148 | 989 |
| All | 1,862 | 8,687 | 1,862 | 12,411 |

## Dialogues per genre and source

| genre | human | llm | All |
|---|---|---|---|
| manipulation | 2,817 | 0 | 2,817 |
| neutral | 5,996 | 347 | 6,343 |
| persuasion | 1,017 | 0 | 1,017 |
| scam | 1,592 | 642 | 2,234 |
| All | 11,422 | 989 | 12,411 |

## Turns per dataset and role

| dataset | actor | target | unknown | All |
|---|---|---|---|---|
| mentalmanip | 0 | 0 | 26,053 | 26,053 |
| p4g | 10,600 | 10,335 | 0 | 20,935 |
| psyscam | 730 | 0 | 0 | 730 |
| sms_human | 5,676 | 0 | 0 | 5,676 |
| sms_llm | 989 | 0 | 0 | 989 |
| All | 17,995 | 10,335 | 26,053 | 54,383 |

## Turn length in words

| dataset | mean | 50% | max |
|---|---|---|---|
| mentalmanip | 13.5 | 9.0 | 347.0 |
| p4g | 16.8 | 13.0 | 100.0 |
| psyscam | 132.8 | 102.0 | 1337.0 |
| sms_human | 15.4 | 12.0 | 171.0 |
| sms_llm | 17.9 | 17.0 | 39.0 |

## Tactic counts

| Tactic | Name | Group | Turn-level labels | Dialogue-level labels |
|---|---|---|---|---|
| T1 | Rational appeal | legitimate | 655 | 0 |
| T2 | Emotional appeal (sympathy) | legitimate | 234 | 0 |
| T3 | Credibility / authority | legitimate | 1,482 | 0 |
| T4 | Personal story / self-modelling | legitimate | 238 | 0 |
| T5 | Urgency / scarcity | pressure | 604 | 0 |
| T6 | Reward / reciprocity | pressure | 310 | 768 |
| T7 | Flattery / liking | pressure | 195 | 768 |
| T8 | Guilt / obligation | manipulative | 0 | 109 |
| T9 | Threat / intimidation | manipulative | 444 | 494 |
| T10 | Distortion and blame | manipulative | 0 | 1,160 |
| X_SOCIAL_PROOF | Social proof (flagged) | extra | 14 | 0 |

Turn-level labelled turns: 6,872 (with no tactic: 4,262).
