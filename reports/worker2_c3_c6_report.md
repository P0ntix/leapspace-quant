# Worker 2 — C3 / C4 / C5 / C6 paper concepts, full validation gauntlet

Specs run: 48 (24 real, 24 negative controls).

## Verdict tally

| verdict | real specs | negative controls |
|---|---|---|
| REFUTED | 23 | 23 |
| INCONCLUSIVE | 1 | 1 |

## NEGATIVE CONTROL AUDIT

PASS: no negative control is SUPPORTED.

| negative control | verdict | pooled OOS Sharpe | gross Sharpe | flags |
|---|---|---|---|---|
| c3_vol_regime_filter_commodities | REFUTED | 0.341 | 0.330 | 2 |
| c3_vol_regime_filter_crypto | REFUTED | -0.091 | 0.521 | 5 |
| c3_vol_regime_filter_futures_broad | REFUTED | 0.174 | 0.169 | 3 |
| c3_vol_regime_filter_fx_major | REFUTED | 0.090 | 0.155 | 3 |
| c3_vol_regime_filter_rates_credit | REFUTED | 0.067 | 0.117 | 4 |
| c3_vol_regime_filter_us_equity_style | REFUTED | -0.209 | -0.143 | 5 |
| c4_volume_confirmation_commodities | REFUTED | 0.108 | 0.074 | 5 |
| c4_volume_confirmation_crypto | REFUTED | -0.170 | 0.136 | 6 |
| c4_volume_confirmation_futures_broad | REFUTED | 0.171 | 0.092 | 5 |
| c4_volume_confirmation_fx_major | INCONCLUSIVE | n/a | n/a | 5 |
| c4_volume_confirmation_rates_credit | REFUTED | -0.016 | 0.177 | 3 |
| c4_volume_confirmation_us_equity_style | REFUTED | -0.086 | 0.212 | 4 |
| c5_rsi_reversion_commodities | REFUTED | 0.073 | 0.028 | 4 |
| c5_rsi_reversion_crypto | REFUTED | -0.686 | 0.226 | 6 |
| c5_rsi_reversion_futures_broad | REFUTED | 0.149 | 0.093 | 3 |
| c5_rsi_reversion_fx_major | REFUTED | -0.364 | -0.298 | 6 |
| c5_rsi_reversion_rates_credit | REFUTED | -0.034 | -0.182 | 5 |
| c5_rsi_reversion_us_equity_style | REFUTED | 0.016 | 0.036 | 5 |
| c6_rebound_danger_commodities | REFUTED | 0.303 | 0.285 | 2 |
| c6_rebound_danger_crypto | REFUTED | 0.119 | 0.183 | 6 |
| c6_rebound_danger_futures_broad | REFUTED | 0.160 | 0.156 | 3 |
| c6_rebound_danger_fx_major | REFUTED | 0.007 | 0.076 | 3 |
| c6_rebound_danger_rates_credit | REFUTED | -0.140 | 0.200 | 3 |
| c6_rebound_danger_us_equity_style | REFUTED | -0.596 | -0.338 | 5 |

## CROSS-ASSET-CLASS CONSISTENCY (pooled OOS Sharpe)

### c3_vol_regime_filter

| asset class | OOS Sharpe | in-sample Sharpe | verdict | n_trades | profitable folds |
|---|---|---|---|---|---|
| us_equity_style | 0.008 | 0.045 | REFUTED | 84 | 2/5 |
| crypto | -0.263 | -0.811 | REFUTED | 10 | 2/5 |
| fx_major | -0.201 | -0.211 | REFUTED | 16 | 1/5 |
| commodities | -0.374 | -0.360 | REFUTED | 13 | 0/5 |
| futures_broad | -0.184 | -0.160 | REFUTED | 15 | 2/5 |
| rates_credit | -0.080 | -0.197 | REFUTED | 12 | 3/5 |

### c4_volume_confirmation

| asset class | OOS Sharpe | in-sample Sharpe | verdict | n_trades | profitable folds |
|---|---|---|---|---|---|
| us_equity_style | -0.111 | -0.312 | REFUTED | 317 | 3/5 |
| crypto | -0.084 | -0.300 | REFUTED | 140 | 2/5 |
| fx_major | n/a | n/a | INCONCLUSIVE | 0 | 0/5 |
| commodities | -0.167 | -0.134 | REFUTED | 13 | 3/5 |
| futures_broad | -0.229 | -0.110 | REFUTED | 227 | 3/5 |
| rates_credit | 0.089 | -0.301 | REFUTED | 126 | 2/5 |

### c5_rsi_reversion

| asset class | OOS Sharpe | in-sample Sharpe | verdict | n_trades | profitable folds |
|---|---|---|---|---|---|
| us_equity_style | -0.066 | -0.061 | REFUTED | 24 | 2/5 |
| crypto | 0.080 | -0.304 | REFUTED | 10 | 1/5 |
| fx_major | 0.299 | 0.258 | REFUTED | 119 | 3/5 |
| commodities | -0.072 | -0.011 | REFUTED | 336 | 3/5 |
| futures_broad | -0.162 | -0.095 | REFUTED | 550 | 1/5 |
| rates_credit | 0.066 | 0.128 | REFUTED | 157 | 2/5 |

### c6_rebound_danger

| asset class | OOS Sharpe | in-sample Sharpe | verdict | n_trades | profitable folds |
|---|---|---|---|---|---|
| us_equity_style | 0.429 | 0.251 | REFUTED | 90 | 3/5 |
| crypto | -0.418 | -0.409 | REFUTED | 30 | 1/5 |
| fx_major | -0.114 | -0.131 | REFUTED | 8 | 2/5 |
| commodities | -0.327 | -0.288 | REFUTED | 13 | 1/5 |
| futures_broad | -0.160 | -0.148 | REFUTED | 15 | 2/5 |
| rates_credit | 0.123 | -0.253 | REFUTED | 12 | 3/5 |

## GROSS vs NET at execution.cost_multiplier = 2.0 (STRESSED)

| spec | gross Sharpe | net Sharpe (2x cost) | costs paid | turnover | interpretation |
|---|---|---|---|---|---|
| NEGATIVE-CONTROL-c3_vol_regime_filter_commodities | 0.330 | 0.293 | 10091 | 20654592 | the edge survives costs with little erosion (11% of the gross Sharpe lost to costs) - costs are not the constraint |
| NEGATIVE-CONTROL-c3_vol_regime_filter_crypto | 0.521 | 0.357 | 15259 | 3511375 | the edge survives costs but is materially eroded (31% of the gross Sharpe lost to costs) - a lower-turnover or larger-size version of this strategy would keep more of it |
| NEGATIVE-CONTROL-c3_vol_regime_filter_futures_broad | 0.169 | 0.142 | 6597 | 20021077 | the edge survives costs but is materially eroded (16% of the gross Sharpe lost to costs) - a lower-turnover or larger-size version of this strategy would keep more of it |
| NEGATIVE-CONTROL-c3_vol_regime_filter_fx_major | 0.155 | 0.102 | 5215 | 14124668 | the edge survives costs but is materially eroded (34% of the gross Sharpe lost to costs) - a lower-turnover or larger-size version of this strategy would keep more of it |
| NEGATIVE-CONTROL-c3_vol_regime_filter_rates_credit | 0.117 | 0.031 | 5938 | 10343237 | the edge survives costs but is materially eroded (74% of the gross Sharpe lost to costs) - a lower-turnover or larger-size version of this strategy would keep more of it |
| NEGATIVE-CONTROL-c3_vol_regime_filter_us_equity_style | -0.143 | -0.247 | 5495 | 9171067 | no positive edge even before costs - the signal itself has no exploitable expectancy in this sample, so costs are not the primary problem |
| NEGATIVE-CONTROL-c4_volume_confirmation_commodities | 0.074 | 0.034 | 9895 | 20517271 | the edge survives costs but is materially eroded (53% of the gross Sharpe lost to costs) - a lower-turnover or larger-size version of this strategy would keep more of it |
| NEGATIVE-CONTROL-c4_volume_confirmation_crypto | 0.136 | -0.026 | 10594 | 2494366 | there IS a positive gross-of-costs edge, but it is too small to survive trading costs - the strategy may be real but is untradeable at this size and frequency |
| NEGATIVE-CONTROL-c4_volume_confirmation_futures_broad | 0.092 | 0.052 | 7138 | 22110321 | the edge survives costs but is materially eroded (43% of the gross Sharpe lost to costs) - a lower-turnover or larger-size version of this strategy would keep more of it |
| NEGATIVE-CONTROL-c4_volume_confirmation_fx_major | n/a | n/a | 0 | 0 | no positive edge even before costs - the signal itself has no exploitable expectancy in this sample, so costs are not the primary problem |
| NEGATIVE-CONTROL-c4_volume_confirmation_rates_credit | 0.177 | 0.084 | 9290 | 16081876 | the edge survives costs but is materially eroded (53% of the gross Sharpe lost to costs) - a lower-turnover or larger-size version of this strategy would keep more of it |
| NEGATIVE-CONTROL-c4_volume_confirmation_us_equity_style | 0.212 | 0.112 | 7273 | 12957565 | the edge survives costs but is materially eroded (47% of the gross Sharpe lost to costs) - a lower-turnover or larger-size version of this strategy would keep more of it |
| NEGATIVE-CONTROL-c5_rsi_reversion_commodities | 0.028 | 0.014 | 1366 | 3183414 | the edge survives costs but is materially eroded (51% of the gross Sharpe lost to costs) - a lower-turnover or larger-size version of this strategy would keep more of it |
| NEGATIVE-CONTROL-c5_rsi_reversion_crypto | 0.226 | 0.143 | 349 | 83538 | the edge survives costs but is materially eroded (37% of the gross Sharpe lost to costs) - a lower-turnover or larger-size version of this strategy would keep more of it |
| NEGATIVE-CONTROL-c5_rsi_reversion_futures_broad | 0.093 | 0.072 | 2258 | 7794117 | the edge survives costs but is materially eroded (22% of the gross Sharpe lost to costs) - a lower-turnover or larger-size version of this strategy would keep more of it |
| NEGATIVE-CONTROL-c5_rsi_reversion_fx_major | -0.298 | -0.327 | 499 | 2288820 | no positive edge even before costs - the signal itself has no exploitable expectancy in this sample, so costs are not the primary problem |
| NEGATIVE-CONTROL-c5_rsi_reversion_rates_credit | -0.182 | -0.235 | 1180 | 2318532 | no positive edge even before costs - the signal itself has no exploitable expectancy in this sample, so costs are not the primary problem |
| NEGATIVE-CONTROL-c5_rsi_reversion_us_equity_style | 0.036 | 0.015 | 200 | 378095 | the edge survives costs but is materially eroded (59% of the gross Sharpe lost to costs) - a lower-turnover or larger-size version of this strategy would keep more of it |
| NEGATIVE-CONTROL-c6_rebound_danger_commodities | 0.285 | 0.250 | 10320 | 21189003 | the edge survives costs with little erosion (12% of the gross Sharpe lost to costs) - costs are not the constraint |
| NEGATIVE-CONTROL-c6_rebound_danger_crypto | 0.183 | 0.015 | 13596 | 3152773 | the edge survives costs but is materially eroded (92% of the gross Sharpe lost to costs) - a lower-turnover or larger-size version of this strategy would keep more of it |
| NEGATIVE-CONTROL-c6_rebound_danger_futures_broad | 0.156 | 0.130 | 6818 | 20589846 | the edge survives costs but is materially eroded (17% of the gross Sharpe lost to costs) - a lower-turnover or larger-size version of this strategy would keep more of it |
| NEGATIVE-CONTROL-c6_rebound_danger_fx_major | 0.076 | 0.025 | 4897 | 13424037 | the edge survives costs but is materially eroded (67% of the gross Sharpe lost to costs) - a lower-turnover or larger-size version of this strategy would keep more of it |
| NEGATIVE-CONTROL-c6_rebound_danger_rates_credit | 0.200 | 0.114 | 6324 | 11006149 | the edge survives costs but is materially eroded (43% of the gross Sharpe lost to costs) - a lower-turnover or larger-size version of this strategy would keep more of it |
| NEGATIVE-CONTROL-c6_rebound_danger_us_equity_style | -0.338 | -0.428 | 5323 | 8798100 | no positive edge even before costs - the signal itself has no exploitable expectancy in this sample, so costs are not the primary problem |
| c3_vol_regime_filter_commodities | -0.318 | -0.360 | 5935 | 11822825 | no positive edge even before costs - the signal itself has no exploitable expectancy in this sample, so costs are not the primary problem |
| c3_vol_regime_filter_crypto | -0.670 | -0.811 | 10405 | 2393547 | no positive edge even before costs - the signal itself has no exploitable expectancy in this sample, so costs are not the primary problem |
| c3_vol_regime_filter_futures_broad | -0.128 | -0.160 | 6125 | 17382683 | no positive edge even before costs - the signal itself has no exploitable expectancy in this sample, so costs are not the primary problem |
| c3_vol_regime_filter_fx_major | -0.157 | -0.211 | 4817 | 12849174 | no positive edge even before costs - the signal itself has no exploitable expectancy in this sample, so costs are not the primary problem |
| c3_vol_regime_filter_rates_credit | -0.111 | -0.197 | 6096 | 9620188 | no positive edge even before costs - the signal itself has no exploitable expectancy in this sample, so costs are not the primary problem |
| c3_vol_regime_filter_us_equity_style | 0.148 | 0.045 | 6217 | 10543066 | the edge survives costs but is materially eroded (69% of the gross Sharpe lost to costs) - a lower-turnover or larger-size version of this strategy would keep more of it |
| c4_volume_confirmation_commodities | -0.083 | -0.134 | 8340 | 17043620 | no positive edge even before costs - the signal itself has no exploitable expectancy in this sample, so costs are not the primary problem |
| c4_volume_confirmation_crypto | -0.136 | -0.300 | 14410 | 3400554 | no positive edge even before costs - the signal itself has no exploitable expectancy in this sample, so costs are not the primary problem |
| c4_volume_confirmation_futures_broad | -0.061 | -0.110 | 7459 | 22148029 | no positive edge even before costs - the signal itself has no exploitable expectancy in this sample, so costs are not the primary problem |
| c4_volume_confirmation_fx_major | n/a | n/a | 0 | 0 | no positive edge even before costs - the signal itself has no exploitable expectancy in this sample, so costs are not the primary problem |
| c4_volume_confirmation_rates_credit | -0.181 | -0.301 | 10507 | 17359966 | no positive edge even before costs - the signal itself has no exploitable expectancy in this sample, so costs are not the primary problem |
| c4_volume_confirmation_us_equity_style | -0.209 | -0.312 | 6278 | 10941521 | no positive edge even before costs - the signal itself has no exploitable expectancy in this sample, so costs are not the primary problem |
| c5_rsi_reversion_commodities | 0.006 | -0.011 | 1659 | 3399147 | there IS a positive gross-of-costs edge, but it is too small to survive trading costs - the strategy may be real but is untradeable at this size and frequency |
| c5_rsi_reversion_crypto | -0.222 | -0.304 | 351 | 83538 | no positive edge even before costs - the signal itself has no exploitable expectancy in this sample, so costs are not the primary problem |
| c5_rsi_reversion_futures_broad | -0.071 | -0.095 | 2614 | 7949756 | no positive edge even before costs - the signal itself has no exploitable expectancy in this sample, so costs are not the primary problem |
| c5_rsi_reversion_fx_major | 0.300 | 0.258 | 774 | 2466818 | the edge survives costs with little erosion (14% of the gross Sharpe lost to costs) - costs are not the constraint |
| c5_rsi_reversion_rates_credit | 0.188 | 0.128 | 1400 | 2469906 | the edge survives costs but is materially eroded (32% of the gross Sharpe lost to costs) - a lower-turnover or larger-size version of this strategy would keep more of it |
| c5_rsi_reversion_us_equity_style | -0.039 | -0.061 | 212 | 383090 | no positive edge even before costs - the signal itself has no exploitable expectancy in this sample, so costs are not the primary problem |
| c6_rebound_danger_commodities | -0.250 | -0.288 | 5600 | 11087170 | no positive edge even before costs - the signal itself has no exploitable expectancy in this sample, so costs are not the primary problem |
| c6_rebound_danger_crypto | -0.245 | -0.409 | 13168 | 3057910 | no positive edge even before costs - the signal itself has no exploitable expectancy in this sample, so costs are not the primary problem |
| c6_rebound_danger_futures_broad | -0.118 | -0.148 | 5541 | 15676821 | no positive edge even before costs - the signal itself has no exploitable expectancy in this sample, so costs are not the primary problem |
| c6_rebound_danger_fx_major | -0.077 | -0.131 | 5178 | 13565815 | no positive edge even before costs - the signal itself has no exploitable expectancy in this sample, so costs are not the primary problem |
| c6_rebound_danger_rates_credit | -0.173 | -0.253 | 6047 | 9599258 | no positive edge even before costs - the signal itself has no exploitable expectancy in this sample, so costs are not the primary problem |
| c6_rebound_danger_us_equity_style | 0.340 | 0.251 | 6187 | 10421746 | the edge survives costs but is materially eroded (26% of the gross Sharpe lost to costs) - a lower-turnover or larger-size version of this strategy would keep more of it |

