# PAPER CLAIM INVENTORY

**Six LeapSpace research papers -> complete enumeration of every testable, falsifiable, quantitative claim.**

Generated for the `leapspace-quant` package. This document is the INPUT to building additional backtest
specifications. It is an inventory, not a summary: every distinct falsifiable claim is enumerated with its
source location, implementation status against the existing 8 concepts (C1-C8) in
`leapspace/paperspecs.py`, the inputs it needs, its claim type, whether it is testable on this package's
daily-bar panels, and what would refute it.

> This file is ASSEMBLED, not hand-maintained. `reports/paper_claims_body.md` holds sections 1-8 (the
> inventory tables); `tools/build_claim_inventory.py` reads it, derives section 9 from the tables
> mechanically, and writes `reports/PAPER_CLAIM_INVENTORY.md`. Re-run the tool after editing the body.
> The `ALSO TESTED` status annotations are applied by `tools/annotate_claim_test_status.py`.

---

## 1. Source documents and the de-duplication map

The six PDFs are **not six independent papers**. Three of them are duplicates or subsets of the others. The
claims were enumerated once, at their most specific occurrence, and cross-referenced here so no claim is
double-counted and none is dropped.

| Code | File | Internal title | Pages | Relationship |
|---|---|---|---|---|
| **GAM** | `C:\Users\HP\Downloads\Gamma exposure and option flow.pdf` | "Options market dynamics and volatility" | 3 | Identical content to **RET pp.6-8**. Does NOT contain the "directional bias" section. |
| **RET** | `C:\Users\HP\Downloads\Trading_strategies_for_retail_traders_LeapSpace 2.0.pdf` | "Trading strategies for retail traders" | 75 | **Superset.** Contains the whole compilation: RET pp.1-54 == the non-2.0 PDF; pp.55-75 are 2.0-only additions. |
| **RET-1** | `C:\Users\HP\Downloads\Trading_strategies_for_retail_traders_LeapSpace.pdf` | "Trading strategies for retail traders" | 54 | Byte-for-byte the first 54 pages of **RET**. No unique claims. |
| **IND** | `C:\Users\HP\Downloads\trading view directional edge.pdf` | "Free trading indicators for directional edge" | 3 | Identical content to **RET pp.12-14**. |
| **REG** | `C:\Users\HP\Downloads\Financial_market_regime_identification_LeapSpace.pdf` | "Financial market regime identification" | 15 | Unique. |
| **NAS** | `C:\Users\HP\Downloads\NASDAQ_market_regime_identification_LeapSpace.pdf` | "NASDAQ market regime identification" | 18 | Unique. |

**Section map of RET (2.0), used for page citations below:**

| Pages | Section |
|---|---|
| 1-2 | Signal-family ranking (order flow / on-chain / options flow / indicators / retail flow) |
| 3-5 | References 1-38 |
| 6-8 | Options market dynamics and volatility (= **GAM**) |
| 9-11 | Option flow and gamma for directional bias |
| 12-14 | Free trading indicators for directional edge (= **IND**) |
| 15-19 | Momentum and Mean Reversion Trading Strategies |
| 20-22 | Trading strategies using order flow and volatility |
| 23-27 | Advanced momentum and mean-reversion trading models |
| 28-31 | Advanced Order Flow Scalping Strategies |
| 32-35 | Intraday scalping strategies and analysis |
| 36-38 | Intraday Scalping Strategy and Analysis |
| 39-41 | Intraday Scalping Strategies (acceptance/rejection, CVD divergence, gamma flips) |
| 43-45 | Intraday trading strategies and market analysis |
| 46-47 | Stop loss and trailing stop strategies |
| 48-51 | Standard deviation based stop-loss strategies |
| 52-54 | Standard deviation for scalping strategies |
| **55-75** | **2.0-ONLY**: volatility-normalized stop mechanics, trailing stops, Nasdaq index arithmetic, Bollinger Band configuration |

**De-duplication policy used:**
- A claim appearing in more than one file is counted **once**, under the most specific source code.
- Claims that are the **same mechanism with a different parameter** (e.g. "1.0 SD stop" vs "1.5 SD stop") are
  counted as **one** claim with a parameter range, not two claims.
- Claims that are **the same mechanism applied to a different market/regime** are counted as one claim with the
  scope noted, because a single backtest spec can test them across asset classes.
- Purely **arithmetic illustrations** with no falsifiable content (the "$100 +/- $4 Nasdaq" worked example, the
  "what is the current Nasdaq Composite level" exchange, the "is 29,000 +/-, 30,000 +/-, or 33,000" question)
  are excluded and listed in Appendix A.

**Citation convention:** the `Source` column gives the document code plus a section or page. Page numbers
are exact for GAM, IND and RET (whose page footers are unambiguous) and are **approximate** for REG and NAS,
whose PDF text layer merges some pages - there the section name is authoritative.

---

## 2. Legend

### 2.1 Claim type

| Code | Meaning | Is it tradable on its own? |
|---|---|---|
| `DIRECTIONAL` | Predicts a sign or a side (up/down, long/short, fade/follow, buy/sell) | **Yes** - this is an edge candidate |
| `GATE` | Changes *when* a strategy should fire (a regime filter, an enable/disable) | No - a gate cannot be an edge by itself; it modifies another signal |
| `SIZING` | How much to hold (position scale, leverage, cap, allocation ladder) | No - risk control |
| `TIMING` | When to enter/exit (horizon, holding period, time stop, refresh rate) | No - modifies an edge |
| `RISK` | A risk control (stop, drawdown, cost, impact, kill switch) | No - risk control |
| `MARKET-STATE` | A classifier: labels the market's state, predicts volatility/regime, not direction | No - a conditioner |
| `COMPARATIVE` | Claims that A beats B (rankings, ablations, "X outperforms Y") | Testable as an ablation, not as a standalone edge |
| `NEGATIVE` | A fragility / limitation / failure mode the paper states about its own claim | **Negative control** - should FAIL to profit if the claim holds |
| `PARAMETER` | A numeric configuration claim (lookback, threshold, band width) | Testable as a parameter sensitivity study |
| `METHOD` | A claim about how to *evaluate* (segmentation, ablation design, validation protocol) | Not an edge; a protocol |

A claim may carry more than one type. Where a claim is `GATE + DIRECTIONAL`, the DIRECTIONAL component is what
makes it tradable and the GATE component is the condition.

### 2.2 Implementation status

| Code | Meaning |
|---|---|
| `IMPLEMENTED` | The claim's core mechanism is directly tested by one of the 8 existing concepts (C1-C8) in `leapspace/paperspecs.py` |
| `PARTIAL` | A C1-C8 spec tests *part* of the claim (e.g. the gate but not the parameterisation, or one leg of a composite), but the claim as stated is not fully tested |
| `NOT` | Nothing in C1-C8 tests this claim |
| `EXCLUDED` | The paper itself says this is NOT supported by its evidence (e.g. charm, vanna). Recorded so it is never silently implemented. |

### 2.3 Inputs

`price` - OHLCV daily bars. `volume` - volume series. `IV` - implied volatility index (VIX/VXN/Deribit DVOL).
`optchain` - options chain / open interest / Greeks. `optflow` - options trade flow / order imbalance in options.
`orderflow` - signed trade flow, CVD, order-book depth/spread. `onchain` - blockchain/on-chain metrics.
`sentiment` - retail flow, attention, Fear&Greed. `intraday` - sub-daily bars, session windows, order book.
`credit` - credit-risk / credit-spread series. `macro` - macro releases, earnings calendar, macro series.

### 2.4 Daily-testability in THIS package

| Code | Meaning |
|---|---|
| `YES` | Testable on the package's existing daily-bar panels with the current feature registry |
| `PROXY` | The paper's own construct needs a proxy; the package has a proxy but the result is evidence about the proxy, not the construct |
| `EXT` | Testable on daily bars but needs a NEW feature to be written (small, contained work) |
| `NO` | Not testable here: needs intraday bars, a historical options chain, an order book, or a data feed the package does not have |

---

## 3. Engine reality check (verified against the code, not assumed)

This is what the "Daily?" column is measured against. Verified by reading the modules and by importing the
engine's registries.

**Data actually available**

| Input | Available? | Where |
|---|---|---|
| Daily OHLCV - equities, ETFs, indices, crypto, FX, commodities, futures, rates | **YES** | `leapspace/market.py` -> Yahoo chart; `UNIVERSE_PRESETS` = us_equity_broad, us_equity_style, futures_broad, fx_major, commodities, crypto, rates_credit, ... |
| Implied volatility index | **YES** | `leapspace/leading.py`: `^VIX`/`^VXN`/`^VXD` (yahoo.chart) for equities; Deribit `DVOL` paginated history for crypto |
| Realised volatility, volatility risk premium (IV - RV) | **YES** | `leapspace/leading.py` -> `build_leading_features` -> iv_level, rv_level, vrp, iv_zscore, vrp_zscore |
| Crypto funding rate + open interest | **YES** | `leapspace/cryptoderivs.py` -> `build_crypto_derivatives_features` |
| Options chain Greeks, gamma exposure, option flow | **PARTIAL** | `leapspace/gamma.py` (`bs_greeks`, `compute_gamma_exposure`, `compute_option_flow`), `leapspace/leading.py` (`deribit_gamma_exposure`, `deribit_option_flow`). **LIVE SNAPSHOT ONLY - no history.** Cannot be backtested as a time series without a chain archive. |
| On-chain / holders / token data | **YES** | `leapspace/onchain.py`, `leapspace/holders.py`, `leapspace/memecoinscan.py` |
| Social / sentiment | **YES** | `leapspace/social.py`, `leapspace/socialedge.py` |
| Intraday bars -> one session-opening-window bar per day | **YES** | skill `intraday.py`: `build_session_panel`, `f_session_drift`, `f_session_gap`, `f_session_return`, `flat_at_close` |
| Historical order book / L2 / spread / depth | **NO** | not present in any module |
| Historical options chain archive / historical OI / historical dealer gamma | **NO** | only a live Deribit snapshot |
| Macro release calendar / earnings calendar | **NO** | not present |

**Engine feature registry (verbatim):** `atr_pct, bollinger_pct, dist_to_high, ma_crossover, max_drawdown,
momentum, return, rsi, skew, sma_gap, vol_ratio, volatility, volume_ratio, zscore`
**Plus `leapspace`-registered:** `regime_momentum_score, leading_iv_level, leading_vrp_score, leading_vrp_zscore,
session_drift`
**Signal registry (verbatim):** `constant, cross_sectional, crossover, time_series_threshold, time_series_zscore`
**Plus `leapspace`-registered:** `regime_switch, regime_switch_cross_sectional, rsi_volume_confirmation,
leading_vrp_switch, vol_regime_momentum, volume_confirmed_momentum, rsi_confirmed_reversion,
rebound_danger_momentum, liquidity_gated_reversion, paper_cross_sectional`

**Risk block already in every spec (`RISK_BLOCK` in `paperspecs.py`):** `gross_leverage 1.0`,
`vol_target 0.15`, `vol_lookback 60`, `max_position 0.10`, `max_names 5`, `net_target 0.0`,
`long_only False`, `rebalance monthly`; execution `fill_at open`, `cost_multiplier 2.0`,
`max_participation 0.10`.
**Portfolio layer (`leapspace/portfolio.py`)** already implements: correlation-aware risk-parity sizing,
`target_vol` (default 0.15), EWMA/realised volatility blending, `gross_leverage`, `max_position`,
`net_target` (dollar-neutral), and a drawdown scaler (`dd_soft_limit 0.05`, `dd_hard_limit 0.20`).
`leapspace/riskguard.py` implements a latching kill switch with `max_drawdown_pct` default 0.20.

**The two structural gaps that drive most of the "NO" ratings:**
1. **No historical options chain.** Every claim that needs net gamma sign, delta/vega-adjusted option flow,
   strike distance, days-to-expiry, or put-call ratios as a *backtested time series* is `NO` here. The package
   can fetch them live, and `leapspace/gamma.py` can compute them, but a live snapshot cannot be backtested.
2. **No order-book history.** Every claim about CVD divergence, bid-ask spread, best-level depth, message
   intensity, or cancellation behaviour is `NO` here. The `session_drift` feature used by C7 is a
   price-and-volume *stand-in*, already disclosed as such in the C7 notes.

---

## 4. GROUP OPT - Options market dynamics, IV and gamma

Source: **GAM** pp.1-3 (= RET pp.6-8) and RET pp.9-11 ("Option flow and gamma for directional bias").
References in the papers are numbered [39]-[60]; they are preserved in the quotes.

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| OPT-01 | "Option flow helps forecast volatility because it reveals shifts in demand, inventory pressure, and hedging activity that move implied volatility and sometimes realized volatility." | GAM p1 | MARKET-STATE | NOT | optflow, IV, price | NO | Option flow carries no information about forward realised vol beyond the IV level already in the model. |
| OPT-02 | "In VIX options, net buying pressure is temporally linked to changes in implied volatility, and higher buying pressure lowers next-day delta-hedged option returns." | GAM p1 | DIRECTIONAL + MARKET-STATE | NOT | optflow, optchain, IV | NO | Net buying pressure does not predict next-day delta-hedged option returns once IV changes are controlled for. |
| OPT-03 | "In Shanghai ETF options, call and put order imbalances are tied to contemporaneous underlying returns and then reverse, which the authors attribute mainly to market-maker delta hedging rather than informed trading." | GAM p1 | DIRECTIONAL | NOT | optflow, price | NO | Imbalance shows no contemporaneous-then-reversing relationship with underlying returns. |
| OPT-04 | "Net demand pressure in TAIEX options has a significant impact on implied volatility level and slope, especially through unhedgeable risk; call buying pressure is negatively related to skewness and put buying pressure positively related to skewness." | GAM p1 | DIRECTIONAL + MARKET-STATE | NOT | optflow, optchain, IV | NO | Skew and IV-slope regressions on net demand pressure are insignificant out of sample. |
| OPT-05 | "Across stocks, FX, bonds, and index options, implied volatility often contains incremental information about future realized volatility, and in several studies it outperforms historical volatility forecasts." | GAM p1 | SIZING + MARKET-STATE | **IMPLEMENTED (C2)** | IV, price | YES | IV-based forecasts do not beat realised-vol forecasts of future realised vol on the same panel and horizon. |
| OPT-06 | "Gamma matters because hedging short gamma requires trading in the direction of price moves, which can create intraday momentum and amplify volatility." | GAM p1 | DIRECTIONAL + GATE | NOT | optchain, intraday | NO | Realised forward returns do not differ between negative- and positive-gamma periods. |
| OPT-07 | "In futures and spot markets linked to options, negative gamma exposure is associated with higher volatility." | GAM p2 | GATE + MARKET-STATE | NOT | optchain, IV, price | NO | Net gamma sign does not separate high- from low-realised-volatility periods. |
| OPT-08 | "One study finds that intraday momentum persists only when VIX options' net gamma exposure is negative." | GAM p2 | DIRECTIONAL (conditional) | NOT | optchain, intraday | NO | Intraday momentum is equally strong in positive-gamma periods. |
| OPT-09 | "Another finds that negative gamma exposure of option-market makers increases spot FX volatility, with a measurable effect in EURUSD and USDJPY." | GAM p2 | DIRECTIONAL + MARKET-STATE | NOT | optchain, price | NO | EURUSD/USDJPY realised vol is not higher in negative-gamma windows. |
| OPT-10 | "A broader simulation study finds that higher net gamma positioning reduces volatility and improves market stability, while negative gamma increases volatility and makes markets more fragile." | GAM p2 | GATE + MARKET-STATE | NOT | optchain, price | NO | No inverse relationship between net gamma and realised vol. |
| OPT-11 | "The 2023 stock study also finds that low net gamma exposure predicts higher future realized volatility, supporting gamma exposure as a forward-looking volatility signal." | GAM p2 | SIZING + MARKET-STATE | NOT | optchain, price | NO | Net gamma adds no forward forecasting power for future realised vol over an IV/vol-only model. |
| OPT-12 | "Use option flow as a near-term pressure signal. Buying pressure and order imbalance can flag impending volatility changes, especially around events or in markets where market makers must hedge aggressively." | GAM p2 (Practical interpretation 1) | GATE | NOT | optflow, IV | NO | Imbalance-conditioned vol changes are not distinguishable from unconditional vol changes. |
| OPT-13 | "Use gamma as a regime signal. Negative gamma suggests hedging flows may push volatility higher and create momentum, while positive gamma tends to damp volatility." | GAM p2 (Practical interpretation 2) | GATE | NOT | optchain | NO | Gamma sign does not separate momentum from mean-reversion regimes. |
| OPT-14 | "Use implied volatility as the baseline forecast. Across many markets, IV is usually the cleaner direct predictor of future realized volatility than historical volatility alone." | GAM p2 (Practical interpretation 3) | SIZING + MARKET-STATE | **IMPLEMENTED (C2)** | IV, price | YES | IV does not beat realised vol as a forward realised-vol predictor. |
| OPT-15 | "gamma exposure is much weaker as a pure direction signal and is better viewed as a price-pressure / volatility regime indicator rather than a forecast of up vs. down." | RET p9 | NEGATIVE | NOT | optchain, price | NO | A net-gamma sign signal produces a significant directional t-statistic net of costs. **(Negative control: must FAIL to profit.)** |
| OPT-16 | "For directional bias, option flow is the better tool than gamma, but only when you can separate informed trading from dealer hedging; gamma mainly tells you how strong and persistent the move may be, not its direction." | RET p9 (Bottom line) | COMPARATIVE | NOT | optflow, optchain | NO | Informed-flow option signals do not outperform gamma-signed signals at predicting direction. |
| OPT-17 | "Can contain directional information when trades are informed; positive and negative informed option trades map to value premium and discount, and options trading can predict stock returns in some settings." | RET p9 | DIRECTIONAL | NOT | optflow, price | NO | Informed option flow does not predict subsequent underlying returns out of sample. |
| OPT-18 | "Dealer hedging / inventory pressure ... Often creates temporary price pressure and reversals, so same-day direction from option flow can be misleading if it reflects hedging rather than information." | RET p9 | DIRECTIONAL + NEGATIVE | NOT | optflow, price | NO | Dealer-hedging-driven flow does not reverse. |
| OPT-19 | "If the signal is mostly order imbalance, it often reflects market-maker delta hedging, which can produce short-lived reversals rather than persistent direction." | RET p11 (Practical interpretation) | DIRECTIONAL | NOT | optflow, price | NO | Imbalance does not produce a short-horizon reversal. |
| OPT-20 | "Negative gamma can amplify both upside and downside moves depending on the initiating shock." | RET p11 | MARKET-STATE | NOT | optchain, price | NO | Negative-gamma windows show no excess absolute move. |
| OPT-21 | "hedging and inventory effects often dominate short-horizon price changes, while gamma is consistently stronger for volatility than for direction." | RET p11 (Confidence) | COMPARATIVE + NEGATIVE | NOT | optflow, optchain | NO | Option flow's directional skill equals or exceeds its volatility skill. |

---

## 5. GROUP IND - Free trading indicators for directional edge

