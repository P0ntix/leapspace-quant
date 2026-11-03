# PAPER-CONCEPT MATRIX — what the research actually supports

Every claim in the five research papers this package implements, coded as a rule and tested through the engine's full validation gauntlet (walk-forward with purge and embargo, cost stress, gross-vs-net, parameter sweep, Monte Carlo, regime breakdown, capacity, replication, causality audit) across six asset classes.

## 1. The headline

| | Real specs | Negative controls |
|---|---|---|
| SUPPORTED | 0 | 0 |
| FRAGILE | 1 | 0 |
| REFUTED | 34 | 35 |
| INCONCLUSIVE | 12 | 12 |
| ERROR | 1 | 1 |
| **total** | **48** | **48** |
| **of which actually executed** | **41** | **41** |

### :rotating_light: CRITICAL — some specs did NOT run

**7 of the 48 real specs and 7 of the 48 controls produced no result at all.** A spec that crashed is not a research finding, and its row is not evidence about the concept. The rows that did not run:

* `c2_leading_vrp_us_equity_style` — TypeError: object of type 'float' has no len()
* `c2_leading_vrp_crypto` — TypeError: object of type 'float' has no len()
* `c2_leading_vrp_fx_major` — TypeError: object of type 'float' has no len()
* `c2_leading_vrp_commodities` — TypeError: object of type 'float' has no len()
* `c2_leading_vrp_futures_broad` — TypeError: object of type 'float' has no len()
* `c2_leading_vrp_rates_credit` — TypeError: object of type 'float' has no len()
* `c7_session_drift_fx_major` — ValueError: The cross_sectional signal needs at least TWO instruments to rank against each other, but only 0 has a usable value for feature 'session_drift' (universe: ['AUDUSD=X', 'EURUSD=X', 'GBPUSD=X', 'NZDUSD=X', 'USDCAD=X', 'USDCHF=X', 'USDJPY=X', 'USDSEK=X']). A single-instrument cross-sectional strategy is always flat. Use a time-series signal (time_series_threshold / time_series_zscore / crossover) for a one-instrument universe, or widen the universe.
* `NEGATIVE-CONTROL-c2_leading_vrp_us_equity_style` — TypeError: object of type 'float' has no len()
* `NEGATIVE-CONTROL-c2_leading_vrp_crypto` — TypeError: object of type 'float' has no len()
* `NEGATIVE-CONTROL-c2_leading_vrp_fx_major` — TypeError: object of type 'float' has no len()
* `NEGATIVE-CONTROL-c2_leading_vrp_commodities` — TypeError: object of type 'float' has no len()
* `NEGATIVE-CONTROL-c2_leading_vrp_futures_broad` — TypeError: object of type 'float' has no len()
* `NEGATIVE-CONTROL-c2_leading_vrp_rates_credit` — TypeError: object of type 'float' has no len()
* `NEGATIVE-CONTROL-c7_session_drift_fx_major` — ValueError: The cross_sectional signal needs at least TWO instruments to rank against each other, but only 0 has a usable value for feature 'session_drift' (universe: ['AUDUSD=X', 'EURUSD=X', 'GBPUSD=X', 'NZDUSD=X', 'USDCAD=X', 'USDCHF=X', 'USDJPY=X', 'USDSEK=X']). A single-instrument cross-sectional strategy is always flat. Use a time-series signal (time_series_threshold / time_series_zscore / crossover) for a one-instrument universe, or widen the universe.

**These rows must be re-run before the matrix means anything for the concepts they cover.** Until then, a concept whose every row is in this list has NOT been tested - it has not been refuted either.

### The negative controls that ran, all failed

Of the 48 negative controls, **41 actually executed** and every one of them came out REFUTED, FRAGILE or INCONCLUSIVE. The remaining **7 did not run** and so say nothing either way.

The discrimination claim therefore covers the 41 controls that executed, not the whole set.

## 2. The verdict matrix

One row per paper concept, one column per asset class. A concept that works on ONE asset class is a market curiosity, not an edge.