## COST STRESS (multiplier -> Sharpe)

- NEGATIVE-CONTROL-c3_vol_regime_filter_commodities: x1.0=0.312, x1.5=0.302, x2.0=0.293, x3.0=0.275
- NEGATIVE-CONTROL-c3_vol_regime_filter_crypto: x1.0=0.439, x1.5=0.398, x2.0=0.357, x3.0=0.275
- NEGATIVE-CONTROL-c3_vol_regime_filter_futures_broad: x1.0=0.155, x1.5=0.149, x2.0=0.142, x3.0=0.128
- NEGATIVE-CONTROL-c3_vol_regime_filter_fx_major: x1.0=0.128, x1.5=0.115, x2.0=0.102, x3.0=0.075
- NEGATIVE-CONTROL-c3_vol_regime_filter_rates_credit: x1.0=0.074, x1.5=0.052, x2.0=0.031, x3.0=-0.012
- NEGATIVE-CONTROL-c3_vol_regime_filter_us_equity_style: x1.0=-0.195, x1.5=-0.221, x2.0=-0.247, x3.0=-0.299
- NEGATIVE-CONTROL-c4_volume_confirmation_commodities: x1.0=0.054, x1.5=0.044, x2.0=0.034, x3.0=0.014
- NEGATIVE-CONTROL-c4_volume_confirmation_crypto: x1.0=0.055, x1.5=0.014, x2.0=-0.026, x3.0=-0.107
- NEGATIVE-CONTROL-c4_volume_confirmation_futures_broad: x1.0=0.072, x1.5=0.062, x2.0=0.052, x3.0=0.031
- NEGATIVE-CONTROL-c4_volume_confirmation_fx_major: x1.0=n/a, x1.5=n/a, x2.0=n/a, x3.0=n/a
- NEGATIVE-CONTROL-c4_volume_confirmation_rates_credit: x1.0=0.130, x1.5=0.106, x2.0=0.084, x3.0=0.040
- NEGATIVE-CONTROL-c4_volume_confirmation_us_equity_style: x1.0=0.162, x1.5=0.137, x2.0=0.112, x3.0=0.062
- NEGATIVE-CONTROL-c5_rsi_reversion_commodities: x1.0=0.021, x1.5=0.017, x2.0=0.014, x3.0=0.007
- NEGATIVE-CONTROL-c5_rsi_reversion_crypto: x1.0=0.184, x1.5=0.164, x2.0=0.143, x3.0=0.103
- NEGATIVE-CONTROL-c5_rsi_reversion_futures_broad: x1.0=0.082, x1.5=0.077, x2.0=0.072, x3.0=0.061
- NEGATIVE-CONTROL-c5_rsi_reversion_fx_major: x1.0=-0.313, x1.5=-0.320, x2.0=-0.327, x3.0=-0.341
- NEGATIVE-CONTROL-c5_rsi_reversion_rates_credit: x1.0=-0.208, x1.5=-0.221, x2.0=-0.235, x3.0=-0.261
- NEGATIVE-CONTROL-c5_rsi_reversion_us_equity_style: x1.0=0.026, x1.5=0.020, x2.0=0.015, x3.0=0.004
- NEGATIVE-CONTROL-c6_rebound_danger_commodities: x1.0=0.267, x1.5=0.259, x2.0=0.250, x3.0=0.232
- NEGATIVE-CONTROL-c6_rebound_danger_crypto: x1.0=0.099, x1.5=0.057, x2.0=0.015, x3.0=-0.070
- NEGATIVE-CONTROL-c6_rebound_danger_futures_broad: x1.0=0.143, x1.5=0.137, x2.0=0.130, x3.0=0.117
- NEGATIVE-CONTROL-c6_rebound_danger_fx_major: x1.0=0.051, x1.5=0.038, x2.0=0.025, x3.0=-0.001
- NEGATIVE-CONTROL-c6_rebound_danger_rates_credit: x1.0=0.157, x1.5=0.135, x2.0=0.114, x3.0=0.071
- NEGATIVE-CONTROL-c6_rebound_danger_us_equity_style: x1.0=-0.384, x1.5=-0.406, x2.0=-0.428, x3.0=-0.473
- c3_vol_regime_filter_commodities: x1.0=-0.339, x1.5=-0.350, x2.0=-0.360, x3.0=-0.381
- c3_vol_regime_filter_crypto: x1.0=-0.741, x1.5=-0.776, x2.0=-0.811, x3.0=-0.879
- c3_vol_regime_filter_futures_broad: x1.0=-0.144, x1.5=-0.152, x2.0=-0.160, x3.0=-0.176
- c3_vol_regime_filter_fx_major: x1.0=-0.184, x1.5=-0.198, x2.0=-0.211, x3.0=-0.238
- c3_vol_regime_filter_rates_credit: x1.0=-0.154, x1.5=-0.175, x2.0=-0.197, x3.0=-0.239
- c3_vol_regime_filter_us_equity_style: x1.0=0.097, x1.5=0.071, x2.0=0.045, x3.0=-0.006
- c4_volume_confirmation_commodities: x1.0=-0.108, x1.5=-0.121, x2.0=-0.134, x3.0=-0.160
- c4_volume_confirmation_crypto: x1.0=-0.219, x1.5=-0.259, x2.0=-0.300, x3.0=-0.381
- c4_volume_confirmation_futures_broad: x1.0=-0.085, x1.5=-0.098, x2.0=-0.110, x3.0=-0.135
- c4_volume_confirmation_fx_major: x1.0=n/a, x1.5=n/a, x2.0=n/a, x3.0=n/a
- c4_volume_confirmation_rates_credit: x1.0=-0.242, x1.5=-0.272, x2.0=-0.301, x3.0=-0.359
- c4_volume_confirmation_us_equity_style: x1.0=-0.261, x1.5=-0.286, x2.0=-0.312, x3.0=-0.363
- c5_rsi_reversion_commodities: x1.0=-0.003, x1.5=-0.007, x2.0=-0.011, x3.0=-0.020
- c5_rsi_reversion_crypto: x1.0=-0.263, x1.5=-0.284, x2.0=-0.304, x3.0=-0.342
- c5_rsi_reversion_futures_broad: x1.0=-0.083, x1.5=-0.089, x2.0=-0.095, x3.0=-0.106
- c5_rsi_reversion_fx_major: x1.0=0.279, x1.5=0.269, x2.0=0.258, x3.0=0.237
- c5_rsi_reversion_rates_credit: x1.0=0.158, x1.5=0.143, x2.0=0.128, x3.0=0.098
- c5_rsi_reversion_us_equity_style: x1.0=-0.050, x1.5=-0.056, x2.0=-0.061, x3.0=-0.072
- c6_rebound_danger_commodities: x1.0=-0.269, x1.5=-0.279, x2.0=-0.288, x3.0=-0.307
- c6_rebound_danger_crypto: x1.0=-0.327, x1.5=-0.369, x2.0=-0.409, x3.0=-0.490
- c6_rebound_danger_futures_broad: x1.0=-0.133, x1.5=-0.141, x2.0=-0.148, x3.0=-0.164
- c6_rebound_danger_fx_major: x1.0=-0.104, x1.5=-0.117, x2.0=-0.131, x3.0=-0.158
- c6_rebound_danger_rates_credit: x1.0=-0.213, x1.5=-0.233, x2.0=-0.253, x3.0=-0.293
- c6_rebound_danger_us_equity_style: x1.0=0.295, x1.5=0.273, x2.0=0.251, x3.0=0.206

## PER-SPEC DETAIL

