# LeapSpace Quant — consolidated report

Generated: 2026-10-27T15:58:20.882317+00:00

> All figures below are computed from LIVE sources at run time unless the entry says otherwise. Sources that could not be reached are listed as gaps; no data was substituted for them.

## 1. Market regime

- **Symbol:** QQQ
- **State labels:** `{"3": "tranquil_uptrend", "2": "range_chop", "1": "regular_bear", "0": "crash_rebound"}`
- **State share:** `{"range_chop": 0.268, "tranquil_uptrend": 0.22, "regular_bear": 0.275, "crash_rebound": 0.237}`
- **Current state:** `range_chop`
- **HMM convergence:** True in 3 iterations
- **Bars used:** 1195 of 1255 (60 in warm-up)
- **Provenance:** Cached data — originally fetched 2026-10-27T15:36:02+00:00 from yahoo.chart (https://query1.finance.yahoo.com/v8/finance/chart/QQQ?range=5y&interval=1d&includeAdjustedClose=true). HTTP 200 Served from local cache; upstream not re-contacted.; 1255 bars 2021-10-27..2026-10-27

> **Limitation:** the HMM's parameters are fitted on the whole panel, so the regime *classification* is in-sample even though the filter itself is causal. A walk-forward refit is the next step.

## 2. Dealer gamma exposure and option flow

- **Underlying:** QQQ
- **Spot:** 719.65 (as of OCT 27, 2026 11:36 AM ET)
- **Net gamma:** 71345.519 → **positive_gamma_damping**
- **Call / put gamma:** -144304.236 / 215649.755
- **Max-pain strike:** 680.0  ·  **Zero-gamma strike:** 320.0
- **Put/call volume ratio:** 0.881
- **Net delta flow:** -155227.777  ·  **net vega flow:** 17419.854

**Paper read:** Positive net gamma: hedging flows tend to damp moves. Paper guidance: treat as a mean-reversion/pinning regime; fade extensions, use passive execution, smaller targets.

**Caveats that apply to every number above:**
- Dealer positioning is ASSUMED from customer-side open interest: customers net long calls and net long puts, so dealers are short calls and long puts. Open interest alone cannot verify this.
- Gamma is Black-Scholes with a flat volatility surface per contract; real smiles and smirks bias these estimates (paper ref 25).
- IV is derived from last-trade prices where available and is APPROXIMATE; some contracts have no usable quote and are excluded.
- Expiry year inference assumes the next occurrence of the stated month.
- Option flow (pressure) and gamma (amplification) are independent axes. The papers state them separately and do not provide a calibrated joint rule, so no combined directional call is made here.

## 3. Backtests — the paper-derived strategies

| Strategy | Paper | Verdict | Validation | Trades | Sharpe | OOS Sharpe | OOS folds |
|---|---|---|---|---|---|---|---|
| `regime_switch_momentum_reversal_us_equity` | Financial market regime identification (LeapSpace) | **REFUTED** | --quick | 80 | 0.027 | -0.081 | 1/5 |
| `regime_switch_momentum_reversal_nasdaq_scalp_proxy` | NASDAQ market regime identification (LeapSpace) | **REFUTED** | --quick | 637 | -0.124 | 0.125 | 4/5 |
| `regime_switch_cross_sectional_sector_rotation` | Financial market regime identification (LeapSpace) | **SUPPORTED** | FULL gauntlet | 2089 | 0.611 | 0.528 | 5/5 |
| `v1_crypto_momentum_20d_ma` | Trading strategies for retail traders (LeapSpace v1) | **FRAGILE** | FULL gauntlet | 1328 | 0.747 | 0.783 | 3/5 |
| `v1_nasdaq_12m_tsm_vol_scaled` | Trading strategies for retail traders (LeapSpace v1) | **REFUTED** | --quick | 166 | -0.097 | -0.384 | 0/5 |
| `v1_sd_band_mean_reversion_1_0_1_5` | Trading strategies for retail traders (LeapSpace v1) | **REFUTED** | --quick | 496 | 0.365 | 0.289 | 4/5 |
| `tradingview_price_volume_rsi_regime_filtered` | Free trading indicators for directional edge (LeapSpace) | **REFUTED** | --quick | 179 | 0.398 | 0.328 | 5/5 |
| `crypto_ma20_trend_momentum` | Trading strategies for retail traders (LeapSpace 2.0) | **REFUTED** | --quick | 1169 | 0.484 | 0.327 | 2/5 |
| `nasdaq_12m_timeseries_momentum` | Trading strategies for retail traders (LeapSpace 2.0) | **SUPPORTED** | FULL gauntlet | 71 | 0.630 | 0.898 | 4/5 |
| `sd_band_mean_reversion_crypto` | Trading strategies for retail traders (LeapSpace 2.0) | **REFUTED** | --quick | 974 | -0.661 | -0.553 | 2/5 |
| `bollinger20_2_breakout_crypto` | Trading strategies for retail traders (LeapSpace 2.0) | **REFUTED** | --quick | 654 | 0.663 | 0.432 | 3/5 |
| `crypto_xs_momentum_volume_confirmed` | Trading strategies for retail traders (LeapSpace 2.0) | **REFUTED** | --quick | 2018 | -0.210 | -0.149 | 2/5 |
| `crypto_rsi_oversold_fade` | Trading strategies for retail traders (LeapSpace 2.0) | **REFUTED** | --quick | 636 | 0.471 | 0.285 | 4/5 |

**Validation note:** Rows marked 'FULL gauntlet' carry the stricter verdict from a complete validation run. Rows without the marker were run with --quick, which skips Monte Carlo, the parameter sweep and replication — their verdict is a preliminary read for those stages.

### Intake gate

The backtest lab's intake gate ran on every spec. It compares each probed condition against the engine's defaults and refuses a spec with an unanswered condition. A condition whose value coincides with an engine default is recorded below as an **accepted default** — the decision was made deliberately and is documented in the spec's `parameter_provenance`, so the gate records the decision instead of reading it as an open question.

| Strategy | Gate | Conditions accepted as engine defaults |
|---|---|---|
| `regime_switch_momentum_reversal_us_equity` | PASS | `universe`, `direction`, `exit`, `costs` |
| `regime_switch_momentum_reversal_nasdaq_scalp_proxy` | PASS | `direction`, `exit`, `costs` |
| `regime_switch_cross_sectional_sector_rotation` | PASS | `exit`, `costs` |
| `v1_crypto_momentum_20d_ma` | PASS | `costs` |
| `v1_nasdaq_12m_tsm_vol_scaled` | PASS | `direction`, `exit`, `rebalance`, `costs` |
| `v1_sd_band_mean_reversion_1_0_1_5` | PASS | `universe`, `costs` |
| `tradingview_price_volume_rsi_regime_filtered` | PASS | `universe`, `exit`, `costs` |
| `crypto_ma20_trend_momentum` | PASS | `costs` |
| `nasdaq_12m_timeseries_momentum` | PASS | `rebalance`, `costs` |
| `sd_band_mean_reversion_crypto` | PASS | `direction`, `costs` |
| `bollinger20_2_breakout_crypto` | PASS | `costs` |
| `crypto_xs_momentum_volume_confirmed` | PASS | `direction`, `exit`, `costs` |
| `crypto_rsi_oversold_fade` | PASS | `costs` |

### `regime_switch_momentum_reversal_us_equity`

**Verdict: REFUTED** — REFUTED — the edge did not survive out-of-sample testing and/or cost stress. See the flags for what specifically killed it.

Flags:
- t-stat 0.13 below 2.0 - the return series is not distinguishable from noise
- only 1/5 walk-forward folds profitable (edge concentrated in a few periods)
- OOS Sharpe retains only -10% of the in-sample Sharpe (need 40%) - the edge degrades out of sample
- edge does not survive 2x cost stress
- parameter stability 0% (< 60%)

**Stages NOT run:** montecarlo, sweep, replication. This was a partial validation; the verdict is a preliminary read for those stages.

Parameter provenance:

| Parameter | Source | Note |
|---|---|---|
| `hypothesis` | paper | Financial market regime identification (LeapSpace), 'Best general edge' |
| `universe` | analyst_choice | The paper names 'Equities, broad indices, crypto'. us_equity_broad (SPY, VTI, IVV, RSP) is a liquid, survivor-bias-free ETF set chosen for a cross-sectional test. |
| `n_states` | paper | '3-5 latent states, not bull/bear'; 4 chosen because the paper also cites a four-state HMM as optimal in one S&P 500 application |
| `momentum_lookback` | analyst_choice | The paper names 'medium-horizon return or moving-trend feature' without a window. 60 trading days ≈ one quarter, the conventional medium-horizon definition. NOT stated in the paper. |
| `reversal_lookback` | analyst_choice | The paper cites short-term reversal and warns it decays quickly and may vanish after costs, but gives no window. 5 trading days is a choice. |
| `rebalance` | analyst_choice | The paper does not specify a rebalance cadence. Weekly chosen to avoid the turnover that destroys short-horizon reversal after costs. |
| `gross_leverage` | analyst_choice | 1.0 (no leverage) chosen as the neutral default for a switching test. |
| `max_position` | analyst_choice | 25% per name on a 4-symbol universe. |
| `costs` | engine_default | The skill's DEFAULT_COSTS per asset class (US ETF), scaled by cost_multiplier=1.0. |
| `period` | analyst_choice | 2005-01-01 onward, to cover the 2008 crisis, the 2020 COVID crash and 2022 bear market — the paper's own examples of stress regimes. SPY history starts 1993, so this leaves a long sample. |
| `variants_tried` | analyst_choice | 1 — this is the first parameterisation; no tuning was performed before the run. |
| `direction` | analyst_choice | Long/short market timing. The signal emits a signed value in [-1, 1] scaled by the regime posterior: long the momentum direction in an orderly-trend state, and the opposite side of the short-horizon move in a stress state. portfolio.long_only=false and portfolio.net_target=null coincide with the engine defaults, so the intake gate reads the direction as unanswered; it is answered here. The paper specifies the direction SWITCH but no net-exposure target, so no net_target is set. |
| `exit` | analyst_choice | The exit is the signal returning 0: the regime posterior is ambiguous (no state clears the hysteresis gap) or the input feature is unavailable. Positions also close when the signal's sign flips. The gate's probed exit fields (signal.params.exit, execution.mode, execution.flat_at_close) cannot express a regime-conditional exit, so the rule lives in the signal implementation and is recorded here. |

Full engine report: `C:\Users\HP\AppData\Local\hermes\projects\leapspace-quant\reports\regime_switch_momentum_reversal_us_equity.md`

### `regime_switch_momentum_reversal_nasdaq_scalp_proxy`

**Verdict: REFUTED** — REFUTED — the edge did not survive out-of-sample testing and/or cost stress. See the flags for what specifically killed it.

Flags:
- t-stat -0.58 below 2.0 - the return series is not distinguishable from noise
- edge does not survive 2x cost stress
- only 8/22 profitable years

**Stages NOT run:** montecarlo, sweep, replication. This was a partial validation; the verdict is a preliminary read for those stages.

Parameter provenance:

| Parameter | Source | Note |
|---|---|---|
| `hypothesis` | paper | NASDAQ market regime identification (LeapSpace), 'Direct Answer' |
| `universe` | analyst_choice | us_equity_style includes QQQ (the Nasdaq proxy) plus SPY/IWM/MDY/RSP/DIA. |
| `n_states` | paper | 'a five-state HSMM better captured U.S. stock regimes than a two-state model' |
| `momentum_lookback` | analyst_choice | 20 trading days — a swing horizon. The paper is intraday-focused; a daily proxy cannot carry a 1-2 minute signal. |
| `reversal_lookback` | analyst_choice | 3 trading days. The paper's 'very short horizon' cannot be tested on daily bars; this is the shortest daily proxy. |
| `rebalance` | analyst_choice | Daily, because the paper's scalping premise is a fast refresh. |
| `costs` | engine_default | Skill DEFAULT_COSTS for US equities. |
| `period` | analyst_choice | Same window as the other spec for comparability. |
| `variants_tried` | analyst_choice | 1 — no tuning before the run. |
| `direction` | analyst_choice | Long/short market timing on the NASDAQ daily proxy. The signal emits a signed value in [-1, 1] scaled by the regime posterior. portfolio.long_only=false and portfolio.net_target=null coincide with the engine defaults, so the intake gate reads the direction as unanswered; it is answered here. |
| `exit` | analyst_choice | The exit is the signal returning 0 (ambiguous posterior or missing input), plus a sign flip. The gate's probed exit fields cannot express a regime-conditional exit; the rule lives in the signal implementation and is recorded here. |

Full engine report: `C:\Users\HP\AppData\Local\hermes\projects\leapspace-quant\reports\regime_switch_momentum_reversal_nasdaq_scalp_proxy.md`

### `regime_switch_cross_sectional_sector_rotation`

**Verdict: SUPPORTED** — SUPPORTED — the out-of-sample evidence survives the stages that ran. Per the backtest lab's rule this means 'warrants paper trading', NEVER 'trade it'.

Validation: **FULL gauntlet**

Parameter provenance:

| Parameter | Source | Note |
|---|---|---|
| `hypothesis` | paper | Financial market regime identification (LeapSpace), 'Best general edge' + suggested further research on position sizing from state probabilities |
| `universe` | analyst_choice | us_equity_sector = 11 SPDR sector ETFs. The paper says 'Equities, broad indices, crypto' and names no list. Sector ETFs give the cross-sectional dispersion a selection rule needs; XLC and XLRE start late (2018/2015), which shortens the panel. |
| `long_rank` | analyst_choice | Top quartile of the universe by the ranking variable. The paper gives no cutoff. |
| `max_names` | analyst_choice | 3 concurrent positions — concentration control, not stated in the paper. |
| `regime_gap` | analyst_choice | 0.10 posterior gap required to act. A hysteresis band: the paper argues for soft probabilities but sets no threshold. |
| `momentum_lookback` | analyst_choice | 60 trading days — the paper's 'medium-horizon' without a stated window. |
| `reversal_lookback` | analyst_choice | 5 trading days — the paper's 'short horizon' without a stated window. |
| `rebalance` | analyst_choice | Weekly. |
| `gross_leverage` | analyst_choice | 1.0, no leverage. |
| `max_position` | analyst_choice | 15% per name. |
| `costs` | engine_default | Skill DEFAULT_COSTS for US equities. |
| `period` | analyst_choice | 2005 onward, covering the 2008, 2020 and 2022 stress regimes the paper discusses. |
| `variants_tried` | analyst_choice | 1 — no tuning before the run. |
| `exit` | analyst_choice | A name exits when the regime MODE changes (trend <-> stress) or when it falls out of the selected rank set at the next rebalance; the engine closes the position when the signal stops naming it. max_names=3 caps the book. The gate's probed exit fields do not exist for a cross-sectional signal, so the rule is recorded here. |

Full engine report: `C:\Users\HP\AppData\Local\hermes\projects\leapspace-quant\reports\regime_switch_cross_sectional_sector_rotation.md`

### `v1_crypto_momentum_20d_ma`

**Verdict: FRAGILE** — FRAGILE — a positive out-of-sample result that a robustness stage failed, or out-of-sample evidence only. Treat as unproven.

Validation: **FULL gauntlet**

> This spec was SUPPORTED under --quick and was DOWNGRADED to FRAGILE by the full gauntlet (Monte Carlo probability of profit 81%, below the 90% bar). That is the gauntlet doing its job, and it is the reason the report names the stages that ran.

Flags:
- Monte Carlo prob(profitable) 81%

Parameter provenance:

| Parameter | Source | Note |
|---|---|---|
| `hypothesis` | paper | v1 §5 Strategy 1 — Crypto Trend-Following Momentum (20-day MA) |
| `momentum_lookback` | paper | v1 §5 Strategy 1: '20-day moving average' and '20-day return is positive' |
| `ma_lookback` | paper | v1 §5 Strategy 1: '20-day moving average' |
| `rebalance` | analyst_choice | The paper states NO rebalance cadence anywhere — the word appears zero times. Daily bar evaluation is inferred from a 20-day MA rule and disclosed as such. |
| `vol_target` | analyst_choice | The paper says 'volatility-scaled position size' but states NO target volatility. 0.50 annualised is chosen because crypto realised vol is far above equities; the engine treats vol_target as an UPPER BOUND, not an exact setting. |
| `max_position` | analyst_choice | 'a capped max allocation' — no % stated. 20% chosen. |
| `max_names` | analyst_choice | 'top liquid crypto names only' — no count stated. 3 chosen. |
| `realized_vol_gate` | analyst_choice | 'Trade only when realized volatility is not extreme' — NO threshold or lookback stated anywhere in the document. This is a REAL GAP: the rule could not be encoded as a hard filter without inventing a number, so it is NOT in the spec and is flagged here instead. |
| `stop_loss` | analyst_choice | The paper prefers a trailing stop at 1.0-1.5 SD but the engine's signal layer has no per-position stop; it is NOT encoded. See the `trailing_stop` entry in the paper's Strategy 8 — it is a separate rule. |
| `additional_conditions` | analyst_choice | The paper's entry is a 3-part AND: close>20dMA, 20d return>0, and realised vol not extreme. The engine's signal consumes ONE feature, so only the close>MA condition is encoded. Encoding the rest would require inventing the volatility cutoff, which the paper does not give. |
| `costs` | engine_default | Skill DEFAULT_COSTS for crypto (~10x the ETF cost). |
| `period` | analyst_choice | 2018 onward — crypto spot history on Yahoo begins 2014-2017 depending on the coin. |
| `variants_tried` | analyst_choice | 1 — no tuning before the run. |

Full engine report: `C:\Users\HP\AppData\Local\hermes\projects\leapspace-quant\reports\v1_crypto_momentum_20d_ma.md`

### `v1_nasdaq_12m_tsm_vol_scaled`

**Verdict: REFUTED** — REFUTED — the edge did not survive out-of-sample testing and/or cost stress. See the flags for what specifically killed it.

Flags:
- t-stat -0.45 below 2.0 - the return series is not distinguishable from noise
- 0/5 walk-forward folds profitable - the edge is absent in every out-of-sample period, not merely concentrated in a few
- edge does not survive 2x cost stress
- only 8/22 profitable years

**Stages NOT run:** montecarlo, sweep, replication. This was a partial validation; the verdict is a preliminary read for those stages.

Parameter provenance:

| Parameter | Source | Note |
|---|---|---|
| `hypothesis` | paper | v1 §5 Strategy 2 — Nasdaq Time-Series Momentum (12-month) |
| `momentum_lookback` | paper | v1 §5 Strategy 2: '12-month time-series momentum on Nasdaq', 'conventionally built on the past 12-month return' |
| `tsm_construction` | analyst_choice | skip=0 (a plain trailing 12-month return). The paper does NOT say whether the conventional skip-month or 12-1 construction is meant. |
| `rebalance` | analyst_choice | The paper states no cadence — 'rebalance' appears zero times. Monthly is the 12-month convention and is disclosed as an inference. |
| `vol_target` | analyst_choice | 'volatility scaling' / 'scale position size by inverse volatility' with NO target stated. 0.15 annualised is the analyst choice; the engine treats it as an upper bound. |
| `realized_vol_gate` | analyst_choice | 'Trade only when realized volatility is not extreme' — no threshold or lookback anywhere in the document. NOT encoded; flagged rather than invented. |
| `max_position` | analyst_choice | 20% per name; the paper states no cap. |
| `costs` | engine_default | Skill DEFAULT_COSTS for US equities. |
| `period` | analyst_choice | 2005 onward. |
| `variants_tried` | analyst_choice | 1 — no tuning before the run. |
| `direction` | analyst_choice | Long/short cross-sectional: long the top quartile by 12-month time-series momentum and short the bottom quartile (signal.params.long_rank / short_rank), sized to a 15% annualised volatility target. portfolio.long_only=false and portfolio.net_target=null coincide with the engine defaults, so the intake gate reads the direction as unanswered; it is answered here. |
| `exit` | analyst_choice | Exit is the cross-sectional rank: a name leaves the book when it drops out of the long (or short) rank set at the next rebalance. signal.params.exit does not exist for a cross_sectional signal, so the gate cannot see the rule; it is recorded here. |

Full engine report: `C:\Users\HP\AppData\Local\hermes\projects\leapspace-quant\reports\v1_nasdaq_12m_tsm_vol_scaled.md`

### `v1_sd_band_mean_reversion_1_0_1_5`

**Verdict: REFUTED** — REFUTED — the edge did not survive out-of-sample testing and/or cost stress. See the flags for what specifically killed it.

Flags:
- t-stat 1.70 below 2.0 - the return series is not distinguishable from noise
- OOS Sharpe retains only 32% of the in-sample Sharpe (need 40%) - the edge degrades out of sample

**Stages NOT run:** montecarlo, sweep, replication. This was a partial validation; the verdict is a preliminary read for those stages.

Parameter provenance:

| Parameter | Source | Note |
|---|---|---|
| `hypothesis` | paper | v1 §14 Strategy 8 — Volatility-Band (1.0-1.5 SD) Filter Framework |
| `entry_band` | paper | v1 §14: 'Use 1.0 SD as the early warning band and 1.5 SD as the stronger trigger band'; 'Enter band at -1.0 SD (watch) / -1.5 SD (higher-conviction stretch)' |
| `zscore_lookback` | paper | v1 §14: rolling window, 'often around a trading month in research examples'; the worked examples use 20-day |
| `exit` | analyst_choice | The paper says 'exit when the spread reverts to mean'. The engine's time_series_zscore needs an exit \|z\| level; 0.0 (the mean) is the literal reading of 'reverts to mean'. |
| `early_warning_band` | analyst_choice | The 1.0 SD early-warning band is stated in the paper but the engine's time_series_zscore supports ONE entry level, so 1.5 is used as the entry and the 1.0 band is not separately encoded. It would need a two-level signal. |
| `rebalance` | analyst_choice | The paper states no cadence. Daily bar evaluation is inferred. |
| `max_position` | analyst_choice | 25% per name; the paper states no cap. |
| `costs` | engine_default | Skill DEFAULT_COSTS for US equities. |
| `period` | analyst_choice | 2005 onward. |
| `variants_tried` | analyst_choice | 1 — no tuning before the run. |
| `universe` | analyst_choice | Broad US equity universe (the engine's us_equity_broad preset). The paper's mean-reversion setup is applied to a liquid broad index rather than a named ticker list, and names no tickers, so the ticker mapping is the analyst's choice. universe.preset coincides with the engine default, so the intake gate reads the universe as unanswered; it is answered here. |

Full engine report: `C:\Users\HP\AppData\Local\hermes\projects\leapspace-quant\reports\v1_sd_band_mean_reversion_1_0_1_5.md`

### `tradingview_price_volume_rsi_regime_filtered`

**Verdict: REFUTED** — REFUTED — the edge did not survive out-of-sample testing and/or cost stress. See the flags for what specifically killed it.

Flags:
- t-stat 1.86 below 2.0 - the return series is not distinguishable from noise
- OOS Sharpe retains only 25% of the in-sample Sharpe (need 40%) - the edge degrades out of sample

**Stages NOT run:** montecarlo, sweep, replication. This was a partial validation; the verdict is a preliminary read for those stages.

Parameter provenance:

| Parameter | Source | Note |
|---|---|---|
| `hypothesis` | paper | Free trading indicators for directional edge (LeapSpace), 'Bottom line' |
| `rsi_lookback` | analyst_choice | 14 trading days — Wilder's standard RSI period. The paper names RSI but gives no period. |
| `oversold_overbought` | analyst_choice | 30/70 — the conventional RSI overbought/oversold bands. The paper names RSI but gives no thresholds. |
| `volume_threshold` | analyst_choice | 1.0 — volume above its 60-day average. The paper says 'volume confirmation' without a definition. |
| `rebalance` | analyst_choice | Weekly, matching the daily-bar horizon. |
| `costs` | engine_default | Skill DEFAULT_COSTS for US equities. |
| `variants_tried` | analyst_choice | 1 — no tuning before the run. |
| `universe` | analyst_choice | Broad US equity universe (the engine's us_equity_broad preset) so the RSI fade is measured on liquid instruments rather than on a ticker list the paper does not name. universe.preset coincides with the engine default, so the intake gate reads the universe as unanswered; it is answered here. |
| `exit` | analyst_choice | Exit is the RSI mean-reversion: the position closes when RSI returns through the neutral band, and the volume confirmation gate can drop the position. signal.params.exit does not exist for the rsi_volume_confirmation signal, so the rule is recorded here. |

Full engine report: `C:\Users\HP\AppData\Local\hermes\projects\leapspace-quant\reports\tradingview_price_volume_rsi_regime_filtered.md`

### `crypto_ma20_trend_momentum`

**Verdict: REFUTED** — REFUTED — the edge did not survive out-of-sample testing and/or cost stress. See the flags for what specifically killed it.

Flags:
- t-stat 1.40 below 2.0 - the return series is not distinguishable from noise
- only 2/5 walk-forward folds profitable (edge concentrated in a few periods)

**Stages NOT run:** montecarlo, sweep, replication. This was a partial validation; the verdict is a preliminary read for those stages.

Parameter provenance:

| Parameter | Source | Note |
|---|---|---|
| `features.sma_gap.lookback` | paper | The paper's trend proxy for crypto is a 20-day moving average ("close > 20-day moving average"; "a shorter, crypto-adapted trend window such as 20-day or 2-4 week lookback for crypto"). sma_gap is (price / SMA) - 1 over 20 bars, so it is that moving average expressed as a relative gap. |
| `features.momentum.lookback` | paper | Second clause of the paper's entry rule, declared as a feature for reference. It is NOT the traded feature - see additional_conditions. |
| `features.momentum.skip` | analyst_choice | The paper states no skip. skip=0 measures the trailing 20 bars including the most recent bar (engine default). |
| `signal.feature` | analyst_choice | The engine's time_series_threshold accepts one feature. sma_gap is chosen as the primary feature because the paper's direction rule is stated relative to the moving average ("Go long when price is above its trend proxy; go short or flat when below, if your venue supports it"). |
| `signal.threshold` | paper | The paper states the comparison rather than a number: go long when price is above the trend proxy. Because sma_gap = price/SMA - 1, threshold 0.0 reproduces the paper's test exactly (positive = above the 20-day MA). |
| `universe.preset` | paper | The crypto preset (BTC, ETH, LTC, BCH, XRP, SOL, ADA, DOGE, AVAX, LINK) is the engine's liquid-crypto basket and stands in for the paper's "top liquid crypto names". The paper names no tickers, so the ticker mapping is the analyst's choice; the universe REQUIREMENT is the paper's. |
| `period.start` | analyst_choice | The paper specifies no backtest window. 2021-01-01 is chosen so every symbol in the crypto preset has history (SOL/AVAX/ADA list from 2020-21), giving ~5.8 years of daily bars through 2026 and more than 20 bars of lookback warm-up. |
| `period.end` | analyst_choice | null = latest available bar (engine default). The paper states no end date. |
| `period.interval` | engine_default | '1d' is the engine default and matches the paper's daily-bar language ("20-day moving average", "20-day return"). |
| `portfolio.rebalance` | analyst_choice | The paper gives no rebalance cadence for the crypto momentum rule. daily re-tests the 20-day MA condition on every close and suits the paper's volatility-aware, stop-managed design. |
| `portfolio.max_position` | analyst_choice | The paper requires "a capped max allocation" but states no number. 0.2 is the analyst's cap; with up to 10 names in the book the cap only binds when fewer than 5 names are held, in which case realised gross falls below the 1.0 target (this is expected behaviour of the engine's hard cap, not a defect). |
| `portfolio.gross_leverage` | engine_default | Engine default 1.0 - no leverage. The paper states no gross exposure target. |
| `portfolio.long_only` | analyst_choice | The paper says "go short or flat when below, if your venue supports it". The engine's time_series_threshold signal emits only 0/+1, so the short leg cannot be expressed; long_only=true is the encodable subset. See additional_conditions. |
| `portfolio.max_names` | engine_default | null = no cap on concurrent names. The paper states no limit. |
| `execution.fill_at` | engine_default | Engine default 'open' (decision on bar t-1, fill at the open of bar t). The paper states no execution convention. |
| `execution.cost_multiplier` | engine_default | Engine default 1.0, i.e. the engine's conservative per-asset-class DEFAULT_COSTS (crypto is already set ~10x the ETF cost). The paper insists costs matter ("nice-looking indicator results can collapse once transaction costs and out-of-sample testing are included") but states no fee, spread or slippage numbers, so the engine defaults are retained unchanged. |
| `execution.max_participation` | engine_default | Engine default 0.10 - at most 10% of a bar's dollar volume per order. The paper's liquidity warning supports keeping the cap but states no number. |
| `capital` | engine_default | Engine default 100000.0. The paper states no account size. |
| `volatility_sizing` | analyst_choice | NOT ENCODED. The paper requires "scale position size by inverse volatility" / "volatility-scaled position size with a capped max allocation", but the fixed portfolio block for these specs has no vol_target field. If the consuming schema allows it, add portfolio.vol_target (the paper gives no target level; 0.15-0.20 annualised is the analyst's suggestion). |
| `additional_conditions` | analyst_choice | The paper's entry rule has two clauses - "close > 20-day moving average" AND "20-day return is positive" - and the engine takes one feature per signal, so only the first is traded (the momentum feature is declared but not enforced). The paper's risk filter ("Trade only when realized volatility is not extreme") and its stop-loss overlay ("Add a stop-loss overlay", "Exit: stop-loss plus trend failure exit") are also not expressible: the engine has no stop primitive and no second gate on a time_series_threshold signal. |

Full engine report: `C:\Users\HP\AppData\Local\hermes\projects\leapspace-quant\reports\crypto_ma20_trend_momentum.md`

### `nasdaq_12m_timeseries_momentum`

**Verdict: SUPPORTED** — SUPPORTED — the out-of-sample evidence survives the stages that ran. Per the backtest lab's rule this means 'warrants paper trading', NEVER 'trade it'.

Validation: **FULL gauntlet**

Parameter provenance:

| Parameter | Source | Note |
|---|---|---|
| `features.momentum.lookback` | paper | The paper states a "12-month time-series momentum" for Nasdaq and that it is "conventionally built on the past 12-month return". 12 months maps to 252 daily bars. |
| `features.momentum.skip` | analyst_choice | The paper states no skip. skip=0 measures the trailing 252 bars including the most recent one, the literal reading of "past 12-month return". The common 12-1 convention (skip=21) is NOT the paper's statement and would be an analyst substitution. |
| `signal.feature` | analyst_choice | Only one feature is declared, so the engine would infer it; naming it explicitly is the analyst's clarity choice. |
| `signal.threshold` | paper | The paper's time-series momentum is the sign of the trailing 12-month return and its direction rule is long-above-the-trend-proxy / flat-below. Threshold 0.0 is that sign test: long when the 12-month return is positive, flat otherwise. |
| `universe.preset` | paper | us_equity_style (SPY, IWM, MDY, RSP, QQQ, DIA) is the engine preset that carries the Nasdaq-100 tracker QQQ alongside other liquid large-cap ETFs, and matches the paper's requirement of liquid Nasdaq names. The paper names no tickers, so the ticker mapping is the analyst's choice; the universe REQUIREMENT (liquid Nasdaq names) is the paper's. |
| `portfolio.rebalance` | analyst_choice | The paper gives no cadence for the 12-month rule and explicitly lists the rebalance cadence as an open question. monthly keeps a 12-month signal fresh on a one-month review and keeps turnover low, which matters because the paper stresses these rules are "sensitive to transaction costs and turnover". NOTE: 'monthly' is also the engine's own default value, so the intake gate will read this field as un-supplied until it is recorded as an accepted default (intake.accepted_defaults: ["rebalance"]). |
| `portfolio.max_position` | analyst_choice | The paper requires a capped allocation ("volatility-scaled position size with a capped max allocation") but states no number. 0.2 is the analyst's cap; with 6 preset members a 1.0 gross book gives ~0.167 per name, so the cap only binds in a narrow book. |
| `portfolio.gross_leverage` | engine_default | Engine default 1.0 - no leverage. The paper states no gross exposure target. |
| `portfolio.long_only` | analyst_choice | The paper's direction rule allows a short leg "if your venue supports it"; the engine's time_series_threshold signal emits only 0/+1, so long_only=true is the encodable subset. See additional_conditions. |
| `portfolio.max_names` | engine_default | null = no cap on concurrent names. The paper states no limit. |
| `execution.fill_at` | engine_default | Engine default 'open'. The paper states no execution convention. |
| `execution.cost_multiplier` | engine_default | Engine default 1.0 (the engine's per-asset-class DEFAULT_COSTS). The paper stresses cost sensitivity but states no fee, spread or slippage numbers. |
| `execution.max_participation` | engine_default | Engine default 0.10 (10% of a bar's dollar volume per order). The paper states no number. |
| `capital` | engine_default | Engine default 100000.0. The paper states no account size. |
| `volatility_sizing` | analyst_choice | NOT ENCODED. The paper's risk filter is "Trade only when realized volatility is not extreme, and scale position size by inverse volatility", but the fixed portfolio block for these specs has no vol_target field. If the consuming schema allows it, add portfolio.vol_target (the paper states no level; 0.10-0.15 annualised is the analyst's suggestion). |
| `additional_conditions` | analyst_choice | Three of the paper's stated components for this model cannot be encoded: (a) the stop-loss overlay ("Add a stop-loss overlay"; "Stop-loss momentum outperforms other crypto momentum variants and improves downside control"); (b) the regime filter ("Avoid broad, always-on exposure; switch off or reduce size in regimes where momentum weakens"); (c) the optional short leg ("go short or flat when below, if your venue supports it"), because time_series_threshold emits only 0/+1. The engine also has no stop-loss primitive, so the volatility-scaled stop the paper describes elsewhere cannot be represented. |

Full engine report: `C:\Users\HP\AppData\Local\hermes\projects\leapspace-quant\reports\nasdaq_12m_timeseries_momentum.md`

### `sd_band_mean_reversion_crypto`

**Verdict: REFUTED** — REFUTED — the edge did not survive out-of-sample testing and/or cost stress. See the flags for what specifically killed it.

Flags:
- t-stat -1.92 below 2.0 - the return series is not distinguishable from noise
- only 2/5 walk-forward folds profitable (edge concentrated in a few periods)
- edge does not survive 2x cost stress
- only 1/6 profitable years
- deflated Sharpe negative (-0.68) — edge likely snooping artifact

**Stages NOT run:** montecarlo, sweep, replication. This was a partial validation; the verdict is a preliminary read for those stages.

Parameter provenance:

| Parameter | Source | Note |
|---|---|---|
| `features.zscore.lookback` | paper | The paper's volatility unit for every band and stop rule is a rolling standard deviation over "a rolling window, often around a trading month in research examples", and every worked example uses a 20-day SD (Nasdaq $100 with 20-day SD $4; BTC $60,000 with 20-day SD $2,000). zscore over 20 bars = (price - SMA) / SD on exactly that window, so the paper's "1.0 to 1.5 SD" language maps directly onto \|z\|. |
| `signal.entry` | paper | The paper reports that "1 and 1.5 standard deviation thresholds produced better results than the classic pairs-trading setup in one study" and labels 1.0 SD the first alert zone and 1.5 SD the stronger signal zone. This spec trades the stronger band (\|z\| > 1.5); the 1.0 SD early-warning band is the paper's alternative and is counted as the second variant. |
| `signal.exit` | paper | "Exit when spread reverts to mean; use tight time stops because crypto mean reversion can be fast." Reverting to the mean is z = 0, so exit = 0.0 closes the position as the stretch normalises; the engine's time_series_zscore holds the position until \|z\| falls below the exit level. |
| `universe.preset` | paper | "Highly liquid pairs or a tightly screened basket; prioritize BTC/ETH-style liquid names and Nasdaq pairs with stable relationships." The crypto preset supplies the BTC/ETH-style liquid names; the paper names no tickers, so the ticker mapping is the analyst's choice and the pair structure is dropped (see additional_conditions). |
| `portfolio.long_only` | paper | "Enter long when price is stretched below fair value ... Enter short on the opposite setup when the stretch and pressure reverse." The model is two-sided, so long_only=false matches the paper. NOTE: false is also the engine's default value, so the intake gate will read this field as un-supplied until it is recorded as an accepted default (intake.accepted_defaults: ["direction"]). |
| `portfolio.rebalance` | analyst_choice | The paper gives no cadence but is emphatic that reversion is a short-horizon edge ("use tight time stops", "shorter holding periods help preserve returns against costs", "crypto reversal can switch within about a month"). daily is the analyst's choice and is the fastest cadence the engine offers. |
| `portfolio.max_position` | analyst_choice | The paper requires a capped allocation but states no number for the reversion model. 0.2 is the analyst's cap; with up to 10 names the cap binds only when fewer than 5 names are held, in which case realised gross is below the 1.0 target. |
| `portfolio.gross_leverage` | engine_default | Engine default 1.0 - no leverage. The paper states no gross exposure target. |
| `portfolio.max_names` | engine_default | null = no cap on concurrent names. The paper states no limit. |
| `execution.fill_at` | engine_default | Engine default 'open'. The paper states no execution convention. |
| `execution.cost_multiplier` | engine_default | Engine default 1.0 (the engine's per-asset-class DEFAULT_COSTS; crypto is ~10x the ETF cost). This matters here: the paper says "shorter holding periods help preserve returns against costs", but states no fee, spread or slippage numbers. |
| `execution.max_participation` | engine_default | Engine default 0.10 (10% of a bar's dollar volume per order). The paper states no number. |
| `capital` | engine_default | Engine default 100000.0. The paper states no account size. |
| `period.start` | analyst_choice | No window stated. 2021-01-01 gives every symbol in the crypto preset history and ~5.8 years of daily bars through 2026, with 20 bars of z-score warm-up. |
| `period.end` | analyst_choice | null = latest available bar. The paper states no end date. |
| `period.interval` | engine_default | '1d' is the engine default and matches the paper's daily-bar, 20-day-SD language. |
| `additional_conditions` | analyst_choice | The paper's model is a SPREAD model: "Use a z-score / s-score or cointegration spread", "For Nasdaq: use a cointegration or spread model on stable pairs", "For crypto: use dynamic cointegration or Hurst-filtered pairs". The engine has no pair, cointegration or Hurst machinery, so the z-score here is each symbol's own price against its own 20-day mean - this tests a weaker, single-name version of the paper's claim and the user must know which question was answered. Three further paper components are not encodable: the regime filter ("only trade mean reversion when the asset/pair is not in a strong trend"), the time stop ("use tight time stops") and the catastrophe stop "placed beyond the spread-entry zone, not inside it" - the engine has no stop primitive. The optional buffer zone ("to avoid noise") is also not encoded. |

Full engine report: `C:\Users\HP\AppData\Local\hermes\projects\leapspace-quant\reports\sd_band_mean_reversion_crypto.md`

### `bollinger20_2_breakout_crypto`

**Verdict: REFUTED** — REFUTED — the edge did not survive out-of-sample testing and/or cost stress. See the flags for what specifically killed it.

Flags:
- t-stat 1.92 below 2.0 - the return series is not distinguishable from noise
- OOS Sharpe retains only 35% of the in-sample Sharpe (need 40%) - the edge degrades out of sample

**Stages NOT run:** montecarlo, sweep, replication. This was a partial validation; the verdict is a preliminary read for those stages.

Parameter provenance:

| Parameter | Source | Note |
|---|---|---|
| `features.bollinger_pct.lookback` | paper | The paper states the default Bollinger configuration as a 20-period moving average with standard-deviation bands, and calls 20 over 2 SD "the conventional starting point". |
| `features.bollinger_pct.nstd` | paper | The paper states the bands at 2 standard deviations; it also notes studies testing 1.5/2/2.5/3 SD widths. |
| `signal.feature` | analyst_choice | Only one feature is declared, so the engine would infer it; naming it explicitly is the analyst's clarity choice. |
| `signal.threshold` | analyst_choice | The paper defines the band but states no trade rule. bollinger_pct = (price - SMA) / (nstd x SD), so with nstd=2 a threshold of 1.0 fires when the close is above the paper's +2 SD upper band (price > SMA + 2 SD). Threshold 0.0 would have been meaningless here - it would reduce to "price above the 20-day SMA" and duplicate the momentum spec instead of testing the band. The analyst reads the upper-band break as a volatility-scaled continuation entry, consistent with the paper's momentum direction rule ("Go long when price is above its trend proxy") and with its scalping reading of the SD band as an entry filter. A fade of the same band would be the mirror reading and would duplicate the mean-reversion spec. |
| `universe.preset` | paper | The paper's momentum model runs on "top liquid crypto names" with "a shorter, crypto-adapted trend window such as 20-day or 2-4 week lookback for crypto"; the Bollinger section is discussed for crypto/commodity/Nepse contexts. The crypto preset supplies the liquid names; the paper names no tickers, so the ticker mapping is the analyst's choice. |
| `portfolio.long_only` | analyst_choice | The paper's direction rule allows "go short or flat when below, if your venue supports it", but the engine's time_series_threshold signal emits only 0/+1, so long_only=true is the encodable subset. See additional_conditions. |
| `portfolio.rebalance` | analyst_choice | No cadence stated. daily re-tests the band on every close, consistent with the paper's short-term, cost-sensitive framing of indicator systems. |
| `portfolio.max_position` | analyst_choice | The paper requires a capped allocation but states no number. 0.2 is the analyst's cap; it binds only when fewer than 5 names are held. |
| `portfolio.gross_leverage` | engine_default | Engine default 1.0 - no leverage. The paper states no gross exposure target. |
| `portfolio.max_names` | engine_default | null = no cap on concurrent names. The paper states no limit. |
| `execution.fill_at` | engine_default | Engine default 'open'. The paper states no execution convention. |
| `execution.cost_multiplier` | engine_default | Engine default 1.0 (the engine's per-asset-class DEFAULT_COSTS). The paper warns that indicator results "can collapse once transaction costs and out-of-sample testing are included" but states no fee, spread or slippage numbers. |
| `execution.max_participation` | engine_default | Engine default 0.10 (10% of a bar's dollar volume per order). The paper states no number. |
| `capital` | engine_default | Engine default 100000.0. The paper states no account size. |
| `period.start` | analyst_choice | No window stated. 2021-01-01 gives every symbol in the crypto preset history and ~5.8 years of daily bars through 2026, with 20 bars of band warm-up. |
| `period.end` | analyst_choice | null = latest available bar. The paper states no end date. |
| `period.interval` | engine_default | '1d' is the engine default and matches the paper's daily-bar, 20-period language. |
| `additional_conditions` | analyst_choice | The paper's stronger momentum versions require layers the engine cannot carry: a participation confirmation ("add volume / turnover / order imbalance so the trade only triggers when participation supports continuation"), an options-implied stage filter ("Avoid trades when options-implied measures suggest the move is in a late momentum stage"), a volatility filter ("Trade only when realized volatility is not extreme") and a stop-loss overlay ("Add a stop-loss overlay"). Only the price/volatility stretch is encoded here. |

Full engine report: `C:\Users\HP\AppData\Local\hermes\projects\leapspace-quant\reports\bollinger20_2_breakout_crypto.md`

### `crypto_xs_momentum_volume_confirmed`

**Verdict: REFUTED** — REFUTED — the edge did not survive out-of-sample testing and/or cost stress. See the flags for what specifically killed it.

Flags:
- t-stat -0.61 below 2.0 - the return series is not distinguishable from noise
- only 2/5 walk-forward folds profitable (edge concentrated in a few periods)
- edge does not survive 2x cost stress

**Stages NOT run:** montecarlo, sweep, replication. This was a partial validation; the verdict is a preliminary read for those stages.

Parameter provenance:

| Parameter | Source | Note |
|---|---|---|
| `features.momentum.lookback` | paper | The paper specifies a shorter, crypto-adapted trend window for crypto rather than a 12-month one; 20 days is the window it names explicitly ("20-day moving average and 20-day return is positive"). |
| `features.momentum.skip` | analyst_choice | The paper states no skip. skip=0 measures the trailing 20 bars including the most recent bar (engine default). |
| `features.volume_ratio.short` | analyst_choice | The paper requires a volume/turnover confirmation ("volume is rising"; "volume-augmented momentum beat pure price momentum") but states no averaging windows. 10 bars is the analyst's choice. volume_ratio is declared for reference only - it is NOT the traded feature. |
| `features.volume_ratio.long` | analyst_choice | 60 bars is the analyst's choice; the paper states no baseline window for "volume is rising". |
| `signal.feature` | analyst_choice | The engine's cross_sectional signal ranks on a single feature. momentum is chosen as the traded feature (the paper's primary signal is the price trend); ranking on volume_ratio would turn the rule into a volume ranking, which is not what the paper describes. |
| `signal.long_rank` | analyst_choice | The paper gives no rank cut-offs. 0.75 on the 10-name crypto basket means roughly the top 3 names are long; it is the analyst's choice, documented so it can be varied. NOTE: 0.75/0.25 coincide with the engine's default rank pair, so the intake gate will read the entry/exit rules as un-supplied until they are recorded as accepted defaults (intake.accepted_defaults: ["signal"]). |
| `signal.short_rank` | analyst_choice | 0.25 (roughly the bottom 3 names short) is the analyst's choice, matching the paper's "go short or flat when below, if your venue supports it". |
| `universe.preset` | paper | The crypto preset supplies the paper's "top liquid crypto names". The paper names no tickers, so the ticker mapping is the analyst's choice; a cross-sectional rule needs at least two instruments, which this preset provides. |
| `portfolio.long_only` | paper | "Go long when price is above its trend proxy; go short or flat when below, if your venue supports it." A cross-sectional book long/short matches the paper, so long_only=false. |
| `portfolio.rebalance` | analyst_choice | No cadence stated for the volume-augmented momentum rule. daily keeps the 20-day momentum rank and the participation filter current; the paper stresses turnover sensitivity, which argues against a longer cadence still being untested - the choice here is the analyst's. |
| `portfolio.max_position` | analyst_choice | The paper requires a capped allocation but states no number. 0.2 is the analyst's cap; with roughly 3 long and 3 short names a 1.0 gross book gives ~0.167 per name, so the cap does not bind. |
| `portfolio.gross_leverage` | engine_default | Engine default 1.0 - no leverage. The paper states no gross exposure target. |
| `portfolio.max_names` | engine_default | null = no cap on concurrent names; the rank thresholds already bound the book. The paper states no limit. |
| `execution.fill_at` | engine_default | Engine default 'open'. The paper states no execution convention. |
| `execution.cost_multiplier` | engine_default | Engine default 1.0 (the engine's per-asset-class DEFAULT_COSTS; crypto is ~10x the ETF cost). The paper warns that momentum rules are "sensitive to transaction costs and turnover" but states no fee, spread or slippage numbers. |
| `execution.max_participation` | engine_default | Engine default 0.10 (10% of a bar's dollar volume per order). The paper states no number. |
| `capital` | engine_default | Engine default 100000.0. The paper states no account size. |
| `period.start` | analyst_choice | No window stated. 2021-01-01 gives every symbol in the crypto preset history and ~5.8 years of daily bars through 2026, with 20 bars of momentum warm-up. |
| `period.end` | analyst_choice | null = latest available bar. The paper states no end date. |
| `period.interval` | engine_default | '1d' is the engine default and matches the paper's daily-bar language. |
| `additional_conditions` | analyst_choice | The paper's confirmation layer is "volume is rising, and order imbalance/turnover is positive"; order imbalance / CVD is not derivable from the engine's daily OHLCV panel, and volume_ratio is declared but not enforced by the one-feature signal, so this spec tests the paper's momentum leg WITHOUT its volume/flow confirmation - a weaker version of the claim. The paper's other stated components are also missing: the options-implied momentum-stage filter, the volatility filter ("Trade only when realized volatility is not extreme"), inverse-volatility sizing and the stop-loss overlay. |
| `exit` | analyst_choice | Exit is the cross-sectional rank: a name leaves the book when it drops out of the long rank set at the next rebalance. signal.params.exit does not exist for a cross_sectional signal, so the gate cannot see the rule; it is recorded here. |

Full engine report: `C:\Users\HP\AppData\Local\hermes\projects\leapspace-quant\reports\crypto_xs_momentum_volume_confirmed.md`

### `crypto_rsi_oversold_fade`

**Verdict: REFUTED** — REFUTED — the edge did not survive out-of-sample testing and/or cost stress. See the flags for what specifically killed it.

Flags:
- t-stat 1.37 below 2.0 - the return series is not distinguishable from noise

**Stages NOT run:** montecarlo, sweep, replication. This was a partial validation; the verdict is a preliminary read for those stages.

Parameter provenance:

| Parameter | Source | Note |
|---|---|---|
| `features.rsi.lookback` | analyst_choice | The paper names RSI but states no period ("RSI and simple momentum tools", "RSI was found more reliable than MACD or Stochastic"). 14 bars is the analyst's conventional choice. |
| `features.rsi.direction` | analyst_choice | -1 inverts the feature so that a single threshold test can express the paper's oversold FADE. With direction -1 the feature value is -RSI, so the test (-RSI > -30) fires exactly when RSI < 30. The engine's threshold signal emits only 0/+1, so without the inversion an oversold fade could not be expressed at all. |
| `signal.feature` | analyst_choice | Only one feature is declared, so the engine would infer it; naming it explicitly is the analyst's clarity choice. |
| `signal.threshold` | analyst_choice | The paper states only that RSI works for "overbought/oversold style signals"; it gives no threshold. -30 on the inverted RSI (i.e. RSI < 30) is the conventional oversold line and the analyst's choice. EXIT: the signal returns to 0 as soon as RSI is back above 30, which stands in for the paper's "exit when the stretch normalises"; the paper states no explicit exit for the RSI setup. |
| `universe.preset` | paper | The RSI finding the paper reports is a crypto finding, so the crypto preset is the paper-supported universe. The paper names no tickers, so the ticker mapping is the analyst's choice. |
| `portfolio.long_only` | analyst_choice | The paper frames RSI as a "Mean reversion and exhaustion setup" with no short leg; the encoded fade is long-only. The engine's threshold signal emits only 0/+1, so a symmetric oversold/overbought fade could not be expressed anyway. |
| `portfolio.rebalance` | analyst_choice | No cadence stated. daily matches the paper's "short-term usefulness" framing for RSI in crypto and keeps the exhaustion read current. |
| `portfolio.max_position` | analyst_choice | The paper requires a capped allocation in its momentum/reversion models but states no number for the RSI setup. 0.2 is the analyst's cap. |
| `portfolio.gross_leverage` | engine_default | Engine default 1.0 - no leverage. The paper states no gross exposure target. |
| `portfolio.max_names` | engine_default | null = no cap on concurrent names. The paper states no limit. |
| `execution.fill_at` | engine_default | Engine default 'open'. The paper states no execution convention. |
| `execution.cost_multiplier` | engine_default | Engine default 1.0 (the engine's per-asset-class DEFAULT_COSTS; crypto is ~10x the ETF cost). The paper warns that indicator results "can collapse once transaction costs and out-of-sample testing are included" but states no fee, spread or slippage numbers. |
| `execution.max_participation` | engine_default | Engine default 0.10 (10% of a bar's dollar volume per order). The paper states no number. |
| `capital` | engine_default | Engine default 100000.0. The paper states no account size. |
| `period.start` | analyst_choice | No window stated. 2021-01-01 gives every symbol in the crypto preset history and ~5.8 years of daily bars through 2026, with 14 bars of RSI warm-up. |
| `period.end` | analyst_choice | null = latest available bar. The paper states no end date. |
| `period.interval` | engine_default | '1d' is the engine default and matches the paper's daily-bar, short-term-indicator framing. |
| `additional_conditions` | analyst_choice | The paper's recommended stack is "price action first, then volume, then one momentum filter" plus a regime filter ("Trade only when the regime matches the strategy", "Mean-reversion tools work better in some markets/periods, while trend tools work better in others"). The engine takes one feature per signal, so RSI alone is traded and neither the volume confirmation nor the regime filter is enforced. The paper also states the RSI edge is a lower-confidence one ("Confidence level: Medium") and that "results vary by market, timeframe, and transaction costs". |

Full engine report: `C:\Users\HP\AppData\Local\hermes\projects\leapspace-quant\reports\crypto_rsi_oversold_fade.md`

## 4. Source reliability of the papers themselves

The seven LeapSpace documents are literature-synthesis transcripts, not research papers. Reading them surfaced defects in the SOURCE material, and a set of sections this package deliberately does not implement. These findings are about the papers' evidence, not about the backtests above.

**15 defects recorded** (6 high severity) across the documents.

| Document | ID | Severity | Finding | Impact on this package |
|---|---|---|---|---|
| Trading strategies for retail traders (LeapSpace 2.0) | D1 | high | Citation numbers are section-scoped and collide: 34 numbers map to different papers in different sections. | None. This package cites by section and quoted phrase. |
| Trading strategies for retail traders (LeapSpace 2.0) | D2 | high | ZERO numeric performance results. No original data, no backtests, no charts, no result tables. | All. |
| Trading strategies for retail traders (LeapSpace v1) | D1 | high | Citation numbers are SECTION-SCOPED, not global. 38 numbers resolve to different papers in different sections. | None. This package's parameter_provenance cites at SECTION-and-QUOTE level, never by reference number. |
| Trading strategies for retail traders (LeapSpace v1) | D2 | high | ZERO numeric performance results anywhere in the document. | All. Documented in each spec's parameter_provenance and in the report's validation note. |
| Trading strategies for retail traders (LeapSpace v1) | D3 | high | Section 9 MIS-CITES an on-chain Bitcoin paper as support for US-equity intraday options-flow and gamma claims, at stated Confidence: High. | None. Section 9 is an intraday-scalping section; the package implements no scalp spec. |
| Trading strategies for retail traders (LeapSpace v1) | D7 | high | The word 'rebalance' appears ZERO times in the document. No rebalance cadence is stated for any strategy. | All momentum and mean-reversion specs: portfolio.rebalance is tagged analyst_choice. |
| Trading strategies for retail traders (LeapSpace 2.0) | D18 | medium | 18 instances of a self-referential marker ('[turn 9 summary]' and similar) — some sections cite the model's own earlier turns rather than primary literature. | None. |
| Trading strategies for retail traders (LeapSpace 2.0) | D19 | medium | Per-section reference lists are truncated: each section lists only the references it cites, so no single global bibliography is recoverable from the PDF text alone. | None. |
| Trading strategies for retail traders (LeapSpace 2.0) | D8 | medium | The document reports no performance statistics of its own — it is a research synthesis, not a test result. | All — recorded in each spec's intake.notes. |
| Trading strategies for retail traders (LeapSpace v1) | D4 | medium | Section 10 is a self-citing regeneration: 14 literal '[turn 9 summary]' citations stand in for real references. | None. |
| Trading strategies for retail traders (LeapSpace v1) | D5 | medium | Duplicate reference entries within a single section: section 1 [1]=[26], [28]=[34]; section 2 [42]=[53]. | None. The package never counts references. |
| Trading strategies for retail traders (LeapSpace v1) | D6 | medium | Sections 9, 10 and 11 answer the same three scalping questions with different evidence sets (Confidence High / Medium / High). | None. |
| Trading strategies for retail traders (LeapSpace v1) | D8 | medium | No momentum take-profit rule. 'Take-profit' appears twice: as a cited relationship, and as an offer to the user. | None — the engine has no take-profit primitive. |
| Trading strategies for retail traders (LeapSpace v1) | D9 | medium | The on-chain signal set is ranked #2 in the document's own priority order but is never operationalized — no strategy section implements an on-chain rule. | None. See scope_exclusions.on_chain_feature_set. |
| Trading strategies for retail traders (LeapSpace v1) | D10 | low | Forward-dated and current-year references appear (e.g. Rathore et al. 2027, several 2026 DOIs). | None. |

**The load-bearing ones:**

- **D1** — Citation numbers are section-scoped and collide: 34 numbers map to different papers in different sections.
  - Evidence: [131] = Dolvin & Foltice (2023) in one section, Gerety & Mulherin (1992) in another, Miori & Cucuringu (2023) in a third.
- **D2** — ZERO numeric performance results. No original data, no backtests, no charts, no result tables.
  - Evidence: Programmatic scan for %, bps, CAGR, drawdown, win rate, annualized, Sharpe, ATR, rebalance, look-ahead, risk per trade confirmed the absence of every numeric performance family.
  - Impact: Every backtest number in this package is INDEPENDENT evidence, not a reproduction.
- **D1** — Citation numbers are SECTION-SCOPED, not global. 38 numbers resolve to different papers in different sections.
  - Evidence: [130] = Kitapbayev & Leung in section 7, Berkman et al. in section 11, Leung & Li in section 13. [131] = Miori & Cucuringu / Gerety & Mulherin / Dolvin & Foltice. [128] = Dudler / Kaminski & Lo / Samarasekara.
  - Impact: Any automated citation resolver must key on (section, reference_number), never on the number alone. Keying on the number silently mis-attributes.
- **D2** — ZERO numeric performance results anywhere in the document.
  - Evidence: A regex sweep for %, CAGR, annualized, win rate, bps, Sharpe ratio, Sortino, Calmar and information coefficient returned no numeric performance match. 'Sharpe'/'alpha' appear only in one qualitative sentence; 'drawdown' only inside two reference titles.
  - Impact: The papers cannot be used to calibrate, validate or rank anything. Every backtest number in this package is INDEPENDENT evidence, not a reproduction of a published result.
- **D3** — Section 9 MIS-CITES an on-chain Bitcoin paper as support for US-equity intraday options-flow and gamma claims, at stated Confidence: High.
  - Evidence: In section 9, reference [8] = Grobys, Nasman & Sandretto (2026), 'Using on-chain data to predict Bitcoin cycles' — cited for premarket levels, value area, premium flow, CVD divergence and 0DTE gamma at the NY open.
  - Impact: Those section-9 claims are unsupported by their own citation. This is the single clearest indication that the section's Confidence rating is not calibrated.
- **D7** — The word 'rebalance' appears ZERO times in the document. No rebalance cadence is stated for any strategy.
  - Impact: Every rebalance cadence in this package is an ANALYST CHOICE, recorded as such in parameter_provenance. It is not a paper rule.

### Sections deliberately not implemented

These paper sections have no automation behind them. Each entry states why, and what would be needed to close the gap.

**charm_vanna**

- Why not: The papers' own subtitle promises 'charm surface, Vanna exposure', but both documents' body text says charm and vanna are NOT directly tested in the retrieved evidence and 'would be an inference rather than a directly supported finding'. The subtitle contradicts the body.
- Decision: Not implemented. Implementing an explicitly untested surface would be inventing a rule, which the papers themselves decline to do.
- To enable it: Requires live charm/vanna surfaces: a full option chain with dealer-side open interest per strike and expiry, plus a defined net-charm/net-vanna sign convention. The Nasdaq chain this package already fetches has OI and volume but not the dealer-sign and greeks needed for a defensible charm/vanna estimate.

**on_chain_feature_set**

- Why not: The papers rank on-chain signals #2 but never operationalize them: 'active users, hashrate, wallet activity, transaction volume' with no lookbacks or thresholds. A ranking is not a specification.
- Decision: Not implemented as a trading signal. The package's wallet tracking and meme-coin screening come from the MEME-COIN paper's concrete rules, not from these four features.
- To enable it: Needs a definition per feature, a lookback, a threshold, and a source for hashrate/active users that is not the Solana RPC.

**intraday_scalping_stack**

- Why not: Opening range, CVD divergence, premium-flow spikes, value-area/POC construction and 0DTE greeks are all required, and all are unavailable here: no Level-2, no trade-by-trade CVD, no intraday option greeks, and CBOE is unreachable from this host (Yahoo options return 401).
- Decision: Not implemented. The 'NASDAQ daily proxy' spec tests only the regime-conditional switching logic, explicitly NOT the gamma/order-flow/spread legs.
- To enable it: A paid intraday feed (CBOE or equivalent) plus a session-level bar builder. The 5-15 minute opening range, the value-area percentage, the CVD divergence rule and the premium-flow sign convention would still all need values — the papers state a range for the opening range and nothing for the rest.

**pairs_cointegration**

- Why not: The papers' reversion model is a PAIR/SPREAD model (cointegration, Hurst, dynamic hedge ratios). The backtest engine has no pair construction: no s-score, no hedge-ratio estimator, no pair universe screen.
- Decision: The SD-band mean-reversion specs compute single-name price z-scores — a weaker question than the papers' — and this is recorded in each spec's additional_conditions. variants_tried reflects the papers' own 1.0 vs 1.5 SD alternatives.
- To enable it: A pair universe with a formation window, a cointegration test, a hedge-ratio estimator (OLS/Kalman/dynamic) and a Hurst cutoff. The z-score entry threshold is the single most important missing value in both documents.

**gamma_computation_spec**

- Why not: The papers give the gamma SIGN rule (negative -> continuation, positive -> dampening) but no computation spec: strikes, expiries, OI source, dealer sign convention, or a magnitude threshold. The scalp sections contain no stop, target or R-multiple for any setup.
- Decision: The package computes gamma under a STATED assumed dealer book from a single aggregate open-interest snapshot, and states that assumption with every number. Only the SIGN is used as a regime switch, matching the papers.
- To enable it: Live per-expiry dealer-side OI, which no free endpoint provides.

### How to use this register

- A spec that depends on a defective section must be flagged in that defect's 'impacts_specs'.
- As of 2026-10-27 no spec in this package depends on a defective section: the defective material is in the intraday/scalping and on-chain sections, which are not implemented (see scope_exclusions).
- D2 (no numeric results) and D7 (no rebalance cadence) apply to EVERY spec, and are recorded per spec in parameter_provenance rather than once here.
- When a new spec is distilled from a paper, check it against this register before running it.

## 5. US officials' financial disclosures — three branches

### Legislative — Members of Congress

- Law: House: annual Financial Disclosure Report and Periodic Transaction Reports under the STOCK Act (5 U.S.C. 13101-13111 and House rules). Senate: the same regime via the Senate eFD system.
- Filings indexed: 1805
- By filing type: `{"Campaign Notice Regarding Financial Disclosure Requirement": 197, "Candidate Report": 874, "Financial Disclosure Extension Request": 247, "Periodic Transaction Report": 437, "Amendment Report": 46, "New Filer Report": 2, "Terminated Filer Report": 2}`

### Executive — Presidentially Appointed Officials (OGE 278e / 278-T)

- Law: OGE Form 278e (annual public financial disclosure) and Form 278-T (periodic transaction report) under 5 CFR part 2634.
- Filings indexed: 16794
- By agency (top): `[["Department of State", 3530], ["Department of Justice", 2205], ["White House Office", 699], ["Department of Defense/Office of The Secretary", 476], ["Department of Health and Human Services", 431], ["Department of Energy", 393], ["Department of The Treasury", 349], ["Department of Transportation", 312], ["Department of Commerce", 305], ["Federal Trade Commission", 305]]`
- With a public PDF: 4492 · request-form-only: 12295

### Judicial — Supreme Court Justices and federal judges

- Law: AO Form 10 annual financial disclosure, filed in JEFS under the Judicial Conference regime (5 U.S.C. 13101-13111).
- Filings indexed: 45
- Primary-source filings: 0 · secondary (mirrors): 45
- Provenance: Judicial records from mirrors are labelled [secondary]. The primary is JEFS, which is registration-gated and TCP-unreachable from this host.
- SCOTUS disclosure page: NOT FOUND on the live site. Verified by live fetch: 11 candidate paths return HTTP 404; the live sitemap's 365 hrefs contain no disclosure link; the on-site search returns no disclosure page. SETTLED by a complete Wayback CDX scan: the domain was partitioned by leading path character (40 partitions), the three that hit the row cap were subdivided by second character (121,743 further unique URLs), and 'reportable' appears in ZERO archived supremecourt.gov URLs. Prefix queries for reportable*, financial* and disclos* each return 0 rows. The only archived disclosure URL is the historical /publicinfo/disclosures/financialdisclosure.aspx (302, 2021-10-05). The one uncovered subtree is /docket*, the court-filing PDF range, excluded as docket noise.

**Coverage:** `{"legislative_house": true, "legislative_senate": false, "executive_oge": true, "judicial": true}`

**Source gaps** — these are availability problems, NOT statements that filings do not exist:

- **senate_efd** — HTTP 403 from this host on every *.senate.gov path (Akamai geo-block on the egress IP; www.house.gov returns 200 from the same IP). This is a SOURCE AVAILABILITY gap — it is NOT evidence that Senate filings do not exist.
- **jefs_database** — GET failed after 1 attempt(s): https://pub.jefs.uscourts.gov/ -> URLError: <urlopen error [WinError 10051] A socket operation was attempted to an unreachable network>
- **fixthecourt.com** — None
- **scotusblog.com** — None

Coverage is INCOMPLETE by design on this host: the Senate branch is IP-geo-blocked and the primary judicial database (JEFS) is registration-gated and TCP-unreachable. The report states this rather than presenting a partial view as a complete one.

---

*This report is produced by an automated research system. It is not investment advice. A SUPPORTED verdict means the hypothesis survived the validation stages that ran — nothing more.*