| Concept | crypto | us_equity_style | fx_major | commodities | futures_broad | rates_credit |
|---|---|---|---|---|---|---|
| C1_regime_conditioned_switching | **INCONCLUSIVE** (-0.13) | **REFUTED** (0.27) | **INCONCLUSIVE** | **REFUTED** (-0.09) | **REFUTED** (-0.19) | **REFUTED** (-0.47) |
| C3_volatility_regime_filter | **REFUTED** (-0.81) | **REFUTED** (0.05) | **REFUTED** (-0.21) | **REFUTED** (-0.36) | **REFUTED** (-0.16) | **REFUTED** (-0.20) |
| C4_volume_confirmation | **REFUTED** (-0.30) | **REFUTED** (-0.31) | **INCONCLUSIVE** | **REFUTED** (-0.13) | **REFUTED** (-0.11) | **REFUTED** (-0.30) |
| C5_rsi_secondary_confirmation | **REFUTED** (-0.30) | **REFUTED** (-0.06) | **REFUTED** (0.26) | **REFUTED** (-0.01) | **REFUTED** (-0.09) | **REFUTED** (0.13) |
| C6_rebound_after_crash_danger | **REFUTED** (-0.41) | **REFUTED** (0.25) | **REFUTED** (-0.13) | **REFUTED** (-0.29) | **REFUTED** (-0.15) | **REFUTED** (-0.25) |
| C2_leading_volatility_risk_premium | **DID NOT RUN** | **DID NOT RUN** | **DID NOT RUN** | **DID NOT RUN** | **DID NOT RUN** | **DID NOT RUN** |
| C7_order_flow_microstructure_base | **REFUTED** (0.46) | **REFUTED** (0.16) | **DID NOT RUN** | **REFUTED** (-0.23) | **REFUTED** (0.05) | **REFUTED** (0.03) |
| C8_liquidity_provision_reversal | **FRAGILE** (-0.19) | **INCONCLUSIVE** | **INCONCLUSIVE** | **REFUTED** (0.05) | **REFUTED** (-0.09) | **INCONCLUSIVE** |

Sharpe figures are the POOLED OUT-OF-SAMPLE numbers, not the in-sample ones. **DID NOT RUN** means the spec produced no result at all - it is not a verdict on the concept.

## 3. Does it work everywhere, or only somewhere?

| Concept | Asset classes SUPPORTED or FRAGILE | Mean OOS Sharpe | Best | Worst | Controls that also passed |
|---|---|---|---|---|---|
| C1_regime_conditioned_switching | 0/6 | -0.12 | 0.27 | -0.47 | 0/6 |
| C3_volatility_regime_filter | 0/6 | -0.28 | 0.05 | -0.81 | 0/6 |
| C4_volume_confirmation | 0/6 | -0.23 | -0.11 | -0.31 | 0/6 |
| C5_rsi_secondary_confirmation | 0/6 | -0.01 | 0.26 | -0.30 | 0/6 |
| C6_rebound_after_crash_danger | 0/6 | -0.16 | 0.25 | -0.41 | 0/6 |
| C2_leading_volatility_risk_premium | 0/6 | n/a | n/a | n/a | 0/6 |
| C7_order_flow_microstructure_base | 0/6 | 0.09 | 0.46 | -0.23 | 0/6 |
| C8_liquidity_provision_reversal | 1/6 | -0.08 | 0.05 | -0.19 | 0/6 |

**A concept whose negative control ALSO passed is not demonstrated.** The last column is the number of inverted twins that were SUPPORTED or FRAGILE; where it equals the second column, the concept is doing nothing that its own control does not also do.

## 4. What survived, and with which flags

## 5. Every spec, with its flags