### NEGATIVE-CONTROL-c3_vol_regime_filter_commodities

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe 0.34 is below 0.5, while the gross-of-costs Sharpe is 0.33 - a real gross edge exists but it is too small to survive costs at this size and frequency.
- **pooled OOS Sharpe**: 0.341
- **in-sample Sharpe (base run)**: 0.293
- **in-sample Sharpe (last fold training)**: -0.335
- **OOS retention**: n/a
- **n_trades**: 13  **max_drawdown**: 0.2221  **total_return**: 0.7521  **cagr**: 0.0261
- **t_stat**: 1.370  **n_bars**: 5492  **PBO inversion rate**: 0.700
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=4
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 13 trades (need >=30)`
- `t-stat 1.37 below 2.0 - the return series is not distinguishable from noise`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-16..2009-05-18 | 858 | -2.121 | 0.225 | 13 |
| 1 | 2010-05-04..2013-09-27 | 858 | -0.297 | -0.054 | 13 |
| 2 | 2014-09-12..2018-02-09 | 858 | -0.442 | 0.925 | 13 |
| 3 | 2019-01-28..2022-06-22 | 858 | -0.626 | 0.531 | 13 |
| 4 | 2023-06-07..2026-11-03 | 858 | -0.335 | 0.176 | 13 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **ERRORED** | only 13 trades — Monte Carlo needs >=20 |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): n/a  (only 13 trades — Monte Carlo needs >=20)
- Parameter sweep stability: 1.0000
- Subperiod/regime: 12/22 profitable years
- Capacity: 19641 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: 0.293

### NEGATIVE-CONTROL-c3_vol_regime_filter_crypto

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.09 is below 0.5, while the gross-of-costs Sharpe is 0.52 - a real gross edge exists but it is too small to survive costs at this size and frequency.
- **pooled OOS Sharpe**: -0.091
- **in-sample Sharpe (base run)**: 0.357
- **in-sample Sharpe (last fold training)**: 1.313
- **OOS retention**: -0.069
- **n_trades**: 10  **max_drawdown**: 0.2759  **total_return**: 0.2967  **cagr**: 0.0312
- **t_stat**: 1.039  **n_bars**: 2132  **PBO inversion rate**: 0.600
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=2
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 10 trades (need >=30)`
- `t-stat 1.04 below 2.0 - the return series is not distinguishable from noise`
- `only 2/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `OOS Sharpe retains only -7% of the in-sample Sharpe (need 40%) - the edge degrades out of sample`
- `only 2/6 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2021-08-30..2022-03-03 | 186 | 0.401 | -0.761 | 10 |
| 1 | 2022-10-31..2023-05-04 | 186 | 0.659 | 0.353 | 10 |
| 2 | 2023-12-31..2024-07-03 | 186 | -0.230 | 1.274 | 10 |
| 3 | 2025-03-01..2025-09-02 | 186 | 1.591 | -0.189 | 10 |
| 4 | 2026-05-01..2026-11-02 | 186 | 1.313 | -0.543 | 10 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **ERRORED** | only 10 trades — Monte Carlo needs >=20 |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): n/a  (only 10 trades — Monte Carlo needs >=20)
- Parameter sweep stability: 0.8750
- Subperiod/regime: 2/6 profitable years
- Capacity: 3238490051 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: 0.357

### NEGATIVE-CONTROL-c3_vol_regime_filter_futures_broad

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe 0.17 is below 0.5, while the gross-of-costs Sharpe is 0.17 - a real gross edge exists but it is too small to survive costs at this size and frequency.
- **pooled OOS Sharpe**: 0.174
- **in-sample Sharpe (base run)**: 0.142
- **in-sample Sharpe (last fold training)**: 0.220
- **OOS retention**: 0.790
- **n_trades**: 15  **max_drawdown**: 0.3311  **total_return**: 0.2293  **cagr**: 0.0095
- **t_stat**: 0.662  **n_bars**: 5497  **PBO inversion rate**: 0.200
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=2
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 15 trades (need >=30)`
- `t-stat 0.66 below 2.0 - the return series is not distinguishable from noise`
- `only 2/5 walk-forward folds profitable (edge concentrated in a few periods)`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-15..2009-05-13 | 859 | -0.125 | -0.234 | 14 |
| 1 | 2010-04-29..2013-09-25 | 859 | 0.946 | -0.016 | 14 |
| 2 | 2014-09-10..2018-02-08 | 859 | 0.975 | 1.017 | 15 |
| 3 | 2019-01-25..2022-06-22 | 859 | 0.403 | -0.065 | 15 |
| 4 | 2023-06-07..2026-11-03 | 859 | 0.220 | 0.610 | 15 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **ERRORED** | only 15 trades — Monte Carlo needs >=20 |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): n/a  (only 15 trades — Monte Carlo needs >=20)
- Parameter sweep stability: 0.8750
- Subperiod/regime: 11/22 profitable years
- Capacity: 23376 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: 0.142

### NEGATIVE-CONTROL-c3_vol_regime_filter_fx_major

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe 0.09 is below 0.5, while the gross-of-costs Sharpe is 0.15 - a real gross edge exists but it is too small to survive costs at this size and frequency.
- **pooled OOS Sharpe**: 0.090
- **in-sample Sharpe (base run)**: 0.102
- **in-sample Sharpe (last fold training)**: 0.356
- **OOS retention**: 0.252
- **n_trades**: 16  **max_drawdown**: 0.2285  **total_return**: 0.0810  **cagr**: 0.0035
- **t_stat**: 0.483  **n_bars**: 5680  **PBO inversion rate**: 0.900
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=4
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 16 trades (need >=30)`
- `t-stat 0.48 below 2.0 - the return series is not distinguishable from noise`
- `OOS Sharpe retains only 25% of the in-sample Sharpe (need 40%) - the edge degrades out of sample`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-06..2009-05-19 | 896 | 2.342 | 0.056 | 8 |
| 1 | 2010-04-21..2013-09-26 | 896 | 0.500 | 0.116 | 8 |
| 2 | 2014-09-01..2018-02-08 | 896 | 0.631 | -0.662 | 8 |
| 3 | 2019-01-11..2022-06-19 | 896 | 0.262 | 0.585 | 8 |
| 4 | 2023-05-22..2026-11-03 | 896 | 0.356 | 0.400 | 16 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **ERRORED** | only 16 trades — Monte Carlo needs >=20 |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): n/a  (only 16 trades — Monte Carlo needs >=20)
- Parameter sweep stability: 0.8750
- Subperiod/regime: 13/22 profitable years
- Capacity: n/a USD (no ADV data)
- Causality audit: causal=True violations=0
- Deflated Sharpe: 0.102

### NEGATIVE-CONTROL-c3_vol_regime_filter_rates_credit

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe 0.07 is below 0.5, while the gross-of-costs Sharpe is 0.12 - a real gross edge exists but it is too small to survive costs at this size and frequency.
- **pooled OOS Sharpe**: 0.067
- **in-sample Sharpe (base run)**: 0.031
- **in-sample Sharpe (last fold training)**: -0.351
- **OOS retention**: n/a
- **n_trades**: 12  **max_drawdown**: 0.2256  **total_return**: 0.0103  **cagr**: 0.0005
- **t_stat**: 0.143  **n_bars**: 5491  **PBO inversion rate**: 0.300
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=2
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 12 trades (need >=30)`
- `t-stat 0.14 below 2.0 - the return series is not distinguishable from noise`
- `only 2/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `only 8/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-19..2009-05-19 | 858 | 0.321 | -0.102 | 12 |
| 1 | 2010-05-04..2013-09-27 | 858 | -0.082 | 0.757 | 12 |
| 2 | 2014-09-12..2018-02-07 | 858 | -0.184 | -0.135 | 12 |
| 3 | 2019-01-24..2022-06-17 | 858 | -0.458 | -0.589 | 12 |
| 4 | 2023-06-05..2026-11-03 | 858 | -0.351 | 0.323 | 12 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **ERRORED** | only 12 trades — Monte Carlo needs >=20 |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): n/a  (only 12 trades — Monte Carlo needs >=20)
- Parameter sweep stability: 0.7500
- Subperiod/regime: 8/22 profitable years
- Capacity: 13464081 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: 0.031

### NEGATIVE-CONTROL-c3_vol_regime_filter_us_equity_style

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.21 is below 0.5, and the gross-of-costs Sharpe is -0.14 - there is NO positive edge even before costs. The signal has no exploitable expectancy in this sample; this is not a cost problem that better execution could solve.
- **pooled OOS Sharpe**: -0.209
- **in-sample Sharpe (base run)**: -0.247
- **in-sample Sharpe (last fold training)**: -0.858
- **OOS retention**: n/a
- **n_trades**: 84  **max_drawdown**: 0.2216  **total_return**: -0.1408  **cagr**: -0.0069
- **t_stat**: -1.153  **n_bars**: 5492  **PBO inversion rate**: 0.700
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=2
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `t-stat -1.15 below 2.0 - the return series is not distinguishable from noise`
- `only 2/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `edge does not survive 2x cost stress`
- `Monte Carlo prob(profitable) 12%`
- `only 7/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-15..2009-05-14 | 858 | -0.031 | -0.736 | 30 |
| 1 | 2010-04-30..2013-09-25 | 858 | -0.743 | 0.107 | 18 |
| 2 | 2014-09-10..2018-02-05 | 858 | -0.496 | -0.072 | 18 |
| 3 | 2019-01-22..2022-06-15 | 858 | -0.842 | -1.063 | 18 |
| 4 | 2023-06-01..2026-10-30 | 858 | -0.858 | 0.706 | 12 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **RAN** |  |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): 0.1183
- Parameter sweep stability: 0.8750
- Subperiod/regime: 7/22 profitable years
- Capacity: 883074401 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: -0.247

### NEGATIVE-CONTROL-c4_volume_confirmation_commodities

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe 0.11 is below 0.5, while the gross-of-costs Sharpe is 0.07 - a real gross edge exists but it is too small to survive costs at this size and frequency.
- **pooled OOS Sharpe**: 0.108
- **in-sample Sharpe (base run)**: 0.034
- **in-sample Sharpe (last fold training)**: 0.063
- **OOS retention**: 1.715
- **n_trades**: 13  **max_drawdown**: 0.2907  **total_return**: -0.0351  **cagr**: -0.0016
- **t_stat**: 0.160  **n_bars**: 5492  **PBO inversion rate**: 0.500
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=2
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 13 trades (need >=30)`
- `t-stat 0.16 below 2.0 - the return series is not distinguishable from noise`
- `only 2/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `parameter stability 50% (< 60%)`
- `only 10/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-16..2009-05-18 | 858 | -0.345 | -0.143 | 13 |
| 1 | 2010-05-04..2013-09-27 | 858 | 0.443 | -0.247 | 13 |
| 2 | 2014-09-12..2018-02-09 | 858 | 0.337 | 0.836 | 13 |
| 3 | 2019-01-28..2022-06-22 | 858 | -0.108 | 0.614 | 13 |
| 4 | 2023-06-07..2026-11-03 | 858 | 0.063 | -0.460 | 13 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **ERRORED** | only 13 trades — Monte Carlo needs >=20 |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): n/a  (only 13 trades — Monte Carlo needs >=20)
- Parameter sweep stability: 0.5000
- Subperiod/regime: 10/22 profitable years
- Capacity: 19773 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: 0.034

### NEGATIVE-CONTROL-c4_volume_confirmation_crypto

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.17 is below 0.5, while the gross-of-costs Sharpe is 0.14 - a real gross edge exists but it is too small to survive costs at this size and frequency.
- **pooled OOS Sharpe**: -0.170
- **in-sample Sharpe (base run)**: -0.026
- **in-sample Sharpe (last fold training)**: 0.616
- **OOS retention**: -0.276
- **n_trades**: 140  **max_drawdown**: 0.4539  **total_return**: -0.0603  **cagr**: -0.0073
- **t_stat**: -0.075  **n_bars**: 2132  **PBO inversion rate**: 0.400
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=2
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `t-stat -0.08 below 2.0 - the return series is not distinguishable from noise`
- `only 2/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `OOS Sharpe retains only -28% of the in-sample Sharpe (need 40%) - the edge degrades out of sample`
- `edge does not survive 2x cost stress`
- `parameter stability 50% (< 60%)`
- `Monte Carlo prob(profitable) 41%`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2021-08-30..2022-03-03 | 186 | -0.834 | -0.184 | 10 |
| 1 | 2022-10-31..2023-05-04 | 186 | -0.069 | -1.192 | 20 |
| 2 | 2023-12-31..2024-07-03 | 186 | -0.305 | -0.744 | 30 |
| 3 | 2025-03-01..2025-09-02 | 186 | 0.414 | 0.865 | 20 |
| 4 | 2026-05-01..2026-11-02 | 186 | 0.616 | 0.680 | 20 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **RAN** |  |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): 0.4133
- Parameter sweep stability: 0.5000
- Subperiod/regime: 4/6 profitable years
- Capacity: 4558894789 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: -0.026

### NEGATIVE-CONTROL-c4_volume_confirmation_futures_broad

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe 0.17 is below 0.5, while the gross-of-costs Sharpe is 0.09 - a real gross edge exists but it is too small to survive costs at this size and frequency.
- **pooled OOS Sharpe**: 0.171
- **in-sample Sharpe (base run)**: 0.052
- **in-sample Sharpe (last fold training)**: 0.527
- **OOS retention**: 0.325
- **n_trades**: 226  **max_drawdown**: 0.2539  **total_return**: 0.0180  **cagr**: 0.0008
- **t_stat**: 0.242  **n_bars**: 5497  **PBO inversion rate**: 0.400
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=2
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `t-stat 0.24 below 2.0 - the return series is not distinguishable from noise`
- `only 2/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `OOS Sharpe retains only 32% of the in-sample Sharpe (need 40%) - the edge degrades out of sample`
- `parameter stability 50% (< 60%)`
- `Monte Carlo prob(profitable) 53%`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-15..2009-05-13 | 859 | -0.866 | -0.294 | 38 |
| 1 | 2010-04-29..2013-09-25 | 859 | 0.903 | -0.101 | 50 |
| 2 | 2014-09-10..2018-02-08 | 859 | 0.822 | 1.259 | 51 |
| 3 | 2019-01-25..2022-06-22 | 859 | 0.330 | 0.221 | 41 |
| 4 | 2023-06-07..2026-11-03 | 859 | 0.527 | -0.047 | 55 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **RAN** |  |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): 0.5260
- Parameter sweep stability: 0.5000
- Subperiod/regime: 12/22 profitable years
- Capacity: 21168 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: 0.052

