# Human vs LLM-written SMS (smishing)

Messages: human 429, LLM 493. Tactic model: m3_no-context_ev (turn thresholds).
Share of messages that use each tactic. * = significant after Holm correction across tactics.
Tactics per message (mean): human 2.17, LLM 2.13. Words per message (median): human 23, LLM 19.

## Model-detected tactics (m3_no-context_ev)

| Tactic | Name | Human | LLM | LLM - human (95% CI) | p (Holm) |
|---|---|---|---|---|---|
| T3 | Credibility / authority | 87.6% | 70.8% | -16.9% (-22.0% to -11.8%) | 3.31e-09 * |
| T5 | Urgency / scarcity | 78.1% | 69.4% | -8.7% (-14.5% to -3.2%) | 0.0226 * |
| T6 | Reward / reciprocity | 19.8% | 14.0% | -5.8% (-10.7% to -1.1%) | 0.149 |
| T7 | Flattery / liking | 0.7% | 0.4% | -0.3% (-1.4% to +0.6%) | 1 |
| T9 | Threat / intimidation | 30.5% | 58.4% | +27.9% (+21.9% to +34.1%) | 1.47e-16 * |

## Model-free check: at least one lexicon cue

| Tactic | Name | Human | LLM | LLM - human (95% CI) | p (Holm) |
|---|---|---|---|---|---|
| T1 | Rational appeal | 3.5% | 12.0% | +8.5% (+5.2% to +12.0%) | 6.92e-06 * |
| T2 | Emotional appeal (sympathy) | 0.7% | 0.2% | -0.5% (-1.4% to +0.4%) | 1 |
| T3 | Credibility / authority | 5.4% | 21.5% | +16.1% (+11.9% to +20.4%) | 3.33e-12 * |
| T4 | Personal story / self-modelling | 0.2% | 0.0% | -0.2% (-0.7% to +0.0%) | 1 |
| T5 | Urgency / scarcity | 43.4% | 83.2% | +39.8% (+34.1% to +45.5%) | 2.7e-36 * |
| T6 | Reward / reciprocity | 58.5% | 32.0% | -26.5% (-32.7% to -20.2%) | 5.16e-15 * |
| T7 | Flattery / liking | 11.9% | 1.0% | -10.9% (-14.2% to -7.7%) | 4.15e-12 * |
| T9 | Threat / intimidation | 3.3% | 20.9% | +17.6% (+13.8% to +21.7%) | 2.34e-16 * |

## Per generator (model-detected share)

| Source | T3 | T5 | T6 | T7 | T9 |
|---|---|---|---|---|---|
| human (Mishra-Soni) | 88% | 78% | 20% | 1% | 31% |
| qwen2.5:3b | 71% | 69% | 14% | 0% | 58% |

Caveat: SMS have no tactic labels, so the tactic heads are applied out of domain here.