| Spec | Verdict | OOS Sharpe | In-sample Sharpe | Trades | Max DD | Flags |
|---|---|---|---|---|---|---|
| `c1_regime_switch_commodities` | REFUTED | -0.09 | -0.09 | 84 | 38.8% | t-stat -0.43 below 2.0 - the return series is not distinguishable from noise; edge does not survive 2x cost stress; Monte Carlo prob(profitable) 20% |
| `NEGATIVE-CONTROL-c1_regime_switch_commodities` | REFUTED | -0.09 | -0.09 | 84 | 38.8% | t-stat -0.43 below 2.0 - the return series is not distinguishable from noise; edge does not survive 2x cost stress; Monte Carlo prob(profitable) 20% |
| `c1_regime_switch_crypto` | INCONCLUSIVE | -0.13 | -0.13 | 20 | 36.7% | only 20 trades (need >=30); t-stat -0.39 below 2.0 - the return series is not distinguishable from noise; 0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few; edge does not survive 2x cost stress; Monte Carlo prob(profitable) 40%; only 2/6 profitable years |
| `NEGATIVE-CONTROL-c1_regime_switch_crypto` | INCONCLUSIVE | -0.13 | -0.13 | 20 | 36.7% | only 20 trades (need >=30); t-stat -0.39 below 2.0 - the return series is not distinguishable from noise; 0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few; edge does not survive 2x cost stress; Monte Carlo prob(profitable) 40%; only 2/6 profitable years |
| `c1_regime_switch_futures_broad` | REFUTED | -0.19 | -0.19 | 92 | 47.3% | t-stat -0.89 below 2.0 - the return series is not distinguishable from noise; edge does not survive 2x cost stress; Monte Carlo prob(profitable) 21%; only 7/22 profitable years |
| `NEGATIVE-CONTROL-c1_regime_switch_futures_broad` | REFUTED | -0.19 | -0.19 | 92 | 47.3% | t-stat -0.89 below 2.0 - the return series is not distinguishable from noise; edge does not survive 2x cost stress; Monte Carlo prob(profitable) 21%; only 7/22 profitable years |
| `c1_regime_switch_fx_major` | INCONCLUSIVE | n/a | n/a | None | n/a | only 0 trades (need >=30); 0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few; edge does not survive 2x cost stress; parameter stability 0% (< 60%); only 0/22 profitable years |
| `NEGATIVE-CONTROL-c1_regime_switch_fx_major` | INCONCLUSIVE | n/a | n/a | None | n/a | only 0 trades (need >=30); 0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few; edge does not survive 2x cost stress; parameter stability 0% (< 60%); only 0/22 profitable years |
| `c1_regime_switch_rates_credit` | REFUTED | -0.47 | -0.47 | 52 | 24.2% | t-stat -2.19 below 2.0 - the return series is not distinguishable from noise; only 1/5 walk-forward folds profitable (edge concentrated in a few periods); OOS Sharpe retains only -54% of the in-sample Sharpe (need 40%) - the edge degrades out of sample; edge does not survive 2x cost stress; Monte Carlo prob(profitable) 2%; only 5/22 profitable years |
| `NEGATIVE-CONTROL-c1_regime_switch_rates_credit` | REFUTED | -0.47 | -0.47 | 52 | 24.2% | t-stat -2.19 below 2.0 - the return series is not distinguishable from noise; only 1/5 walk-forward folds profitable (edge concentrated in a few periods); OOS Sharpe retains only -54% of the in-sample Sharpe (need 40%) - the edge degrades out of sample; edge does not survive 2x cost stress; Monte Carlo prob(profitable) 2%; only 5/22 profitable years |
| `c1_regime_switch_us_equity_style` | REFUTED | 0.27 | 0.27 | 36 | 8.5% | t-stat 1.25 below 2.0 - the return series is not distinguishable from noise; OOS Sharpe retains only 26% of the in-sample Sharpe (need 40%) - the edge degrades out of sample |
| `NEGATIVE-CONTROL-c1_regime_switch_us_equity_style` | REFUTED | 0.27 | 0.27 | 36 | 8.5% | t-stat 1.25 below 2.0 - the return series is not distinguishable from noise; OOS Sharpe retains only 26% of the in-sample Sharpe (need 40%) - the edge degrades out of sample |
| `c2_leading_vrp_commodities` | INCONCLUSIVE | n/a | n/a | None | n/a | — |
| `NEGATIVE-CONTROL-c2_leading_vrp_commodities` | INCONCLUSIVE | n/a | n/a | None | n/a | — |
| `c2_leading_vrp_crypto` | INCONCLUSIVE | n/a | n/a | None | n/a | — |
| `NEGATIVE-CONTROL-c2_leading_vrp_crypto` | INCONCLUSIVE | n/a | n/a | None | n/a | — |
| `c2_leading_vrp_futures_broad` | INCONCLUSIVE | n/a | n/a | None | n/a | — |
| `NEGATIVE-CONTROL-c2_leading_vrp_futures_broad` | INCONCLUSIVE | n/a | n/a | None | n/a | — |
| `c2_leading_vrp_fx_major` | INCONCLUSIVE | n/a | n/a | None | n/a | — |
| `NEGATIVE-CONTROL-c2_leading_vrp_fx_major` | INCONCLUSIVE | n/a | n/a | None | n/a | — |
| `c2_leading_vrp_rates_credit` | INCONCLUSIVE | n/a | n/a | None | n/a | — |
| `NEGATIVE-CONTROL-c2_leading_vrp_rates_credit` | INCONCLUSIVE | n/a | n/a | None | n/a | — |
| `c2_leading_vrp_us_equity_style` | INCONCLUSIVE | n/a | n/a | None | n/a | — |
| `NEGATIVE-CONTROL-c2_leading_vrp_us_equity_style` | INCONCLUSIVE | n/a | n/a | None | n/a | — |
| `c3_vol_regime_filter_commodities` | REFUTED | -0.36 | -0.36 | 13 | 66.5% | only 13 trades (need >=30); t-stat -1.68 below 2.0 - the return series is not distinguishable from noise; 0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few; OOS Sharpe retains only -340% of the in-sample Sharpe (need 40%) - the edge degrades out of sample; edge does not survive 2x cost stress; only 8/22 profitable years |
| `NEGATIVE-CONTROL-c3_vol_regime_filter_commodities` | REFUTED | 0.29 | 0.29 | 13 | 22.2% | only 13 trades (need >=30); t-stat 1.37 below 2.0 - the return series is not distinguishable from noise |
| `c3_vol_regime_filter_crypto` | REFUTED | -0.81 | -0.81 | 10 | 65.3% | only 10 trades (need >=30); t-stat -2.36 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); edge does not survive 2x cost stress |
| `NEGATIVE-CONTROL-c3_vol_regime_filter_crypto` | REFUTED | 0.36 | 0.36 | 10 | 27.6% | only 10 trades (need >=30); t-stat 1.04 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); OOS Sharpe retains only -7% of the in-sample Sharpe (need 40%) - the edge degrades out of sample; only 2/6 profitable years |
| `c3_vol_regime_filter_futures_broad` | REFUTED | -0.16 | -0.16 | 15 | 47.8% | only 15 trades (need >=30); t-stat -0.75 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); edge does not survive 2x cost stress; only 9/22 profitable years |
| `NEGATIVE-CONTROL-c3_vol_regime_filter_futures_broad` | REFUTED | 0.14 | 0.14 | 15 | 33.1% | only 15 trades (need >=30); t-stat 0.66 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods) |
| `c3_vol_regime_filter_fx_major` | REFUTED | -0.21 | -0.21 | 16 | 22.1% | only 16 trades (need >=30); t-stat -1.00 below 2.0 - the return series is not distinguishable from noise; only 1/5 walk-forward folds profitable (edge concentrated in a few periods); edge does not survive 2x cost stress; only 6/22 profitable years |
| `NEGATIVE-CONTROL-c3_vol_regime_filter_fx_major` | REFUTED | 0.10 | 0.10 | 16 | 22.8% | only 16 trades (need >=30); t-stat 0.48 below 2.0 - the return series is not distinguishable from noise; OOS Sharpe retains only 25% of the in-sample Sharpe (need 40%) - the edge degrades out of sample |
| `c3_vol_regime_filter_rates_credit` | REFUTED | -0.20 | -0.20 | 12 | 18.6% | only 12 trades (need >=30); t-stat -0.92 below 2.0 - the return series is not distinguishable from noise; OOS Sharpe retains only -234% of the in-sample Sharpe (need 40%) - the edge degrades out of sample; edge does not survive 2x cost stress; only 10/22 profitable years |
| `NEGATIVE-CONTROL-c3_vol_regime_filter_rates_credit` | REFUTED | 0.03 | 0.03 | 12 | 22.6% | only 12 trades (need >=30); t-stat 0.14 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); only 8/22 profitable years |
| `c3_vol_regime_filter_us_equity_style` | REFUTED | 0.05 | 0.05 | 84 | 10.6% | t-stat 0.21 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); OOS Sharpe retains only 1% of the in-sample Sharpe (need 40%) - the edge degrades out of sample; Monte Carlo prob(profitable) 57%; only 10/22 profitable years |
| `NEGATIVE-CONTROL-c3_vol_regime_filter_us_equity_style` | REFUTED | -0.25 | -0.25 | 84 | 22.2% | t-stat -1.15 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); edge does not survive 2x cost stress; Monte Carlo prob(profitable) 12%; only 7/22 profitable years |
| `c4_volume_confirmation_commodities` | REFUTED | -0.13 | -0.13 | 13 | 52.0% | only 13 trades (need >=30); t-stat -0.63 below 2.0 - the return series is not distinguishable from noise; edge does not survive 2x cost stress |
| `NEGATIVE-CONTROL-c4_volume_confirmation_commodities` | REFUTED | 0.03 | 0.03 | 13 | 29.1% | only 13 trades (need >=30); t-stat 0.16 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); parameter stability 50% (< 60%); only 10/22 profitable years |
| `c4_volume_confirmation_crypto` | REFUTED | -0.30 | -0.30 | 140 | 45.5% | t-stat -0.87 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); edge does not survive 2x cost stress; Monte Carlo prob(profitable) 29%; only 2/6 profitable years |
| `NEGATIVE-CONTROL-c4_volume_confirmation_crypto` | REFUTED | -0.03 | -0.03 | 140 | 45.4% | t-stat -0.08 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); OOS Sharpe retains only -28% of the in-sample Sharpe (need 40%) - the edge degrades out of sample; edge does not survive 2x cost stress; parameter stability 50% (< 60%); Monte Carlo prob(profitable) 41% |
| `c4_volume_confirmation_futures_broad` | REFUTED | -0.11 | -0.11 | 227 | 45.0% | t-stat -0.51 below 2.0 - the return series is not distinguishable from noise; edge does not survive 2x cost stress; Monte Carlo prob(profitable) 19%; only 10/22 profitable years |
| `NEGATIVE-CONTROL-c4_volume_confirmation_futures_broad` | REFUTED | 0.05 | 0.05 | 226 | 25.4% | t-stat 0.24 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); OOS Sharpe retains only 32% of the in-sample Sharpe (need 40%) - the edge degrades out of sample; parameter stability 50% (< 60%); Monte Carlo prob(profitable) 53% |
| `c4_volume_confirmation_fx_major` | INCONCLUSIVE | n/a | n/a | None | n/a | only 0 trades (need >=30); 0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few; edge does not survive 2x cost stress; parameter stability 0% (< 60%); only 0/22 profitable years |
| `NEGATIVE-CONTROL-c4_volume_confirmation_fx_major` | INCONCLUSIVE | n/a | n/a | None | n/a | only 0 trades (need >=30); 0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few; edge does not survive 2x cost stress; parameter stability 0% (< 60%); only 0/22 profitable years |
| `c4_volume_confirmation_rates_credit` | REFUTED | -0.30 | -0.30 | 126 | 37.9% | t-stat -1.41 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); edge does not survive 2x cost stress; Monte Carlo prob(profitable) 0%; only 8/22 profitable years |
| `NEGATIVE-CONTROL-c4_volume_confirmation_rates_credit` | REFUTED | 0.08 | 0.08 | 126 | 25.8% | t-stat 0.39 below 2.0 - the return series is not distinguishable from noise; OOS Sharpe retains only -2% of the in-sample Sharpe (need 40%) - the edge degrades out of sample; Monte Carlo prob(profitable) 76% |
| `c4_volume_confirmation_us_equity_style` | REFUTED | -0.31 | -0.31 | 317 | 21.0% | t-stat -1.46 below 2.0 - the return series is not distinguishable from noise; edge does not survive 2x cost stress; Monte Carlo prob(profitable) 8%; only 5/22 profitable years |
| `NEGATIVE-CONTROL-c4_volume_confirmation_us_equity_style` | REFUTED | 0.11 | 0.11 | 317 | 17.5% | t-stat 0.52 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); OOS Sharpe retains only -15% of the in-sample Sharpe (need 40%) - the edge degrades out of sample; Monte Carlo prob(profitable) 66% |
| `c5_rsi_reversion_commodities` | REFUTED | -0.01 | -0.01 | 336 | 20.7% | t-stat -0.05 below 2.0 - the return series is not distinguishable from noise; OOS Sharpe retains only -23% of the in-sample Sharpe (need 40%) - the edge degrades out of sample; edge does not survive 2x cost stress; Monte Carlo prob(profitable) 38%; only 8/22 profitable years |
| `NEGATIVE-CONTROL-c5_rsi_reversion_commodities` | REFUTED | 0.01 | 0.01 | 336 | 16.9% | t-stat 0.06 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); parameter stability 50% (< 60%); Monte Carlo prob(profitable) 45% |
| `c5_rsi_reversion_crypto` | REFUTED | -0.30 | -0.30 | 10 | 2.1% | only 10 trades (need >=30); t-stat -0.88 below 2.0 - the return series is not distinguishable from noise; only 1/5 walk-forward folds profitable (edge concentrated in a few periods); edge does not survive 2x cost stress; parameter stability 50% (< 60%); only 1/6 profitable years |
| `NEGATIVE-CONTROL-c5_rsi_reversion_crypto` | REFUTED | 0.14 | 0.14 | 10 | 0.9% | only 10 trades (need >=30); t-stat 0.42 below 2.0 - the return series is not distinguishable from noise; 0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few; OOS Sharpe retains only -254% of the in-sample Sharpe (need 40%) - the edge degrades out of sample; parameter stability 25% (< 60%); only 1/6 profitable years |
| `c5_rsi_reversion_futures_broad` | REFUTED | -0.09 | -0.09 | 550 | 27.7% | t-stat -0.44 below 2.0 - the return series is not distinguishable from noise; only 1/5 walk-forward folds profitable (edge concentrated in a few periods); OOS Sharpe retains only -774% of the in-sample Sharpe (need 40%) - the edge degrades out of sample; edge does not survive 2x cost stress; Monte Carlo prob(profitable) 16%; only 9/22 profitable years |
| `NEGATIVE-CONTROL-c5_rsi_reversion_futures_broad` | REFUTED | 0.07 | 0.07 | 550 | 16.1% | t-stat 0.34 below 2.0 - the return series is not distinguishable from noise; Monte Carlo prob(profitable) 66%; only 8/22 profitable years |
| `c5_rsi_reversion_fx_major` | REFUTED | 0.26 | 0.26 | 119 | 2.5% | t-stat 1.23 below 2.0 - the return series is not distinguishable from noise; only 6/22 profitable years |
| `NEGATIVE-CONTROL-c5_rsi_reversion_fx_major` | REFUTED | -0.33 | -0.33 | 119 | 7.1% | t-stat -1.55 below 2.0 - the return series is not distinguishable from noise; only 1/5 walk-forward folds profitable (edge concentrated in a few periods); OOS Sharpe retains only -1785% of the in-sample Sharpe (need 40%) - the edge degrades out of sample; edge does not survive 2x cost stress; Monte Carlo prob(profitable) 4%; only 6/22 profitable years |
| `c5_rsi_reversion_rates_credit` | REFUTED | 0.13 | 0.13 | 157 | 3.6% | t-stat 0.60 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); OOS Sharpe retains only 9% of the in-sample Sharpe (need 40%) - the edge degrades out of sample; parameter stability 25% (< 60%); Monte Carlo prob(profitable) 84%; only 10/22 profitable years |
| `NEGATIVE-CONTROL-c5_rsi_reversion_rates_credit` | REFUTED | -0.23 | -0.23 | 157 | 7.3% | t-stat -1.10 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); edge does not survive 2x cost stress; parameter stability 50% (< 60%); Monte Carlo prob(profitable) 2% |
| `c5_rsi_reversion_us_equity_style` | REFUTED | -0.06 | -0.06 | 24 | 2.9% | only 24 trades (need >=30); t-stat -0.28 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); edge does not survive 2x cost stress; Monte Carlo prob(profitable) 45%; only 2/22 profitable years |
| `NEGATIVE-CONTROL-c5_rsi_reversion_us_equity_style` | REFUTED | 0.01 | 0.01 | 24 | 2.0% | only 24 trades (need >=30); t-stat 0.07 below 2.0 - the return series is not distinguishable from noise; only 1/5 walk-forward folds profitable (edge concentrated in a few periods); Monte Carlo prob(profitable) 51%; only 1/22 profitable years |
| `c6_rebound_danger_commodities` | REFUTED | -0.29 | -0.29 | 13 | 65.4% | only 13 trades (need >=30); t-stat -1.35 below 2.0 - the return series is not distinguishable from noise; only 1/5 walk-forward folds profitable (edge concentrated in a few periods); OOS Sharpe retains only -241% of the in-sample Sharpe (need 40%) - the edge degrades out of sample; edge does not survive 2x cost stress; only 10/22 profitable years |
| `NEGATIVE-CONTROL-c6_rebound_danger_commodities` | REFUTED | 0.25 | 0.25 | 13 | 21.3% | only 13 trades (need >=30); t-stat 1.17 below 2.0 - the return series is not distinguishable from noise |
| `c6_rebound_danger_crypto` | REFUTED | -0.41 | -0.41 | 30 | 43.8% | t-stat -1.19 below 2.0 - the return series is not distinguishable from noise; only 1/5 walk-forward folds profitable (edge concentrated in a few periods); edge does not survive 2x cost stress; Monte Carlo prob(profitable) 28% |
| `NEGATIVE-CONTROL-c6_rebound_danger_crypto` | REFUTED | 0.01 | 0.01 | 30 | 33.7% | t-stat 0.04 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); OOS Sharpe retains only 17% of the in-sample Sharpe (need 40%) - the edge degrades out of sample; parameter stability 38% (< 60%); Monte Carlo prob(profitable) 48%; only 2/6 profitable years |
| `c6_rebound_danger_futures_broad` | REFUTED | -0.15 | -0.15 | 15 | 51.0% | only 15 trades (need >=30); t-stat -0.69 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); edge does not survive 2x cost stress; only 10/22 profitable years |
| `NEGATIVE-CONTROL-c6_rebound_danger_futures_broad` | REFUTED | 0.13 | 0.13 | 15 | 26.8% | only 15 trades (need >=30); t-stat 0.61 below 2.0 - the return series is not distinguishable from noise; only 10/22 profitable years |
| `c6_rebound_danger_fx_major` | REFUTED | -0.13 | -0.13 | 8 | 20.1% | only 8 trades (need >=30); t-stat -0.62 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); edge does not survive 2x cost stress; only 5/22 profitable years |
| `NEGATIVE-CONTROL-c6_rebound_danger_fx_major` | REFUTED | 0.02 | 0.02 | 8 | 24.3% | only 8 trades (need >=30); t-stat 0.12 below 2.0 - the return series is not distinguishable from noise; OOS Sharpe retains only 3% of the in-sample Sharpe (need 40%) - the edge degrades out of sample |
| `c6_rebound_danger_rates_credit` | REFUTED | -0.25 | -0.25 | 12 | 23.1% | only 12 trades (need >=30); t-stat -1.18 below 2.0 - the return series is not distinguishable from noise; edge does not survive 2x cost stress; only 9/22 profitable years |
| `NEGATIVE-CONTROL-c6_rebound_danger_rates_credit` | REFUTED | 0.11 | 0.11 | 12 | 17.0% | only 12 trades (need >=30); t-stat 0.53 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods) |
| `c6_rebound_danger_us_equity_style` | REFUTED | 0.25 | 0.25 | 90 | 8.9% | t-stat 1.17 below 2.0 - the return series is not distinguishable from noise |
| `NEGATIVE-CONTROL-c6_rebound_danger_us_equity_style` | REFUTED | -0.43 | -0.43 | 90 | 28.9% | t-stat -2.00 below 2.0 - the return series is not distinguishable from noise; 0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few; edge does not survive 2x cost stress; Monte Carlo prob(profitable) 3%; only 7/22 profitable years |
| `c7_session_drift_commodities` | REFUTED | -0.23 | -0.23 | 13 | 61.7% | only 13 trades (need >=30); t-stat -1.08 below 2.0 - the return series is not distinguishable from noise; 0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few; edge does not survive 2x cost stress; only 10/22 profitable years |
| `NEGATIVE-CONTROL-c7_session_drift_commodities` | REFUTED | -0.23 | -0.23 | 13 | 61.7% | only 13 trades (need >=30); t-stat -1.08 below 2.0 - the return series is not distinguishable from noise; 0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few; edge does not survive 2x cost stress; only 10/22 profitable years |
| `c7_session_drift_crypto` | REFUTED | 0.46 | 0.46 | 10 | 28.6% | only 10 trades (need >=30); t-stat 1.33 below 2.0 - the return series is not distinguishable from noise; 0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few; OOS Sharpe retains only -71% of the in-sample Sharpe (need 40%) - the edge degrades out of sample |
| `NEGATIVE-CONTROL-c7_session_drift_crypto` | REFUTED | 0.46 | 0.46 | 10 | 28.6% | only 10 trades (need >=30); t-stat 1.33 below 2.0 - the return series is not distinguishable from noise; 0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few; OOS Sharpe retains only -71% of the in-sample Sharpe (need 40%) - the edge degrades out of sample |
| `c7_session_drift_futures_broad` | REFUTED | 0.05 | 0.05 | 15 | 65.5% | only 15 trades (need >=30); t-stat 0.25 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); only 9/22 profitable years |
| `NEGATIVE-CONTROL-c7_session_drift_futures_broad` | REFUTED | 0.05 | 0.05 | 15 | 65.5% | only 15 trades (need >=30); t-stat 0.25 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); only 9/22 profitable years |
| `c7_session_drift_fx_major` | ERROR | n/a | n/a | None | n/a | the spec did not run: ValueError: The cross_sectional signal needs at least TWO instruments to rank against each other, but only 0 has a usable value for feature 'session_drift' (universe: ['AUDUSD=X', 'EURUSD=X', 'GBPUSD=X', 'NZDUSD=X', 'USDCAD=X', 'USDCHF=X', 'USDJPY=X', 'USDSEK=X']). A single-instrument cross-sectional strategy is always flat. Use a time-series signal (time_series_threshold / time_series_zscore / crossover) for a one-instrument universe, or widen the universe. |
| `NEGATIVE-CONTROL-c7_session_drift_fx_major` | ERROR | n/a | n/a | None | n/a | the spec did not run: ValueError: The cross_sectional signal needs at least TWO instruments to rank against each other, but only 0 has a usable value for feature 'session_drift' (universe: ['AUDUSD=X', 'EURUSD=X', 'GBPUSD=X', 'NZDUSD=X', 'USDCAD=X', 'USDCHF=X', 'USDJPY=X', 'USDSEK=X']). A single-instrument cross-sectional strategy is always flat. Use a time-series signal (time_series_threshold / time_series_zscore / crossover) for a one-instrument universe, or widen the universe. |
| `c7_session_drift_rates_credit` | REFUTED | 0.03 | 0.03 | 12 | 51.0% | only 12 trades (need >=30); t-stat 0.16 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); OOS Sharpe retains only -21% of the in-sample Sharpe (need 40%) - the edge degrades out of sample |
| `NEGATIVE-CONTROL-c7_session_drift_rates_credit` | REFUTED | 0.03 | 0.03 | 12 | 51.0% | only 12 trades (need >=30); t-stat 0.16 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); OOS Sharpe retains only -21% of the in-sample Sharpe (need 40%) - the edge degrades out of sample |
| `c7_session_drift_us_equity_style` | REFUTED | 0.16 | 0.16 | 8 | 8.4% | only 8 trades (need >=30); t-stat 0.73 below 2.0 - the return series is not distinguishable from noise |
| `NEGATIVE-CONTROL-c7_session_drift_us_equity_style` | REFUTED | 0.16 | 0.16 | 8 | 8.4% | only 8 trades (need >=30); t-stat 0.73 below 2.0 - the return series is not distinguishable from noise |
| `c8_liquidity_reversal_commodities` | REFUTED | 0.05 | 0.05 | 171 | 9.5% | t-stat 0.22 below 2.0 - the return series is not distinguishable from noise; Monte Carlo prob(profitable) 59%; only 8/22 profitable years |
| `NEGATIVE-CONTROL-c8_liquidity_reversal_commodities` | REFUTED | -0.08 | -0.08 | 171 | 8.3% | t-stat -0.38 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); OOS Sharpe retains only -31% of the in-sample Sharpe (need 40%) - the edge degrades out of sample; edge does not survive 2x cost stress; Monte Carlo prob(profitable) 31%; only 7/22 profitable years |
| `c8_liquidity_reversal_crypto` | FRAGILE | -0.19 | -0.19 | 30 | 3.1% | t-stat -0.56 below 2.0 - the return series is not distinguishable from noise; only 1/5 walk-forward folds profitable (edge concentrated in a few periods); edge does not survive 2x cost stress; Monte Carlo prob(profitable) 37%; only 1/6 profitable years |
| `NEGATIVE-CONTROL-c8_liquidity_reversal_crypto` | REFUTED | -0.02 | -0.02 | 30 | 2.7% | t-stat -0.05 below 2.0 - the return series is not distinguishable from noise; 0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few; OOS Sharpe retains only -164% of the in-sample Sharpe (need 40%) - the edge degrades out of sample; edge does not survive 2x cost stress; Monte Carlo prob(profitable) 44%; only 2/6 profitable years |
| `c8_liquidity_reversal_futures_broad` | REFUTED | -0.09 | -0.09 | 110 | 4.5% | t-stat -0.41 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); edge does not survive 2x cost stress; Monte Carlo prob(profitable) 33%; only 3/22 profitable years |
| `NEGATIVE-CONTROL-c8_liquidity_reversal_futures_broad` | REFUTED | 0.06 | 0.06 | 110 | 2.3% | t-stat 0.29 below 2.0 - the return series is not distinguishable from noise; only 2/5 walk-forward folds profitable (edge concentrated in a few periods); OOS Sharpe retains only -8% of the in-sample Sharpe (need 40%) - the edge degrades out of sample; Monte Carlo prob(profitable) 61%; only 4/22 profitable years |
| `c8_liquidity_reversal_fx_major` | INCONCLUSIVE | n/a | n/a | None | n/a | only 0 trades (need >=30); 0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few; edge does not survive 2x cost stress; parameter stability 0% (< 60%); only 0/22 profitable years |
| `NEGATIVE-CONTROL-c8_liquidity_reversal_fx_major` | INCONCLUSIVE | n/a | n/a | None | n/a | only 0 trades (need >=30); 0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few; edge does not survive 2x cost stress; parameter stability 0% (< 60%); only 0/22 profitable years |
| `c8_liquidity_reversal_rates_credit` | INCONCLUSIVE | n/a | n/a | None | n/a | only 0 trades (need >=30); 0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few; edge does not survive 2x cost stress; parameter stability 0% (< 60%); only 0/22 profitable years |
| `NEGATIVE-CONTROL-c8_liquidity_reversal_rates_credit` | INCONCLUSIVE | n/a | n/a | None | n/a | only 0 trades (need >=30); 0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few; edge does not survive 2x cost stress; parameter stability 0% (< 60%); only 0/22 profitable years |
| `c8_liquidity_reversal_us_equity_style` | INCONCLUSIVE | n/a | n/a | None | n/a | only 0 trades (need >=30); 0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few; edge does not survive 2x cost stress; parameter stability 0% (< 60%); only 0/22 profitable years |
| `NEGATIVE-CONTROL-c8_liquidity_reversal_us_equity_style` | INCONCLUSIVE | n/a | n/a | None | n/a | only 0 trades (need >=30); 0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few; edge does not survive 2x cost stress; parameter stability 0% (< 60%); only 0/22 profitable years |