Source: **IND** pp.1-3 (= RET pp.12-14).

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| IND-01 | "A good low-cost edge for him is price action + volume + regime filtering on TradingView, not indicator stacking: the evidence here supports price/volume reading, volume-based signals, RSI/EMA-type tools, and market-regime filters as the most practical substitutes when order flow, Level 2, and paid flow data are unavailable." | IND p1 | COMPOSITE | PARTIAL (C3+C4+C5 test the parts separately, not the composite) - ALSO TESTED: tradingview_price_volume_rsi_regime_filtered [crypto+equity mix] -> REFUTED| price, volume | YES | The composite is no better than any single leg. |
| IND-02 | "price action and simple technical rules can work better as a disciplined framework than as a 'signal soup'." | IND p1 | COMPARATIVE + NEGATIVE | NOT - ALSO TESTED: crypto_rsi_oversold_fade [crypto] -> REFUTED; tradingview_price_volume_rsi_regime_filtered [crypto+equity mix] -> REFUTED| price, volume | YES | A stacked multi-indicator signal outperforms the same rule tested one indicator at a time. **(Negative control on indicator stacking.)** |
| IND-03 | "Price-chart reading is presented as a straightforward, practical method that can improve entry/exit decisions without complex indicators." | IND p1 | DIRECTIONAL (discretionary) | NOT - NOT BACKTESTABLE AS STATED | price | NO | Requires a rule-level formalisation; no rule is given. Cannot be specified as a falsifiable signal without inventing the paper's rule. |
| IND-04 | "Volume carries information that price alone does not, and volume-based signals can improve forecastability in some settings." | IND p1 | DIRECTIONAL | **IMPLEMENTED (C4)** - ALSO TESTED: tradingview_price_volume_rsi_regime_filtered [crypto+equity mix] -> REFUTED| volume, price | YES | Volume confirmation does not improve on price-only momentum. |
| IND-05 | "In crypto, RSI was found more reliable than MACD or Stochastic for overbought/oversold style signals, and some indicator combinations using RSI/EMA/MACD/Bollinger show short-term usefulness." | IND p1 | DIRECTIONAL + COMPARATIVE | PARTIAL (C5 implements the RSI leg; the RSI-vs-MACD-vs-Stochastic ranking is untested) - ALSO TESTED: crypto_rsi_oversold_fade [crypto] -> REFUTED; tradingview_price_volume_rsi_regime_filtered [crypto+equity mix] -> REFUTED| price | YES | MACD or Stochastic gates produce equal or better results than the RSI gate on the same universe. |
| IND-06 | "Several studies show technical signals work better in certain regimes - medium-frequency components, recession-like periods, or mean-reverting conditions - rather than all the time." | IND p1 | GATE | **IMPLEMENTED (C3)** - ALSO TESTED: tradingview_price_volume_rsi_regime_filtered [crypto+equity mix] -> REFUTED| price, volume | YES | The regime filter does not change the signal's outcome. |
| IND-07 | "The evidence favors focused, rule-based systems over broad indicator stacks." | IND p2 | COMPARATIVE | NOT | price, volume | YES | A multi-indicator stack beats a single-rule system on the same universe and risk block. |
| IND-08 | "Use price action first, then volume, then one momentum filter. Price/volume analysis is repeatedly supported as a practical base, while volume and RSI add confirmation." | IND p2 | DIRECTIONAL (ordering) | NOT - ALSO TESTED: crypto_rsi_oversold_fade [crypto] -> REFUTED| price, volume | YES | The stated ordering of signal construction does not matter for outcomes. |
| IND-09 | "Trade only when the regime matches the strategy. Mean-reversion tools work better in some markets/periods, while trend tools work better in others." | IND p2 | GATE | **IMPLEMENTED (C1, C3, C8)** - ALSO TESTED: tradingview_price_volume_rsi_regime_filtered [crypto+equity mix] -> REFUTED; regime_switch_cross_sectional_sector_rotation [us_equity_style] -> SUPPORTED| price, volume | YES | Regime-conditional results are the same as unconditional results. |
| IND-10 | "Several studies warn that nice-looking indicator results can collapse once transaction costs and out-of-sample testing are included." | IND p2 | NEGATIVE | PARTIAL (the package's `cost_multiplier 2.0` + walk-forward embody this, but it is not a paper claim/spec) | price, volume | YES | Gross-of-cost performance survives the stressed cost case and out-of-sample. **(Negative control on cost sensitivity.)** |
| IND-11 | "the most defensible TradingView edge is a simple price-action system with volume confirmation and a regime filter, using RSI or EMA only as a secondary confirmation layer." | IND p2 (Bottom line) | COMPOSITE | PARTIAL - ALSO TESTED: tradingview_price_volume_rsi_regime_filtered [crypto+equity mix] -> REFUTED| price, volume | YES | Adding the regime filter and RSI layer to price+volume does not improve the result. |
| IND-12 | "the evidence is fairly consistent that price/volume and regime-based technical approaches are the best low-cost substitutes, but results vary by market, timeframe, and transaction costs." | IND p3 (Confidence) | COMPARATIVE | NOT | price, volume | YES | The same rule performs identically across markets, timeframes and cost levels. |
---

## 6. GROUP RET - Trading strategies for retail traders

Source: **RET** (2.0, 75pp). Claims RET-01..RET-86 also appear in **RET-1** (the 54-page PDF), which is the
same content. RET-87..RET-95 are **2.0-ONLY**.

### 6.1 Signal-family ranking (RET pp.1-2)

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| RET-01 | "On-chain and blockchain variables repeatedly improve crypto forecasting and regime detection, with studies finding strong performance for active users, hashrate, wallet activity, transaction volume, and related features." | RET p1 | DIRECTIONAL + MARKET-STATE | NOT (the package has `onchain.py`/`holders.py`/`socialedge.py`, but no C-spec tests this) | onchain, price | YES (crypto) | On-chain features add no forecastability over price+volume on the same crypto panel. |
| RET-02 | "Some technical rules work in crypto, but results are mixed: candlestick and indicator-based studies find pockets of predictive power, yet other work says technical rules have limited practical value." | RET p1 | DIRECTIONAL + COMPARATIVE | NOT | price | YES | Candlestick rules are uniformly profitable and stable across samples. |
| RET-03 | "Retail trading behavior and retail attention are often noisy or contrarian: retail crypto order behavior predicts returns in one study, but retail option activity is linked to poorer option returns, and retail attention can hurt returns." | RET p1 | DIRECTIONAL (contrarian) | NOT | sentiment, onchain | YES | Retail attention has no contrarian predictive power. |
| RET-04 | "Options order flow can inform future volatility, but not consistently future returns; retail option demand is associated with lower option returns, and net gamma is negatively related to future volatility in one study." | RET p1 | MARKET-STATE + NEGATIVE | NOT | optflow, optchain | NO | Options flow predicts future returns as consistently as it predicts future volatility. |
| RET-05 | "Charm surface and vanna exposure are not directly tested in the retrieved evidence, so any claim that they are the 'best' retail edge would be an inference rather than a directly supported finding." | RET p2 | NEGATIVE | **EXCLUDED** (correctly) | optchain | NO | n/a - the paper states there is no evidence. Recorded so charm/vanna is never implemented as if evidenced. |
| RET-06 | "Order flow + liquidity/volatility regime filtering - strongest general edge because it appears across markets and repeatedly ties to volatility, information, and execution quality." | RET p2 (ranking 1) | COMPARATIVE | PARTIAL (C7 is the order-flow base; the ranking against the other families is untested) | orderflow, price, volume | PROXY | Order-flow signals do not beat on-chain or indicator signals on the same risk block. |
| RET-07 | "On-chain / blockchain signals for crypto - strongest crypto-specific edge, especially when combined with sentiment and market-state features." | RET p2 (ranking 2) | COMPARATIVE | NOT | onchain, sentiment | YES (crypto) | On-chain features do not beat price/volume on crypto. |
| RET-08 | "Options flow / gamma-style volatility positioning - useful for forecasting volatility, weaker for outright direction." | RET p2 (ranking 3) | COMPARATIVE | NOT | optflow, optchain | NO | Options flow is as directional as it is volatility-informative. |
| RET-09 | "Classic indicators alone - can work, but the evidence is inconsistent and usually weaker than microstructure or blockchain features." | RET p2 (ranking 4) | COMPARATIVE | PARTIAL (C5 is an indicator rule; the comparison is untested) | price | YES | Indicator signals beat microstructure features. |
| RET-10 | "the most defensible path is trade only when order flow, volatility regime, and liquidity conditions align, then use on-chain/blockchain signals for crypto and options flow for volatility timing; that combination is better supported than relying on indicators, candlestick patterns, or untested charm/vanna overlays." | RET p2 (Bottom line) | GATE (three-way alignment) | NOT | orderflow, price, volume, IV | PROXY | The three-way alignment gate does not improve over any single condition. |

### 6.2 Momentum and Mean Reversion Trading Strategies (RET pp.15-19)

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| RET-11 | "Order flow can contain information about future volatility and returns in several markets, but the effect depends on trader type, trade size, liquidity, and execution costs; in crypto, trade-flow imbalance and order-book features often matter more than broad technical rules." | RET p1 | DIRECTIONAL + GATE | **IMPLEMENTED (C7)** - but only via the session-drift proxy | orderflow, price, volume | PROXY | The daily-bar session-drift proxy carries no directional information. |
| RET-12 | "in crypto, trade-flow imbalance and order-book features often matter more than broad technical rules." | RET p1 | COMPARATIVE | PARTIAL (C7) | orderflow, price | PROXY | The proxy does not beat the technical rule on crypto. |
| RET-13 | "Momentum and trend rules are more likely to survive in liquid assets and are sensitive to transaction costs and turnover." | RET p15 | UNIVERSE + RISK | NOT (no liquidity-ranked universe selection in any spec) - ALSO TESTED: crypto_ma20_trend_momentum [crypto] -> REFUTED; nasdaq_12m_timeseries_momentum [us_equity_style] -> SUPPORTED| price, volume | YES | Momentum works equally well in illiquid names, or the effect vanishes once costs are stressed. |
| RET-14 | "Use a 12-month time-series momentum on Nasdaq and a shorter, crypto-adapted trend window such as 20-day or 2-4 week lookback for crypto." | RET p15 | DIRECTIONAL + TIMING | NOT (C1 uses a 60-day momentum feature inside a regime switch; there is no standalone time-series-momentum spec and no 12-month horizon) - ALSO TESTED: nasdaq_12m_timeseries_momentum [us_equity_style] -> SUPPORTED; v1_nasdaq_12m_tsm_vol_scaled [us_equity_style] -> REFUTED; crypto_ma20_trend_momentum [crypto] -> REFUTED; v1_crypto_momentum_20d_ma [crypto] -> FRAGILE| price | YES | The stated horizons do not beat the 60-day default, or the Nasdaq and crypto optima are the same. |
| RET-15 | "Time-series momentum is conventionally built on the past 12-month return, while crypto evidence shows short-horizon momentum can exist and 20-day moving-average rules can work." | RET p15 | DIRECTIONAL | NOT | price | YES | 12-month and 20-day momentum have the same cross-sectional predictive power. |
| RET-16 | "Go long when price is above its trend proxy; go short or flat when below, if your venue supports it." | RET p15 | DIRECTIONAL (long/short) | NOT - ALSO TESTED: nasdaq_12m_timeseries_momentum [us_equity_style] -> SUPPORTED; v1_nasdaq_12m_tsm_vol_scaled [us_equity_style] -> REFUTED| price | YES | The long/short trend rule has no positive risk-adjusted result net of costs. |
| RET-17 | "Trade only when realized volatility is not extreme, and scale position size by inverse volatility." | RET p15 (Risk filter) | GATE + SIZING | PARTIAL (C3 implements the gate; inverse-vol scaling exists only as the generic `vol_target 0.15` in the risk block, not as the paper's inverse-vol rule applied to the signal) - ALSO TESTED: nasdaq_12m_timeseries_momentum [us_equity_style] -> SUPPORTED; v1_nasdaq_12m_tsm_vol_scaled [us_equity_style] -> REFUTED; v1_crypto_momentum_20d_ma [crypto] -> FRAGILE| price | YES | Vol filtering and inverse-vol sizing do not improve the momentum result. |
| RET-18 | "Risk-managed momentum improves crypto performance, and volatility scaling is a core part of momentum strategy design." | RET p15 | SIZING | PARTIAL - ALSO TESTED: nasdaq_12m_timeseries_momentum [us_equity_style] -> SUPPORTED; crypto_ma20_trend_momentum [crypto] -> REFUTED| price | YES | Inverse-vol scaling does not improve risk-adjusted momentum. |
| RET-19 | "Stop-loss momentum outperforms other crypto momentum variants and improves downside control." | RET p15 (Stop rule) | RISK | NOT (no stop-loss overlay exists in any C-spec) - ALSO TESTED: nasdaq_12m_timeseries_momentum [us_equity_style] -> SUPPORTED| price | YES | A stop-loss overlay does not improve return, Sharpe or downside control over the unstopped momentum rule. |
| RET-20 | "Crypto momentum is temporally heterogeneous and can fail in some sample periods; trend-based rules perform better in some bull regimes than others." | RET p15 (Regime filter) | GATE + NEGATIVE | PARTIAL (C1/C3 capture regime dependence; "can fail in some sample periods" is untested) - ALSO TESTED: nasdaq_12m_timeseries_momentum [us_equity_style] -> SUPPORTED| price | YES | Momentum performs equally in all sub-periods and all bull regimes. |
| RET-21 | "Entry: long if close > 20-day moving average and 20-day return is positive; short or exit if not." | RET p15 (Practical momentum version) | DIRECTIONAL (explicit rule) | NOT - ALSO TESTED: crypto_ma20_trend_momentum [crypto] -> REFUTED; nasdaq_12m_timeseries_momentum [us_equity_style] -> SUPPORTED; v1_crypto_momentum_20d_ma [crypto] -> FRAGILE| price | YES | This exact rule has no positive risk-adjusted result net of costs. |
| RET-22 | "Sizing: volatility-scaled position size with a capped max allocation." | RET p15 | SIZING | PARTIAL - ALSO TESTED: crypto_ma20_trend_momentum [crypto] -> REFUTED; v1_crypto_momentum_20d_ma [crypto] -> FRAGILE| price | YES | Fixed-dollar sizing performs the same. |
| RET-23 | "Exit: stop-loss plus trend failure exit." | RET p15 | TIMING + RISK | NOT - ALSO TESTED: crypto_ma20_trend_momentum [crypto] -> REFUTED; v1_crypto_momentum_20d_ma [crypto] -> FRAGILE| price | YES | The exit rule does not change the result. |
| RET-24 | "Crypto pairs trading works better when the spread is well-behaved and liquidity is high; dynamic cointegration and higher-frequency data improve results." | RET p16 | DIRECTIONAL (pairs) | NOT | price, volume | YES | Pair spreads do not mean-revert profitably, or liquidity/cointegration quality does not predict which pairs work. |
| RET-25 | "Mean-reversion evidence in crypto is strongest for pairs/spread frameworks, and the Hurst exponent can identify faster reversion; resilient filtering and dynamic cointegration help stabilize signals." | RET p16 | DIRECTIONAL (pairs) + MARKET-STATE (pair selector) | NOT | price | YES | Single-asset z-score reversion matches the pairs result, or Hurst does not predict reversion speed. |
| RET-26 | "Enter when spread is stretched beyond a threshold; optionally use a buffer zone to avoid noise." | RET p16 (Entry) | TIMING / DIRECTIONAL | NOT (C5/C8 use a single-asset z-score, not a pair spread with a buffer zone) - ALSO TESTED: sd_band_mean_reversion_crypto [crypto] -> REFUTED| price | YES | The entry threshold does not predict reversion. |
| RET-27 | "Exit when spread reverts to mean; use tight time stops because crypto mean reversion can be fast." | RET p16 (Exit) | TIMING | NOT - ALSO TESTED: sd_band_mean_reversion_crypto [crypto] -> REFUTED| price | YES | Holding longer does not reduce net returns. |
| RET-28 | "Crypto reversal can switch within about a month, and shorter holding periods help preserve returns against costs." | RET p16 | TIMING + HORIZON | NOT | price | YES | Holding-period length has no effect on net returns. |
| RET-29 | "Require a regime check: only trade mean reversion when the asset/pair is not in a strong trend." | RET p16 (Risk filter) | GATE | PARTIAL (C8 gates on liquidity and volatility, not on trend strength) - ALSO TESTED: sd_band_mean_reversion_crypto [crypto] -> REFUTED| price | YES | Adding a trend-strength gate does not improve reversion. |
| RET-30 | "mean-reversion strategies can under-perform in trending periods." | RET p16 | GATE + NEGATIVE | PARTIAL (C8) | price | YES | Reversion performs equally in trending and ranging periods. |
| RET-31 | "For Nasdaq: use a cointegration or spread model on stable pairs, with a z-score entry and a mean-reversion exit. Cointegration-style pairs trading and mean-reversion filters are consistently supported." | RET p16 | DIRECTIONAL (pairs, long/short) | NOT | price | YES | Pair trading has no positive net result on Nasdaq pairs. |
| RET-32 | "For crypto: use dynamic cointegration or Hurst-filtered pairs, with a short holding period and transaction-cost-aware exits. Crypto pairs trading shows intraday mean reversion and better results at higher frequency." | RET p16 | DIRECTIONAL (pairs) | NOT | price | YES | Crypto pairs trading has no positive net result. |
| RET-33 | "regime-switching and faster holding periods improved pairs-trading results in the retrieved studies." | RET p25 | GATE + TIMING | NOT | price | YES | Regime switching does not improve pairs results. |

### 6.3 Trading strategies using order flow and volatility (RET pp.20-22)

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| RET-34 | "Order flow is a major mechanism through which private information gets into prices, and informed flow is positively related to volatility and returns in several markets." | RET p20 | DIRECTIONAL + MARKET-STATE | PARTIAL (C7) | orderflow, price | PROXY | The proxy is unrelated to forward returns or vol. |
| RET-35 | "Microstructure design also affects how informative and executable quotes are, with tighter spreads and better quote quality attracting more order flow." | RET p20 | CONDITION | NOT | orderflow (spread/depth) | NO | Tight spreads do not attract more order flow. |
| RET-36 | "Net buying pressure affects implied volatility and the shape of the implied-volatility function, and options trading can contain information about future realized volatility in volatility-sensitive strategies." | RET p20 | MARKET-STATE | NOT | optflow, optchain, IV | NO | Net buying pressure does not affect the IV level or slope. |
| RET-37 | "Options-implied measures can also help identify momentum stage and improve stage-aware momentum selection." | RET p20 | DIRECTIONAL + MARKET-STATE (stage) | NOT | IV, optchain | NO | Options-implied stage carries no information about forward returns. |
| RET-38 | "Options order flow can transmit information to the underlying market through informed trading or dealer hedging, but direction is weaker than the volatility signal because some flow is just inventory management." | RET p20 | NEGATIVE + COMPARATIVE | NOT | optflow | NO | Options flow is as directional as it is volatility-informative. |

### 6.4 Advanced momentum and mean-reversion trading models (RET pp.23-27)

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| RET-39 | "volume-augmented momentum beat pure price momentum in the UK study." | RET p23 | DIRECTIONAL (augmentation) | **IMPLEMENTED (C4)** - ALSO TESTED: crypto_xs_momentum_volume_confirmed [crypto] -> REFUTED| volume, price | YES | Volume confirmation does not improve on price-only momentum. |
| RET-40 | "order-imbalance momentum outperformed plain price momentum in Taiwan." | RET p23 | DIRECTIONAL | NOT (C7 ranks the universe on session drift; no order-imbalance momentum-confirmation leg) - ALSO TESTED: crypto_xs_momentum_volume_confirmed [crypto] -> REFUTED (declared but UNENFORCED)| orderflow, price | NO | Order-imbalance confirmation does not improve momentum. |
| RET-41 | "the retrieved study found early-stage momentum outperformed conventional momentum, while late-stage momentum underperformed." | RET p23 | DIRECTIONAL + GATE (stage) | NOT | IV, optchain | NO | Options-implied momentum stage does not separate winners from losers. |
| RET-42 | "Go long when price is above its trend proxy, volume is rising, and order imbalance/turnover is positive." | RET p24 | DIRECTIONAL (composite entry) | NOT - ALSO TESTED: crypto_xs_momentum_volume_confirmed [crypto] -> REFUTED| price, volume, orderflow | NO | The three-condition entry is no better than the price-only rule. |
| RET-43 | "Avoid trades when options-implied measures suggest the move is in a late momentum stage." | RET p24 | GATE | NOT | IV, optchain | NO | The late-stage gate does not improve results. |
| RET-44 | "Size positions by inverse volatility and cut losers quickly; this is consistent with the volatility-normalized momentum literature and the deep-learning/changepoint result that momentum improves when it adapts faster to regime change." | RET p24 | SIZING + TIMING | PARTIAL (inverse-vol sizing exists as the generic risk block; "adapts faster to regime change" untested) | price | YES | Inverse-vol sizing and fast adaptation do not improve momentum. |
| RET-45 | "A pure momentum rule is weaker than a momentum rule that uses volume, order imbalance, and options-implied stage information. Across the evidence, the more robust versions are the ones that incorporate participation and regime context, not just past return direction." | RET p24 | COMPARATIVE (ablation) | PARTIAL (C4 tests the volume leg only) - ALSO TESTED: crypto_xs_momentum_volume_confirmed [crypto] -> REFUTED| price, volume, orderflow | PROXY | The augmented rule is no better than the pure rule. |
| RET-46 | "Enter long when price is stretched below fair value, order imbalance is extreme, and options activity implies temporary pressure rather than sustained informed demand." | RET p24 | DIRECTIONAL (composite reversion entry) | NOT | price, orderflow, optflow | NO | The composite reversion entry does not predict the reversion. |
| RET-47 | "Enter short on the opposite setup when the stretch and pressure reverse." | RET p24 | DIRECTIONAL (short leg) | NOT | price, orderflow, optflow | NO | The short leg of the reversion setup is not profitable. |
| RET-48 | "Exit fast when spread normalizes; shorter holding periods produced better performance in the regime-switching pairs study, and intraday or short-horizon reversion was repeatedly more viable than long holds." | RET p24 | TIMING | NOT | price | YES | Holding-period length has no effect on net returns. |
| RET-49 | "order imbalance in both stocks and options can create short-lived reversals and is often tied to hedging pressure." | RET p24 | DIRECTIONAL (reversal) | NOT | orderflow, optflow | NO | Imbalance does not produce a short-lived reversal. |
| RET-50 | "options flow was shown to be informative for volatility but not reliably for direction." | RET p24 (Options overlay) | NEGATIVE | NOT | optflow | NO | Options flow predicts direction as reliably as volatility. |

### 6.5 Advanced Order Flow Scalping Strategies (RET pp.28-31)

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| RET-51 | "Intraday volume and return relations are strong in derivatives and futures markets, and informed trading / price discovery is concentrated during regular trading hours when volume and volatility are highest." | RET p28 | TIMING + MARKET-STATE (session) | NOT | intraday, volume | NO (partially EXT: session-window returns are buildable from `intraday.py`, but the volume/return relation within the session is not) | Return-volume relation is not stronger in the regular session than outside it. |
| RET-52 | "Intraday liquidity is not uniform: spreads, depth, and trading activity vary materially by time of day, and execution conditions differ around open/close and news windows." | RET p28 | MARKET-STATE (session) | NOT | intraday, orderflow | NO | Session makes no difference to liquidity or execution. |
| RET-53 | "Overnight return patterns can predict intraday behavior in some markets, and the open/close are structurally important because traders adjust for overnight risk and information arrival." | RET p28 | DIRECTIONAL (overnight -> intraday) | NOT | price, intraday | NO (the predictor is daily-computable, the target is not) | Overnight return does not predict the intraday session's direction. |
| RET-54 | "0DTE deltas change rapidly and require frequent hedging, making them especially noisy for scalping if you treat them as a clean directional signal." | RET p29 | NEGATIVE | NOT | optchain, intraday | NO | 0DTE flow is a clean directional signal. **(Negative control: must FAIL to profit.)** |
| RET-55 | "Negative gamma is the cleaner continuation / momentum regime, while positive gamma is more consistent with dampening and mean reversion." | RET p29 | GATE | NOT | optchain | NO | Gamma sign does not separate continuation from mean-reversion regimes. |
| RET-56 | "Intraday volume also tends to follow a U-shaped or M-shaped pattern, so the early session and late session usually deserve more weight than mid-session noise." | RET p32 | MARKET-STATE (session seasonality) | NOT | intraday, volume | NO | Session volume is flat, or mid-session is not the noisiest part of the day. |
| RET-57 | "Treat these as the day's first auction boundaries; breaks that fail back inside often matter more than small inside-day moves." (premarket high/low/balance area) | RET p32 | DIRECTIONAL (reversal at level) | NOT | intraday, price | NO | Failed breaks of prior-day levels do not reverse more than in-day moves. |
| RET-58 | "Use high-volume areas as acceptance zones and low-volume areas as fast-travel zones; intraday volume patterning is important for execution and liquidity." | RET p32 | MARKET-STATE (liquidity zones) | NOT | intraday, volume | NO | Price does not travel faster through low-volume areas. |
| RET-59 | "Use it as the first real test of whether premarket levels are being accepted or rejected; trading activity spikes around the open." (first 5-15 minute range) | RET p32 | TIMING | NOT | intraday, volume | NO | The opening range carries no information about the rest of the session. |

### 6.6 Intraday scalping strategies and analysis (RET pp.32-35)

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| RET-60 | "Net premium flow becomes more useful for reversals when it disagrees with CVD or fails to generate follow-through." | RET p32 | DIRECTIONAL (divergence) | NOT | optflow, orderflow | NO | Premium flow disagreeing with CVD does not precede a reversal. |
| RET-61 | "A strong impulse into a low-volume area then stalls near volume-profile extremes: that is a better candidate for a fade than a breakout continuation." | RET p32 | DIRECTIONAL (fade) | NOT | intraday, volume | NO | The fade is not better than the continuation. |
| RET-62 | "Fade long when price sweeps a premarket low, premium flow shows aggressive put buying or bearish pressure, but CVD stops making new lows and price reclaims the level." | RET p32 | DIRECTIONAL (fade long) | NOT | price, orderflow, optflow, intraday | NO | The fade setup does not produce positive net returns. |
| RET-63 | "Fade short when price sweeps premarket high, premium flow is aggressive on calls, but CVD fails to confirm and price loses the level." | RET p32 | DIRECTIONAL (fade short) | NOT | price, orderflow, optflow, intraday | NO | The fade setup does not produce positive net returns. |
| RET-64 | "If gamma flips more negative into the open, treat the session as more likely to trend and be less forgiving of countertrend entries." | RET p33 | GATE | NOT | optchain, intraday | NO | Gamma sign does not predict whether the session trends or chops. |
| RET-65 | "If gamma is positive or becomes less negative, treat the open as more likely to chop, rotate, or revert after the first impulse." | RET p33 | GATE | NOT | optchain, intraday | NO | Gamma sign does not predict whether the session trends or chops. |
| RET-66 | "If gamma shifts but CVD and tape speed do not confirm, the gamma signal is probably telling you about regime, not immediate direction." | RET p33 | GATE + NEGATIVE | NOT | optchain, orderflow | NO | Gamma sign predicts immediate direction as well as regime. |

### 6.7 Intraday Scalping Strategy and Analysis (RET pp.36-38)

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| RET-67 | "Reversal risk is higher around the open because the market often overreacts there before prices normalize." | RET p36 (and p43) | DIRECTIONAL (reversal) + TIMING | NOT | intraday, price | NO | Opening overreaction does not reverse. |
| RET-68 | "opening prices can be biased high relative to intraday prices, with reversals concentrated near the open." | RET p39 | DIRECTIONAL (open vs intraday) | NOT | intraday, price | NO | Opens are not biased high, or the bias does not reverse. |

### 6.8 Acceptance / rejection, CVD divergence and gamma flips (RET pp.39-45)

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| RET-69 | "opening-range acceptance shows up when price holds beyond the opening range with supportive volume and no immediate CVD failure, rejection shows up when price sweeps the range edge and quickly re-enters the prior area with divergent CVD." | RET p39 | MARKET-STATE (acceptance/rejection classifier) + DIRECTIONAL | NOT | intraday, volume, orderflow | NO | The acceptance/rejection read does not distinguish extending from reverting breaks. |
| RET-70 | "gamma flips mainly change whether the opening-range breakout is likely to continue or fail by altering liquidity/hedging pressure rather than by giving a clean directional bias." | RET p39 | GATE | NOT | optchain, intraday | NO | Gamma sign does not change breakout continuation odds. |
| RET-71 | "New high + stronger CVD = more consistent with acceptance; New low + weaker CVD = more consistent with acceptance lower." (confirmation, not divergence, is the cleaner continuation signal) | RET p44 | DIRECTIONAL (continuation confirmation) | NOT | orderflow, intraday | NO | CVD confirmation does not predict continuation. |
| RET-72 | "The most reliable edge is not any single metric alone, but the alignment of location (opening range/premarket level), confirmation (CVD), and regime (gamma)." | RET p40 (Bottom line) | COMPOSITE | NOT | intraday, orderflow, optchain | NO | The three-part alignment is not better than any single part. |

### 6.9 Stop loss and trailing stop strategies (RET pp.46-47)

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| RET-73 | "the best stop framework is: tight-to-moderate trailing stop for momentum, and wider hard stop or time stop for mean reversion - because stop-losses help momentum payoffs but can hurt mean-reversion returns by cutting off the rebound." | RET p46 | RISK | NOT - ALSO TESTED: sd_band_mean_reversion_crypto [crypto] -> REFUTED| price | YES | A tight trailing stop on momentum and a wide fixed stop on reversion do not beat the unstopped rules. |
| RET-74 | "Stop-loss momentum outperformed other momentum variants in crypto, and broader trailing-stop studies found narrower stops reduce returns while wider stops perform better; one empirical result suggests thresholds around 1.0 to 1.5 standard deviations were stronger than tight stops." | RET p46 | RISK | NOT | price | YES | Stop width has no monotone effect on momentum returns. |
| RET-75 | "For mean-reverting spreads, stop-losses should sit outside the entry region; higher stop-loss levels lower the optimal take-profit level, and stop-loss policies can reduce expected returns because they cut off the reversal that reversion strategies depend on." | RET p46 | RISK | NOT - ALSO TESTED: sd_band_mean_reversion_crypto [crypto] -> REFUTED| price | YES | Adding a stop outside the entry band does not reduce reversion returns. |
| RET-76 | "For crypto momentum, the evidence is especially supportive of using stop-loss rules because they improved returns, Sharpe, and alpha across many coins and across market states." | RET p46 | RISK | NOT | price | YES | Stop-loss rules do not improve return, Sharpe or alpha. |
| RET-77 | "Avoid a tight trailing stop, because mean reversion needs room to snap back and stop-losses can destroy that edge." | RET p46 | RISK + NEGATIVE | NOT | price | YES | A tight trailing stop improves reversion results. |
| RET-78 | "Prefer a time stop if the spread does not revert quickly, since short-horizon reversion is where the edge is strongest and prolonged holds increase damage from drift or costs." | RET p46 | TIMING + RISK | NOT - ALSO TESTED: sd_band_mean_reversion_crypto [crypto] -> REFUTED| price | YES | Holding longer does not increase drift/cost damage. |

### 6.10 Standard deviation based stop-loss strategies (RET pp.48-51)

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| RET-79 | "1 and 1.5 standard deviation thresholds produced better results than the classic pairs-trading setup in one study, and a separate trailing-stop study found higher thresholds, typically 1.0 to 1.5 standard deviations, delivered higher excess returns than narrower ones." | RET p48 | RISK + PARAMETER | NOT - ALSO TESTED: sd_band_mean_reversion_crypto [crypto] -> REFUTED; v1_sd_band_mean_reversion_1_0_1_5 [crypto] -> REFUTED| price | YES | Band width has no effect on net returns, or the optimum is not in 1.0-1.5 SD. |
| RET-80 | "That makes the band a selectivity filter: tighter bands trigger more often but are noisier; wider bands trigger less often but usually on cleaner extremes." | RET p48 | PARAMETER | NOT - ALSO TESTED: v1_sd_band_mean_reversion_1_0_1_5 [crypto] -> REFUTED| price | YES | Tighter bands are not noisier, or wider bands are not cleaner. |
| RET-81 | "Measure the recent standard deviation. Use a rolling window, often around a trading month in research examples." (20-day rolling SD) | RET p48 | PARAMETER | NOT (paper-grounded window not used; the package uses a 20-bar realised-vol lookback for `volatility` but no SD band feature) - ALSO TESTED: v1_sd_band_mean_reversion_1_0_1_5 [crypto] -> REFUTED| price | YES | The 20-day window is not better than alternatives. |
| RET-82 | "1.0 SD = first alert zone. 1.5 SD = stronger signal zone. You can use the band as an entry trigger, an exit trigger, or a stop buffer." | RET p48 | RISK + TIMING | NOT - ALSO TESTED: sd_band_mean_reversion_crypto [crypto] -> REFUTED; v1_sd_band_mean_reversion_1_0_1_5 [crypto] -> REFUTED; bollinger20_2_breakout_crypto [crypto] -> REFUTED| price | YES | The 1.0/1.5 SD band is not a better entry/exit/stop than the alternatives. |
| RET-83 | "Mean reversion long: if price drops to $96 or lower, you may start looking for a bounce; $94 is the more extreme, higher-conviction stretch." (two-tier 1.0 SD / 1.5 SD entry) | RET p50 | DIRECTIONAL (two-tier entry) | NOT | price | YES | The two-tier band does not predict the bounce, or the 1.5 SD tier is not the higher-conviction one. |
| RET-84 | "these thresholds can apply to scalping, but only as volatility/exit filters, not as a universal entry signal." | RET p52 | GATE (classification of the band) | NOT - ALSO TESTED: bollinger20_2_breakout_crypto [crypto] -> REFUTED| price | YES | The SD band works as a standalone entry signal. |

### 6.11 Standard deviation for scalping strategies (RET pp.52-54)

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| RET-85 | "Intraday mean reversion appears at shorter observation intervals, while momentum can dominate at even shorter intervals; that switching pattern is consistent with scalping being interval-dependent." | RET p52 | DIRECTIONAL + HORIZON | NOT - but **the highest-value untested claim in this group** | price | YES | The reversal-then-momentum ordering by horizon does not hold on daily bars when the lookback is varied. |
| RET-86 | "Stop-losses can improve momentum-style systems, but in some settings too-tight stops reduce performance or increase downside exposure; the best results in the retrieved studies come from moderate, not ultra-tight, thresholds." | RET p53 | RISK | NOT | price | YES | Stop tightness has no effect on performance or downside. |

### 6.12 RET 2.0-ONLY (RET pp.55-75) - absent from the 54-page PDF

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| RET-87 | "For a BTC momentum long, the 1.0 standard deviation rule is better understood as a volatility-based stop distance from your entry or reference price, not '1 SD of the current price' in a raw sense." | RET p55 | RISK | NOT | price | YES | The stop measured from the entry is materially worse than one measured from the current price. |
| RET-88 | "The evidence on Bitcoin says volatility is high, persistent, and regime-dependent, so a stop that is too tight is more likely to get clipped by noise." | RET p55 | RISK + MARKET-STATE (vol persistence) | NOT | price | YES | Bitcoin volatility is not persistent, or tight stops are not clipped more often. |
| RET-89 | "A volatility-normalized stop band means your stop is set as a distance measured in units of recent market volatility, not as a fixed dollar or percentage amount." | RET p57 | RISK + SIZING | NOT | price | YES | A fixed-percent stop performs the same as a volatility-scaled stop. |
| RET-90 | "It adapts to regime changes: higher volatility usually means a wider stop band is needed." | RET p58 | SIZING + RISK | NOT | price | YES | A constant stop width performs the same across volatility regimes. |
| RET-91 | "For a BTC momentum long, you can trail the stop upward as price rises, and a 1.0 to 1.5 standard deviation band is a reasonable way to size that trailing distance because the evidence favors moderately wide, volatility-scaled stops over tight ones in crypto momentum and trailing-stop settings." | RET p59 | RISK (trailing) | NOT | price | YES | A trailing stop does not improve momentum results. |
| RET-92 | "Do not anchor the stop to the original entry only; instead, ratchet the stop up as BTC makes new highs, using a recent volatility measure as the buffer." | RET p59 | RISK (ratchet) | NOT | price | YES | An entry-anchored trailing stop performs the same as a ratcheted one. |
| RET-93 | "HFT scalpers can increase intraday volatility, worsen market quality, and front-run order flow in some settings." / "Scalping can be effective for the trader but costly or disruptive in execution-heavy markets." | RET p68 | NEGATIVE (market impact) | NOT | intraday, volume | NO | Scalping does not raise intraday volatility or worsen market quality. |
| RET-94 | "The standard Bollinger Bands setting is a 20-period moving average with bands set at 2 standard deviations above and below the middle band." / "Some studies test different band widths such as 1.5, 2, 2.5, or 3 standard deviations" / "a shorter moving average can create more fluctuations and potentially more false signals, while a longer one is smoother" | RET p74 | PARAMETER | NOT (the engine HAS a `bollinger_pct` feature but no spec uses it) - ALSO TESTED: bollinger20_2_breakout_crypto [crypto] -> REFUTED| price | YES | A different (period, band) pair does not change the result, or the 20/2 default is not the optimum. |
| RET-95 | "In practice, 1.0 SD is the earlier warning zone and 1.5 SD is the stronger trigger zone, which fits scalp logic better than waiting for large daily-style moves." | RET p52 / p59 | PARAMETER + TIMING | NOT | price | YES | The 1.0/1.5 split is not the right pair of thresholds. |
---

## 7. GROUP REG - Financial market regime identification

Source: **REG** (15pp). Section names are cited; page numbers are approximate because the PDF text layer
merges some pages.

### 7.1 Key findings and the Direct Answer (REG pp.1-3)

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| REG-01 | "The most defensible edge is regime-conditioned switching: run momentum in orderly trending states, and switch toward reversal/liquidity-provision in stressed, high-volatility, rebound, or illiquid states." | REG p1 (Key Findings, "Best general edge") | DIRECTIONAL (switch) | **IMPLEMENTED (C1)** - ALSO TESTED: regime_switch_cross_sectional_sector_rotation [us_equity_style] -> SUPPORTED; regime_switch_momentum_reversal_us_equity [us_equity] -> REFUTED; regime_switch_momentum_reversal_nasdaq_scalp_proxy [us_equity_style] -> REFUTED| price, volume | YES | The switched strategy is not better than either leg alone, and not better than the raw signal. |
| REG-02 | "Markets are usually better represented by 3-5 latent states rather than a simple bull/bear split." | REG p1 ("Regime structure") | MARKET-STATE | **IMPLEMENTED (C1**, n_states=4**)** - ALSO TESTED: regime_switch_cross_sectional_sector_rotation [us_equity_style] -> SUPPORTED| price, volume | YES | A 2-state split performs as well as 3-5 states. |
| REG-03 | "tranquil states tend to persist longer, while stress states are shorter and more violent." | REG p1 | MARKET-STATE (duration) | NOT (C1 uses an HMM filter with no duration model; no HSMM) | price | YES | State durations are equal across states, or stress states are the longer-lived ones. |
| REG-04 | "The most transferable regime inputs are volatility level/change, trend, drawdown, and liquidity/volume proxies; forward-looking option/VIX signals can improve early stress detection." | REG p1 ("Best regime indicators") | MARKET-STATE (feature set) | **IMPLEMENTED (C1, C2, C3)** | price, volume, IV | YES | Volatility alone matches the four-feature set. |
| REG-05 | "Momentum tends to work better in bullish/trending or calmer states and weakens sharply in downturns, crisis periods, and rebound-after-crash states." | REG p1 ("Momentum behavior") | GATE + DIRECTIONAL | **IMPLEMENTED (C3, C6)** | price | YES | Momentum performs equally in calm and crisis states. |
| REG-06 | "Short-term reversal strengthens when liquidity is poor, volatility is high, and order imbalance is large; this is consistent with liquidity-provision compensation." | REG p2 ("Reversal behavior") | GATE + DIRECTIONAL | PARTIAL (C8 implements the liquidity and volatility legs; the order-imbalance leg is missing) | price, volume, orderflow | PROXY | Adding an order-imbalance condition to C8's gate does not improve reversion. |
| REG-07 | "Crypto regime behavior is more horizon-specific and structurally unstable than equities; daily, weekly, and intraday findings often disagree." | REG p2 ("Crypto caution") | MARKET-STATE + NEGATIVE | NOT | price, volume | YES (daily vs weekly) | The crypto regime classification is equally stable across horizons. |
| REG-08 | "Directional-change and threshold/event-based methods are promising for faster markets and can outperform fixed-time baselines in some studies." | REG p2 ("Event-based detection") | DIRECTIONAL + MARKET-STATE | NOT | price, volume | EXT (directional-change needs a threshold overlay on daily bars) | Directional-change does not outperform a fixed-time baseline. |
| REG-09 | "Classify the market each day (or bar) using 4 core features: realized/implied volatility, trend, drawdown, and liquidity/volume." | REG p2 (Direct Answer, 1) | MARKET-STATE | **IMPLEMENTED (C1)** - ALSO TESTED: regime_switch_cross_sectional_sector_rotation [us_equity_style] -> SUPPORTED| price, volume, IV | YES | A different feature set classifies better. |
| REG-10 | "Use 3-5 regimes, not just bull/bear. A practical taxonomy is: tranquil uptrend, high-vol uptrend, range/chop, regular bear, crash/rebound." | REG p2 (Direct Answer, 2) | MARKET-STATE | **IMPLEMENTED (C1)** - ALSO TESTED: regime_switch_cross_sectional_sector_rotation [us_equity_style] -> SUPPORTED| price, volume | YES | A 2-state or 6-state model is better. |
| REG-11 | "Trade momentum only in orderly trend states and reduce or shut it down in panic/rebound states, because momentum crashes are repeatedly linked to high volatility, prior declines, and rebounds." | REG p2 (Direct Answer, 3) | GATE | **IMPLEMENTED (C3, C6)** - ALSO TESTED: regime_switch_momentum_reversal_us_equity [us_equity] -> REFUTED| price | YES | Switching momentum off in panic/rebound states does not reduce drawdown or improve Sharpe. |
| REG-12 | "Activate reversal/liquidity-provision in stress states, especially when VIa/volatility is high and liquidity is poor, because reversal payoffs tend to spike when other traders withdraw liquidity." | REG p3 (Direct Answer, 4) | GATE + DIRECTIONAL | **IMPLEMENTED (C8)** - ALSO TESTED: regime_switch_momentum_reversal_us_equity [us_equity] -> REFUTED| price, volume | YES | The stress-state reversion activation does not improve the result. |
| REG-13 | "For crypto, make the model horizon-specific. Hourly, daily, and weekly regimes can behave differently, and stock-crypto correlations also shift by crisis regime, so one fixed rule is less reliable there." | REG p3 (Direct Answer, 5) | MARKET-STATE | NOT | price, volume | YES (daily vs weekly) | One shared classifier works equally at every horizon. |
| REG-14 | "Translate state probabilities into explicit position-sizing and turnover controls rather than signal switching alone." | REG p3 (Suggested Further Research) | SIZING | PARTIAL (C1's `regime_switch` uses the posterior as a size multiplier and C2 has an `exposure_cap`, but there is no dedicated state-proportional sizing spec, and no turnover control) - ALSO TESTED: regime_switch_cross_sectional_sector_rotation [us_equity_style] -> SUPPORTED| price | YES | State-proportional sizing adds nothing over the flat 15% vol target. |
| REG-15 | "Regimes are persistent, asymmetric, and often latent, which means the same signal can work well in one state and fail badly in another." | REG p4 ("Why Regime Identification Matters") | MARKET-STATE | PARTIAL (C1) - ALSO TESTED: regime_switch_cross_sectional_sector_rotation [us_equity_style] -> SUPPORTED| price | YES | The signal's conditional performance is the same in every state. |
| REG-16 | "the edge is often the switch, not the raw signal." | REG p4 | DIRECTIONAL (meta) | **IMPLEMENTED (C1)** - ALSO TESTED: regime_switch_cross_sectional_sector_rotation [us_equity_style] -> SUPPORTED; regime_switch_momentum_reversal_us_equity [us_equity] -> REFUTED| price, volume | YES | The raw signal alone is as good as the switch. |

### 7.2 Latent-state models and feature-based detection (REG pp.4-6)

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| REG-17 | "HSMMs explicitly model how long a state tends to last, which can be useful because tranquil regimes are generally longer-lived while crisis states are shorter and more abrupt." | REG p5 | MARKET-STATE | NOT | price | YES | A duration model does not improve regime classification or allocation. |
| REG-18 | "One supplied study reports that a five-state HSMM better captured U.S. stock regimes than a two-state model and improved allocation performance." | REG p5 | COMPARATIVE | NOT | price | YES | 5 states do not beat 2 states on allocation performance. |
| REG-19 | "a four-state HMM was selected as optimal in one S&P 500 application, while other studies support three-state and five-state structures for capturing calm, volatile, and crisis-like conditions." | REG p5 | COMPARATIVE | NOT (C1 hard-codes n_states=4 with no comparison across state counts) | price | YES | The state count does not matter for the outcome. |
| REG-20 | "Volatility is the most consistently useful regime feature in the evidence. It appears in regime detection, momentum crash prediction, reversal payoffs, and systemic stress monitoring." | REG p6 | COMPARATIVE (feature ranking) | NOT | price | YES | Volatility is not the most useful regime feature when the others are added one at a time. |
| REG-21 | "Drawdown-focused work adds that rising credit risk predicts deeper drawdowns well ahead of time, although the evidence does not compare drawdown features directly against other feature families in a unified test." | REG p6 | DIRECTIONAL (forward-looking) | NOT | credit, price | EXT (credit series available via rates_credit preset: HYG/LQD/EMB/TIP/BND) | Credit risk does not predict deeper drawdowns ahead of price. |
| REG-22 | "start with volatility, trend, drawdown, and liquidity rather than trying to optimize dozens of indicators." | REG p6 (Practical implication) | COMPARATIVE | NOT | price, volume | YES | A large indicator set beats the four-feature set. |
| REG-23 | "Option-implied horizon spreads, implied volatilities, VIX, and financial-stress indicators as useful forward-looking signals for regime detection and early distress warning." | REG p6 ("Forward-looking and event-based signals") | MARKET-STATE (leading) | PARTIAL (C2 uses the IV LEVEL and the IV-minus-RV premium; the horizon SPREAD is not implemented, though `iv_term_slope` exists in `leading.py`) | IV, price | YES (for crypto DVOL term structure; equities term structure is not available) | The IV term slope adds nothing to the IV level. |
| REG-24 | "Directional-change methods classify market behavior based on threshold moves rather than fixed time bars and have been reported to detect abnormal-volatility spells accurately while also outperforming some fixed-time baselines in trading applications." | REG p6 | DIRECTIONAL + MARKET-STATE | NOT | price | EXT | Directional-change does not detect abnormal-volatility spells better than a fixed-time classifier. |
| REG-25 | "Threshold models such as SETAR also outperformed simpler linear time-series baselines in some settings." | REG p6 | COMPARATIVE | NOT | price | EXT | SETAR does not beat a linear baseline. |
| REG-26 | "A hybrid design may be especially useful in trading: a slower latent-state model for background regime plus a faster directional-change trigger for sharp transitions. This inference connects separate findings and is not directly tested as one unified model in the supplied evidence." | REG p6 | COMPOSITE | NOT - **THE PAPER LABELS THIS "Inferred" AND "not directly tested"** | price | EXT | The hybrid does not beat either component. |
| REG-27 | "The most reusable feature set across the supplied evidence is: Volatility level and change; Trend / return direction; Drawdown depth and rebound condition; Liquidity / turnover / Amihud / volume interactions." | REG p6 | MARKET-STATE (feature set) | **IMPLEMENTED (C1)** - Amihud is a proxy, not an implementation | price, volume | YES | A different feature set classifies better. |

### 7.3 Momentum behaviour across regimes (REG pp.6-7)

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| REG-28 | "One study's crash dummy combines negative trailing market returns, a positive current return, and elevated short-versus-long volatility, which is effectively a rebound-danger state." | REG p6 | GATE | **IMPLEMENTED (C6)** | price | YES | The rebound dummy does not separate momentum-crash from ordinary periods. |
| REG-29 | "the broader evidence that momentum losses often arrive after the market has already begun rebinding." | REG p6 | GATE | **IMPLEMENTED (C6)** | price | YES | Momentum losses do not cluster after rebounds. |
| REG-30 | "Some studies need 2-5 regimes, and one five-state market split separates low-vol bull, high-vol bull, bubble, regular bear, and crash/correction." | REG p6 | MARKET-STATE | PARTIAL (C1 has 4 states and no explicit "bubble" state) | price | YES | The 5-state taxonomy does not outperform a 4-state model. |
| REG-31 | "momentum may behave differently in low-vol bull and high-vol bull states even though both are 'up' markets." | REG p6 | DIRECTIONAL (regime-dependent within direction) | NOT (C1 has both uptrend states but no separate comparison spec) | price | YES | Momentum performs identically in low- and high-vol bull states. |
| REG-32 | "Favor momentum in orderly low-vol trend states." | REG p7 (Practical momentum rules) | GATE | **IMPLEMENTED (C3)** | price | YES | Low-vol gating does not improve momentum. |
| REG-33 | "Cut or disable momentum in high-volatility states." | REG p7 | GATE | **IMPLEMENTED (C3)** | price | YES | Vol gating does not improve momentum. |
| REG-34 | "Be especially cautious in post-crash rebounds." | REG p7 | GATE | **IMPLEMENTED (C6)** | price | YES | Post-crash caution does not improve momentum. |
| REG-35 | "Consider risk-managed or crash-aware variants where possible." | REG p7 | RISK | NOT (no crash-aware momentum variant exists) | price | YES | A crash-aware variant does not reduce drawdown. |

### 7.4 Mean reversion and reversal by market state (REG pp.7-8)

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| REG-36 | "Reversal payoffs tend to strengthen in high VIX, illiquid, volatile, or order-imbalanced periods." | REG p7 | GATE + DIRECTIONAL | PARTIAL (C8 covers high-vol and illiquid; not VIX level and not order imbalance) | price, volume, IV | YES (VIX available) | The VIX level adds nothing to the C8 gate. |
| REG-37 | "Foundational studies interpret short-term reversal as a liquidity effect: large price moves reverse because liquidity providers demand compensation for absorbing temporary order imbalances." | REG p7 | MECHANISM (rationale for REG-36/REG-38) | NOT as a separate spec - the implied test is REG-38 | price, volume, orderflow | PROXY | (Mechanism claim; tested indirectly by whether reversal is stronger where liquidity is scarce.) |
| REG-38 | "Reversal is stronger in illiquid stocks, lower-turnover environments, and more volatile conditions; profits are especially concentrated where liquidity is scarce." | REG p7 | DIRECTIONAL + GATE | **IMPLEMENTED (C8)** | price, volume | YES (proxy) | Reversal is not stronger in thin-activity names. |
| REG-39 | "In crypto, reversal/liquidity-provision returns are concentrated in lower-activity, less liquid, more volatile pairs, and panel evidence shows lagged return interacted with volume helps predict the effect." | REG p7 | DIRECTIONAL | PARTIAL (C8 uses a volume RATIO as a liquidity proxy; the specific feature - **lagged return INTERACTED with volume** - is not implemented) | price, volume | EXT | The return x volume interaction does not predict the reversion effect. |
| REG-40 | "The evidence repeatedly warns that reversal is horizon-specific. Intraday and one-day effects can be strong even when longer-horizon effects are weak or different." | REG p7 | TIMING + HORIZON | NOT | price | YES | The reversal effect does not decay with horizon. |
| REG-41 | "In U.S. index futures, there may be a brief continuation after the open followed by a longer sequence of intraday reversals, although the effect can weaken sharply after costs." | REG p7 | DIRECTIONAL | NOT | intraday, price | NO | The post-open continuation is absent. |
| REG-42 | "Crypto studies similarly emphasize that daily aggregation can hide intraday mean reversion." | REG p7 | NEGATIVE / LIMITATION | NOT as a spec, but it is a **binding caveat on C8**: a SUPPORTED daily-bar C8 verdict is evidence about daily bars only and must not be reported as evidence for an intraday edge. | price | n/a | n/a |
| REG-43 | "Favor reversal when VIX/volatility is elevated." | REG p7 (Practical reversal rules) | GATE | **IMPLEMENTED (C8)** | price | YES | The vol gate does not improve reversion. |
| REG-44 | "Favor reversal when liquidity is poor or volume/turnover interactions indicate temporary dislocation." | REG p7 | GATE | **IMPLEMENTED (C8)** | price, volume | YES (proxy) | The liquidity gate does not improve reversion. |
| REG-45 | "For intraday systems, use short horizons because some reversal signals decay quickly and may disappear after costs." | REG p7 | TIMING | NOT | price, intraday | NO | The reversal does not decay. |

### 7.5 Cross-asset, crypto regimes and hedging (REG pp.8-9)

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| REG-46 | "Crypto-equity correlation is also regime-dependent. During some crisis windows, crypto co-moves with equities and loses safe-haven properties; in others, linkage weakens or temporarily flips." | REG p8 | DIRECTIONAL + HEDGING | NOT | price | YES | Crypto-equity correlation is constant, or does not change across crisis vs calm windows. |
| REG-47 | "a crypto regime model should include not only internal features like volatility and liquidity, but also external linkage conditions with equities or macro shocks." | REG p8 | MARKET-STATE (feature set) | NOT | price, macro | YES (equity linkage daily) | Adding equity linkage does not improve crypto regime classification. |
| REG-48 | "For crypto, a useful extra state may be 'microstructure stress,' combining volume collapse, jump intensity, and broader market-linkage changes. This is a synthesis rather than a directly tested named regime." | REG p8 | MARKET-STATE - **the paper labels this a synthesis, not a tested regime** | NOT | price, volume | YES | The microstructure-stress state does not separate a distinct return distribution. |
| REG-49 | "Horizon alignment: Intraday - event-based signals, liquidity measures, jump conditions, short-horizon reversal, and very short continuation effects. Swing/daily - trend, realized/implied volatility, drawdown, VIX, and crash/rebound filters. Longer horizon - broader latent-state allocation frameworks, multistate HMM/HSMM models, slower regime persistence measures." | REG p8-9 | MARKET-STATE (horizon mapping) | PARTIAL (C1 is the swing/daily implementation; no intraday or long-horizon spec) | price, volume, IV | YES (swing/daily); NO (intraday) | A single horizon-agnostic feature set works equally well at all three horizons. |
| REG-50 | "Suggested state map with per-state exposure: 1. Tranquil uptrend - momentum on. 2. High-vol uptrend - momentum reduced, selective only. 3. Range/chop - low exposure or short-horizon mean reversion. 4. Regular bear - cautious, smaller size, some reversal setups. 5. Crash/rebound - momentum off, reversal/liquidity-provision favored." | REG p9 | SIZING + DIRECTIONAL | PARTIAL (C1 switches hard between two legs; the **graded five-step exposure ladder** is not implemented) - ALSO TESTED: regime_switch_cross_sectional_sector_rotation [us_equity_style] -> SUPPORTED| price, volume | YES | A flat exposure per state performs the same as the graded ladder. |
| REG-51 | "Add event-based directional-change triggers for faster transitions if trading frequency is high." | REG p9 (Model choice) | TIMING | NOT | price | EXT | Event triggers do not improve transitions. |
| REG-52 | "For crypto, train separately by horizon rather than forcing one shared regime classifier." | REG p9 (Model choice) | MARKET-STATE | NOT | price | YES | A shared classifier works as well at every horizon. |

### 7.6 The paper's own stated limitations, contradictions and evidence gaps (REG pp.3, 8, 10)

These are the paper's admissions about its own claims. They are recorded as claims because they are testable
**negative controls**, and several of them are directly actionable as new specs.

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| REG-53 | "The supplied evidence does not provide a clean head-to-head out-of-sample ranking of volatility, trend, autocorrelation, drawdown, and liquidity features for Nasdaq, stocks, and crypto under identical protocols, so no single 'best detector' can be declared from this set." | REG p3 (Assumptions & Limitations) | NEGATIVE + COMPARATIVE | NOT (no feature-ablation spec exists) | price, volume | YES | **Ablation test:** no feature family dominates; every detector performs within noise of the others. The paper's admission becomes the finding. |
| REG-54 | "Nasdaq-specific evidence is thinner than broader U.S. equity/S&P 500 evidence, so some Nasdaq guidance is inferred from broader index behavior rather than directly tested on Nasdaq-only datasets." | REG p3 | NEGATIVE / LIMITATION | NOT | price | YES | Nasdaq-only results match the broader equity results, contradicting the transfer caveat. |
| REG-55 | "Several strategy findings are directionally strong, but the provided excerpts often lack standardized transaction-cost-adjusted Sharpe/drawdown comparisons across assets." | REG p3 | NEGATIVE | PARTIAL (the package's constant risk block and `cost_multiplier 2.0` supply the comparison the papers lacked, but it is not a paper claim) | price | YES | Cross-asset Sharpe/drawdown differences vanish once costs are standardised. |
| REG-56 | "The main evidence gap is methodological: the supplied studies do not provide a unified out-of-sample comparison proving whether volatility, trend, drawdown, liquidity, HMMs, HSMMs, or event-based classifiers are best across Nasdaq, stocks, and crypto under one common design." | REG p10 (Contradictions and Evidence Gaps; Confidence: High - "This limitation is explicitly supported by the retrieved evidence") | NEGATIVE + COMPARATIVE | NOT (no classifier horse-race exists) | price, volume | YES | **The horse race the paper says is missing:** one classifier dominates across assets under one design. |
| REG-57 | "Crypto is sometimes described as a diversifier and sometimes not; momentum appears at some crypto horizons and disappears or reverses at others." | REG p10 | NEGATIVE | NOT | price | YES | Crypto momentum is stable in sign and strength across horizons. |
| REG-58 | "reversal signals can be economically meaningful before costs but much weaker after costs in some intraday futures settings." | REG p10 | NEGATIVE | PARTIAL (the package's stressed-cost stage tests this for its own specs) | price | YES | **Cost-sensitivity control:** reversal survives the stressed cost case. |
| REG-59 | "This is not presented as a proven optimal design; rather, it is the design most consistent with the supplied evidence." | REG p9 | META / caveat | n/a - recorded so C1's result is never reported as "the proven optimal regime design" | - | n/a | n/a |
| REG-60 | "Use multi-state classification rather than bull/bear." (Equities and Nasdaq-like assets) | REG p8 | MARKET-STATE | **IMPLEMENTED (C1)** | price | YES | Bull/bear performs as well as multi-state. |
| REG-61 | "Treat rebound after decline as distinct from healthy uptrend." | REG p8 | GATE | **IMPLEMENTED (C6)** | price | YES | The two states are indistinguishable. |
| REG-62 | "Use volatility and liquidity filters to decide whether momentum or reversal should dominate." | REG p8 | GATE | **IMPLEMENTED (C3, C8)** | price, volume | YES | The filters do not change which signal dominates. |
| REG-63 | "Regime features: Volatility: realized volatility, implied volatility/VIX, short-vs-long volatility spread. Trend: medium-horizon return or moving-trend feature. Drawdown/rebound: rolling drawdown plus rebound flag after prior decline. Liquidity: turnover, volume interaction, Amihud-like illiquidity proxy, bid-ask proxy if available." | REG p9 | MARKET-STATE (input set) | PARTIAL (all present except a true Amihud illiquidity measure and a bid-ask proxy) | price, volume, IV | YES | A different input set classifies better. |
| REG-64 | "Momentum belongs to orderly trend states." / "Reversal belongs to stressed, illiquid, high-volatility, or rebound states." / "Volatility, drawdown/rebound, and liquidity are the most important regime variables." / "3-5 state models are more realistic than simple bull/bear labels." / "Crypto must be modeled by horizon, not by one fixed universal rule." | REG p10 (Conclusion) | GATE + MARKET-STATE | PARTIAL (first four implemented in C1/C3/C6/C8; the horizon rule is not) - ALSO TESTED: regime_switch_cross_sectional_sector_rotation [us_equity_style] -> SUPPORTED| price, volume | YES | The conclusions do not survive the same test applied to them. |
| REG-65 | "the best evidence-backed starting point is a small multi-state classifier with volatility, trend, drawdown, and liquidity inputs, used to switch between momentum and reversal rather than forcing one model to work all the time." | REG p10 (Conclusion) | COMPOSITE | **IMPLEMENTED (C1)** - ALSO TESTED: regime_switch_cross_sectional_sector_rotation [us_equity_style] -> SUPPORTED| price, volume | YES | The composite is no better than its parts. |

---

## 8. GROUP NAS - NASDAQ market regime identification

Source: **NAS** (18pp). Section names cited; page numbers approximate.

### 8.1 Key findings and the Direct Answer (NAS pp.1-2)

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| NAS-01 | "Market regime is multi-dimensional: volatility, trend/mean reversion, liquidity, and flow all matter. A single 'bull/bear' label is too coarse for intraday execution." | NAS p1 | MARKET-STATE | PARTIAL (C1 uses volatility, trend, drawdown and liquidity; **flow is not a regime input in C1**) | price, volume, orderflow | YES (without flow) | A bull/bear label classifies as well as the multi-axis model. |
| NAS-02 | "Positive/high gamma tends to damp volatility and favor pinning or mean reversion; negative gamma tends to amplify moves and breakout risk. Gamma state should change whether you fade moves or follow them." | NAS p1 | GATE + DIRECTIONAL | NOT | optchain | NO | Gamma sign does not separate fade-regimes from follow-regimes. |
| NAS-03 | "Order-flow imbalance is useful, but mainly at very short horizons. For scalping, 1-2 minute updates are more defensible than fixed morning labels." | NAS p1 | TIMING | PARTIAL (C7 refreshes daily; not 1-2 minute) | orderflow | NO | The imbalance signal is equally durable at longer horizons. |
| NAS-04 | "Time-of-day is itself a regime variable. Open, midday, and close should be traded differently." | NAS p1 | MARKET-STATE (session) | NOT | intraday | NO | The session does not change signal quality or trade style. |
| NAS-05 | "Raw option-flow counts are weaker than exposure-adjusted measures. Delta-, vega-, and notional-adjusted flow is more interpretable than contract counts." | NAS p1 | COMPARATIVE | NOT | optflow, optchain | NO | Raw contract counts are as informative as exposure-adjusted flow. |
| NAS-06 | "Flow signals have failure modes. Gamma estimates can be stale/model-dependent; option flow may reflect hedging or vol demand, not direction." | NAS p1 | NEGATIVE | NOT | optchain, optflow | NO | Gamma estimates are never stale and option flow always means direction. |
| NAS-07 | "classify each session and intraday block on four axes: (1) volatility state, (2) gamma state, (3) order-flow/liquidity state, and (4) event/time-of-day state rather than using one label such as 'trend day' or 'range day' alone." | NAS p2 (Direct Answer) | MARKET-STATE (four-axis) | PARTIAL (axis 1 partially via C1/C3; axes 2-4 not implemented) | price, volume, optchain, orderflow, macro | NO (3 of 4 axes) | A single-label model works as well. |
| NAS-08 | "Positive/high gamma + narrow spreads + balanced flow + healthy depth: treat as a mean-reversion / pinning regime; fading stretched moves is more consistent with the evidence." | NAS p2 | DIRECTIONAL + GATE | NOT | optchain, orderflow, price | NO | The four-condition regime does not separate mean-reversion from momentum periods. |
| NAS-09 | "Negative gamma + rising realized volatility + one-sided imbalance + depth depletion: treat as a momentum / breakout regime; continuation and faster tape response become more plausible." | NAS p2 | DIRECTIONAL + GATE | NOT | optchain, orderflow, price | NO | The four-condition regime does not separate momentum from mean-reversion periods. |
| NAS-10 | "Expiration, major strikes, or catalyst windows: treat as distorted/event regimes that can override normal behavior because hedging and announcement effects alter both volatility and price response." | NAS p2 | MARKET-STATE (event) | NOT | macro, optchain | NO (macro calendar absent) | Event windows behave like ordinary windows. |
| NAS-11 | "For scalping specifically, refresh the regime frequently. The evidence is much stronger for very short-horizon flow signals than for stable 30-minute forecasts, so a rolling 1-2 minute regime update is more defensible than assuming the morning state persists." | NAS p2 | TIMING | NOT | intraday | NO | The regime label is equally stable over 30 minutes as over 2 minutes. |

### 8.2 The paper's own stated limitations (NAS p2)

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| NAS-12 | "The supplied evidence does not include a NASDAQ-specific integrated intraday regime model that jointly combines gamma, option flow, realized volatility, and order imbalance with out-of-sample 5-30 minute classification accuracy or PnL." | NAS p2 (Assumptions & Limitations) | NEGATIVE / LIMITATION | NOT | - | n/a | n/a - but it defines the gap a combined spec must fill. |
| NAS-13 | "NASDAQ-specific evidence for intraday half-life around VWAP, opening range, or prior-day close is not directly provided." | NAS p2 | NEGATIVE / LIMITATION | NOT | intraday | NO | Half-life estimates are provided by the evidence. |
| NAS-14 | "Dealer-gamma measures based on open interest can be stale and model-sensitive, especially for single-stock estimation." | NAS p2 | NEGATIVE | NOT | optchain | NO | Dealer-gamma estimates are stable and precise. |
| NAS-15 | "Some option-flow evidence comes from broader U.S. options samples rather than directly from NASDAQ underlyings, so application to QQQ/NDX should be treated as informed transfer rather than direct proof." | NAS p2 | NEGATIVE / LIMITATION | NOT | optflow | NO | Nasdaq-specific option flow behaves identically to the broader sample. |

### 8.3 Regime families and conditional expectancy (NAS pp.3-4)

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| NAS-16 | "the same setup can have opposite expectancy in different states: a pullback can be a fade in a damped market but an entry in an amplified market." | NAS p3 | DIRECTIONAL (conditional expectancy) | NOT - **the single most testable statement in the NASDAQ paper on daily bars** - ALSO TESTED: regime_switch_momentum_reversal_nasdaq_scalp_proxy [us_equity_style] -> REFUTED| price, volume | YES | The expectancy of a pullback entry is the same in every regime state. |
| NAS-17 | "Low-volatility / pinned / balanced regime: smaller realized movement, tighter behavior around strikes or local anchors, often better for mean-reversion scalps." | NAS p3 | MARKET-STATE + GATE | NOT - ALSO TESTED: regime_switch_momentum_reversal_nasdaq_scalp_proxy [us_equity_style] -> REFUTED| price | YES (the low-vol part) | The regime is not better for mean reversion. |
| NAS-18 | "High-volatility / fragile regime: larger realized movement, more abrupt repricing, higher breakout risk." | NAS p3 | MARKET-STATE | PARTIAL (C3 has a vol state) | price | YES | High-vol periods are not larger-movement or more breakout-prone. |
| NAS-19 | "Trending / persistence regime: returns propagate over short horizons rather than snap back quickly." | NAS p3 | MARKET-STATE | PARTIAL (C1) - ALSO TESTED: regime_switch_momentum_reversal_nasdaq_scalp_proxy [us_equity_style] -> REFUTED| price | YES | The persistence is not regime-dependent. |
| NAS-20 | "Mean-reverting / oscillating regime: deviations are corrected rather than extended." | NAS p3 | MARKET-STATE | PARTIAL (C1, C8) - ALSO TESTED: regime_switch_momentum_reversal_nasdaq_scalp_proxy [us_equity_style] -> REFUTED| price | YES | The correction is not regime-dependent. |
| NAS-21 | "Event-distorted regime: catalysts or expiry flows dominate normal tape logic." | NAS p3 | MARKET-STATE | NOT | macro, optchain | NO | Event windows behave normally. |
| NAS-22 | "Studies report higher intraday volatility versus NYSE comparators, and strong intraday/session effects in volatility and trading behavior." | NAS p4 | MARKET-STATE | NOT | intraday | NO | Nasdaq intraday vol is not higher than NYSE. |
| NAS-23 | "Volatility clusters: calm and stressed periods behave differently and require different execution and sizing assumptions." | NAS p4 | MARKET-STATE | PARTIAL (C3) | price | YES | Calm and stressed periods behave identically. |
| NAS-24 | "Time-of-day changes execution quality: midday tends to have lower execution cost but slower execution, while open/close tends to be faster but more expensive and more event-sensitive." | NAS p4 | RISK + MARKET-STATE (session) | NOT | intraday | NO | Execution cost is flat across the session. |
| NAS-25 | "Order-flow information decays quickly: imbalance matters, but mainly at short horizons." | NAS p4 | TIMING | NOT | orderflow | NO | The imbalance signal does not decay. |
| NAS-26 | "Options-related hedging can reshape intraday path: especially around strikes and expiry." | NAS p4 | MARKET-STATE | NOT | optchain, intraday | NO | The path is unreshaped around strikes and expiry. |
| NAS-27 | "for NASDAQ scalping, regime detection ... is part of deciding whether to fade, follow, provide liquidity, cross the spread, reduce size, or stand aside." | NAS p4 | MARKET-STATE (six decision modes) | PARTIAL (C1 implements fade / follow / stand-aside; "provide liquidity", "cross the spread" and "reduce size" are not decision outputs) | price | YES | Regime state does not change the decision. |

### 8.4 Volatility diagnostics and latent-state models (NAS pp.5-6)

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| NAS-28 | "Intraday high-low ranges are about as effective as implied volatility for major indexes including NASDAQ-100 contexts, and intraday squared returns are preferred for daily volatility estimation when overnight trading is absent." | NAS p5 | MARKET-STATE (vol estimator) | NOT | price (high/low available on daily bars), IV | YES for the daily-bar range estimator | A daily high/low range estimator is not as good as the implied vol as a vol-state input. |
| NAS-29 | "Range-based estimators such as Parkinson, Garman-Klass, and realized range are repeatedly used because they are more efficient than simple close-to-close returns in volatility measurement." | NAS p5 | MARKET-STATE (vol estimator) | NOT - **directly buildable on daily bars; the package has OHLC but no range estimator feature** | price | EXT | Parkinson/Garman-Klass are not more efficient than close-to-close on this sample. |
| NAS-30 | "log-scale realized-variance models generally outperform level-scale models in both high- and low-volatility subsamples because they handle heteroscedastic measurement error better." | NAS p5 | COMPARATIVE | NOT | price | EXT | Level-scale models perform the same. |
| NAS-31 | "HAR-type and GARCH-MIDAS variants also suggest that combining intraday realized information with slower components and macro/volatility indices improves performance." | NAS p5 | COMPARATIVE | NOT | intraday, macro | NO | The combination does not improve performance. |
| NAS-32 | "Treat large changes in realized volatility as state changes, not just noise." | NAS p5 | GATE + MARKET-STATE | NOT | price | YES | Large vol changes are pure noise with no effect on conditional returns. |
| NAS-33 | "Markov/regime-switching models identify low- and high-volatility states, and broader stock-market work finds strong evidence of switching behavior with asymmetric predictability across states." | NAS p5 | MARKET-STATE | **IMPLEMENTED (C1)** | price, volume | YES | No switching behaviour exists. |
| NAS-34 | "Markov heteroskedasticity research also links volatility regimes to changing perceived risk and surprise, showing that high-variance periods differ structurally rather than only by magnitude." | NAS p5 | MARKET-STATE | PARTIAL (C1) | price | YES | High-vol periods differ only in magnitude. |
| NAS-35 | "Fuzzy regime methods and soft-transition ideas improve the fit/performance trade-off in index volatility settings, which is especially relevant near regime transitions." | NAS p5 | COMPARATIVE | PARTIAL (C1 emits soft posteriors but no hard-vs-soft comparison is run) | price, volume | YES | Hard labels perform as well as soft posteriors. |
| NAS-36 | "This pattern supports a practical move away from 'today is definitely trend day' toward 'trend probability just rose from 35% to 65%'." | NAS p5 | MARKET-STATE (output format) | PARTIAL (C1 uses soft posteriors) | price, volume | YES | Hard labels perform as well. |
| NAS-37 | "index-arbitrage work shows negative first-order autocorrelations consistent with prices being pulled back toward equilibrium." | NAS p5 | DIRECTIONAL | PARTIAL (C5, C8) | price | YES | First-order autocorrelation is not negative. |
| NAS-38 | "persistence and reversion are asymmetric: negative prior returns tend to show stronger mean reversion than positive prior returns." | NAS p5 | DIRECTIONAL (**asymmetric**) | NOT - **highly testable on daily bars and directly relevant to a long/short design** | price | YES | Prior positive and negative returns revert with equal strength. |
| NAS-39 | "There is no direct supplied evidence giving NASDAQ-specific half-life estimates around VWAP or opening range, so those thresholds must be empirically estimated in your own data." | NAS p5 | LIMITATION + instruction | NOT | price, intraday | YES (half-life can be estimated on daily bars) | The half-life is not estimable from the data. |
| NAS-40 | "Mean reversion is a real phenomenon, but it is context-dependent." | NAS p5 | DIRECTIONAL + GATE | PARTIAL (C8) | price | YES | Reversion is unconditional. |

### 8.5 Gamma exposure and dealer positioning (NAS pp.6-7)

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| NAS-41 | "High net gamma exposure is associated with lower future volatility and better market stability, while negative net gamma is associated with higher volatility and greater fragility." | NAS p6 | MARKET-STATE + GATE | NOT (cf. OPT-07/OPT-10, same claim) | optchain, price | NO | No relationship between net gamma and future realised vol. |
| NAS-42 | "Short-gamma hedging creates momentum because hedgers trade in the same direction as the move, which can reinforce continuation intraday." | NAS p6 | DIRECTIONAL + GATE | NOT | optchain, intraday | NO | Continuation is not stronger in short-gamma periods. |
| NAS-43 | "As expiration approaches, hedging and exercise-related pressures can pull prices toward option strikes and constrain behavior around them." | NAS p6 | DIRECTIONAL (pinning) | NOT | optchain | NO | Prices are not pulled toward strikes near expiry. |
| NAS-44 | "Near-strike conditions are further associated with more fleeting orders and a higher chance of crossing the strike on expiration day, implying local instability even inside an otherwise 'pinned' regime." | NAS p6 | NEGATIVE (nuance that qualifies NAS-43) | NOT | optchain, intraday | NO | Near-strike conditions are stable. |
| NAS-45 | "For regime classification, the most practical gamma variables are: Net gamma sign: positive vs negative." | NAS p6 | MARKET-STATE (variable) | NOT | optchain | NO | n/a - variable definition. |
| NAS-46 | "Distance to zero-gamma boundary: a likely transition variable when dealer behavior flips from damping to amplifying." | NAS p6 | MARKET-STATE (variable) | NOT | optchain | NO | Proximity to the zero-gamma boundary does not predict a regime flip. |
| NAS-47 | "Distance to major strikes / strike concentration: local attractor or repeller effects around expiry." | NAS p6 | MARKET-STATE (variable) | NOT | optchain | NO | Strike proximity has no effect on returns. |
| NAS-48 | "Days to expiration / expiration week: because expiry alters hedging intensity and return behaviour." | NAS p6 | MARKET-STATE (variable) | NOT | optchain, price | NO | Expiry week is an ordinary week. |
| NAS-49 | "hedging-damped vs hedging-amplified tape action" (the distinction the paper calls "especially useful for scalpers") | NAS p7 | MARKET-STATE | NOT | optchain | NO | The distinction does not exist. |

### 8.6 Order flow, liquidity state and time-of-day (NAS pp.7-8)

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| NAS-50 | "Order imbalance repeatedly shows more predictive content than raw trading volume for NASDAQ names." | NAS p7 | COMPARATIVE | NOT | orderflow, volume | NO | Raw volume is as predictive as imbalance. |
| NAS-51 | "predictability often fades beyond a few minutes in faster markets." | NAS p7 | TIMING | NOT | orderflow | NO | The signal does not decay. |
| NAS-52 | "This makes imbalance highly relevant for scalping, but only if it is treated as a short-lived state variable, not a durable directional forecast." | NAS p7 | TIMING + NEGATIVE | NOT | orderflow | NO | Imbalance is a durable directional forecast. |
| NAS-53 | "Low depth worsens execution quality by increasing price impact and sensitivity to order-book events." | NAS p7 | RISK | NOT | orderflow (depth) | NO | Depth does not affect price impact. |
| NAS-54 | "Balanced flow + good depth + narrow spread: range/mean-reversion conditions become more plausible." | NAS p7 | GATE + DIRECTIONAL | NOT | orderflow | NO | The condition does not predict mean reversion. |
| NAS-55 | "One-sided flow + thin depth + rising message intensity: breakout/momentum conditions become more plausible." | NAS p7 | GATE + DIRECTIONAL | NOT | orderflow | NO | The condition does not predict momentum. |
| NAS-56 | "Midday orders on Nasdaq execute more slowly but at lower cost, while open and close offer faster execution but higher cost and often stronger signal intensity." | NAS p7 | MARKET-STATE (session) | NOT | intraday | NO | Execution is uniform across the session. |
| NAS-57 | "Some studies report strongest scalpable predictability around the open and weaker predictability later, while other NASDAQ evidence finds imbalance-return effects strongest in the 11:30 a.m. to 2:00 p.m. window." | NAS p7 | MARKET-STATE (session) - **the paper flags this as a contradiction** | NOT | intraday | NO | Session does not matter. |
| NAS-58 | "That is not a contradiction so much as a warning: time-of-day affects both signal quality and execution quality, and the best window may depend on whether your edge is informational, liquidity-provision based, or momentum-execution based." | NAS p7 | CONDITION | NOT | intraday | NO | The best window is edge-independent. |
| NAS-59 | "Open: fast, expensive, information-rich, event-sensitive. Midday: slower, lower-cost, sometimes cleaner for informed imbalance or mean-reversion setups. Close: fast, potentially flow-heavy, more hedging-sensitive." | NAS p7 | MARKET-STATE (session) | NOT | intraday | NO | The three sessions are identical. |

### 8.7 Option flow as information, and the failure modes (NAS pp.8-9)

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| NAS-60 | "Studies use delta-weighted, absolute-delta-weighted, dollar-value, and vega-adjusted measures rather than relying only on contract counts." | NAS p8 | METHOD + PARAMETER | NOT | optflow, optchain | NO | Raw counts are as interpretable. |
| NAS-61 | "One study separates directional option flow from volatility-demand flow and finds that only volatility-strategy order flow predicts next-day realized volatility, not next-day index returns." | NAS p8 | DIRECTIONAL **NEGATIVE** | NOT | optflow | NO | Directional option flow also predicts next-day index returns. |
| NAS-62 | "Other studies show predictive power in open-buy put-call ratios, especially for more leveraged OTM options and in conditions associated with informed trading." | NAS p8 | DIRECTIONAL | NOT | optflow, optchain | NO | The put-call ratio does not predict returns. |
| NAS-63 | "raw options activity should not be read mechanically as bullish or bearish. The same gross volume can reflect: a directional bet, a hedge, volatility demand, or positioning around an event." | NAS p8 | NEGATIVE | NOT | optflow | NO | Gross options volume has a stable directional sign. |
| NAS-64 | "For regime work, the strongest use of option flow is likely as a context variable: Does options flow imply directional pressure? Does it imply volatility demand instead? Is the flow consistent with the underlying tape, or diverging from it?" | NAS p8 | GATE + FRAMEWORK | NOT | optflow, orderflow | NO | Option flow is not informative as a context variable. |
| NAS-65 | "Dealer gamma proxies often rely on strong assumptions about who holds what, whether dealers are counterparties, and whether exposures are fully delta-hedged." | NAS p9 | NEGATIVE | NOT | optchain | NO | The proxy assumptions hold. |
| NAS-66 | "Individual-stock gamma estimates can be severely noisy, highly dispersed, and sometimes of doubtful usefulness beyond averages." | NAS p9 | NEGATIVE | NOT | optchain | NO | Single-stock gamma estimates are precise. |
| NAS-67 | "Gamma estimates also depend on implied-volatility modeling, and Black-Scholes-based deltas/gammas can be biased under actual smiles and smirks." | NAS p9 | NEGATIVE | NOT | optchain, IV | NO | Black-Scholes gammas are unbiased under real smiles. |
| NAS-68 | "More recent work even questions whether empirical 'gamma' in some studies cleanly identifies the convexity coefficient traders think they are using." | NAS p9 | NEGATIVE | NOT | optchain | NO | Empirically-estimated gamma is the true convexity coefficient. |
| NAS-69 | "Order-flow predictability is strongest at short horizons and can weaken in more liquid, narrow-spread conditions." | NAS p9 | NEGATIVE | NOT | orderflow | NO | Predictability does not weaken in liquid conditions. |
| NAS-70 | "intraday price discovery is driven more by stock net trade volume than by option net trade volume; option information may show up more in quote revisions than in trade flow." | NAS p9 | NEGATIVE + COMPARATIVE | NOT | optflow, orderflow | NO | Option trade volume drives price discovery as much as stock trade volume. |
| NAS-71 | "Public order flow can also move implied volatility directly, which means heavy options activity may reflect repricing of vol rather than clean directional information." | NAS p9 | NEGATIVE | NOT | optflow, IV | NO | Heavy options activity is always clean directional information. |
| NAS-72 | "use gamma, option flow, and imbalance as conditional evidence, not standalone truth." | NAS p9 (Practical implication) | NEGATIVE + framing | NOT | optchain, optflow, orderflow | NO | The signals work as standalone truth. |

### 8.8 The four-axis scorecard, the regime labels and the execution rules (NAS pp.9-11)

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| NAS-73 | "Volatility Pressure Inputs: realized variance, realized range, recent range expansion/compression, implied-vol context." | NAS p9 | MARKET-STATE (input set) | PARTIAL | price, IV | YES | A different vol input classifies better. |
| NAS-74 | "Gamma Constraint Inputs: net gamma sign, proximity to zero-gamma, distance to major strikes, expiration proximity." | NAS p9 | MARKET-STATE (input set) | NOT | optchain | NO | The gamma inputs carry no regime information. |
| NAS-75 | "Flow Aggression Inputs: 1-minute order imbalance, trade aggressor imbalance, option-flow imbalance adjusted by delta/vega/notional." | NAS p9 | MARKET-STATE (input set) | NOT | orderflow, optflow | NO | The flow inputs carry no regime information. |
| NAS-76 | "Liquidity Fragility Inputs: spread, best-level depth, message intensity, cancellation/revision rates, market-sidedness." | NAS p9 | MARKET-STATE (input set) | NOT | orderflow | NO | The liquidity inputs carry no regime information. |
| NAS-77 | "Event/Session State: Open / midday / close / macro release / earnings / expiration." | NAS p9 | MARKET-STATE (input set) | NOT | macro, intraday | NO | Event and session state carry no regime information. |
| NAS-78 | "Mean-reversion / pinning - Positive gamma, balanced flow, narrower spread, decent depth, strike proximity - Fade extensions; smaller targets; passive or semi-passive execution." | NAS p10 (regime label table) | DIRECTIONAL + SIZING + RISK | NOT | optchain, orderflow | NO | The label does not predict the trade style that works. |
| NAS-79 | "Momentum / breakout - Negative gamma, rising realized vol, one-sided imbalance, depth depletion - Follow breaks; faster exits/entries; more aggressive execution." | NAS p10 | DIRECTIONAL + TIMING | NOT | optchain, orderflow | NO | The label does not predict the trade style that works. |
| NAS-80 | "Calm / low-friction - Lower vol, lower cost, slower execution, often midday - Selective scalps; patience matters more than urgency." | NAS p10 | MARKET-STATE | NOT | price, intraday | NO | The label does not predict the trade style that works. |
| NAS-81 | "Event-distorted - Macro/earnings/expiry, IV buildup or collapse, hedging surges - Reduce reliance on normal templates; size down or switch to event logic." | NAS p10 | SIZING | NOT | macro, IV | NO | The label does not predict the trade style that works. |
| NAS-82 | "Fragile liquidity - Thin depth, wider spreads, faster quote revisions - Smaller size, aggressive only when urgency justified." | NAS p10 | SIZING + RISK | NOT | orderflow | NO | The label does not predict the trade style that works. |
| NAS-83 | "It is likely more effective to store these labels as probabilities rather than fixed bins, because the supplied soft-regime evidence suggests fuzzy boundaries are more realistic." | NAS p10 | MARKET-STATE (output format) | PARTIAL (C1 uses soft posteriors) | price, volume | YES | Hard bins perform as well as soft probabilities. |
| NAS-84 | "Use more passive execution when depth is adequate, spreads are narrower, and imbalance is not strongly one-sided; waiting cost is lower and fill probability is more acceptable." | NAS p11 | RISK + EXECUTION | NOT | orderflow | NO | Passive execution is not better in that state. |
| NAS-85 | "Use more aggressive execution when imbalance is one-sided, volatility is elevated, spreads reflect informed trading, or immediacy is critical." | NAS p11 | RISK + EXECUTION | NOT | orderflow | NO | Aggressive execution is not better in that state. |
| NAS-86 | "Reduce size or avoid trading in low-depth, high-fragility states because price impact risk rises materially." | NAS p11 | SIZING + RISK | NOT | orderflow | NO | Size does not need to shrink in fragile states. |
| NAS-87 | "Fade less and follow more when short-gamma dynamics likely amplify price movement." | NAS p11 | GATE + DIRECTIONAL | NOT | optchain | NO | Gamma sign does not change which way to trade. |
| NAS-88 | "Fade more and chase less when gamma is stabilizing and strike pinning is plausible." | NAS p11 | GATE + DIRECTIONAL | NOT | optchain | NO | Gamma sign does not change which way to trade. |

### 8.9 Validation design, the five upgrades and the conclusion (NAS pp.11-12)

| ID | Claim (paper's wording) | Source | Type | Status | Inputs | Daily? | Refuted if |
|---|---|---|---|---|---|---|---|
| NAS-89 | "testing should focus on very short-horizon outcomes because flow signals decay quickly." | NAS p11 | METHOD (evaluation horizon) | NOT | intraday | NO | The best evaluation horizon is daily regardless. |
| NAS-90 | "A practical validation design ... would test whether current regime scores improve: next 1-2 minute return direction, probability of extension vs snapback, slippage and fill quality, and conditional PnL by regime." | NAS p11 | METHOD (evaluation protocol) | PARTIAL (the package computes conditional results; it does not compute extension-vs-snapback or fill quality) | intraday | NO | n/a - protocol. |
| NAS-91 | "Validation should also be segmented by: open / midday / close, expiration vs non-expiration, high vs low gamma sign, event vs non-event days." | NAS p11 | METHOD (segmentation) | NOT | intraday, optchain, macro | NO | n/a - protocol. |
| NAS-92 | "Because no retrieved paper integrates all components, the most defensible approach is incremental: first test each axis alone, then test whether combinations improve discrimination." | NAS p11 | METHOD (ablation protocol) | NOT | price, volume, orderflow, optchain | YES (for the non-flow axes) | n/a - protocol. **This is the paper's own instruction for how to order the new specs.** |
| NAS-93 | "Stop treating regime as one variable. Use a dashboard of volatility, gamma, flow, liquidity, and event state." | NAS p12 (upgrade 1) | MARKET-STATE (framework) | PARTIAL (C1 is a 5-feature single-axis classifier) | price, volume, optchain, orderflow | NO | The single-axis classifier is sufficient. |
| NAS-94 | "Let gamma decide whether price is likely to be damped or amplified. That is often more actionable than trend labels alone." | NAS p12 (upgrade 2) | GATE | NOT | optchain | NO | Trend labels are as actionable as gamma. |
| NAS-95 | "Use order-flow imbalance on very short refresh cycles. Its edge is strongest there." | NAS p12 (upgrade 3) | TIMING | NOT | orderflow | NO | The edge is not concentrated at short cycles. |
| NAS-96 | "Normalize option flow by exposure. Raw contract counts are too blunt." | NAS p12 (upgrade 4) | METHOD + PARAMETER | NOT | optflow | NO | Raw counts are as good. |
| NAS-97 | "Treat time-of-day and catalysts as regime inputs, not background details." | NAS p12 (upgrade 5) | MARKET-STATE | NOT | macro, intraday | NO | They are background details. |
| NAS-98 | "Positive gamma and balanced liquidity favor mean-reversion and pinning behavior; negative gamma, rising volatility, and one-sided flow favor momentum and breakout behavior." | NAS p12 (Conclusion) | GATE + DIRECTIONAL | NOT | optchain, orderflow | NO | Gamma and flow do not select between mean reversion and momentum. |
| NAS-99 | "Option flow adds value when exposure-adjusted, but it must be interpreted carefully because it may represent volatility demand or hedging rather than pure directional information." | NAS p12 (Conclusion) | NEGATIVE | NOT | optflow | NO | Exposure-adjusted option flow is clean directional information. |
| NAS-100 | "the supplied literature does not provide a complete NASDAQ-specific integrated intraday model with tested 5-30 minute predictive accuracy or trading PnL, so the final edge will come from building and validating this framework on your own data." | NAS p12 (Conclusion) | NEGATIVE / LIMITATION | NOT | - | n/a | n/a - the gap a combined spec must fill. |

---

## 9. Derived views

All four lists below are **derived mechanically from the tables in sections 4-8**, not written by hand,
so they cannot drift from the inventory. The generator is `tools/build_claim_inventory.py`.

### 9.1 DIRECTIONAL claims - the tradable set

**80 of 293 distinct claims predict a direction** (long/short, up/down, fade/follow,
buy/sell, or a directional payoff). These are the only claims that can be an EDGE on their own. A gate,
a sizing rule, a classifier or a stop cannot be an edge - it modifies another signal.

The `Tradable here` column is the honest one: `YES` = the claim can be tested on this package's daily
panels today; `PROXY` = only via a stand-in that tests the proxy, not the construct; `NO` = the data
(historical options chain, order book, intraday) does not exist in this package.

| ID | Claim | Source | Status | Tradable here |
|---|---|---|---|---|
| OPT-02 | In VIX options, net buying pressure is temporally linked to changes in implied volatility, and higher buying pressure lowers next-day delta-hedged option returns. | GAM p1 | NOT | NO - data absent |
| OPT-03 | In Shanghai ETF options, call and put order imbalances are tied to contemporaneous underlying returns and then reverse, which the authors attribute mainly to market-maker delta hedging rather than informed trading. | GAM p1 | NOT | NO - data absent |
| OPT-04 | "Net demand pressure in TAIEX options has a significant impact on implied volatility level and slope, especially through unhedgeable risk; call buying pressure is negatively related to skewness and pu | GAM p1 | NOT | NO - data absent |
| OPT-06 | Gamma matters because hedging short gamma requires trading in the direction of price moves, which can create intraday momentum and amplify volatility. | GAM p1 | NOT | NO - data absent |
| OPT-08 | One study finds that intraday momentum persists only when VIX options' net gamma exposure is negative. | GAM p2 | NOT | NO - data absent |
| OPT-09 | Another finds that negative gamma exposure of option-market makers increases spot FX volatility, with a measurable effect in EURUSD and USDJPY. | GAM p2 | NOT | NO - data absent |
| OPT-17 | Can contain directional information when trades are informed; positive and negative informed option trades map to value premium and discount, and options trading can predict stock returns in some settings. | RET p9 | NOT | NO - data absent |
| OPT-18 | Dealer hedging / inventory pressure ... Often creates temporary price pressure and reversals, so same-day direction from option flow can be misleading if it reflects hedging rather than information. | RET p9 | NOT | NO - data absent |
| OPT-19 | If the signal is mostly order imbalance, it often reflects market-maker delta hedging, which can produce short-lived reversals rather than persistent direction. | RET p11 (Practical interpretation) | NOT | NO - data absent |
| IND-03 | Price-chart reading is presented as a straightforward, practical method that can improve entry/exit decisions without complex indicators. | IND p1 | NOT | NO - data absent |
| IND-04 | Volume carries information that price alone does not, and volume-based signals can improve forecastability in some settings. | IND p1 | IMPLEMENTED C4 | YES |
| IND-05 | In crypto, RSI was found more reliable than MACD or Stochastic for overbought/oversold style signals, and some indicator combinations using RSI/EMA/MACD/Bollinger show short-term usefulness. | IND p1 | PARTIAL | YES |
| IND-08 | Use price action first, then volume, then one momentum filter. Price/volume analysis is repeatedly supported as a practical base, while volume and RSI add confirmation. | IND p2 | NOT | YES |
| RET-01 | On-chain and blockchain variables repeatedly improve crypto forecasting and regime detection, with studies finding strong performance for active users, hashrate, wallet activity, transaction volume, and related features. | RET p1 | NOT | YES |
| RET-02 | Some technical rules work in crypto, but results are mixed: candlestick and indicator-based studies find pockets of predictive power, yet other work says technical rules have limited practical value. | RET p1 | NOT | YES |
| RET-03 | "Retail trading behavior and retail attention are often noisy or contrarian: retail crypto order behavior predicts returns in one study, but retail option activity is linked to poorer option returns,  | RET p1 | NOT | YES |
| RET-11 | "Order flow can contain information about future volatility and returns in several markets, but the effect depends on trader type, trade size, liquidity, and execution costs; in crypto, trade-flow imb | RET p1 | IMPLEMENTED C7 | PROXY only |
| RET-14 | Use a 12-month time-series momentum on Nasdaq and a shorter, crypto-adapted trend window such as 20-day or 2-4 week lookback for crypto. | RET p15 | NOT | YES |
| RET-15 | Time-series momentum is conventionally built on the past 12-month return, while crypto evidence shows short-horizon momentum can exist and 20-day moving-average rules can work. | RET p15 | NOT | YES |
| RET-16 | Go long when price is above its trend proxy; go short or flat when below, if your venue supports it. | RET p15 | NOT | YES |
| RET-21 | Entry: long if close > 20-day moving average and 20-day return is positive; short or exit if not. | RET p15 (Practical momentum version) | NOT | YES |
| RET-24 | Crypto pairs trading works better when the spread is well-behaved and liquidity is high; dynamic cointegration and higher-frequency data improve results. | RET p16 | NOT | YES |
| RET-25 | Mean-reversion evidence in crypto is strongest for pairs/spread frameworks, and the Hurst exponent can identify faster reversion; resilient filtering and dynamic cointegration help stabilize signals. | RET p16 | NOT | YES |
| RET-26 | Enter when spread is stretched beyond a threshold; optionally use a buffer zone to avoid noise. | RET p16 (Entry) | NOT | YES |
| RET-31 | For Nasdaq: use a cointegration or spread model on stable pairs, with a z-score entry and a mean-reversion exit. Cointegration-style pairs trading and mean-reversion filters are consistently supported. | RET p16 | NOT | YES |
| RET-32 | For crypto: use dynamic cointegration or Hurst-filtered pairs, with a short holding period and transaction-cost-aware exits. Crypto pairs trading shows intraday mean reversion and better results at higher frequency. | RET p16 | NOT | YES |
| RET-34 | Order flow is a major mechanism through which private information gets into prices, and informed flow is positively related to volatility and returns in several markets. | RET p20 | PARTIAL | PROXY only |
| RET-37 | Options-implied measures can also help identify momentum stage and improve stage-aware momentum selection. | RET p20 | NOT | NO - data absent |
| RET-39 | volume-augmented momentum beat pure price momentum in the UK study. | RET p23 | IMPLEMENTED C4 | YES |
| RET-40 | order-imbalance momentum outperformed plain price momentum in Taiwan. | RET p23 | NOT | NO - data absent |
| RET-41 | the retrieved study found early-stage momentum outperformed conventional momentum, while late-stage momentum underperformed. | RET p23 | NOT | NO - data absent |
| RET-42 | Go long when price is above its trend proxy, volume is rising, and order imbalance/turnover is positive. | RET p24 | NOT | NO - data absent |
| RET-46 | Enter long when price is stretched below fair value, order imbalance is extreme, and options activity implies temporary pressure rather than sustained informed demand. | RET p24 | NOT | NO - data absent |
| RET-47 | Enter short on the opposite setup when the stretch and pressure reverse. | RET p24 | NOT | NO - data absent |
| RET-49 | order imbalance in both stocks and options can create short-lived reversals and is often tied to hedging pressure. | RET p24 | NOT | NO - data absent |
| RET-53 | Overnight return patterns can predict intraday behavior in some markets, and the open/close are structurally important because traders adjust for overnight risk and information arrival. | RET p28 | NOT | NO - data absent |
| RET-57 | Treat these as the day's first auction boundaries; breaks that fail back inside often matter more than small inside-day moves. | RET p32 | NOT | NO - data absent |
| RET-60 | Net premium flow becomes more useful for reversals when it disagrees with CVD or fails to generate follow-through. | RET p32 | NOT | NO - data absent |
| RET-61 | A strong impulse into a low-volume area then stalls near volume-profile extremes: that is a better candidate for a fade than a breakout continuation. | RET p32 | NOT | NO - data absent |
| RET-62 | Fade long when price sweeps a premarket low, premium flow shows aggressive put buying or bearish pressure, but CVD stops making new lows and price reclaims the level. | RET p32 | NOT | NO - data absent |
| RET-63 | Fade short when price sweeps premarket high, premium flow is aggressive on calls, but CVD fails to confirm and price loses the level. | RET p32 | NOT | NO - data absent |
| RET-67 | Reversal risk is higher around the open because the market often overreacts there before prices normalize. | RET p36 (and p43) | NOT | NO - data absent |
| RET-68 | opening prices can be biased high relative to intraday prices, with reversals concentrated near the open. | RET p39 | NOT | NO - data absent |
| RET-69 | "opening-range acceptance shows up when price holds beyond the opening range with supportive volume and no immediate CVD failure, rejection shows up when price sweeps the range edge and quickly re-ent | RET p39 | NOT | NO - data absent |
| RET-71 | New high + stronger CVD = more consistent with acceptance; New low + weaker CVD = more consistent with acceptance lower. | RET p44 | NOT | NO - data absent |
| RET-83 | Mean reversion long: if price drops to $96 or lower, you may start looking for a bounce; $94 is the more extreme, higher-conviction stretch. | RET p50 | NOT | YES |
| RET-85 | Intraday mean reversion appears at shorter observation intervals, while momentum can dominate at even shorter intervals; that switching pattern is consistent with scalping being interval-dependent. | RET p52 | NOT | YES |
| REG-01 | The most defensible edge is regime-conditioned switching: run momentum in orderly trending states, and switch toward reversal/liquidity-provision in stressed, high-volatility, rebound, or illiquid states. | REG p1 (Key Findings, "Best general edge") | IMPLEMENTED C1 | YES |
| REG-05 | Momentum tends to work better in bullish/trending or calmer states and weakens sharply in downturns, crisis periods, and rebound-after-crash states. | REG p1 ("Momentum behavior") | IMPLEMENTED C3, C6 | YES |
| REG-06 | Short-term reversal strengthens when liquidity is poor, volatility is high, and order imbalance is large; this is consistent with liquidity-provision compensation. | REG p2 ("Reversal behavior") | PARTIAL | PROXY only |
| REG-08 | Directional-change and threshold/event-based methods are promising for faster markets and can outperform fixed-time baselines in some studies. | REG p2 ("Event-based detection") | NOT | YES (new feature needed) |
| REG-12 | Activate reversal/liquidity-provision in stress states, especially when VIa/volatility is high and liquidity is poor, because reversal payoffs tend to spike when other traders withdraw liquidity. | REG p3 (Direct Answer, 4) | IMPLEMENTED C8 | YES |
| REG-16 | the edge is often the switch, not the raw signal. | REG p4 | IMPLEMENTED C1 | YES |
| REG-21 | Drawdown-focused work adds that rising credit risk predicts deeper drawdowns well ahead of time, although the evidence does not compare drawdown features directly against other feature families in a unified test. | REG p6 | NOT | YES (new feature needed) |
| REG-24 | "Directional-change methods classify market behavior based on threshold moves rather than fixed time bars and have been reported to detect abnormal-volatility spells accurately while also outperformin | REG p6 | NOT | YES (new feature needed) |
| REG-31 | momentum may behave differently in low-vol bull and high-vol bull states even though both are 'up' markets. | REG p6 | NOT | YES |
| REG-36 | Reversal payoffs tend to strengthen in high VIX, illiquid, volatile, or order-imbalanced periods. | REG p7 | PARTIAL | YES |
| REG-38 | Reversal is stronger in illiquid stocks, lower-turnover environments, and more volatile conditions; profits are especially concentrated where liquidity is scarce. | REG p7 | IMPLEMENTED C8 | YES |
| REG-39 | In crypto, reversal/liquidity-provision returns are concentrated in lower-activity, less liquid, more volatile pairs, and panel evidence shows lagged return interacted with volume helps predict the effect. | REG p7 | PARTIAL | YES (new feature needed) |
| REG-41 | In U.S. index futures, there may be a brief continuation after the open followed by a longer sequence of intraday reversals, although the effect can weaken sharply after costs. | REG p7 | NOT | NO - data absent |
| REG-46 | Crypto-equity correlation is also regime-dependent. During some crisis windows, crypto co-moves with equities and loses safe-haven properties; in others, linkage weakens or temporarily flips. | REG p8 | NOT | YES |
| REG-50 | "Suggested state map with per-state exposure: 1. Tranquil uptrend - momentum on. 2. High-vol uptrend - momentum reduced, selective only. 3. Range/chop - low exposure or short-horizon mean reversion. 4 | REG p9 | PARTIAL | YES |
| NAS-02 | Positive/high gamma tends to damp volatility and favor pinning or mean reversion; negative gamma tends to amplify moves and breakout risk. Gamma state should change whether you fade moves or follow them. | NAS p1 | NOT | NO - data absent |
| NAS-08 | Positive/high gamma + narrow spreads + balanced flow + healthy depth: treat as a mean-reversion / pinning regime; fading stretched moves is more consistent with the evidence. | NAS p2 | NOT | NO - data absent |
| NAS-09 | Negative gamma + rising realized volatility + one-sided imbalance + depth depletion: treat as a momentum / breakout regime; continuation and faster tape response become more plausible. | NAS p2 | NOT | NO - data absent |
| NAS-16 | the same setup can have opposite expectancy in different states: a pullback can be a fade in a damped market but an entry in an amplified market. | NAS p3 | NOT | YES |
| NAS-37 | index-arbitrage work shows negative first-order autocorrelations consistent with prices being pulled back toward equilibrium. | NAS p5 | PARTIAL | YES |
| NAS-38 | persistence and reversion are asymmetric: negative prior returns tend to show stronger mean reversion than positive prior returns. | NAS p5 | NOT | YES |
| NAS-40 | Mean reversion is a real phenomenon, but it is context-dependent. | NAS p5 | PARTIAL | YES |
| NAS-42 | Short-gamma hedging creates momentum because hedgers trade in the same direction as the move, which can reinforce continuation intraday. | NAS p6 | NOT | NO - data absent |
| NAS-43 | As expiration approaches, hedging and exercise-related pressures can pull prices toward option strikes and constrain behavior around them. | NAS p6 | NOT | NO - data absent |
| NAS-54 | Balanced flow + good depth + narrow spread: range/mean-reversion conditions become more plausible. | NAS p7 | NOT | NO - data absent |
| NAS-55 | One-sided flow + thin depth + rising message intensity: breakout/momentum conditions become more plausible. | NAS p7 | NOT | NO - data absent |
| NAS-61 | One study separates directional option flow from volatility-demand flow and finds that only volatility-strategy order flow predicts next-day realized volatility, not next-day index returns. | NAS p8 | NOT | NO - data absent |
| NAS-62 | Other studies show predictive power in open-buy put-call ratios, especially for more leveraged OTM options and in conditions associated with informed trading. | NAS p8 | NOT | NO - data absent |
| NAS-78 | Mean-reversion / pinning - Positive gamma, balanced flow, narrower spread, decent depth, strike proximity - Fade extensions; smaller targets; passive or semi-passive execution. | NAS p10 (regime label table) | NOT | NO - data absent |
| NAS-79 | Momentum / breakout - Negative gamma, rising realized vol, one-sided imbalance, depth depletion - Follow breaks; faster exits/entries; more aggressive execution. | NAS p10 | NOT | NO - data absent |
| NAS-87 | Fade less and follow more when short-gamma dynamics likely amplify price movement. | NAS p11 | NOT | NO - data absent |
| NAS-88 | Fade more and chase less when gamma is stabilizing and strike pinning is plausible. | NAS p11 | NOT | NO - data absent |
| NAS-98 | Positive gamma and balanced liquidity favor mean-reversion and pinning behavior; negative gamma, rising volatility, and one-sided flow favor momentum and breakout behavior. | NAS p12 (Conclusion) | NOT | NO - data absent |

**Summary:** 80 directional claims total. 35 are testable on this package's daily
panels (with 22 of those not implemented in C1-C8). 45 need data the
package does not have - predominantly a historical options chain (gamma, option flow, strike distance)
or an order book (CVD, spread, depth).

**After removing the claims that a standalone spec has already tested** (section 9.7), the genuinely
NEW directional backlog that is testable on daily bars is **16 claims**.

**The single most important structural finding:** of the directional claims that ARE testable here, the
paper-supported ones cluster into three families - (a) time-series momentum, (b) short-horizon mean
reversion, and (c) pairs/spread reversion. Everything the options papers assert directionally is
untestable without a chain archive. That is a data-acquisition problem, not a modelling one.

### 9.2 Claims specifically about LONG / SHORT, PAIRS and HEDGING

**37 claims.** The user wants a strategy that can go long OR short and can hedge. This is
exactly what the papers do and do not supply.

**What the papers DO support:**
- **Long/short via a regime switch** (REG-01, REG-12, REG-50, REG-64, REG-65; RET-16, RET-21).
- **Market-neutral long/short via PAIRS / cointegrated spreads** (RET-24, RET-25, RET-26, RET-27,
  RET-31, RET-32, RET-33, RET-48). This is the papers' only genuine HEDGING construction, and it is a
  relative-value one: long the cheap leg, short the rich leg.
- **A short leg that is stronger than the long leg** (NAS-38) - directly actionable for how a long/short
  book should be weighted.
- **A crypto-vs-equity hedge condition** (REG-46, REG-47) - the papers explicitly state that crypto
  loses safe-haven properties in some crisis regimes and that a crypto regime model needs an external
  linkage input. That is a hedge-timing rule, not a hedge instrument.

**What the papers DO NOT support - stated plainly, because it changes the build:**
- **No paper proposes hedging a position with options or derivatives as a strategy.** Across all six
  papers, options and gamma appear only as *signal inputs* (regime classifier, volatility forecaster,
  flow pressure gauge). There is no long-options / put-write / collar / tail-hedge construction, no
  long-vol-versus-short-vol trade, and no option-spread overlay anywhere in the evidence set. If the
  user wants option-based hedging, that is NEW construction with no paper claim behind it, and it must be
  labelled as such rather than attributed to these papers.
- **The gamma claims are directional-AGNOSTIC by the papers' own statement** (OPT-20, OPT-21, NAS-98,
  NAS-100): gamma predicts whether a move PERSISTS, not which way it goes. It is a fade-vs-follow
  switch, not a long/short signal.
- **The one standalone long/short result that exists is the strongest single finding in the set:**
  `nasdaq_12m_timeseries_momentum` (12-month time-series momentum, long above the trend proxy / short
  below, vol-scaled) came out **SUPPORTED**, while the vol-gated variant `v1_nasdaq_12m_tsm_vol_scaled`
  came out **REFUTED** and the crypto 20-day analogue came out **REFUTED / FRAGILE**. The difference
  between the two Nasdaq runs is the only thing that discriminates them, and it should be the first
  thing a new spec replicates.

| ID | Claim | Why it is a long/short or hedging claim | Status | Daily? |
|---|---|---|---|---|
| OPT-08 | One study finds that intraday momentum persists only when VIX options' net gamma exposure is negative. | Intraday momentum persists ONLY when net gamma is negative - a conditional long/short continuation. | NOT | NO |
| OPT-17 | Can contain directional information when trades are informed; positive and negative informed option trades map to value premium and discount, and options trading can predict stock returns in some settings. | Informed option trades map to value premium and discount - a long/short mapping from options flow. | NOT | NO |
| OPT-18 | Dealer hedging / inventory pressure ... Often creates temporary price pressure and reversals, so same-day direction from option flow can be misleading if it reflects hedging rather than information. | Dealer hedging creates temporary price pressure and REVERSALS - a contrarian short leg. | NOT | NO |
| OPT-19 | If the signal is mostly order imbalance, it often reflects market-maker delta hedging, which can produce short-lived reversals rather than persistent direction. | Order imbalance often reflects market-maker delta hedging, producing short-lived REVERSALS. | NOT | NO |
| OPT-20 | Negative gamma can amplify both upside and downside moves depending on the initiating shock. | Negative gamma amplifies BOTH upside and downside - the sign of the amplification is not predicted. | NOT | NO |
| IND-09 | Trade only when the regime matches the strategy. Mean-reversion tools work better in some markets/periods, while trend tools work better in others. | Trend tools vs mean-reversion tools: choose the side by regime. | IMPLEMENTED | YES |
| RET-16 | Go long when price is above its trend proxy; go short or flat when below, if your venue supports it. | 'Go long when price is above its trend proxy; go short or flat when below' - explicit long/short. | NOT | YES |
| RET-21 | Entry: long if close > 20-day moving average and 20-day return is positive; short or exit if not. | 'long if close > 20-day MA and 20-day return positive; short or exit if not' - explicit long/short. | NOT | YES |
| RET-24 | Crypto pairs trading works better when the spread is well-behaved and liquidity is high; dynamic cointegration and higher-frequency data improve results. | Crypto PAIRS trading - a market-neutral long/short construction. | NOT | YES |
| RET-25 | Mean-reversion evidence in crypto is strongest for pairs/spread frameworks, and the Hurst exponent can identify faster reversion; resilient filtering and dynamic cointegration help stabilize signals. | Mean-reversion evidence in crypto is strongest for PAIRS/SPREAD frameworks. | NOT | YES |
| RET-26 | Enter when spread is stretched beyond a threshold; optionally use a buffer zone to avoid noise. | Pair-spread entry: enter when the spread is stretched beyond a threshold, with a buffer zone. | NOT | YES |
| RET-27 | Exit when spread reverts to mean; use tight time stops because crypto mean reversion can be fast. | Pair-spread exit: exit when the spread reverts to mean. | NOT | YES |
| RET-31 | For Nasdaq: use a cointegration or spread model on stable pairs, with a z-score entry and a mean-reversion exit. Cointegration-style pairs trading and mean-reversion filters are consistently supported. | Nasdaq PAIRS: cointegration/spread model, z-score entry, mean-reversion exit - long/short basket. | NOT | YES |
| RET-32 | For crypto: use dynamic cointegration or Hurst-filtered pairs, with a short holding period and transaction-cost-aware exits. Crypto pairs trading shows intraday mean reversion and better results at higher frequency. | Crypto PAIRS: dynamic cointegration or Hurst-filtered pairs with short holds. | NOT | YES |
| RET-33 | regime-switching and faster holding periods improved pairs-trading results in the retrieved studies. | Regime-switching plus faster holding periods improved PAIRS-trading results. | NOT | YES |
| RET-46 | Enter long when price is stretched below fair value, order imbalance is extreme, and options activity implies temporary pressure rather than sustained informed demand. | Composite reversion ENTRY LONG: stretched below fair value + extreme imbalance + temporary pressure. | NOT | NO |
| RET-47 | Enter short on the opposite setup when the stretch and pressure reverse. | 'Enter short on the opposite setup when the stretch and pressure reverse' - the explicit SHORT leg. | NOT | NO |
| RET-48 | Exit fast when spread normalizes; shorter holding periods produced better performance in the regime-switching pairs study, and intraday or short-horizon reversion was repeatedly more viable than long holds. | Exit fast when the spread normalizes - the exit rule for a long/short spread book. | NOT | YES |
| RET-49 | order imbalance in both stocks and options can create short-lived reversals and is often tied to hedging pressure. | Imbalance-driven short-lived reversals - the mechanism behind a contrarian short leg. | NOT | NO |
| REG-01 | The most defensible edge is regime-conditioned switching: run momentum in orderly trending states, and switch toward reversal/liquidity-provision in stressed, high-volatility, rebound, or illiquid states. | The regime switch is the two-leg long/short construction (momentum leg / reversal leg). | IMPLEMENTED | YES |
| REG-12 | Activate reversal/liquidity-provision in stress states, especially when VIa/volatility is high and liquidity is poor, because reversal payoffs tend to spike when other traders withdraw liquidity. | Activates the reversal (opposite-side) leg in stress states. | IMPLEMENTED | YES |
| REG-40 | The evidence repeatedly warns that reversal is horizon-specific. Intraday and one-day effects can be strong even when longer-horizon effects are weak or different. | Reversal is horizon-specific; the long and short legs differ by horizon. | NOT | YES |
| REG-46 | Crypto-equity correlation is also regime-dependent. During some crisis windows, crypto co-moves with equities and loses safe-haven properties; in others, linkage weakens or temporarily flips. | HEDGING: crypto-equity correlation is regime-dependent; crypto loses safe-haven properties in some crisis windows. | NOT | YES |
| REG-47 | a crypto regime model should include not only internal features like volatility and liquidity, but also external linkage conditions with equities or macro shocks. | HEDGING: a crypto regime model should include external linkage to equities - i.e. a hedge-condition input. | NOT | YES |
| REG-50 | "Suggested state map with per-state exposure: 1. Tranquil uptrend - momentum on. 2. High-vol uptrend - momentum reduced, selective only. 3. Range/chop - low exposure or short-horizon mean reversion. 4 | The 5-state map assigns momentum-on / reversal-favoured / smaller-size per state - a long/short ladder. | PARTIAL | YES |
| REG-64 | Momentum belongs to orderly trend states. | Conclusion: momentum belongs to trend states, reversal to stress states - the core long/short rule. | PARTIAL | YES |
| REG-65 | "the best evidence-backed starting point is a small multi-state classifier with volatility, trend, drawdown, and liquidity inputs, used to switch between momentum and reversal rather than forcing one  | Switch between momentum and reversal rather than forcing one model to work all the time. | IMPLEMENTED | YES |
| NAS-16 | the same setup can have opposite expectancy in different states: a pullback can be a fade in a damped market but an entry in an amplified market. | 'A pullback can be a fade in a damped market but an ENTRY in an amplified market' - same setup, opposite side by state. | NOT | YES |
| NAS-38 | persistence and reversion are asymmetric: negative prior returns tend to show stronger mean reversion than positive prior returns. | ASYMMETRY: negative prior returns mean-revert MORE strongly than positive ones - the short leg deserves more size. | NOT | YES |
| NAS-43 | As expiration approaches, hedging and exercise-related pressures can pull prices toward option strikes and constrain behavior around them. | Pinning: prices are pulled toward option strikes near expiry - a mean-reversion mechanism. | NOT | NO |
| NAS-54 | Balanced flow + good depth + narrow spread: range/mean-reversion conditions become more plausible. | Balanced flow + good depth + narrow spread -> range/mean-reversion conditions become more plausible. | NOT | NO |
| NAS-55 | One-sided flow + thin depth + rising message intensity: breakout/momentum conditions become more plausible. | One-sided flow + thin depth + rising message intensity -> breakout/momentum conditions become more plausible. | NOT | NO |
| NAS-78 | Mean-reversion / pinning - Positive gamma, balanced flow, narrower spread, decent depth, strike proximity - Fade extensions; smaller targets; passive or semi-passive execution. | Mean-reversion/pinning regime -> FADE extensions. | NOT | NO |
| NAS-79 | Momentum / breakout - Negative gamma, rising realized vol, one-sided imbalance, depth depletion - Follow breaks; faster exits/entries; more aggressive execution. | Momentum/breakout regime -> FOLLOW breaks. | NOT | NO |
| NAS-87 | Fade less and follow more when short-gamma dynamics likely amplify price movement. | 'Fade less and follow more when short-gamma dynamics likely amplify price movement.' | NOT | NO |
| NAS-88 | Fade more and chase less when gamma is stabilizing and strike pinning is plausible. | 'Fade more and chase less when gamma is stabilizing and strike pinning is plausible.' | NOT | NO |
| NAS-98 | Positive gamma and balanced liquidity favor mean-reversion and pinning behavior; negative gamma, rising volatility, and one-sided flow favor momentum and breakout behavior. | Positive gamma + balanced liquidity -> mean reversion; negative gamma + rising vol + one-sided flow -> momentum. | NOT | NO |

### 9.3 Claims about RISK MANAGEMENT and POSITION SIZING

**36 claims.** These are not edges. They are what makes an edge tradable - and they are
the area where the package is weakest, because the current `RISK_BLOCK` in `paperspecs.py` is a set of
**analyst choices with no paper behind them** (`vol_target 0.15`, `max_position 0.10`, `max_names 5`,
`net_target 0.0`, `rebalance monthly`, `gross_leverage 1.0` are all marked `analyst_choice` in
`parameter_provenance`).

The papers do supply concrete, testable risk rules. Adopting them would replace analyst choices with
paper-grounded parameters - the single cheapest improvement available to the spec set.

| ID | Claim | Type | Status | Daily? |
|---|---|---|---|---|
| OPT-05 | Across stocks, FX, bonds, and index options, implied volatility often contains incremental information about future realized volatility, and in several studies it outperforms historical volatility forecasts. | SIZING + MARKET-STATE | IMPLEMENTED | YES |
| OPT-11 | The 2023 stock study also finds that low net gamma exposure predicts higher future realized volatility, supporting gamma exposure as a forward-looking volatility signal. | SIZING + MARKET-STATE | NOT | NO |
| OPT-14 | Use implied volatility as the baseline forecast. Across many markets, IV is usually the cleaner direct predictor of future realized volatility than historical volatility alone. | SIZING + MARKET-STATE | IMPLEMENTED | YES |
| RET-13 | Momentum and trend rules are more likely to survive in liquid assets and are sensitive to transaction costs and turnover. | UNIVERSE + RISK | NOT | YES |
| RET-17 | Trade only when realized volatility is not extreme, and scale position size by inverse volatility. | GATE + SIZING | PARTIAL | YES |
| RET-18 | Risk-managed momentum improves crypto performance, and volatility scaling is a core part of momentum strategy design. | SIZING | PARTIAL | YES |
| RET-19 | Stop-loss momentum outperforms other crypto momentum variants and improves downside control. | RISK | NOT | YES |
| RET-22 | Sizing: volatility-scaled position size with a capped max allocation. | SIZING | PARTIAL | YES |
| RET-23 | Exit: stop-loss plus trend failure exit. | TIMING + RISK | NOT | YES |
| RET-44 | "Size positions by inverse volatility and cut losers quickly; this is consistent with the volatility-normalized momentum literature and the deep-learning/changepoint result that momentum improves when | SIZING + TIMING | PARTIAL | YES |
| RET-73 | "the best stop framework is: tight-to-moderate trailing stop for momentum, and wider hard stop or time stop for mean reversion - because stop-losses help momentum payoffs but can hurt mean-reversion r | RISK | NOT | YES |
| RET-74 | "Stop-loss momentum outperformed other momentum variants in crypto, and broader trailing-stop studies found narrower stops reduce returns while wider stops perform better; one empirical result suggest | RISK | NOT | YES |
| RET-75 | "For mean-reverting spreads, stop-losses should sit outside the entry region; higher stop-loss levels lower the optimal take-profit level, and stop-loss policies can reduce expected returns because th | RISK | NOT | YES |
| RET-76 | For crypto momentum, the evidence is especially supportive of using stop-loss rules because they improved returns, Sharpe, and alpha across many coins and across market states. | RISK | NOT | YES |
| RET-77 | Avoid a tight trailing stop, because mean reversion needs room to snap back and stop-losses can destroy that edge. | RISK + NEGATIVE | NOT | YES |
| RET-78 | Prefer a time stop if the spread does not revert quickly, since short-horizon reversion is where the edge is strongest and prolonged holds increase damage from drift or costs. | TIMING + RISK | NOT | YES |
| RET-79 | "1 and 1.5 standard deviation thresholds produced better results than the classic pairs-trading setup in one study, and a separate trailing-stop study found higher thresholds, typically 1.0 to 1.5 sta | RISK + PARAMETER | NOT | YES |
| RET-82 | 1.0 SD = first alert zone. 1.5 SD = stronger signal zone. You can use the band as an entry trigger, an exit trigger, or a stop buffer. | RISK + TIMING | NOT | YES |
| RET-86 | "Stop-losses can improve momentum-style systems, but in some settings too-tight stops reduce performance or increase downside exposure; the best results in the retrieved studies come from moderate, no | RISK | NOT | YES |
| RET-87 | For a BTC momentum long, the 1.0 standard deviation rule is better understood as a volatility-based stop distance from your entry or reference price, not '1 SD of the current price' in a raw sense. | RISK | NOT | YES |
| RET-88 | The evidence on Bitcoin says volatility is high, persistent, and regime-dependent, so a stop that is too tight is more likely to get clipped by noise. | RISK + MARKET-STATE (vol persistence) | NOT | YES |
| RET-89 | A volatility-normalized stop band means your stop is set as a distance measured in units of recent market volatility, not as a fixed dollar or percentage amount. | RISK + SIZING | NOT | YES |
| RET-90 | It adapts to regime changes: higher volatility usually means a wider stop band is needed. | SIZING + RISK | NOT | YES |
| RET-91 | "For a BTC momentum long, you can trail the stop upward as price rises, and a 1.0 to 1.5 standard deviation band is a reasonable way to size that trailing distance because the evidence favors moderate | RISK (trailing) | NOT | YES |
| RET-92 | Do not anchor the stop to the original entry only; instead, ratchet the stop up as BTC makes new highs, using a recent volatility measure as the buffer. | RISK (ratchet) | NOT | YES |
| REG-14 | Translate state probabilities into explicit position-sizing and turnover controls rather than signal switching alone. | SIZING | PARTIAL | YES |
| REG-35 | Consider risk-managed or crash-aware variants where possible. | RISK | NOT | YES |
| REG-50 | "Suggested state map with per-state exposure: 1. Tranquil uptrend - momentum on. 2. High-vol uptrend - momentum reduced, selective only. 3. Range/chop - low exposure or short-horizon mean reversion. 4 | SIZING + DIRECTIONAL | PARTIAL | YES |
| NAS-24 | Time-of-day changes execution quality: midday tends to have lower execution cost but slower execution, while open/close tends to be faster but more expensive and more event-sensitive. | RISK + MARKET-STATE (session) | NOT | NO |
| NAS-53 | Low depth worsens execution quality by increasing price impact and sensitivity to order-book events. | RISK | NOT | NO |
| NAS-78 | Mean-reversion / pinning - Positive gamma, balanced flow, narrower spread, decent depth, strike proximity - Fade extensions; smaller targets; passive or semi-passive execution. | DIRECTIONAL + SIZING + RISK | NOT | NO |
| NAS-81 | Event-distorted - Macro/earnings/expiry, IV buildup or collapse, hedging surges - Reduce reliance on normal templates; size down or switch to event logic. | SIZING | NOT | NO |
| NAS-82 | Fragile liquidity - Thin depth, wider spreads, faster quote revisions - Smaller size, aggressive only when urgency justified. | SIZING + RISK | NOT | NO |
| NAS-84 | Use more passive execution when depth is adequate, spreads are narrower, and imbalance is not strongly one-sided; waiting cost is lower and fill probability is more acceptable. | RISK + EXECUTION | NOT | NO |
| NAS-85 | Use more aggressive execution when imbalance is one-sided, volatility is elevated, spreads reflect informed trading, or immediacy is critical. | RISK + EXECUTION | NOT | NO |
| NAS-86 | Reduce size or avoid trading in low-depth, high-fragility states because price impact risk rises materially. | SIZING + RISK | NOT | NO |

**Concretely, the papers license these risk changes to the existing block:**
- A **stop-loss overlay** differentiated by model type (RET-19, RET-73, RET-74, RET-76): a
  tight-to-moderate TRAILING stop for momentum, a wider FIXED stop plus a TIME stop for mean reversion.
  Note the polarity that matters: the papers say stop-losses HELP momentum and HURT mean reversion
  (RET-73, RET-75, RET-77).
- A **volatility-normalized stop distance** of 1.0-1.5 rolling standard deviations from the entry, with
  the stop RATCHETING as new highs are made (RET-79, RET-82, RET-87, RET-89, RET-90, RET-91, RET-92).
  This is a paper-grounded replacement for the current flat `vol_target 0.15`.
- **Inverse-volatility position scaling** as an explicit momentum sizing rule (RET-17, RET-18, RET-22,
  RET-44) - the package has the machinery (`blended_volatility`, `target_vol`) but the paper's rule is
  not expressed as a spec.
- **State-proportional exposure** (REG-14, REG-50): translate state probabilities into position sizing and
  turnover controls, with the specific 5-step ladder (full / reduced / low / smaller / off). C1 currently
  switches hard between two legs instead of grading exposure.
- **Per-regime size cuts** in the NASDAQ taxonomy (NAS-81, NAS-82, NAS-86): size down or stand aside in
  event-distorted and fragile-liquidity states.
- **Cost discipline** (IND-10, REG-58): the papers explicitly warn that reversal is 'much weaker after
  costs' and that 'nice-looking indicator results can collapse once transaction costs and out-of-sample
  testing are included'. The package's `cost_multiplier 2.0` already encodes this, and every risk claim
  above must be evaluated at that stressed multiple, not at 1.0.

**A warning the risk section must carry:** the standalone runs already show that adding risk machinery
does NOT rescue a weak signal - `sd_band_mean_reversion_crypto` (wide fixed stop + time stop + 1.0/1.5 SD
band) was REFUTED, and `crypto_ma20_trend_momentum` (vol-scaled sizing + stop-loss + trend-failure exit)
was REFUTED with a gross Sharpe of 0.74 that costs consumed. Risk overlay is a filter on an edge, not a
substitute for one.

### 9.4 The papers' own fragility, limitation and failure-mode claims

**43 claims.** These are worth testing DIRECTLY as negative controls, because a claim that
is right about its own limits is falsifiable in the same way as an edge. Two rules make them useful:

1. **Every claim that says a signal is NOT directional should be tested as a spec whose expected verdict is
   FAIL.** If a 'gamma does not predict direction' control comes out SUPPORTED, the validation is not
   discriminating and every other verdict is void. The package already builds inverted-polarity twins
   (`build_negative_controls` in `paperspecs.py`); these claims are the same idea at the level of the
   paper's content, and they need their own twin set.
2. **The limitations are a specification of what NOT to build.** REG-53, REG-56, NAS-12, NAS-100 and
   NAS-92 together tell you the order of work: test each axis alone first, then test whether
   combinations improve discrimination - and do not claim a single best detector until that horse race
   has been run.

| ID | Claim | Type | Status | Daily? |
|---|---|---|---|---|
| OPT-15 | gamma exposure is much weaker as a pure direction signal and is better viewed as a price-pressure / volatility regime indicator rather than a forecast of up vs. down. | NEGATIVE | NOT | NO |
| OPT-18 | Dealer hedging / inventory pressure ... Often creates temporary price pressure and reversals, so same-day direction from option flow can be misleading if it reflects hedging rather than information. | DIRECTIONAL + NEGATIVE | NOT | NO |
| OPT-21 | hedging and inventory effects often dominate short-horizon price changes, while gamma is consistently stronger for volatility than for direction. | COMPARATIVE + NEGATIVE | NOT | NO |
| IND-02 | price action and simple technical rules can work better as a disciplined framework than as a 'signal soup'. | COMPARATIVE + NEGATIVE | NOT | YES |
| IND-10 | Several studies warn that nice-looking indicator results can collapse once transaction costs and out-of-sample testing are included. | NEGATIVE | PARTIAL | YES |
| RET-04 | Options order flow can inform future volatility, but not consistently future returns; retail option demand is associated with lower option returns, and net gamma is negatively related to future volatility in one study. | MARKET-STATE + NEGATIVE | NOT | NO |
| RET-05 | Charm surface and vanna exposure are not directly tested in the retrieved evidence, so any claim that they are the 'best' retail edge would be an inference rather than a directly supported finding. | NEGATIVE | OTHER | NO |
| RET-20 | Crypto momentum is temporally heterogeneous and can fail in some sample periods; trend-based rules perform better in some bull regimes than others. | GATE + NEGATIVE | PARTIAL | YES |
| RET-30 | mean-reversion strategies can under-perform in trending periods. | GATE + NEGATIVE | PARTIAL | YES |
| RET-38 | Options order flow can transmit information to the underlying market through informed trading or dealer hedging, but direction is weaker than the volatility signal because some flow is just inventory management. | NEGATIVE + COMPARATIVE | NOT | NO |
| RET-50 | options flow was shown to be informative for volatility but not reliably for direction. | NEGATIVE | NOT | NO |
| RET-54 | 0DTE deltas change rapidly and require frequent hedging, making them especially noisy for scalping if you treat them as a clean directional signal. | NEGATIVE | NOT | NO |
| RET-66 | If gamma shifts but CVD and tape speed do not confirm, the gamma signal is probably telling you about regime, not immediate direction. | GATE + NEGATIVE | NOT | NO |
| RET-77 | Avoid a tight trailing stop, because mean reversion needs room to snap back and stop-losses can destroy that edge. | RISK + NEGATIVE | NOT | YES |
| RET-93 | HFT scalpers can increase intraday volatility, worsen market quality, and front-run order flow in some settings. | NEGATIVE (market impact) | NOT | NO |
| REG-07 | Crypto regime behavior is more horizon-specific and structurally unstable than equities; daily, weekly, and intraday findings often disagree. | MARKET-STATE + NEGATIVE | NOT | YES |
| REG-42 | Crypto studies similarly emphasize that daily aggregation can hide intraday mean reversion. | NEGATIVE / LIMITATION | NOT | n/a |
| REG-53 | "The supplied evidence does not provide a clean head-to-head out-of-sample ranking of volatility, trend, autocorrelation, drawdown, and liquidity features for Nasdaq, stocks, and crypto under identica | NEGATIVE + COMPARATIVE | NOT | YES |
| REG-54 | Nasdaq-specific evidence is thinner than broader U.S. equity/S&P 500 evidence, so some Nasdaq guidance is inferred from broader index behavior rather than directly tested on Nasdaq-only datasets. | NEGATIVE / LIMITATION | NOT | YES |
| REG-55 | Several strategy findings are directionally strong, but the provided excerpts often lack standardized transaction-cost-adjusted Sharpe/drawdown comparisons across assets. | NEGATIVE | PARTIAL | YES |
| REG-56 | "The main evidence gap is methodological: the supplied studies do not provide a unified out-of-sample comparison proving whether volatility, trend, drawdown, liquidity, HMMs, HSMMs, or event-based cla | NEGATIVE + COMPARATIVE | NOT | YES |
| REG-57 | Crypto is sometimes described as a diversifier and sometimes not; momentum appears at some crypto horizons and disappears or reverses at others. | NEGATIVE | NOT | YES |
| REG-58 | reversal signals can be economically meaningful before costs but much weaker after costs in some intraday futures settings. | NEGATIVE | PARTIAL | YES |
| NAS-06 | Flow signals have failure modes. Gamma estimates can be stale/model-dependent; option flow may reflect hedging or vol demand, not direction. | NEGATIVE | NOT | NO |
| NAS-12 | "The supplied evidence does not include a NASDAQ-specific integrated intraday regime model that jointly combines gamma, option flow, realized volatility, and order imbalance with out-of-sample 5-30 mi | NEGATIVE / LIMITATION | NOT | n/a |
| NAS-13 | NASDAQ-specific evidence for intraday half-life around VWAP, opening range, or prior-day close is not directly provided. | NEGATIVE / LIMITATION | NOT | NO |
| NAS-14 | Dealer-gamma measures based on open interest can be stale and model-sensitive, especially for single-stock estimation. | NEGATIVE | NOT | NO |
| NAS-15 | Some option-flow evidence comes from broader U.S. options samples rather than directly from NASDAQ underlyings, so application to QQQ/NDX should be treated as informed transfer rather than direct proof. | NEGATIVE / LIMITATION | NOT | NO |
| NAS-39 | There is no direct supplied evidence giving NASDAQ-specific half-life estimates around VWAP or opening range, so those thresholds must be empirically estimated in your own data. | LIMITATION + instruction | NOT | YES |
| NAS-44 | Near-strike conditions are further associated with more fleeting orders and a higher chance of crossing the strike on expiration day, implying local instability even inside an otherwise 'pinned' regime. | NEGATIVE (nuance that qualifies NAS-43) | NOT | NO |
| NAS-52 | This makes imbalance highly relevant for scalping, but only if it is treated as a short-lived state variable, not a durable directional forecast. | TIMING + NEGATIVE | NOT | NO |
| NAS-61 | One study separates directional option flow from volatility-demand flow and finds that only volatility-strategy order flow predicts next-day realized volatility, not next-day index returns. | DIRECTIONAL **NEGATIVE** | NOT | NO |
| NAS-63 | raw options activity should not be read mechanically as bullish or bearish. The same gross volume can reflect: a directional bet, a hedge, volatility demand, or positioning around an event. | NEGATIVE | NOT | NO |
| NAS-65 | Dealer gamma proxies often rely on strong assumptions about who holds what, whether dealers are counterparties, and whether exposures are fully delta-hedged. | NEGATIVE | NOT | NO |
| NAS-66 | Individual-stock gamma estimates can be severely noisy, highly dispersed, and sometimes of doubtful usefulness beyond averages. | NEGATIVE | NOT | NO |
| NAS-67 | Gamma estimates also depend on implied-volatility modeling, and Black-Scholes-based deltas/gammas can be biased under actual smiles and smirks. | NEGATIVE | NOT | NO |
| NAS-68 | More recent work even questions whether empirical 'gamma' in some studies cleanly identifies the convexity coefficient traders think they are using. | NEGATIVE | NOT | NO |
| NAS-69 | Order-flow predictability is strongest at short horizons and can weaken in more liquid, narrow-spread conditions. | NEGATIVE | NOT | NO |
| NAS-70 | intraday price discovery is driven more by stock net trade volume than by option net trade volume; option information may show up more in quote revisions than in trade flow. | NEGATIVE + COMPARATIVE | NOT | NO |
| NAS-71 | Public order flow can also move implied volatility directly, which means heavy options activity may reflect repricing of vol rather than clean directional information. | NEGATIVE | NOT | NO |
| NAS-72 | use gamma, option flow, and imbalance as conditional evidence, not standalone truth. | NEGATIVE + framing | NOT | NO |
| NAS-99 | Option flow adds value when exposure-adjusted, but it must be interpreted carefully because it may represent volatility demand or hedging rather than pure directional information. | NEGATIVE | NOT | NO |
| NAS-100 | "the supplied literature does not provide a complete NASDAQ-specific integrated intraday model with tested 5-30 minute predictive accuracy or trading PnL, so the final edge will come from building and | NEGATIVE / LIMITATION | NOT | n/a |

**The highest-value negative controls, in order:**

| Rank | ID | Why |
|---|---|---|
| 1 | REG-56 | The paper explicitly says no unified out-of-sample comparison exists for volatility vs trend vs drawdown vs liquidity vs HMM vs event classifiers. The horse race it asks for is a spec, and it is the one that would let the package claim (or refuse) a best detector. |
| 2 | REG-53 | Feature-family ablation. If no family dominates, then 'volatility is the most consistently useful regime feature' (REG-20) is refuted and C1's four-feature design has no privileged input. |
| 3 | NAS-61 | Only volatility-strategy order flow predicts next-day realised volatility, NOT next-day index returns. A clean directional negative that would be embarrassing to get wrong. |
| 4 | OPT-15 | Gamma is 'much weaker as a pure direction signal' - Medium for direction, High for volatility regime. If gamma-as-direction profits, this control fails. |
| 5 | IND-10 | Results collapse once costs and out-of-sample are included. Tests whether the package's own gross-of-costs stage is doing real work. |
| 6 | REG-58 | Reversal is economically meaningful before costs but much weaker after. A direct cost-sensitivity control on C8. |
| 7 | NAS-66 | Individual-stock gamma estimates are 'severely noisy... of doubtful usefulness beyond averages'. Kills a whole family of gamma specs if true. |
| 8 | REG-42 | 'Daily aggregation can hide intraday mean reversion.' This is a binding CAVEAT on C8, not a spec: a SUPPORTED daily-bar C8 verdict may NOT be reported as evidence for an intraday edge. |
| 9 | RET-85 | Reversal at short horizons, momentum at even shorter ones, with the sign FLIPPING by horizon. If the flip is real, a single-horizon reversion spec will report a misleading sign. |
| 10 | IND-02 | Indicator stacking is 'signal soup' and is weaker than a disciplined single rule. A direct ablation against a stacked baseline. NOTE: already tested - both `crypto_rsi_oversold_fade` and `tradingview_price_volume_rsi_regime_filtered` came out REFUTED, so the control has a prior result. |

### 9.5 Build priority: proposed new specifications

Each proposed concept below is grounded in at least one NOT-implemented claim that is testable on daily
bars. IDs continue the existing C1-C8 convention. The 'Prior test' column records what the standalone
specs already found, so nothing refuted is rebuilt without a new reason.

| Proposed | Concept | Paper claims | What it tests | Prior test | New work needed |
|---|---|---|---|---|---|
| C9 | Standalone time-series momentum (long/short), cross-asset | RET-14, RET-15, RET-16, RET-21, REG-31 | Does the 12-month Nasdaq rule and the 20-day crypto rule behave differently by asset class, and does the horizon interact with the regime? | MIXED: `nasdaq_12m_timeseries_momentum` SUPPORTED; `v1_nasdaq_12m_tsm_vol_scaled` REFUTED; `crypto_ma20_trend_momentum` REFUTED; `v1_crypto_momentum_20d_ma` FRAGILE. The two Nasdaq runs differ only in the volatility gate - that difference IS the hypothesis. | signal `time_series_momentum` (needs a 252-bar lookback and an explicit short leg); run it across all 6 asset classes, not just one |
| C10 | Asymmetric reversal - the short leg is stronger | NAS-38, REG-39, REG-40 | Does mean reversion after DOWN moves exceed mean reversion after UP moves, and does sizing the short leg accordingly beat symmetric reversion? | NONE. This is the single most actionable untested directional claim for a long/short book. | sign-split feature (lagged return x sign) and a two-sided reversion signal |
| C11 | Pairs / cointegration spread mean reversion | RET-24, RET-25, RET-26, RET-27, RET-31, RET-32, RET-33 | Does a cointegration-spread z-score rule with a buffer zone and a time stop profit on liquid Nasdaq pairs and on crypto pairs, net of costs? | PARTIAL: `sd_band_mean_reversion_crypto` REFUTED - but that was a SINGLE-ASSET z-score, not a pair spread. The pair construction is untested. | pair-selection (cointegration) and a spread-series feature; the engine has no pair construct |
| C12 | Volatility-normalized trailing stop overlay | RET-19, RET-73, RET-74, RET-76, RET-87, RET-89, RET-90, RET-91, RET-92 | Does a 1.0-1.5 SD volatility-scaled trailing stop improve the SUPPORTED 12m Nasdaq momentum result, and does it HURT mean reversion, as the papers claim? | NONE as a clean ablation - the standalone momentum specs mention a stop-loss but do not isolate its effect against the same signal without it. | stop/overlay logic in the signal layer; the engine has no stop feature or exit band beyond 'signal returns to flat' |
| C13 | 1.0/1.5 SD band as a two-tier entry | RET-79, RET-80, RET-81, RET-82, RET-83, RET-95, NAS-29 | Does a 1.5 SD entry beat a 1.0 SD entry on expectancy, and does a Parkinson/Garman-Klass range estimator beat close-to-close vol as the denominator? | REFUTED: `v1_sd_band_mean_reversion_1_0_1_5` (gross Sharpe 0.39 - a real gross edge, too small for costs) and `sd_band_mean_reversion_crypto` (gross Sharpe -0.47). Do NOT rebuild this as a reversion entry. The range-estimator half is untested. | rolling-SD band feature (the paper-grounded 20-day window) and a range-based volatility estimator (Parkinson / Garman-Klass from daily OHLC) |
| C14 | Regime-graded exposure ladder | REG-14, REG-50, NAS-80, NAS-81, NAS-82, NAS-86 | Does translating state probabilities into a graded 5-step exposure ladder beat C1's hard two-leg switch? | PARTIAL: `regime_switch_cross_sectional_sector_rotation` SUPPORTED with the posterior AS the size. The 5-step discrete ladder is untested. | per-state exposure mapping; the portfolio layer needs a per-state scale input |
| C15 | Horizon-specific regime models (crypto first) | REG-07, REG-13, REG-40, REG-49, REG-52, REG-62, RET-85 | Do daily and weekly crypto regime classifiers disagree, and does fitting them separately beat one shared classifier? | NONE. | a weekly-bar panel variant; the engine's spec interval is fixed to 1d but the panel loader supports other intervals |
| C16 | Range-based volatility as the regime input | NAS-28, NAS-29, NAS-30, NAS-32 | Does a Parkinson/Garman-Klass range volatility classify regimes better than close-to-close realised vol, and does a log-scale variance model beat a level-scale one? | NONE. | range estimator feature; the engine has `atr_pct`, which is close but is not Parkinson or Garman-Klass |
| C17 | Crash-aware momentum variant | REG-35, REG-27, REG-31 | Does a momentum rule that conditions on the crash dummy (negative trailing return + positive current return + elevated short-vs-long vol) beat plain momentum, and do low-vol and high-vol bulls differ? | NONE. | none beyond C6's features; needs the variant wired as a separate signal |
| C18 | Regime-feature ablation and classifier horse race | REG-20, REG-22, REG-53, REG-56, NAS-92 | Which single feature family (volatility / trend / drawdown / liquidity) and which classifier (HMM / hard-threshold / event-based) actually earns its place? | NONE. This is the spec REG-56 explicitly says the evidence lacks. | a runner that varies features and state counts across the same universe and risk block |
| C19 | Credit-risk leading drawdown signal | REG-21 | Does rising credit risk (HYG/LQD/EMB spread) predict a deeper drawdown ahead of the price? | NONE. | credit spread series feature (the `rates_credit` preset already carries HYG, LQD, EMB, TIP, BND) |
| C20 | Crypto-equity linkage / safe-haven regime feature | REG-46, REG-47, REG-48 | Does adding an equity-linkage feature to the crypto regime classifier improve it, and is crypto's safe-haven status genuinely regime-dependent? | NONE. | cross-asset correlation feature across the crypto and equity panels |
| C21 | Directional-change / threshold event trigger | REG-08, REG-24, REG-25, REG-26, REG-51 | Does a threshold-based (directional-change) regime trigger outperform the fixed-time-bar baseline? | NONE. | directional-change / threshold overlay on daily bars |
| C22 | Duration-aware regime classifier (HSMM-style) | REG-03, REG-17, REG-18, REG-19 | Do tranquil states really persist longer than stress states, and does modelling duration improve the switch? | NONE. | duration modelling in `leapspace/regime.py`; `identify_regimes` is currently a Gaussian HMM filter |
| C23 | VIX-level augmentation of the reversal gate | REG-36, REG-43 | Does adding the VIX level to C8's liquidity+volatility gate improve the reversal result, or is it collinear with realised vol? | NONE. | none beyond C8's features; VIX is already available as a leading series |
| C24 | On-chain crypto features | RET-01, RET-07 | Do on-chain variables (active users, hashrate, wallet activity, transaction volume) add forecastability over price+volume on crypto? | NONE. | on-chain feature wiring into the backtest panel; `leapspace/onchain.py` exists but no spec uses it |
| C25 | Return x volume interaction (crypto reversion) | REG-39 | Does the interaction of lagged return with volume predict the reversal effect, as the panel evidence states? | NONE. | an interaction feature (lagged return x volume) |
| C26 | Bollinger / MA parameter study | RET-94 | Is the conventional 20-period + 2 SD setting optimal, and how much do band width and MA length matter? | REFUTED: `bollinger20_2_breakout_crypto` tested the 20/2 configuration as a breakout and it failed. The PARAMETER study (band width x MA length) is still untested - but do not assume a better pair exists. | none - the engine already has `bollinger_pct` and `ma_crossover`; only the sweep is missing |

### 9.6 The backlog that needs DATA, not code

135 claims are rated `NO` and cannot be built with the data this package holds. They fall into
three buckets:

| Bucket | What it covers | What would unblock it |
|---|---|---|
| **Historical options chain** | net gamma sign (OPT-07, OPT-10, OPT-11, OPT-13, NAS-02, NAS-41, NAS-49), delta/vega/notional-adjusted option flow (OPT-01, OPT-02, OPT-04, NAS-05, NAS-60, NAS-96), strike distance and days-to-expiry / pinning (NAS-43, NAS-46, NAS-47, NAS-48), put-call ratios (NAS-62), the directional-bias claims (OPT-15..OPT-21), the momentum-stage claims (RET-37, RET-41, RET-43), and every NAS failure-mode claim (NAS-65..NAS-71) | A historical options chain archive (open interest + quotes by strike and expiry) so `leapspace/gamma.py` can be run over time instead of once. **This is the single largest gap: it is the difference between 'the papers' options claims are untested' and 'they are tested'.** |
| **Order book / L2 / trade-level** | CVD divergence (RET-60, RET-66, RET-71), spread and depth (NAS-53, NAS-54, NAS-55, NAS-76, NAS-84, NAS-85), trade-flow imbalance (RET-11, RET-12, RET-34, RET-40, RET-42, RET-46, RET-49, REG-06, NAS-03, NAS-25, NAS-50, NAS-69), the acceptance/rejection and open-range claims (RET-56..RET-72, RET-93, NAS-04, NAS-11, NAS-56..NAS-59) | A historical L2 feed or a trade-level archive. The package's `session_drift` is a daily-bar stand-in and is already disclosed as such in the C7 notes. |
| **Intraday bars / session structure** | session and time-of-day effects (RET-51..RET-53, RET-56..RET-67, NAS-04, NAS-07, NAS-22, NAS-24, NAS-26, NAS-39, NAS-44, NAS-56..NAS-59, NAS-89..NAS-91), intraday reversal and continuation (OPT-06, OPT-08, RET-41, REG-41, REG-45) | The skill's `intraday.py` already collapses 60-minute bars into a session-opening-window bar per day, which covers a subset (session drift, opening-window return). Full intraday testing needs a session panel with per-session high/low/POC plus a macro/earnings calendar. |

**A macro-release / earnings / expiry calendar is also absent** (NAS-10, NAS-21, NAS-30, NAS-81, NAS-91,
NAS-97). Event-conditioned claims need it.

### 9.7 Claims ALREADY tested outside the C1-C8 matrix

The C1-C8 matrix is not the only place these papers have been built. There is a set of STANDALONE specs
- the six "LeapSpace 2.0" specs in `leapspace/data/leapspace_2_0_specs.json`, the earlier `v1_*` specs,
and `REGIME_SWITCH_SPECS` in `leapspace/backtest.py` - each with a verdict in `reports/*.md`.

**This changes what "not yet implemented" means.** A claim that was built and REFUTED is not an open
item; a claim that was never built is. The `ALSO TESTED` annotation in the Status column of sections 4-8
records this claim by claim, and it is applied by `tools/annotate_claim_test_status.py`.

| Standalone spec | Universe | Verdict | Claims it covers |
|---|---|---|---|
| `nasdaq_12m_timeseries_momentum` | us_equity_style | **SUPPORTED** | RET-13, RET-14, RET-16, RET-17, RET-18, RET-19, RET-20, RET-21 |
| `regime_switch_cross_sectional_sector_rotation` | us_equity_style | **SUPPORTED** | IND-09, REG-01, REG-02, REG-09, REG-10, REG-14, REG-15, REG-16, REG-50, REG-64, REG-65 |
| `v1_crypto_momentum_20d_ma` | crypto | **FRAGILE** | RET-14, RET-17, RET-21, RET-22, RET-23 |
| `v1_nasdaq_12m_tsm_vol_scaled` | us_equity_style | **REFUTED** | RET-14, RET-16, RET-17 |
| `v1_sd_band_mean_reversion_1_0_1_5` | crypto | **REFUTED** | RET-79, RET-80, RET-81, RET-82 |
| `regime_switch_momentum_reversal_us_equity` | us_equity | **REFUTED** | REG-01, REG-11, REG-12, REG-16 |
| `regime_switch_momentum_reversal_nasdaq_scalp_proxy` | us_equity_style | **REFUTED** | REG-01, NAS-16, NAS-17, NAS-19, NAS-20 |
| `crypto_ma20_trend_momentum` | crypto | **REFUTED** | RET-13, RET-14, RET-18, RET-21, RET-22, RET-23 |
| `sd_band_mean_reversion_crypto` | crypto | **REFUTED** | RET-26, RET-27, RET-29, RET-73, RET-75, RET-78, RET-79, RET-82 |
| `crypto_xs_momentum_volume_confirmed` | crypto | **REFUTED** | RET-39, RET-40 (declared but UNENFORCED), RET-42, RET-45 |
| `tradingview_price_volume_rsi_regime_filtered` | crypto+equity mix | **REFUTED** | IND-01, IND-02, IND-04, IND-05, IND-06, IND-09, IND-11 |
| `crypto_rsi_oversold_fade` | crypto | **REFUTED** | IND-02, IND-05, IND-08 |
| `bollinger20_2_breakout_crypto` | crypto | **REFUTED** | RET-82, RET-84, RET-94 |

**50 of the 293 claims carry an `ALSO TESTED` annotation.** The rest have never
been built in any form.

**Three findings a spec writer must not skip:**

1. **The single best-supported long/short result in the whole evidence set is
   `nasdaq_12m_timeseries_momentum` (SUPPORTED).** Its REFUTED twin `v1_nasdaq_12m_tsm_vol_scaled` differs
   only in the volatility gate. That single difference - volatility gate ON vs OFF - is the cleanest
   natural experiment in the package, and it is exactly REG-03's claim ("cut or disable momentum in
   high-volatility states") coming out the other way. **Replicate that pair before anything else.**
2. **Crypto 20-day momentum has been tested three times and failed every time** (REFUTED, REFUTED,
   FRAGILE), with a gross Sharpe of 0.74 that costs consumed. RET-14's crypto leg should not be rebuilt
   as-is.
3. **The 1.0/1.5 SD band mean-reversion entry has been tested twice and failed twice**, and it fails
   GROSS of costs (Sharpe -0.47 in `sd_band_mean_reversion_crypto`), so it is not a cost problem - the
   signal itself has no expectancy. C13's SD-band work should be aimed at the *risk overlay* and the
   *range estimator*, not at a third reversion entry.

---

## 10. Totals

| Metric | Count |
|---|---|
| **TOTAL distinct testable claims** | **293** |
| - GROUP OPT (options flow, IV, gamma) | 21 |
| - GROUP RET (retail trader compilation) | 95 |
| - GROUP IND (free trading indicators) | 12 |
| - GROUP REG (financial market regime identification) | 65 |
| - GROUP NAS (NASDAQ market regime identification) | 100 |
| **ALREADY FULLY IMPLEMENTED as C1-C8** | **30** |
| PARTIALLY implemented (a C-spec covers part of the claim) | 46 |
| **NOT IMPLEMENTED in C1-C8** | **215** |
| EXCLUDED (the paper states there is no evidence - e.g. charm/vanna) | 0 |
| meta / not-a-claim row | 2 |
| | |
| of which ALSO already tested by a standalone spec | 50 |
| **NEVER BUILT IN ANY FORM** | **243** |
| | |
| **DIRECTIONAL (tradable) claims** | **80** |
| GATE claims | 53 |
| SIZING claims | 15 |
| TIMING claims | 24 |
| RISK claims | 26 |
| MARKET-STATE / classifier claims | 81 |
| COMPARATIVE (ablation) claims | 27 |
| NEGATIVE (fragility / limitation) claims | 42 |
| | |
| Testable on daily bars today (YES) | 137 |
| Testable on daily bars with a NEW small feature (EXT) | 9 |
| Testable only via a proxy (PROXY) | 8 |
| NOT testable here - data absent (NO) | 135 |
| n/a (meta rows) | 4 |

**Headline numbers.** 293 distinct testable claims. **215 are not implemented in the C1-C8**
matrix**; of those, 50 claims have in fact been built as standalone specs and already carry a
verdict, so the **genuinely open backlog is 192 claims**, of which **59 are
testable on this package's daily panels** with the engine's existing feature registry or with one small new
feature. Section 9.5 proposes 18 new concepts (C9-C26) to cover the highest-value ones; section 9.6 lists
the claims that need a data acquisition (historical options chain, order book, intraday session structure,
macro calendar) rather than more code.

### Appendix A - excluded from the claim count

The following content was read and deliberately **not** counted as claims, because each is an arithmetic
illustration or a non-answer rather than a falsifiable claim about markets:

- The '$100 average, $4 standard deviation -> $96 / $94 / $104 / $106' Nasdaq worked example (RET pp.48-51).
- The '$60,000 / $2,000 -> $58,000 / $57,000' BTC worked example (RET pp.48-49).
- The '29,943 - 1x300 = 29,643' arithmetic exercises (RET pp.70-71).
- The 'is the Nasdaq 29,000, 30,000 or 33,000?' exchange and the paper's own 'I can't confirm the current
  Nasdaq Composite level' non-answer (RET pp.63-65).
- The reference lists themselves (each paper cites 30-160 academic sources; the reference titles are
  bibliography, not claims made by the paper).

### Appendix B - how to read this document

- **The claim column is the paper's own wording**, quoted, so a reader can check it against the PDF
  without re-deriving it. Where the paper used an em-dash or an ellipsis, it is preserved.
- **The refutation column is the acceptance test.** A spec for a claim is SUPPORTED only if the refutation
  condition does NOT hold. If it holds, the claim is refuted and that verdict must be reported as such.
- **The Daily? column is the build filter.** `NO` claims should not be queued for spec-writing until the
  underlying data exists; writing a spec for them would produce a proxy dressed up as a paper test, which
  is exactly the failure mode the existing C7 notes already warn about.
- **The Status column distinguishes FULL implementation from PARTIAL**, and the `ALSO TESTED` suffix
  distinguishes 'never built' from 'built and refuted'. Read them together: a claim marked
  `NOT - ALSO TESTED: ... -> REFUTED` is a CLOSED item, not an open one.

---

*Inventory generated from the six LeapSpace PDFs in `C:\Users\HP\Downloads\` via the Hermes native PDF
text extractor. Sections 9 and 10 are generated by `tools/build_claim_inventory.py` directly from the
tables in sections 4-8, so they cannot drift from the inventory. The `ALSO TESTED` annotations are applied
by `tools/annotate_claim_test_status.py`.*
