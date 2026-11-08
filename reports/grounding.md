# Grounding audit (evidence spans: PsyScam quotes, P4G strategy sentences; test split)

Scores are drops in the model's probability for the gold tactic, mean (95% CI over dialogues).
Comprehensiveness: evidence cut out. Random control: the same number of other words cut out.
Evidence effect = comprehensiveness - random control (> 0 means the evidence matters more than other text).
Sufficiency: evidence alone (lower is better). Flips: share of detected cases that fall below threshold.

## All evidence cases

| Model | Dataset | n | Comprehensiveness | Random control | Evidence effect | Sufficiency | Flip (evidence) | Flip (random) |
|---|---|---|---|---|---|---|---|---|
| m0 | all | 294 | 0.263 (0.198 to 0.327) | 0.078 (0.046 to 0.110) | 0.185 (0.131 to 0.239) | 0.142 (0.096 to 0.196) | 0.38 | 0.15 |
| m0 | p4g | 153 | 0.475 (0.410 to 0.535) | 0.133 (0.077 to 0.195) | 0.342 (0.274 to 0.408) | -0.025 (-0.068 to 0.012) | 0.93 | 0.37 |
| m0 | psyscam | 141 | 0.032 (0.015 to 0.053) | 0.019 (0.009 to 0.030) | 0.014 (-0.003 to 0.035) | 0.324 (0.276 to 0.373) | 0.07 | 0.04 |
| m3_full | all | 294 | 0.085 (0.053 to 0.116) | 0.012 (-0.002 to 0.027) | 0.073 (0.036 to 0.110) | 0.072 (0.036 to 0.110) | 0.15 | 0.06 |
| m3_full | p4g | 153 | 0.157 (0.112 to 0.197) | 0.019 (-0.010 to 0.050) | 0.138 (0.081 to 0.188) | 0.028 (-0.019 to 0.075) | 0.49 | 0.18 |
| m3_full | psyscam | 141 | 0.007 (0.001 to 0.013) | 0.004 (-0.000 to 0.010) | 0.003 (-0.006 to 0.010) | 0.119 (0.075 to 0.164) | 0.00 | 0.00 |
| m3_no-context | all | 294 | 0.235 (0.178 to 0.291) | 0.056 (0.029 to 0.082) | 0.179 (0.128 to 0.229) | 0.110 (0.058 to 0.166) | 0.34 | 0.14 |
| m3_no-context | p4g | 153 | 0.432 (0.383 to 0.480) | 0.098 (0.054 to 0.147) | 0.334 (0.276 to 0.392) | -0.055 (-0.092 to -0.018) | 0.83 | 0.34 |
| m3_no-context | psyscam | 141 | 0.023 (0.004 to 0.044) | 0.011 (-0.002 to 0.029) | 0.011 (-0.003 to 0.029) | 0.290 (0.228 to 0.349) | 0.02 | 0.00 |
| m3_no-context_ev | all | 294 | 0.237 (0.183 to 0.287) | 0.016 (-0.010 to 0.041) | 0.221 (0.162 to 0.276) | -0.034 (-0.077 to 0.011) | 0.35 | 0.11 |
| m3_no-context_ev | p4g | 153 | 0.412 (0.361 to 0.465) | 0.022 (-0.030 to 0.078) | 0.389 (0.321 to 0.453) | -0.168 (-0.213 to -0.128) | 0.74 | 0.26 |
| m3_no-context_ev | psyscam | 141 | 0.048 (0.029 to 0.074) | 0.009 (0.003 to 0.017) | 0.039 (0.021 to 0.060) | 0.111 (0.076 to 0.148) | 0.10 | 0.02 |

## Cases the model detected

| Model | Dataset | n | Comprehensiveness | Random control | Evidence effect | Sufficiency | Flip (evidence) | Flip (random) |
|---|---|---|---|---|---|---|---|---|
| m0 | all | 200 | 0.291 (0.201 to 0.380) | 0.095 (0.053 to 0.140) | 0.196 (0.130 to 0.263) | 0.210 (0.162 to 0.261) | 0.38 | 0.15 |
| m0 | p4g | 71 | 0.759 (0.700 to 0.817) | 0.240 (0.158 to 0.334) | 0.520 (0.443 to 0.605) | 0.005 (-0.019 to 0.033) | 0.93 | 0.37 |
| m0 | psyscam | 129 | 0.034 (0.017 to 0.056) | 0.016 (0.007 to 0.027) | 0.018 (0.001 to 0.040) | 0.322 (0.275 to 0.374) | 0.07 | 0.04 |
| m3_full | all | 195 | 0.118 (0.071 to 0.165) | 0.033 (0.017 to 0.051) | 0.085 (0.044 to 0.129) | 0.129 (0.090 to 0.168) | 0.15 | 0.06 |
| m3_full | p4g | 61 | 0.362 (0.276 to 0.450) | 0.093 (0.046 to 0.153) | 0.269 (0.177 to 0.355) | 0.124 (0.048 to 0.203) | 0.49 | 0.18 |
| m3_full | psyscam | 134 | 0.007 (0.002 to 0.014) | 0.006 (0.001 to 0.012) | 0.002 (-0.007 to 0.010) | 0.131 (0.087 to 0.175) | 0.00 | 0.00 |
| m3_no-context | all | 222 | 0.217 (0.151 to 0.280) | 0.072 (0.043 to 0.099) | 0.145 (0.097 to 0.193) | 0.204 (0.154 to 0.256) | 0.34 | 0.14 |
| m3_no-context | p4g | 87 | 0.516 (0.449 to 0.591) | 0.162 (0.113 to 0.221) | 0.354 (0.281 to 0.428) | 0.047 (0.010 to 0.091) | 0.83 | 0.34 |
| m3_no-context | psyscam | 135 | 0.023 (0.004 to 0.045) | 0.013 (-0.001 to 0.030) | 0.010 (-0.006 to 0.028) | 0.305 (0.243 to 0.364) | 0.02 | 0.00 |
| m3_no-context_ev | all | 218 | 0.230 (0.172 to 0.289) | 0.064 (0.037 to 0.094) | 0.166 (0.119 to 0.215) | 0.060 (0.034 to 0.088) | 0.35 | 0.11 |
| m3_no-context_ev | p4g | 84 | 0.521 (0.453 to 0.583) | 0.154 (0.096 to 0.220) | 0.367 (0.276 to 0.448) | -0.009 (-0.027 to 0.012) | 0.74 | 0.26 |
| m3_no-context_ev | psyscam | 134 | 0.047 (0.028 to 0.070) | 0.007 (0.002 to 0.013) | 0.040 (0.024 to 0.060) | 0.103 (0.068 to 0.137) | 0.10 | 0.02 |

## Evidence effect per tactic (all cases, mean)

| Tactic | m0 | m3_full | m3_no-context | m3_no-context_ev |
|---|---|---|---|---|
| T1 | 0.384 | -0.027 | 0.305 | 0.205 |
| T2 | 0.403 | 0.447 | 0.493 | 0.376 |
| T3 | 0.201 | 0.096 | 0.199 | 0.252 |
| T4 | 0.144 | -0.021 | 0.094 | 0.325 |
| T5 | 0.015 | 0.010 | 0.015 | 0.047 |
| T6 | 0.179 | 0.198 | 0.230 | 0.379 |
| T7 | 0.234 | 0.047 | 0.287 | 0.496 |
| T9 | -0.005 | -0.003 | -0.022 | 0.002 |