### NEGATIVE-CONTROL-c4_volume_confirmation_fx_major

- **verdict**: INCONCLUSIVE
- **reasoning**: Too few trades (0) to distinguish signal from noise.
- **pooled OOS Sharpe**: n/a
- **in-sample Sharpe (base run)**: n/a
- **in-sample Sharpe (last fold training)**: n/a
- **OOS retention**: n/a
- **n_trades**: 0  **max_drawdown**: 0.0000  **total_return**: 0.0000  **cagr**: 0.0000
- **t_stat**: n/a  **n_bars**: 5680  **PBO inversion rate**: n/a
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=0
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 0 trades (need >=30)`
- `0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few`
- `edge does not survive 2x cost stress`
- `parameter stability 0% (< 60%)`
- `only 0/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-06..2009-05-19 | 896 | n/a | n/a | 0 |
| 1 | 2010-04-21..2013-09-26 | 896 | n/a | n/a | 0 |
| 2 | 2014-09-01..2018-02-08 | 896 | n/a | n/a | 0 |
| 3 | 2019-01-11..2022-06-19 | 896 | n/a | n/a | 0 |
| 4 | 2023-05-22..2026-11-03 | 896 | n/a | n/a | 0 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **ERRORED** | only 0 trades — Monte Carlo needs >=20 |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): n/a  (only 0 trades — Monte Carlo needs >=20)
- Parameter sweep stability: 0.0000
- Subperiod/regime: 0/22 profitable years
- Capacity: n/a USD (no traded symbols or zero turnover)
- Causality audit: causal=True violations=0

### NEGATIVE-CONTROL-c4_volume_confirmation_rates_credit

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.02 is below 0.5, while the gross-of-costs Sharpe is 0.18 - a real gross edge exists but it is too small to survive costs at this size and frequency.
- **pooled OOS Sharpe**: -0.016
- **in-sample Sharpe (base run)**: 0.084
- **in-sample Sharpe (last fold training)**: 1.038
- **OOS retention**: -0.015
- **n_trades**: 126  **max_drawdown**: 0.2583  **total_return**: 0.0638  **cagr**: 0.0028
- **t_stat**: 0.391  **n_bars**: 5491  **PBO inversion rate**: 0.400
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=3
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `t-stat 0.39 below 2.0 - the return series is not distinguishable from noise`
- `OOS Sharpe retains only -2% of the in-sample Sharpe (need 40%) - the edge degrades out of sample`
- `Monte Carlo prob(profitable) 76%`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-19..2009-05-19 | 858 | 0.940 | 0.721 | 21 |
| 1 | 2010-05-04..2013-09-27 | 858 | 0.480 | 0.666 | 36 |
| 2 | 2014-09-12..2018-02-07 | 858 | 0.356 | -0.337 | 24 |
| 3 | 2019-01-24..2022-06-17 | 858 | 0.593 | -0.941 | 36 |
| 4 | 2023-06-05..2026-11-03 | 858 | 1.038 | 0.296 | 72 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **RAN** |  |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): 0.7590
- Parameter sweep stability: 0.6667
- Subperiod/regime: 13/22 profitable years
- Capacity: 8659573 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: 0.084

### NEGATIVE-CONTROL-c4_volume_confirmation_us_equity_style

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.09 is below 0.5, while the gross-of-costs Sharpe is 0.21 - a real gross edge exists but it is too small to survive costs at this size and frequency.
- **pooled OOS Sharpe**: -0.086
- **in-sample Sharpe (base run)**: 0.112
- **in-sample Sharpe (last fold training)**: 0.562
- **OOS retention**: -0.153
- **n_trades**: 317  **max_drawdown**: 0.1746  **total_return**: 0.0685  **cagr**: 0.0030
- **t_stat**: 0.522  **n_bars**: 5492  **PBO inversion rate**: 0.700
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=2
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `t-stat 0.52 below 2.0 - the return series is not distinguishable from noise`
- `only 2/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `OOS Sharpe retains only -15% of the in-sample Sharpe (need 40%) - the edge degrades out of sample`
- `Monte Carlo prob(profitable) 66%`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-15..2009-05-14 | 858 | 1.197 | 0.133 | 48 |
| 1 | 2010-04-30..2013-09-25 | 858 | 1.135 | -0.331 | 48 |
| 2 | 2014-09-10..2018-02-05 | 858 | 1.389 | -0.439 | 53 |
| 3 | 2019-01-22..2022-06-15 | 858 | 1.024 | -0.420 | 54 |
| 4 | 2023-06-01..2026-10-30 | 858 | 0.562 | 0.708 | 60 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **RAN** |  |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): 0.6580
- Parameter sweep stability: 0.6667
- Subperiod/regime: 16/22 profitable years
- Capacity: 625019758 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: 0.112

### NEGATIVE-CONTROL-c5_rsi_reversion_commodities

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe 0.07 is below 0.5, while the gross-of-costs Sharpe is 0.03 - a real gross edge exists but it is too small to survive costs at this size and frequency.
- **pooled OOS Sharpe**: 0.073
- **in-sample Sharpe (base run)**: 0.014
- **in-sample Sharpe (last fold training)**: -0.354
- **OOS retention**: n/a
- **n_trades**: 336  **max_drawdown**: 0.1687  **total_return**: -0.0096  **cagr**: -0.0004
- **t_stat**: 0.064  **n_bars**: 5492  **PBO inversion rate**: 0.333
- **walk-forward**: mode=purged_embargoed folds=5 purge=14 embargo=14 profitable_folds=2
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `t-stat 0.06 below 2.0 - the return series is not distinguishable from noise`
- `only 2/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `parameter stability 50% (< 60%)`
- `Monte Carlo prob(profitable) 45%`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-08-05..2009-05-18 | 950 | n/a | -0.154 | 63 |
| 1 | 2009-12-18..2013-09-27 | 950 | -0.935 | -0.222 | 38 |
| 2 | 2014-05-02..2018-02-09 | 950 | -0.290 | -0.211 | 94 |
| 3 | 2018-09-13..2022-06-22 | 950 | 0.019 | 0.207 | 39 |
| 4 | 2023-01-25..2026-11-03 | 950 | -0.354 | 0.415 | 68 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **RAN** |  |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): 0.4483
- Parameter sweep stability: 0.5000
- Subperiod/regime: 12/22 profitable years
- Capacity: 127437 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: 0.014

### NEGATIVE-CONTROL-c5_rsi_reversion_crypto

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.69 is below 0.5, while the gross-of-costs Sharpe is 0.23 - a real gross edge exists but it is too small to survive costs at this size and frequency.
- **pooled OOS Sharpe**: -0.686
- **in-sample Sharpe (base run)**: 0.143
- **in-sample Sharpe (last fold training)**: 0.270
- **OOS retention**: -2.545
- **n_trades**: 10  **max_drawdown**: 0.0092  **total_return**: 0.0065  **cagr**: 0.0008
- **t_stat**: 0.417  **n_bars**: 2132  **PBO inversion rate**: n/a
- **walk-forward**: mode=purged_embargoed folds=5 purge=14 embargo=14 profitable_folds=0
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 10 trades (need >=30)`
- `t-stat 0.42 below 2.0 - the return series is not distinguishable from noise`
- `0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few`
- `OOS Sharpe retains only -254% of the in-sample Sharpe (need 40%) - the edge degrades out of sample`
- `parameter stability 25% (< 60%)`
- `only 1/6 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2021-05-30..2022-03-03 | 278 | n/a | n/a | 0 |
| 1 | 2022-07-31..2023-05-04 | 278 | n/a | n/a | 0 |
| 2 | 2023-09-30..2024-07-03 | 278 | n/a | n/a | 0 |
| 3 | 2024-11-29..2025-09-02 | 278 | n/a | n/a | 0 |
| 4 | 2026-01-29..2026-11-02 | 278 | 0.270 | -1.537 | 10 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **ERRORED** | only 10 trades — Monte Carlo needs >=20 |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): n/a  (only 10 trades — Monte Carlo needs >=20)
- Parameter sweep stability: 0.2500
- Subperiod/regime: 1/6 profitable years
- Capacity: 136124459293 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: 0.143

### NEGATIVE-CONTROL-c5_rsi_reversion_futures_broad

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe 0.15 is below 0.5, while the gross-of-costs Sharpe is 0.09 - a real gross edge exists but it is too small to survive costs at this size and frequency.
- **pooled OOS Sharpe**: 0.149
- **in-sample Sharpe (base run)**: 0.072
- **in-sample Sharpe (last fold training)**: -0.088
- **OOS retention**: n/a
- **n_trades**: 550  **max_drawdown**: 0.1615  **total_return**: 0.0529  **cagr**: 0.0024
- **t_stat**: 0.336  **n_bars**: 5497  **PBO inversion rate**: 0.833
- **walk-forward**: mode=purged_embargoed folds=5 purge=14 embargo=14 profitable_folds=4
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `t-stat 0.34 below 2.0 - the return series is not distinguishable from noise`
- `Monte Carlo prob(profitable) 66%`
- `only 8/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-08-05..2009-05-13 | 951 | n/a | -0.647 | 83 |
| 1 | 2009-12-15..2013-09-25 | 951 | -1.005 | 0.938 | 96 |
| 2 | 2014-04-30..2018-02-08 | 951 | 0.598 | 0.035 | 138 |
| 3 | 2018-09-12..2022-06-22 | 951 | 0.644 | 0.188 | 119 |
| 4 | 2023-01-25..2026-11-03 | 951 | -0.088 | 0.690 | 45 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **RAN** |  |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): 0.6633
- Parameter sweep stability: 1.0000
- Subperiod/regime: 8/22 profitable years
- Capacity: 60048 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: 0.072

### NEGATIVE-CONTROL-c5_rsi_reversion_fx_major

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.36 is below 0.5, and the gross-of-costs Sharpe is -0.30 - there is NO positive edge even before costs. The signal has no exploitable expectancy in this sample; this is not a cost problem that better execution could solve.
- **pooled OOS Sharpe**: -0.364
- **in-sample Sharpe (base run)**: -0.327
- **in-sample Sharpe (last fold training)**: 0.020
- **OOS retention**: -17.847
- **n_trades**: 119  **max_drawdown**: 0.0706  **total_return**: -0.0581  **cagr**: -0.0027
- **t_stat**: -1.552  **n_bars**: 5680  **PBO inversion rate**: 0.667
- **walk-forward**: mode=purged_embargoed folds=5 purge=14 embargo=14 profitable_folds=1
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `t-stat -1.55 below 2.0 - the return series is not distinguishable from noise`
- `only 1/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `OOS Sharpe retains only -1785% of the in-sample Sharpe (need 40%) - the edge degrades out of sample`
- `edge does not survive 2x cost stress`
- `Monte Carlo prob(profitable) 4%`
- `only 6/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-07-27..2009-05-19 | 988 | n/a | -0.786 | 23 |
| 1 | 2009-12-15..2013-09-26 | 988 | n/a | -0.460 | 8 |
| 2 | 2014-04-24..2018-02-08 | 988 | 1.111 | -0.037 | 8 |
| 3 | 2018-09-04..2022-06-19 | 988 | 0.962 | -0.204 | 40 |
| 4 | 2023-01-13..2026-11-03 | 988 | 0.020 | 0.121 | 24 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **RAN** |  |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): 0.0403
- Parameter sweep stability: 1.0000
- Subperiod/regime: 6/22 profitable years
- Capacity: n/a USD (no ADV data)
- Causality audit: causal=True violations=0
- Deflated Sharpe: -0.327

### NEGATIVE-CONTROL-c5_rsi_reversion_rates_credit

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.03 is below 0.5, and the gross-of-costs Sharpe is -0.18 - there is NO positive edge even before costs. The signal has no exploitable expectancy in this sample; this is not a cost problem that better execution could solve.
- **pooled OOS Sharpe**: -0.034
- **in-sample Sharpe (base run)**: -0.235
- **in-sample Sharpe (last fold training)**: -0.751
- **OOS retention**: n/a
- **n_trades**: 157  **max_drawdown**: 0.0731  **total_return**: -0.0543  **cagr**: -0.0026
- **t_stat**: -1.095  **n_bars**: 5491  **PBO inversion rate**: 0.300
- **walk-forward**: mode=purged_embargoed folds=5 purge=14 embargo=14 profitable_folds=2
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `t-stat -1.10 below 2.0 - the return series is not distinguishable from noise`
- `only 2/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `edge does not survive 2x cost stress`
- `parameter stability 50% (< 60%)`
- `Monte Carlo prob(profitable) 2%`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-08-05..2009-05-19 | 950 | -0.902 | -0.083 | 20 |
| 1 | 2009-12-18..2013-09-27 | 950 | -0.539 | -0.640 | 36 |
| 2 | 2014-05-02..2018-02-07 | 950 | -0.440 | -0.025 | 60 |
| 3 | 2018-09-11..2022-06-17 | 950 | -0.415 | 0.998 | 48 |
| 4 | 2023-01-23..2026-11-03 | 950 | -0.751 | 0.667 | 24 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **RAN** |  |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): 0.0207
- Parameter sweep stability: 0.5000
- Subperiod/regime: 12/22 profitable years
- Capacity: 60064819 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: -0.235

