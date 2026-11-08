# Cross-genre transfer (leave one genre out)

Macro-F1 over the tactics the held-out genre shares with the training genres, 95% CI over dialogues;
AUC-PR = threshold-free macro average precision over the same tactics.
In-domain = the main model (trained on all genres) on the same test dialogues and tactics.
Training excludes every dataset that appears in the held-out test set (also its neutral dialogues).

| Held-out genre | Level | Model | Shared tactics | F1 in-domain | F1 transfer | AUC-PR in-domain | AUC-PR transfer |
|---|---|---|---|---|---|---|---|
| persuasion | turn | m0 | T3, T6, T7 | 0.273 (0.236 to 0.310) | 0.118 (0.089 to 0.147) | 0.338 | 0.096 |
| persuasion | turn | m3_no-context_ev | T3, T6, T7 | 0.493 (0.418 to 0.549) | 0.126 (0.099 to 0.151) | 0.612 | 0.156 |
| manipulation | dialogue | m0 | T6, T7, T9 | 0.441 (0.396 to 0.480) | 0.070 (0.042 to 0.100) | 0.364 | 0.287 |
| manipulation | dialogue | m3_no-context_ev | T6, T7, T9 | 0.444 (0.398 to 0.485) | 0.261 (0.210 to 0.308) | 0.364 | 0.311 |
| scam | turn | m0 | T3, T6, T7, T9 | 0.547 (0.498 to 0.591) | 0.144 (0.082 to 0.204) | 0.608 | 0.501 |
| scam | turn | m3_no-context_ev | T3, T6, T7, T9 | 0.688 (0.521 to 0.791) | 0.055 (0.031 to 0.079) | 0.749 | 0.509 |

## Per tactic (F1 in-domain -> transfer; AUC-PR in-domain -> transfer)

- **persuasion, m0**: T3 Credibility / authority: F1 0.62 -> 0.24, AP 0.72 -> 0.22; T6 Reward / reciprocity: F1 0.20 -> 0.09, AP 0.24 -> 0.06; T7 Flattery / liking: F1 0.00 -> 0.02, AP 0.05 -> 0.01 (not labelled in training: T1, T2, T4)
- **persuasion, m3_no-context_ev**: T3 Credibility / authority: F1 0.66 -> 0.25, AP 0.76 -> 0.36; T6 Reward / reciprocity: F1 0.56 -> 0.10, AP 0.62 -> 0.09; T7 Flattery / liking: F1 0.26 -> 0.03, AP 0.46 -> 0.02 (not labelled in training: T1, T2, T4)
- **manipulation, m0**: T6 Reward / reciprocity: F1 0.50 -> 0.08, AP 0.42 -> 0.38; T7 Flattery / liking: F1 0.52 -> 0.13, AP 0.42 -> 0.32; T9 Threat / intimidation: F1 0.30 -> 0.00, AP 0.25 -> 0.16 (not labelled in training: T10, T8)
- **manipulation, m3_no-context_ev**: T6 Reward / reciprocity: F1 0.51 -> 0.36, AP 0.39 -> 0.37; T7 Flattery / liking: F1 0.51 -> 0.25, AP 0.42 -> 0.34; T9 Threat / intimidation: F1 0.31 -> 0.17, AP 0.28 -> 0.22 (not labelled in training: T10, T8)
- **scam, m0**: T3 Credibility / authority: F1 0.98 -> 0.29, AP 0.99 -> 0.98; T6 Reward / reciprocity: F1 0.46 -> 0.19, AP 0.36 -> 0.30; T7 Flattery / liking: F1 0.00 -> 0.00, AP 0.28 -> 0.03; T9 Threat / intimidation: F1 0.75 -> 0.09, AP 0.81 -> 0.69 (not labelled in training: T5)
- **scam, m3_no-context_ev**: T3 Credibility / authority: F1 0.97 -> 0.22, AP 0.98 -> 0.97; T6 Reward / reciprocity: F1 0.53 -> 0.00, AP 0.63 -> 0.37; T7 Flattery / liking: F1 0.50 -> 0.00, AP 0.57 -> 0.11; T9 Threat / intimidation: F1 0.75 -> 0.00, AP 0.81 -> 0.58 (not labelled in training: T5)
