# False alarms on everyday chat (DailyDialog test, 300 dialogues)

Model: m3_no-context_ev (onnx). Every tactic flagged here is a false alarm.

## balanced

| Measure | Value |
|---|---|
| Turns with any tactic flagged | 4.5% (105 of 2322) |
| Conversations with no tactic in the verdict | 47.7% (143 of 300) |
| ... of which show possible signals only | 0.0% |
| Conversations labelled neutral genre | 97.7% |

| Verdict | Conversations |
|---|---|
| No influence tactic found | 143 |
| Pressure tactics | 114 |
| Manipulation signals | 25 |
| Persuasion with legitimate appeals | 18 |

| Tactic flagged (false alarm) | Turns |
|---|---|
| Credibility / authority | 32 |
| Flattery / liking | 24 |
| Distortion and blame | 19 |
| Reward / reciprocity | 17 |
| Rational appeal | 9 |
| Emotional appeal (sympathy) | 6 |
| Threat / intimidation | 4 |
| Personal story / self-modelling | 1 |
| Urgency / scarcity | 1 |

| Genre | Conversations |
|---|---|
| neutral | 293 |
| manipulation | 7 |

## careful

| Measure | Value |
|---|---|
| Turns with any tactic flagged | 0.9% (22 of 2322) |
| Conversations with no tactic in the verdict | 94.0% (282 of 300) |
| ... of which show possible signals only | 46.3% |
| Conversations labelled neutral genre | 97.7% |

| Verdict | Conversations |
|---|---|
| No influence tactic found | 143 |
| No clear tactic, but possible signals | 139 |
| Persuasion with legitimate appeals | 14 |
| Manipulation signals | 4 |

| Tactic flagged (false alarm) | Turns |
|---|---|
| Credibility / authority | 9 |
| Emotional appeal (sympathy) | 6 |
| Threat / intimidation | 4 |
| Urgency / scarcity | 1 |
| Rational appeal | 1 |
| Distortion and blame | 1 |

| Genre | Conversations |
|---|---|
| neutral | 293 |
| manipulation | 7 |