### NEGATIVE-CONTROL-c5_rsi_reversion_us_equity_style

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe 0.02 is below 0.5, while the gross-of-costs Sharpe is 0.04 - a real gross edge exists but it is too small to survive costs at this size and frequency.
- **pooled OOS Sharpe**: 0.016
- **in-sample Sharpe (base run)**: 0.015
- **in-sample Sharpe (last fold training)**: n/a
- **OOS retention**: n/a
- **n_trades**: 24  **max_drawdown**: 0.0200  **total_return**: 0.0012  **cagr**: 0.0001
- **t_stat**: 0.070  **n_bars**: 5492  **PBO inversion rate**: n/a
- **walk-forward**: mode=purged_embargoed folds=5 purge=14 embargo=14 profitable_folds=1
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 24 trades (need >=30)`
- `t-stat 0.07 below 2.0 - the return series is not distinguishable from noise`
- `only 1/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `Monte Carlo prob(profitable) 51%`
- `only 1/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-08-05..2009-05-14 | 950 | n/a | -0.643 | 6 |
| 1 | 2009-12-16..2013-09-25 | 950 | n/a | -0.701 | 6 |
| 2 | 2014-04-30..2018-02-05 | 950 | n/a | n/a | 0 |
| 3 | 2018-09-07..2022-06-15 | 950 | n/a | 1.009 | 6 |
| 4 | 2023-01-19..2026-10-30 | 950 | n/a | -0.017 | 6 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **RAN** |  |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): 0.5057
- Parameter sweep stability: 1.0000
- Subperiod/regime: 1/22 profitable years
- Capacity: 21419825130 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: 0.015

### NEGATIVE-CONTROL-c6_rebound_danger_commodities

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe 0.30 is below 0.5, while the gross-of-costs Sharpe is 0.29 - a real gross edge exists but it is too small to survive costs at this size and frequency.
- **pooled OOS Sharpe**: 0.303
- **in-sample Sharpe (base run)**: 0.250
- **in-sample Sharpe (last fold training)**: -0.343
- **OOS retention**: n/a
- **n_trades**: 13  **max_drawdown**: 0.2132  **total_return**: 0.5705  **cagr**: 0.0209
- **t_stat**: 1.166  **n_bars**: 5492  **PBO inversion rate**: 0.500
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=4
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 13 trades (need >=30)`
- `t-stat 1.17 below 2.0 - the return series is not distinguishable from noise`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-16..2009-05-18 | 858 | -1.739 | 0.542 | 13 |
| 1 | 2010-05-04..2013-09-27 | 858 | -0.187 | 0.252 | 13 |
| 2 | 2014-09-12..2018-02-09 | 858 | -0.136 | 0.255 | 13 |
| 3 | 2019-01-28..2022-06-22 | 858 | -0.279 | 0.561 | 13 |
| 4 | 2023-06-07..2026-11-03 | 858 | -0.343 | -0.112 | 13 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **ERRORED** | only 13 trades — Monte Carlo needs >=20 |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): n/a  (only 13 trades — Monte Carlo needs >=20)
- Parameter sweep stability: 1.0000
- Subperiod/regime: 12/22 profitable years
- Capacity: 19146 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: 0.250

### NEGATIVE-CONTROL-c6_rebound_danger_crypto

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe 0.12 is below 0.5, while the gross-of-costs Sharpe is 0.18 - a real gross edge exists but it is too small to survive costs at this size and frequency.
- **pooled OOS Sharpe**: 0.119
- **in-sample Sharpe (base run)**: 0.015
- **in-sample Sharpe (last fold training)**: 0.698
- **OOS retention**: 0.170
- **n_trades**: 30  **max_drawdown**: 0.3374  **total_return**: -0.0310  **cagr**: -0.0037
- **t_stat**: 0.043  **n_bars**: 2132  **PBO inversion rate**: 0.600
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=2
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `t-stat 0.04 below 2.0 - the return series is not distinguishable from noise`
- `only 2/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `OOS Sharpe retains only 17% of the in-sample Sharpe (need 40%) - the edge degrades out of sample`
- `parameter stability 38% (< 60%)`
- `Monte Carlo prob(profitable) 48%`
- `only 2/6 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2021-08-30..2022-03-03 | 186 | 0.156 | -0.419 | 10 |
| 1 | 2022-10-31..2023-05-04 | 186 | 0.559 | -0.073 | 10 |
| 2 | 2023-12-31..2024-07-03 | 186 | -0.293 | 1.596 | 10 |
| 3 | 2025-03-01..2025-09-02 | 186 | 0.885 | -0.335 | 10 |
| 4 | 2026-05-01..2026-11-02 | 186 | 0.698 | 0.337 | 10 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **RAN** |  |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): 0.4763
- Parameter sweep stability: 0.3750
- Subperiod/regime: 2/6 profitable years
- Capacity: 3606842391 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: 0.015

### NEGATIVE-CONTROL-c6_rebound_danger_futures_broad

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe 0.16 is below 0.5, while the gross-of-costs Sharpe is 0.16 - a real gross edge exists but it is too small to survive costs at this size and frequency.
- **pooled OOS Sharpe**: 0.160
- **in-sample Sharpe (base run)**: 0.130
- **in-sample Sharpe (last fold training)**: 0.367
- **OOS retention**: 0.435
- **n_trades**: 15  **max_drawdown**: 0.2680  **total_return**: 0.1956  **cagr**: 0.0082
- **t_stat**: 0.609  **n_bars**: 5497  **PBO inversion rate**: 0.100
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=4
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 15 trades (need >=30)`
- `t-stat 0.61 below 2.0 - the return series is not distinguishable from noise`
- `only 10/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-15..2009-05-13 | 859 | -0.288 | -0.131 | 14 |
| 1 | 2010-04-29..2013-09-25 | 859 | 1.109 | 0.315 | 14 |
| 2 | 2014-09-10..2018-02-08 | 859 | 1.256 | 0.805 | 15 |
| 3 | 2019-01-25..2022-06-22 | 859 | 0.701 | 0.071 | 15 |
| 4 | 2023-06-07..2026-11-03 | 859 | 0.367 | 0.098 | 15 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **ERRORED** | only 15 trades — Monte Carlo needs >=20 |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): n/a  (only 15 trades — Monte Carlo needs >=20)
- Parameter sweep stability: 1.0000
- Subperiod/regime: 10/22 profitable years
- Capacity: 22731 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: 0.130

### NEGATIVE-CONTROL-c6_rebound_danger_fx_major

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe 0.01 is below 0.5, while the gross-of-costs Sharpe is 0.08 - a real gross edge exists but it is too small to survive costs at this size and frequency.
- **pooled OOS Sharpe**: 0.007
- **in-sample Sharpe (base run)**: 0.025
- **in-sample Sharpe (last fold training)**: 0.264
- **OOS retention**: 0.028
- **n_trades**: 8  **max_drawdown**: 0.2433  **total_return**: 0.0028  **cagr**: 0.0001
- **t_stat**: 0.118  **n_bars**: 5680  **PBO inversion rate**: 0.700
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=3
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 8 trades (need >=30)`
- `t-stat 0.12 below 2.0 - the return series is not distinguishable from noise`
- `OOS Sharpe retains only 3% of the in-sample Sharpe (need 40%) - the edge degrades out of sample`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-06..2009-05-19 | 896 | 1.477 | -0.206 | 8 |
| 1 | 2010-04-21..2013-09-26 | 896 | 0.142 | 0.046 | 8 |
| 2 | 2014-09-01..2018-02-08 | 896 | 0.333 | -0.478 | 8 |
| 3 | 2019-01-11..2022-06-19 | 896 | 0.164 | 0.608 | 8 |
| 4 | 2023-05-22..2026-11-03 | 896 | 0.264 | 0.281 | 8 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **ERRORED** | only 8 trades — Monte Carlo needs >=20 |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): n/a  (only 8 trades — Monte Carlo needs >=20)
- Parameter sweep stability: 0.7500
- Subperiod/regime: 14/22 profitable years
- Capacity: n/a USD (no ADV data)
- Causality audit: causal=True violations=0
- Deflated Sharpe: 0.025

### NEGATIVE-CONTROL-c6_rebound_danger_rates_credit

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.14 is below 0.5, while the gross-of-costs Sharpe is 0.20 - a real gross edge exists but it is too small to survive costs at this size and frequency.
- **pooled OOS Sharpe**: -0.140
- **in-sample Sharpe (base run)**: 0.114
- **in-sample Sharpe (last fold training)**: -0.291
- **OOS retention**: n/a
- **n_trades**: 12  **max_drawdown**: 0.1700  **total_return**: 0.0741  **cagr**: 0.0033
- **t_stat**: 0.531  **n_bars**: 5491  **PBO inversion rate**: 0.100
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=2
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 12 trades (need >=30)`
- `t-stat 0.53 below 2.0 - the return series is not distinguishable from noise`
- `only 2/5 walk-forward folds profitable (edge concentrated in a few periods)`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-19..2009-05-19 | 858 | 0.235 | 0.158 | 12 |
| 1 | 2010-05-04..2013-09-27 | 858 | 0.128 | 0.472 | 12 |
| 2 | 2014-09-12..2018-02-07 | 858 | -0.147 | -0.052 | 12 |
| 3 | 2019-01-24..2022-06-17 | 858 | -0.403 | -1.162 | 12 |
| 4 | 2023-06-05..2026-11-03 | 858 | -0.291 | -0.290 | 12 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **ERRORED** | only 12 trades — Monte Carlo needs >=20 |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): n/a  (only 12 trades — Monte Carlo needs >=20)
- Parameter sweep stability: 0.8750
- Subperiod/regime: 11/22 profitable years
- Capacity: 12653126 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: 0.114

