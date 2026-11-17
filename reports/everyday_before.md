# False alarms on everyday chat (DailyDialog test, 300 dialogues)

Model: m3_no-context_ev (onnx). Every tactic flagged here is a false alarm.

## balanced

| Measure | Value |
|---|---|
| Turns with any tactic flagged | 32.9% (763 of 2322) |
| Conversations with no tactic in the verdict | 8.3% (25 of 300) |
| ... of which show possible signals only | 4.3% |
| Conversations labelled neutral genre | 69.0% |

| Verdict | Conversations |
|---|---|
| Pressure tactics | 157 |
| Manipulation signals | 68 |
| Persuasion with legitimate appeals | 50 |
| No clear tactic, but possible signals | 13 |
| No influence tactic found | 12 |

| Tactic flagged (false alarm) | Turns |
|---|---|
| Flattery / liking | 222 |
| Credibility / authority | 189 |
| Reward / reciprocity | 126 |
| Personal story / self-modelling | 73 |
| Emotional appeal (sympathy) | 68 |
| Rational appeal | 67 |
| Threat / intimidation | 60 |
| Urgency / scarcity | 46 |
| Distortion and blame | 33 |

| Genre | Conversations |
|---|---|
| neutral | 207 |
| manipulation | 77 |
| persuasion | 11 |
| scam | 5 |

## careful

| Measure | Value |
|---|---|
| Turns with any tactic flagged | 17.8% (413 of 2322) |
| Conversations with no tactic in the verdict | 31.0% (93 of 300) |
| ... of which show possible signals only | 22.7% |
| Conversations labelled neutral genre | 69.0% |

| Verdict | Conversations |
|---|---|
| Persuasion with legitimate appeals | 99 |
| No clear tactic, but possible signals | 68 |
| Pressure tactics | 60 |
| Manipulation signals | 48 |
| No influence tactic found | 25 |

| Tactic flagged (false alarm) | Turns |
|---|---|
| Credibility / authority | 189 |
| Emotional appeal (sympathy) | 68 |
| Threat / intimidation | 60 |
| Reward / reciprocity | 48 |
| Urgency / scarcity | 46 |
| Rational appeal | 16 |
| Distortion and blame | 1 |

| Genre | Conversations |
|---|---|
| neutral | 207 |
| manipulation | 77 |
| persuasion | 11 |
| scam | 5 |
