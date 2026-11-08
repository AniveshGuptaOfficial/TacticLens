# Human vs LLM-written SMS (spam)

Messages: human 433, LLM 149. Tactic model: m3_no-context_ev (turn thresholds).
Share of messages that use each tactic. * = significant after Holm correction across tactics.
Tactics per message (mean): human 1.86, LLM 1.61. Words per message (median): human 24, LLM 21.

## Model-detected tactics (m3_no-context_ev)

| Tactic | Name | Human | LLM | LLM - human (95% CI) | p (Holm) |
|---|---|---|---|---|---|
| T1 | Rational appeal | 0.0% | 0.7% | +0.7% (+0.0% to +2.0%) | 1 |
| T2 | Emotional appeal (sympathy) | 0.2% | 0.0% | -0.2% (-0.7% to +0.0%) | 1 |
| T3 | Credibility / authority | 73.9% | 54.4% | -19.5% (-28.6% to -10.7%) | 0.000132 * |
| T5 | Urgency / scarcity | 63.5% | 57.0% | -6.5% (-16.1% to +2.7%) | 1 |
| T6 | Reward / reciprocity | 23.8% | 41.6% | +17.8% (+9.0% to +26.6%) | 0.000445 * |
| T7 | Flattery / liking | 3.0% | 4.7% | +1.7% (-1.9% to +5.5%) | 1 |
| T9 | Threat / intimidation | 21.2% | 2.7% | -18.6% (-23.1% to -13.7%) | 5.86e-08 * |

## Model-free check: at least one lexicon cue

| Tactic | Name | Human | LLM | LLM - human (95% CI) | p (Holm) |
|---|---|---|---|---|---|
| T1 | Rational appeal | 10.6% | 43.6% | +33.0% (+24.5% to +41.7%) | 6.99e-16 * |
| T2 | Emotional appeal (sympathy) | 2.8% | 6.7% | +3.9% (-0.1% to +8.2%) | 0.217 |
| T3 | Credibility / authority | 4.6% | 0.0% | -4.6% (-6.7% to -2.8%) | 0.0269 * |
| T4 | Personal story / self-modelling | 0.7% | 0.0% | -0.7% (-1.6% to +0.0%) | 1 |
| T5 | Urgency / scarcity | 31.2% | 93.3% | +62.1% (+55.9% to +68.1%) | 1.19e-42 * |
| T6 | Reward / reciprocity | 37.4% | 49.7% | +12.3% (+2.7% to +21.4%) | 0.0642 |
| T7 | Flattery / liking | 5.1% | 10.7% | +5.7% (+0.7% to +11.3%) | 0.125 |
| T9 | Threat / intimidation | 0.5% | 0.0% | -0.5% (-1.2% to +0.0%) | 1 |
| T10 | Distortion and blame | 0.9% | 0.0% | -0.9% (-1.8% to -0.2%) | 1 |

## Per generator (model-detected share)

| Source | T1 | T2 | T3 | T5 | T6 | T7 | T9 |
|---|---|---|---|---|---|---|---|
| human (Mishra-Soni) | 0% | 0% | 74% | 64% | 24% | 3% | 21% |
| qwen2.5:3b | 1% | 0% | 54% | 57% | 42% | 5% | 3% |

Caveat: SMS have no tactic labels, so the tactic heads are applied out of domain here.