### NEGATIVE-CONTROL-c6_rebound_danger_us_equity_style

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.60 is below 0.5, and the gross-of-costs Sharpe is -0.34 - there is NO positive edge even before costs. The signal has no exploitable expectancy in this sample; this is not a cost problem that better execution could solve.
- **pooled OOS Sharpe**: -0.596
- **in-sample Sharpe (base run)**: -0.428
- **in-sample Sharpe (last fold training)**: -0.144
- **OOS retention**: n/a
- **n_trades**: 90  **max_drawdown**: 0.2888  **total_return**: -0.2540  **cagr**: -0.0134
- **t_stat**: -2.000  **n_bars**: 5492  **PBO inversion rate**: 0.500
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=0
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `t-stat -2.00 below 2.0 - the return series is not distinguishable from noise`
- `0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few`
- `edge does not survive 2x cost stress`
- `Monte Carlo prob(profitable) 3%`
- `only 7/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-15..2009-05-14 | 858 | 1.419 | -0.631 | 30 |
| 1 | 2010-04-30..2013-09-25 | 858 | 0.685 | -0.528 | 18 |
| 2 | 2014-09-10..2018-02-05 | 858 | 1.238 | -0.052 | 18 |
| 3 | 2019-01-22..2022-06-15 | 858 | 0.403 | -1.320 | 18 |
| 4 | 2023-06-01..2026-10-30 | 858 | -0.144 | -0.162 | 6 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **RAN** |  |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): 0.0287
- Parameter sweep stability: 1.0000
- Subperiod/regime: 7/22 profitable years
- Capacity: 920509458 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: -0.428

### c3_vol_regime_filter_commodities

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.37 is below 0.5, and the gross-of-costs Sharpe is -0.32 - there is NO positive edge even before costs. The signal has no exploitable expectancy in this sample; this is not a cost problem that better execution could solve.
- **pooled OOS Sharpe**: -0.374
- **in-sample Sharpe (base run)**: -0.360
- **in-sample Sharpe (last fold training)**: 0.110
- **OOS retention**: -3.399
- **n_trades**: 13  **max_drawdown**: 0.6655  **total_return**: -0.6056  **cagr**: -0.0418
- **t_stat**: -1.681  **n_bars**: 5492  **PBO inversion rate**: 0.600
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=0
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 13 trades (need >=30)`
- `t-stat -1.68 below 2.0 - the return series is not distinguishable from noise`
- `0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few`
- `OOS Sharpe retains only -340% of the in-sample Sharpe (need 40%) - the edge degrades out of sample`
- `edge does not survive 2x cost stress`
- `only 8/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-16..2009-05-18 | 858 | 2.054 | -0.314 | 13 |
| 1 | 2010-05-04..2013-09-27 | 858 | 0.188 | -0.051 | 13 |
| 2 | 2014-09-12..2018-02-09 | 858 | 0.290 | -1.002 | 13 |
| 3 | 2019-01-28..2022-06-22 | 858 | 0.452 | -0.492 | 13 |
| 4 | 2023-06-07..2026-11-03 | 858 | 0.110 | -0.172 | 13 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **ERRORED** | only 13 trades — Monte Carlo needs >=20 |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): n/a  (only 13 trades — Monte Carlo needs >=20)
- Parameter sweep stability: 1.0000
- Subperiod/regime: 8/22 profitable years
- Capacity: 34314 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: -0.360

### c3_vol_regime_filter_crypto

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.26 is below 0.5, and the gross-of-costs Sharpe is -0.67 - there is NO positive edge even before costs. The signal has no exploitable expectancy in this sample; this is not a cost problem that better execution could solve.
- **pooled OOS Sharpe**: -0.263
- **in-sample Sharpe (base run)**: -0.811
- **in-sample Sharpe (last fold training)**: -1.629
- **OOS retention**: n/a
- **n_trades**: 10  **max_drawdown**: 0.6532  **total_return**: -0.6011  **cagr**: -0.1029
- **t_stat**: -2.358  **n_bars**: 2132  **PBO inversion rate**: 0.600
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=2
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 10 trades (need >=30)`
- `t-stat -2.36 below 2.0 - the return series is not distinguishable from noise`
- `only 2/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `edge does not survive 2x cost stress`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2021-08-30..2022-03-03 | 186 | -0.371 | 0.442 | 10 |
| 1 | 2022-10-31..2023-05-04 | 186 | -0.720 | -0.767 | 10 |
| 2 | 2023-12-31..2024-07-03 | 186 | 0.057 | -1.713 | 10 |
| 3 | 2025-03-01..2025-09-02 | 186 | -1.872 | -0.051 | 10 |
| 4 | 2026-05-01..2026-11-02 | 186 | -1.629 | 0.055 | 10 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **ERRORED** | only 10 trades — Monte Carlo needs >=20 |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): n/a  (only 10 trades — Monte Carlo needs >=20)
- Parameter sweep stability: 1.0000
- Subperiod/regime: 3/6 profitable years
- Capacity: 4750920665 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: -0.811

### c3_vol_regime_filter_futures_broad

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.18 is below 0.5, and the gross-of-costs Sharpe is -0.13 - there is NO positive edge even before costs. The signal has no exploitable expectancy in this sample; this is not a cost problem that better execution could solve.
- **pooled OOS Sharpe**: -0.184
- **in-sample Sharpe (base run)**: -0.160
- **in-sample Sharpe (last fold training)**: -0.322
- **OOS retention**: n/a
- **n_trades**: 15  **max_drawdown**: 0.4777  **total_return**: -0.3782  **cagr**: -0.0215
- **t_stat**: -0.746  **n_bars**: 5497  **PBO inversion rate**: 0.200
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=2
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 15 trades (need >=30)`
- `t-stat -0.75 below 2.0 - the return series is not distinguishable from noise`
- `only 2/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `edge does not survive 2x cost stress`
- `only 9/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-15..2009-05-13 | 859 | 0.007 | 0.186 | 14 |
| 1 | 2010-04-29..2013-09-25 | 859 | -1.006 | -0.031 | 14 |
| 2 | 2014-09-10..2018-02-08 | 859 | -1.041 | -1.099 | 15 |
| 3 | 2019-01-25..2022-06-22 | 859 | -0.480 | 0.173 | 15 |
| 4 | 2023-06-07..2026-11-03 | 859 | -0.322 | -0.654 | 15 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **ERRORED** | only 15 trades — Monte Carlo needs >=20 |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): n/a  (only 15 trades — Monte Carlo needs >=20)
- Parameter sweep stability: 0.8750
- Subperiod/regime: 9/22 profitable years
- Capacity: 26925 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: -0.160

### c3_vol_regime_filter_fx_major

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.20 is below 0.5, and the gross-of-costs Sharpe is -0.16 - there is NO positive edge even before costs. The signal has no exploitable expectancy in this sample; this is not a cost problem that better execution could solve.
- **pooled OOS Sharpe**: -0.201
- **in-sample Sharpe (base run)**: -0.211
- **in-sample Sharpe (last fold training)**: -0.448
- **OOS retention**: n/a
- **n_trades**: 16  **max_drawdown**: 0.2214  **total_return**: -0.2018  **cagr**: -0.0099
- **t_stat**: -1.002  **n_bars**: 5680  **PBO inversion rate**: 0.900
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=1
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 16 trades (need >=30)`
- `t-stat -1.00 below 2.0 - the return series is not distinguishable from noise`
- `only 1/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `edge does not survive 2x cost stress`
- `only 6/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-06..2009-05-19 | 896 | -2.470 | -0.133 | 8 |
| 1 | 2010-04-21..2013-09-26 | 896 | -0.588 | -0.222 | 8 |
| 2 | 2014-09-01..2018-02-08 | 896 | -0.740 | 0.519 | 8 |
| 3 | 2019-01-11..2022-06-19 | 896 | -0.376 | -0.734 | 8 |
| 4 | 2023-05-22..2026-11-03 | 896 | -0.448 | -0.524 | 16 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **ERRORED** | only 16 trades — Monte Carlo needs >=20 |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): n/a  (only 16 trades — Monte Carlo needs >=20)
- Parameter sweep stability: 0.8750
- Subperiod/regime: 6/22 profitable years
- Capacity: n/a USD (no ADV data)
- Causality audit: causal=True violations=0
- Deflated Sharpe: -0.211

### c3_vol_regime_filter_rates_credit

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.08 is below 0.5, and the gross-of-costs Sharpe is -0.11 - there is NO positive edge even before costs. The signal has no exploitable expectancy in this sample; this is not a cost problem that better execution could solve.
- **pooled OOS Sharpe**: -0.080
- **in-sample Sharpe (base run)**: -0.197
- **in-sample Sharpe (last fold training)**: 0.034
- **OOS retention**: -2.341
- **n_trades**: 12  **max_drawdown**: 0.1860  **total_return**: -0.1463  **cagr**: -0.0072
- **t_stat**: -0.918  **n_bars**: 5491  **PBO inversion rate**: 0.300
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=3
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 12 trades (need >=30)`
- `t-stat -0.92 below 2.0 - the return series is not distinguishable from noise`
- `OOS Sharpe retains only -234% of the in-sample Sharpe (need 40%) - the edge degrades out of sample`
- `edge does not survive 2x cost stress`
- `only 10/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-19..2009-05-19 | 858 | -0.448 | 0.132 | 12 |
| 1 | 2010-05-04..2013-09-27 | 858 | -0.154 | -0.741 | 12 |
| 2 | 2014-09-12..2018-02-07 | 858 | -0.038 | 0.248 | 12 |
| 3 | 2019-01-24..2022-06-17 | 858 | 0.202 | 0.550 | 12 |
| 4 | 2023-06-05..2026-11-03 | 858 | 0.034 | -0.440 | 12 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **ERRORED** | only 12 trades — Monte Carlo needs >=20 |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): n/a  (only 12 trades — Monte Carlo needs >=20)
- Parameter sweep stability: 1.0000
- Subperiod/regime: 10/22 profitable years
- Capacity: 14476036 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: -0.197

### c3_vol_regime_filter_us_equity_style

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe 0.01 is below 0.5, while the gross-of-costs Sharpe is 0.15 - a real gross edge exists but it is too small to survive costs at this size and frequency.
- **pooled OOS Sharpe**: 0.008
- **in-sample Sharpe (base run)**: 0.045
- **in-sample Sharpe (last fold training)**: 0.614
- **OOS retention**: 0.013
- **n_trades**: 84  **max_drawdown**: 0.1065  **total_return**: 0.0188  **cagr**: 0.0009
- **t_stat**: 0.211  **n_bars**: 5492  **PBO inversion rate**: 0.700
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=2
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `t-stat 0.21 below 2.0 - the return series is not distinguishable from noise`
- `only 2/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `OOS Sharpe retains only 1% of the in-sample Sharpe (need 40%) - the edge degrades out of sample`
- `Monte Carlo prob(profitable) 57%`
- `only 10/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-15..2009-05-14 | 858 | -0.282 | 0.519 | 30 |
| 1 | 2010-04-30..2013-09-25 | 858 | 0.526 | -0.324 | 18 |
| 2 | 2014-09-10..2018-02-05 | 858 | 0.259 | -0.199 | 18 |
| 3 | 2019-01-22..2022-06-15 | 858 | 0.606 | 0.922 | 18 |
| 4 | 2023-06-01..2026-10-30 | 858 | 0.614 | -0.883 | 12 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **RAN** |  |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): 0.5727
- Parameter sweep stability: 0.6250
- Subperiod/regime: 10/22 profitable years
- Capacity: 768157387 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: 0.045

### c4_volume_confirmation_commodities

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.17 is below 0.5, and the gross-of-costs Sharpe is -0.08 - there is NO positive edge even before costs. The signal has no exploitable expectancy in this sample; this is not a cost problem that better execution could solve.
- **pooled OOS Sharpe**: -0.167
- **in-sample Sharpe (base run)**: -0.134
- **in-sample Sharpe (last fold training)**: -0.246
- **OOS retention**: n/a
- **n_trades**: 13  **max_drawdown**: 0.5203  **total_return**: -0.3355  **cagr**: -0.0186
- **t_stat**: -0.625  **n_bars**: 5492  **PBO inversion rate**: 0.500
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=3
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 13 trades (need >=30)`
- `t-stat -0.63 below 2.0 - the return series is not distinguishable from noise`
- `edge does not survive 2x cost stress`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-16..2009-05-18 | 858 | 0.274 | 0.016 | 13 |
| 1 | 2010-05-04..2013-09-27 | 858 | -0.545 | 0.133 | 13 |
| 2 | 2014-09-12..2018-02-09 | 858 | -0.456 | -0.903 | 13 |
| 3 | 2019-01-28..2022-06-22 | 858 | -0.009 | -0.534 | 13 |
| 4 | 2023-06-07..2026-11-03 | 858 | -0.246 | 0.442 | 13 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **ERRORED** | only 13 trades — Monte Carlo needs >=20 |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): n/a  (only 13 trades — Monte Carlo needs >=20)
- Parameter sweep stability: 1.0000
- Subperiod/regime: 11/22 profitable years
- Capacity: 23803 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: -0.134

### c4_volume_confirmation_crypto

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.08 is below 0.5, and the gross-of-costs Sharpe is -0.14 - there is NO positive edge even before costs. The signal has no exploitable expectancy in this sample; this is not a cost problem that better execution could solve.
- **pooled OOS Sharpe**: -0.084
- **in-sample Sharpe (base run)**: -0.300
- **in-sample Sharpe (last fold training)**: -0.848
- **OOS retention**: n/a
- **n_trades**: 140  **max_drawdown**: 0.4546  **total_return**: -0.2478  **cagr**: -0.0331
- **t_stat**: -0.873  **n_bars**: 2132  **PBO inversion rate**: 0.400
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=2
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `t-stat -0.87 below 2.0 - the return series is not distinguishable from noise`
- `only 2/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `edge does not survive 2x cost stress`
- `Monte Carlo prob(profitable) 29%`
- `only 2/6 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2021-08-30..2022-03-03 | 186 | 0.888 | -0.132 | 10 |
| 1 | 2022-10-31..2023-05-04 | 186 | 0.014 | 1.155 | 20 |
| 2 | 2023-12-31..2024-07-03 | 186 | 0.158 | 0.330 | 30 |
| 3 | 2025-03-01..2025-09-02 | 186 | -0.624 | -1.071 | 20 |
| 4 | 2026-05-01..2026-11-02 | 186 | -0.848 | -0.996 | 20 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **RAN** |  |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): 0.2927
- Parameter sweep stability: 1.0000
- Subperiod/regime: 2/6 profitable years
- Capacity: 3344029579 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: -0.300