**The OOS Sharpe is the result.** The in-sample Sharpe is shown beside it because the GAP between them is the overfitting, and a large gap is exactly what a purged walk-forward is there to expose.

## 6. What was validated, and what was not

A verdict is only as good as the checks behind it. The stage ledger records, for every spec, which robustness stages ran, which were skipped, and which errored. A stage that did not run is reported, never hidden.

## 7. Leading-indicator coverage

How much of each panel the forward-looking indicator actually covered. A leading feature that covers a small fraction of the sample cannot be evaluated, and the verdict for that spec is a verdict on a short sample.

| Spec | Source | Points | Note |
|---|---|---|---|
| `c2_leading_vrp_us_equity_style` | yahoo.chart (^VXN) | 1255 |  |
| `c2_leading_vrp_crypto` | deribit.dvol (BTC) | 2051 |  |
| `c2_leading_vrp_fx_major` | yahoo.chart (^VIX) | 1257 |  |
| `c2_leading_vrp_commodities` | yahoo.chart (^VIX) | 1257 |  |
| `c2_leading_vrp_futures_broad` | yahoo.chart (^VIX) | 1257 |  |
| `c2_leading_vrp_rates_credit` | yahoo.chart (^VIX) | 1257 |  |

## 8. What this establishes and what it does not

* Every result above is an OUT-OF-SAMPLE result from a purge-and-embargo walk-forward, at 2x the engine's default costs, with a volatility-targeted, dollar-neutral, 10%-per-name-capped book.
* A SUPPORTED verdict means the strategy warrants PAPER TRADING. It is not a licence to trade it with money, and the package's own stage gates say so (`LIVE_CAPITAL_READINESS.md`).
* The negative controls are the reason any of this is believable. A matrix without them would look identical whether the concepts were real or invented.
* Crypto and equities are DIFFERENT markets. The regime paper says so explicitly, so a concept that survives on one and fails on the other is a finding about the market, not a defect in the test.