### c4_volume_confirmation_futures_broad

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.23 is below 0.5, and the gross-of-costs Sharpe is -0.06 - there is NO positive edge even before costs. The signal has no exploitable expectancy in this sample; this is not a cost problem that better execution could solve.
- **pooled OOS Sharpe**: -0.229
- **in-sample Sharpe (base run)**: -0.110
- **in-sample Sharpe (last fold training)**: -0.599
- **OOS retention**: n/a
- **n_trades**: 227  **max_drawdown**: 0.4504  **total_return**: -0.2413  **cagr**: -0.0126
- **t_stat**: -0.514  **n_bars**: 5497  **PBO inversion rate**: 0.300
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=3
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `t-stat -0.51 below 2.0 - the return series is not distinguishable from noise`
- `edge does not survive 2x cost stress`
- `Monte Carlo prob(profitable) 19%`
- `only 10/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-15..2009-05-13 | 859 | 0.807 | 0.205 | 38 |
| 1 | 2010-04-29..2013-09-25 | 859 | -0.947 | 0.030 | 50 |
| 2 | 2014-09-10..2018-02-08 | 859 | -0.863 | -1.317 | 51 |
| 3 | 2019-01-25..2022-06-22 | 859 | -0.390 | -0.255 | 41 |
| 4 | 2023-06-07..2026-11-03 | 859 | -0.599 | 0.033 | 56 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **RAN** |  |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): 0.1863
- Parameter sweep stability: 0.8333
- Subperiod/regime: 10/22 profitable years
- Capacity: 21132 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: -0.110

### c4_volume_confirmation_fx_major

- **verdict**: INCONCLUSIVE
- **reasoning**: Too few trades (0) to distinguish signal from noise.
- **pooled OOS Sharpe**: n/a
- **in-sample Sharpe (base run)**: n/a
- **in-sample Sharpe (last fold training)**: n/a
- **OOS retention**: n/a
- **n_trades**: 0  **max_drawdown**: 0.0000  **total_return**: 0.0000  **cagr**: 0.0000
- **t_stat**: n/a  **n_bars**: 5680  **PBO inversion rate**: n/a
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=0
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 0 trades (need >=30)`
- `0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few`
- `edge does not survive 2x cost stress`
- `parameter stability 0% (< 60%)`
- `only 0/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-06..2009-05-19 | 896 | n/a | n/a | 0 |
| 1 | 2010-04-21..2013-09-26 | 896 | n/a | n/a | 0 |
| 2 | 2014-09-01..2018-02-08 | 896 | n/a | n/a | 0 |
| 3 | 2019-01-11..2022-06-19 | 896 | n/a | n/a | 0 |
| 4 | 2023-05-22..2026-11-03 | 896 | n/a | n/a | 0 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **ERRORED** | only 0 trades — Monte Carlo needs >=20 |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): n/a  (only 0 trades — Monte Carlo needs >=20)
- Parameter sweep stability: 0.0000
- Subperiod/regime: 0/22 profitable years
- Capacity: n/a USD (no traded symbols or zero turnover)
- Causality audit: causal=True violations=0

### c4_volume_confirmation_rates_credit

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe 0.09 is below 0.5, and the gross-of-costs Sharpe is -0.18 - there is NO positive edge even before costs. The signal has no exploitable expectancy in this sample; this is not a cost problem that better execution could solve.
- **pooled OOS Sharpe**: 0.089
- **in-sample Sharpe (base run)**: -0.301
- **in-sample Sharpe (last fold training)**: -1.323
- **OOS retention**: n/a
- **n_trades**: 126  **max_drawdown**: 0.3793  **total_return**: -0.2649  **cagr**: -0.0140
- **t_stat**: -1.406  **n_bars**: 5491  **PBO inversion rate**: 0.300
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=2
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `t-stat -1.41 below 2.0 - the return series is not distinguishable from noise`
- `only 2/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `edge does not survive 2x cost stress`
- `Monte Carlo prob(profitable) 0%`
- `only 8/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-19..2009-05-19 | 858 | -1.131 | -0.803 | 21 |
| 1 | 2010-05-04..2013-09-27 | 858 | -0.765 | -0.422 | 36 |
| 2 | 2014-09-12..2018-02-07 | 858 | -0.761 | 0.512 | 24 |
| 3 | 2019-01-24..2022-06-17 | 858 | -0.954 | 0.986 | 36 |
| 4 | 2023-06-05..2026-11-03 | 858 | -1.323 | -0.513 | 72 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **RAN** |  |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): 0.0023
- Parameter sweep stability: 1.0000
- Subperiod/regime: 8/22 profitable years
- Capacity: 8022031 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: -0.301

### c4_volume_confirmation_us_equity_style

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.11 is below 0.5, and the gross-of-costs Sharpe is -0.21 - there is NO positive edge even before costs. The signal has no exploitable expectancy in this sample; this is not a cost problem that better execution could solve.
- **pooled OOS Sharpe**: -0.111
- **in-sample Sharpe (base run)**: -0.312
- **in-sample Sharpe (last fold training)**: -0.850
- **OOS retention**: n/a
- **n_trades**: 317  **max_drawdown**: 0.2103  **total_return**: -0.2031  **cagr**: -0.0104
- **t_stat**: -1.456  **n_bars**: 5492  **PBO inversion rate**: 0.600
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=3
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `t-stat -1.46 below 2.0 - the return series is not distinguishable from noise`
- `edge does not survive 2x cost stress`
- `Monte Carlo prob(profitable) 8%`
- `only 5/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-15..2009-05-14 | 858 | -1.530 | -0.267 | 48 |
| 1 | 2010-04-30..2013-09-25 | 858 | -1.347 | 0.074 | 48 |
| 2 | 2014-09-10..2018-02-05 | 858 | -1.640 | 0.226 | 53 |
| 3 | 2019-01-22..2022-06-15 | 858 | -1.285 | 0.246 | 54 |
| 4 | 2023-06-01..2026-10-30 | 858 | -0.850 | -0.938 | 60 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **RAN** |  |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): 0.0803
- Parameter sweep stability: 0.8333
- Subperiod/regime: 5/22 profitable years
- Capacity: 740183588 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: -0.312

### c5_rsi_reversion_commodities

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.07 is below 0.5, while the gross-of-costs Sharpe is 0.01 - a real gross edge exists but it is too small to survive costs at this size and frequency.
- **pooled OOS Sharpe**: -0.072
- **in-sample Sharpe (base run)**: -0.011
- **in-sample Sharpe (last fold training)**: 0.320
- **OOS retention**: -0.225
- **n_trades**: 336  **max_drawdown**: 0.2069  **total_return**: -0.0308  **cagr**: -0.0014
- **t_stat**: -0.052  **n_bars**: 5492  **PBO inversion rate**: 0.333
- **walk-forward**: mode=purged_embargoed folds=5 purge=14 embargo=14 profitable_folds=3
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `t-stat -0.05 below 2.0 - the return series is not distinguishable from noise`
- `OOS Sharpe retains only -23% of the in-sample Sharpe (need 40%) - the edge degrades out of sample`
- `edge does not survive 2x cost stress`
- `Monte Carlo prob(profitable) 38%`
- `only 8/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-08-05..2009-05-18 | 950 | n/a | 0.115 | 63 |
| 1 | 2009-12-18..2013-09-27 | 950 | 0.930 | 0.173 | 38 |
| 2 | 2014-05-02..2018-02-09 | 950 | 0.188 | 0.169 | 94 |
| 3 | 2018-09-13..2022-06-22 | 950 | -0.089 | -0.147 | 39 |
| 4 | 2023-01-25..2026-11-03 | 950 | 0.320 | -0.464 | 68 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **RAN** |  |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): 0.3827
- Parameter sweep stability: 0.7500
- Subperiod/regime: 8/22 profitable years
- Capacity: 119349 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: -0.011

### c5_rsi_reversion_crypto

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe 0.08 is below 0.5, and the gross-of-costs Sharpe is -0.22 - there is NO positive edge even before costs. The signal has no exploitable expectancy in this sample; this is not a cost problem that better execution could solve.
- **pooled OOS Sharpe**: 0.080
- **in-sample Sharpe (base run)**: -0.304
- **in-sample Sharpe (last fold training)**: -0.572
- **OOS retention**: n/a
- **n_trades**: 10  **max_drawdown**: 0.0207  **total_return**: -0.0135  **cagr**: -0.0016
- **t_stat**: -0.884  **n_bars**: 2132  **PBO inversion rate**: n/a
- **walk-forward**: mode=purged_embargoed folds=5 purge=14 embargo=14 profitable_folds=1
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 10 trades (need >=30)`
- `t-stat -0.88 below 2.0 - the return series is not distinguishable from noise`
- `only 1/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `edge does not survive 2x cost stress`
- `parameter stability 50% (< 60%)`
- `only 1/6 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2021-05-30..2022-03-03 | 278 | n/a | n/a | 0 |
| 1 | 2022-07-31..2023-05-04 | 278 | n/a | n/a | 0 |
| 2 | 2023-09-30..2024-07-03 | 278 | n/a | n/a | 0 |
| 3 | 2024-11-29..2025-09-02 | 278 | n/a | n/a | 0 |
| 4 | 2026-01-29..2026-11-02 | 278 | -0.572 | 0.179 | 10 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **ERRORED** | only 10 trades — Monte Carlo needs >=20 |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): n/a  (only 10 trades — Monte Carlo needs >=20)
- Parameter sweep stability: 0.5000
- Subperiod/regime: 1/6 profitable years
- Capacity: 136124459293 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: -0.304

### c5_rsi_reversion_futures_broad

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.16 is below 0.5, and the gross-of-costs Sharpe is -0.07 - there is NO positive edge even before costs. The signal has no exploitable expectancy in this sample; this is not a cost problem that better execution could solve.
- **pooled OOS Sharpe**: -0.162
- **in-sample Sharpe (base run)**: -0.095
- **in-sample Sharpe (last fold training)**: 0.021
- **OOS retention**: -7.738
- **n_trades**: 550  **max_drawdown**: 0.2773  **total_return**: -0.1243  **cagr**: -0.0061
- **t_stat**: -0.442  **n_bars**: 5497  **PBO inversion rate**: 0.833
- **walk-forward**: mode=purged_embargoed folds=5 purge=14 embargo=14 profitable_folds=1
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `t-stat -0.44 below 2.0 - the return series is not distinguishable from noise`
- `only 1/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `OOS Sharpe retains only -774% of the in-sample Sharpe (need 40%) - the edge degrades out of sample`
- `edge does not survive 2x cost stress`
- `Monte Carlo prob(profitable) 16%`
- `only 9/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-08-05..2009-05-13 | 951 | n/a | 0.639 | 83 |
| 1 | 2009-12-15..2013-09-25 | 951 | 1.001 | -0.995 | 97 |
| 2 | 2014-04-30..2018-02-08 | 951 | -0.634 | -0.100 | 138 |
| 3 | 2018-09-12..2022-06-22 | 951 | -0.686 | -0.140 | 119 |
| 4 | 2023-01-25..2026-11-03 | 951 | 0.021 | -0.719 | 45 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **RAN** |  |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): 0.1650
- Parameter sweep stability: 1.0000
- Subperiod/regime: 9/22 profitable years
- Capacity: 58872 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: -0.095

### c5_rsi_reversion_fx_major

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe 0.30 is below 0.5, while the gross-of-costs Sharpe is 0.30 - a real gross edge exists but it is too small to survive costs at this size and frequency.
- **pooled OOS Sharpe**: 0.299
- **in-sample Sharpe (base run)**: 0.258
- **in-sample Sharpe (last fold training)**: -0.138
- **OOS retention**: n/a
- **n_trades**: 119  **max_drawdown**: 0.0253  **total_return**: 0.0462  **cagr**: 0.0020
- **t_stat**: 1.225  **n_bars**: 5680  **PBO inversion rate**: 0.667
- **walk-forward**: mode=purged_embargoed folds=5 purge=14 embargo=14 profitable_folds=3
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `t-stat 1.23 below 2.0 - the return series is not distinguishable from noise`
- `only 6/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-07-27..2009-05-19 | 988 | n/a | 0.742 | 23 |
| 1 | 2009-12-15..2013-09-26 | 988 | n/a | 0.440 | 8 |
| 2 | 2014-04-24..2018-02-08 | 988 | -1.240 | -0.023 | 8 |
| 3 | 2018-09-04..2022-06-19 | 988 | -1.073 | 0.101 | 40 |
| 4 | 2023-01-13..2026-11-03 | 988 | -0.138 | -0.282 | 24 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **RAN** |  |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): 0.9137
- Parameter sweep stability: 0.7500
- Subperiod/regime: 6/22 profitable years
- Capacity: n/a USD (no ADV data)
- Causality audit: causal=True violations=0
- Deflated Sharpe: 0.258

### c5_rsi_reversion_rates_credit

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe 0.07 is below 0.5, while the gross-of-costs Sharpe is 0.19 - a real gross edge exists but it is too small to survive costs at this size and frequency.
- **pooled OOS Sharpe**: 0.066
- **in-sample Sharpe (base run)**: 0.128
- **in-sample Sharpe (last fold training)**: 0.705
- **OOS retention**: 0.094
- **n_trades**: 157  **max_drawdown**: 0.0356  **total_return**: 0.0284  **cagr**: 0.0013
- **t_stat**: 0.596  **n_bars**: 5491  **PBO inversion rate**: 0.400
- **walk-forward**: mode=purged_embargoed folds=5 purge=14 embargo=14 profitable_folds=2
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `t-stat 0.60 below 2.0 - the return series is not distinguishable from noise`
- `only 2/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `OOS Sharpe retains only 9% of the in-sample Sharpe (need 40%) - the edge degrades out of sample`
- `parameter stability 25% (< 60%)`
- `Monte Carlo prob(profitable) 84%`
- `only 10/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-08-05..2009-05-19 | 950 | 0.859 | -0.047 | 20 |
| 1 | 2009-12-18..2013-09-27 | 950 | 0.509 | 0.620 | 36 |
| 2 | 2014-05-02..2018-02-07 | 950 | 0.416 | 0.147 | 60 |
| 3 | 2018-09-11..2022-06-17 | 950 | 0.371 | -1.051 | 48 |
| 4 | 2023-01-23..2026-11-03 | 950 | 0.705 | -0.874 | 24 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **RAN** |  |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): 0.8367
- Parameter sweep stability: 0.2500
- Subperiod/regime: 10/22 profitable years
- Capacity: 56383601 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: 0.128

### c5_rsi_reversion_us_equity_style

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.07 is below 0.5, and the gross-of-costs Sharpe is -0.04 - there is NO positive edge even before costs. The signal has no exploitable expectancy in this sample; this is not a cost problem that better execution could solve.
- **pooled OOS Sharpe**: -0.066
- **in-sample Sharpe (base run)**: -0.061
- **in-sample Sharpe (last fold training)**: n/a
- **OOS retention**: n/a
- **n_trades**: 24  **max_drawdown**: 0.0293  **total_return**: -0.0060  **cagr**: -0.0003
- **t_stat**: -0.285  **n_bars**: 5492  **PBO inversion rate**: n/a
- **walk-forward**: mode=purged_embargoed folds=5 purge=14 embargo=14 profitable_folds=2
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 24 trades (need >=30)`
- `t-stat -0.28 below 2.0 - the return series is not distinguishable from noise`
- `only 2/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `edge does not survive 2x cost stress`
- `Monte Carlo prob(profitable) 45%`
- `only 2/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-08-05..2009-05-14 | 950 | n/a | 0.597 | 6 |
| 1 | 2009-12-16..2013-09-25 | 950 | n/a | 0.660 | 6 |
| 2 | 2014-04-30..2018-02-05 | 950 | n/a | n/a | 0 |
| 3 | 2018-09-07..2022-06-15 | 950 | n/a | -1.040 | 6 |
| 4 | 2023-01-19..2026-10-30 | 950 | n/a | -0.029 | 6 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **RAN** |  |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): 0.4467
- Parameter sweep stability: 1.0000
- Subperiod/regime: 2/22 profitable years
- Capacity: 21140540725 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: -0.061

### c6_rebound_danger_commodities

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.33 is below 0.5, and the gross-of-costs Sharpe is -0.25 - there is NO positive edge even before costs. The signal has no exploitable expectancy in this sample; this is not a cost problem that better execution could solve.
- **pooled OOS Sharpe**: -0.327
- **in-sample Sharpe (base run)**: -0.288
- **in-sample Sharpe (last fold training)**: 0.135
- **OOS retention**: -2.414
- **n_trades**: 13  **max_drawdown**: 0.6538  **total_return**: -0.5303  **cagr**: -0.0341
- **t_stat**: -1.345  **n_bars**: 5492  **PBO inversion rate**: 0.600
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=1
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 13 trades (need >=30)`
- `t-stat -1.35 below 2.0 - the return series is not distinguishable from noise`
- `only 1/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `OOS Sharpe retains only -241% of the in-sample Sharpe (need 40%) - the edge degrades out of sample`
- `edge does not survive 2x cost stress`
- `only 10/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-16..2009-05-18 | 858 | 1.648 | -0.630 | 13 |
| 1 | 2010-05-04..2013-09-27 | 858 | 0.092 | -0.329 | 13 |
| 2 | 2014-09-12..2018-02-09 | 858 | -0.023 | -0.337 | 13 |
| 3 | 2019-01-28..2022-06-22 | 858 | 0.107 | -0.525 | 13 |
| 4 | 2023-06-07..2026-11-03 | 858 | 0.135 | 0.136 | 13 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **ERRORED** | only 13 trades — Monte Carlo needs >=20 |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): n/a  (only 13 trades — Monte Carlo needs >=20)
- Parameter sweep stability: 1.0000
- Subperiod/regime: 10/22 profitable years
- Capacity: 36590 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: -0.288

### c6_rebound_danger_crypto

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.42 is below 0.5, and the gross-of-costs Sharpe is -0.24 - there is NO positive edge even before costs. The signal has no exploitable expectancy in this sample; this is not a cost problem that better execution could solve.
- **pooled OOS Sharpe**: -0.418
- **in-sample Sharpe (base run)**: -0.409
- **in-sample Sharpe (last fold training)**: -1.033
- **OOS retention**: n/a
- **n_trades**: 30  **max_drawdown**: 0.4381  **total_return**: -0.3427  **cagr**: -0.0484
- **t_stat**: -1.191  **n_bars**: 2132  **PBO inversion rate**: 0.500
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=1
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `t-stat -1.19 below 2.0 - the return series is not distinguishable from noise`
- `only 1/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `edge does not survive 2x cost stress`
- `Monte Carlo prob(profitable) 28%`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2021-08-30..2022-03-03 | 186 | -0.159 | 0.156 | 10 |
| 1 | 2022-10-31..2023-05-04 | 186 | -0.646 | -0.027 | 10 |
| 2 | 2023-12-31..2024-07-03 | 186 | 0.058 | -1.965 | 10 |
| 3 | 2025-03-01..2025-09-02 | 186 | -1.212 | -0.215 | 10 |
| 4 | 2026-05-01..2026-11-02 | 186 | -1.033 | -0.804 | 10 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **RAN** |  |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): 0.2760
- Parameter sweep stability: 0.8750
- Subperiod/regime: 3/6 profitable years
- Capacity: 3718733678 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: -0.409

### c6_rebound_danger_futures_broad

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.16 is below 0.5, and the gross-of-costs Sharpe is -0.12 - there is NO positive edge even before costs. The signal has no exploitable expectancy in this sample; this is not a cost problem that better execution could solve.
- **pooled OOS Sharpe**: -0.160
- **in-sample Sharpe (base run)**: -0.148
- **in-sample Sharpe (last fold training)**: -0.503
- **OOS retention**: n/a
- **n_trades**: 15  **max_drawdown**: 0.5101  **total_return**: -0.3550  **cagr**: -0.0199
- **t_stat**: -0.693  **n_bars**: 5497  **PBO inversion rate**: 0.100
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=2
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 15 trades (need >=30)`
- `t-stat -0.69 below 2.0 - the return series is not distinguishable from noise`
- `only 2/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `edge does not survive 2x cost stress`
- `only 10/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-15..2009-05-13 | 859 | 0.214 | 0.095 | 14 |
| 1 | 2010-04-29..2013-09-25 | 859 | -1.169 | -0.371 | 14 |
| 2 | 2014-09-10..2018-02-08 | 859 | -1.333 | -0.860 | 15 |
| 3 | 2019-01-25..2022-06-22 | 859 | -0.797 | 0.026 | 15 |
| 4 | 2023-06-07..2026-11-03 | 859 | -0.503 | -0.117 | 15 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **ERRORED** | only 15 trades — Monte Carlo needs >=20 |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): n/a  (only 15 trades — Monte Carlo needs >=20)
- Parameter sweep stability: 1.0000
- Subperiod/regime: 10/22 profitable years
- Capacity: 29854 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: -0.148

### c6_rebound_danger_fx_major

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe -0.11 is below 0.5, and the gross-of-costs Sharpe is -0.08 - there is NO positive edge even before costs. The signal has no exploitable expectancy in this sample; this is not a cost problem that better execution could solve.
- **pooled OOS Sharpe**: -0.114
- **in-sample Sharpe (base run)**: -0.131
- **in-sample Sharpe (last fold training)**: -0.353
- **OOS retention**: n/a
- **n_trades**: 8  **max_drawdown**: 0.2012  **total_return**: -0.1397  **cagr**: -0.0067
- **t_stat**: -0.622  **n_bars**: 5680  **PBO inversion rate**: 0.700
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=2
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 8 trades (need >=30)`
- `t-stat -0.62 below 2.0 - the return series is not distinguishable from noise`
- `only 2/5 walk-forward folds profitable (edge concentrated in a few periods)`
- `edge does not survive 2x cost stress`
- `only 5/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-06..2009-05-19 | 896 | -1.608 | 0.126 | 8 |
| 1 | 2010-04-21..2013-09-26 | 896 | -0.229 | -0.144 | 8 |
| 2 | 2014-09-01..2018-02-08 | 896 | -0.443 | 0.367 | 8 |
| 3 | 2019-01-11..2022-06-19 | 896 | -0.268 | -0.758 | 8 |
| 4 | 2023-05-22..2026-11-03 | 896 | -0.353 | -0.398 | 8 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **ERRORED** | only 8 trades — Monte Carlo needs >=20 |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): n/a  (only 8 trades — Monte Carlo needs >=20)
- Parameter sweep stability: 0.8750
- Subperiod/regime: 5/22 profitable years
- Capacity: n/a USD (no ADV data)
- Causality audit: causal=True violations=0
- Deflated Sharpe: -0.131

### c6_rebound_danger_rates_credit

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe 0.12 is below 0.5, and the gross-of-costs Sharpe is -0.17 - there is NO positive edge even before costs. The signal has no exploitable expectancy in this sample; this is not a cost problem that better execution could solve.
- **pooled OOS Sharpe**: 0.123
- **in-sample Sharpe (base run)**: -0.253
- **in-sample Sharpe (last fold training)**: 0.089
- **OOS retention**: 1.392
- **n_trades**: 12  **max_drawdown**: 0.2306  **total_return**: -0.1943  **cagr**: -0.0099
- **t_stat**: -1.182  **n_bars**: 5491  **PBO inversion rate**: 0.100
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=3
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `only 12 trades (need >=30)`
- `t-stat -1.18 below 2.0 - the return series is not distinguishable from noise`
- `edge does not survive 2x cost stress`
- `only 9/22 profitable years`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-19..2009-05-19 | 858 | -0.349 | -0.161 | 12 |
| 1 | 2010-05-04..2013-09-27 | 858 | -0.349 | -0.508 | 12 |
| 2 | 2014-09-12..2018-02-07 | 858 | -0.033 | 0.156 | 12 |
| 3 | 2019-01-24..2022-06-17 | 858 | 0.195 | 1.254 | 12 |
| 4 | 2023-06-05..2026-11-03 | 858 | 0.089 | 0.187 | 12 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **ERRORED** | only 12 trades — Monte Carlo needs >=20 |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): n/a  (only 12 trades — Monte Carlo needs >=20)
- Parameter sweep stability: 1.0000
- Subperiod/regime: 9/22 profitable years
- Capacity: 14507599 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: -0.253

### c6_rebound_danger_us_equity_style

- **verdict**: REFUTED
- **reasoning**: Pooled OOS Sharpe 0.43 is below 0.5, while the gross-of-costs Sharpe is 0.34 - a real gross edge exists but it is too small to survive costs at this size and frequency.
- **pooled OOS Sharpe**: 0.429
- **in-sample Sharpe (base run)**: 0.251
- **in-sample Sharpe (last fold training)**: -0.121
- **OOS retention**: n/a
- **n_trades**: 90  **max_drawdown**: 0.0888  **total_return**: 0.1666  **cagr**: 0.0071
- **t_stat**: 1.170  **n_bars**: 5492  **PBO inversion rate**: 0.500
- **walk-forward**: mode=purged_embargoed folds=5 purge=60 embargo=60 profitable_folds=3
- **disjointness**: ok=True violations=0 failed_checks=0

**flags (verbatim)**:

- `t-stat 1.17 below 2.0 - the return series is not distinguishable from noise`

**walk-forward folds**:

| fold | test range | test bars | IS Sharpe | OOS Sharpe | OOS trades |
|---|---|---|---|---|---|
| 0 | 2005-12-15..2009-05-14 | 858 | -1.839 | 0.480 | 30 |
| 1 | 2010-04-30..2013-09-25 | 858 | -0.970 | 0.367 | 18 |
| 2 | 2014-09-10..2018-02-05 | 858 | -1.589 | -0.221 | 18 |
| 3 | 2019-01-22..2022-06-15 | 858 | -0.736 | 1.231 | 18 |
| 4 | 2023-06-01..2026-10-30 | 858 | -0.121 | -0.042 | 6 |

**robustness stages**:

| stage | status | detail |
|---|---|---|
| walk-forward OOS (purge+embargo) | **RAN** |  |
| gross-vs-net decomposition | **RAN** |  |
| cost stress | **RAN** |  |
| parameter sweep | **RAN** |  |
| Monte Carlo | **RAN** |  |
| subperiod / regime breakdown | **RAN** |  |
| capacity | **RAN** |  |
| cross-market replication | **SKIPPED** | stage key absent from the scorecard |
| causality audit | **RAN** |  |

- Monte Carlo prob(profitable): 0.8547
- Parameter sweep stability: 0.8750
- Subperiod/regime: 13/22 profitable years
- Capacity: 777099607 USD
- Causality audit: causal=True violations=0
- Deflated Sharpe: 0.251
