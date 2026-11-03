# Backtest Report — nasdaq_12m_timeseries_momentum

**Hypothesis:** Section "Momentum and Mean Reversion Trading Strategies", subsection "A+ momentum model setup": "Signal: Use a 12-month time-series momentum on Nasdaq and a shorter, crypto-adapted trend window such as 20-day or 2-4 week lookback for crypto. Time-series momentum is conventionally built on the past 12-month return." Direction rule: "Go long when price is above its trend proxy; go short or flat when below, if your venue supports it." Risk filter: "Trade only when realized volatility is not extreme, and scale position size by inverse volatility." Stop rule: "Add a stop-loss overlay." Regime filter: "Avoid broad, always-on exposure; switch off or reduce size in regimes where momentum weakens." The paper's claim is that a risk-managed 12-month time-series momentum rule on liquid Nasdaq names is the higher-frequency-liquid, evidence-backed retail momentum setup - "the most defensible setup from this evidence is risk-managed trend following for momentum" - with the caveat that momentum rules "are sensitive to transaction costs and turnover".

## VERDICT: **SUPPORTED**

Pooled OOS Sharpe 0.90 clears the 0.5 bar and every robustness check that WAS RUN passed. NOTE: Monte Carlo, cross-market replication and sweep were NOT run, so this is a preliminary read, not a full validation.

> **PARTIAL VALIDATION.** Monte Carlo, cross-market replication and sweep were NOT run. Every statement below is limited to the checks that were actually executed. This is a preliminary read, not a full validation.

## In-Sample Metrics

| Metric | Value |
|--------|-------|
| Trades | 71 |
| Bars | 5487 |
| Sharpe | 0.63 |
| Sortino | 0.87 |
| CAGR | 8.29% |
| Max Drawdown | 30.96% |
| Calmar | 0.27 |
| Profit Factor (net of costs) | 7.24 |
| Win Rate (net of costs) | 73.2% |
| t-stat | 2.94 |
| Time in Market | 85% |
| Costs Paid | $1,941 |

## Walk-Forward (Out-of-Sample)

- Pooled OOS Sharpe: **0.90**
- Pooled OOS CAGR: 11.81%
- Profitable folds: 4/5
- Purge: 252 bars · Embargo: 252 bars (label horizon 252)
- Disjointness: **PASS** (4 checks: a_oos_blocks_disjoint, b_no_oos_bar_in_own_training, c_embargo_band_not_in_next_training, d_no_training_bar_inside_any_test_block)
- OOS Sharpe retention vs final in-sample: 163%
- PBO proxy (overfit signature): 30%

| Fold | Test Window | IS Sharpe | OOS Sharpe | OOS Trades |
|------|-------------|-----------|------------|------------|
| 0 | 2007-06-28 → 2009-05-13 | -0.01 | -0.31 | 6 |
| 1 | 2011-11-03 → 2013-09-23 | 0.36 | 1.31 | 13 |
| 2 | 2016-03-17 → 2018-01-31 | 0.60 | 2.18 | 7 |
| 3 | 2020-07-27 → 2022-06-09 | 0.64 | 0.97 | 7 |
| 4 | 2024-12-04 → 2026-10-23 | 0.55 | 0.71 | 10 |

## By Year

| Year | Return | Sharpe |
|------|--------|--------|
| 2005 | 0.0% | n/a |
| 2006 | 11.5% | 0.95 |
| 2007 | 6.3% | 0.46 |
| 2008 | -4.8% | -0.62 |
| 2009 | 10.3% | 1.61 |
| 2010 | 20.6% | 1.06 |
| 2011 | -8.4% | -0.26 |
| 2012 | 11.6% | 1.03 |
| 2013 | 34.4% | 2.59 |
| 2014 | 11.9% | 0.99 |
| 2015 | 0.4% | 0.10 |
| 2016 | 8.2% | 0.90 |
| 2017 | 21.9% | 2.59 |
| 2018 | -6.5% | -0.30 |
| 2019 | 12.1% | 1.12 |
| 2020 | 5.5% | 0.33 |
| 2021 | 24.3% | 1.56 |
| 2022 | -13.5% | -1.02 |
| 2023 | 4.8% | 0.59 |
| 2024 | 17.3% | 1.24 |
| 2025 | 12.5% | 0.79 |
| 2026 | 12.6% | 1.14 |

## Parameter Sensitivity

- Stability: **100%** — broad plateau - robust

| Perturbation | Sharpe |
|--------------|--------|
| lookback=189 | 0.52 |
| lookback=315 | 0.50 |
| skip=1 | 0.61 |
| skip=1 | 0.61 |

## Gross vs Net (cost decomposition)

| | Sharpe | CAGR |
|----|--------|------|
| Gross of costs | 0.63 | 8.32% |
| Net of costs | 0.63 | 8.29% |

Costs paid: $1,941 on $7,762,766 of turnover.

> the edge survives costs with little erosion (0% of the gross Sharpe lost to costs) - costs are not the constraint.

## Cost Stress

| Cost Multiple | Sharpe | CAGR |
|---------------|--------|------|
| 1.0x | 0.63 | 8.3% |
| 1.5x | 0.63 | 8.3% |
| 2.0x | 0.63 | 8.3% |
| 3.0x | 0.63 | 8.2% |

## Causality Audit

**PASS** — no look-ahead detected.

---

## Due-Diligence Coverage

- Questions answered: **83/111** (75%)
- Answered by the engine (verified): 82
- Answered by the user: 1
- Still UNKNOWN: **28**

## Multi-Asset Due-Diligence Disclosure

Source markers: **[user]** supplied by the user · **[engine]** verified property of the engine · **[UNKNOWN]** not answered by either — treat as a gap.

### A. Strategy definition and multi-asset scope

- **A.asset_classes** — Which asset classes are in scope, and which are explicitly excluded? Why?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine can only run the universes it has presets for: US equity sector/style/broad, futures, FX major/emerging, commodities, crypto, rates/credit, international equity, real assets and multi-asset. Which of those are in scope for THIS strategy, and which are excluded and why, is the user's call.
- **A.rationale** — What is the economic rationale for combining these classes - diversification, carry, trend, relative value, or risk premia?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine has no verified view of this: it is a statement about the user's own reasoning, hypothesis or process, which no amount of market data can supply. The engine's role is to test the stated rule, not to vouch for the story behind it. The engine does apply its OWN fixed objective refutation criteria to every run, independently of the user's pre-registration: REFUTED if pooled OOS Sharpe < 0.5, or if the edge does not survive 2x cost stress, or if the causality audit fails (unconditional - the numbers are void); INCONCLUSIVE if fewer than 30 trades; and FRAGILE (SUPPORTED downgraded) if fewer than 50% of calendar years are profitable, fewer than 60% of walk-forward folds are profitable, parameter-sweep stability < 0.6, Monte Carlo P(profitable) < 0.85, OOS Sharpe retention < 40% of in-sample, or a negative deflated Sharpe.
- **A.currency** — What is the base currency, reporting currency, and hedging policy?
  - *[engine]* Base and reporting currency are NOT configured. Returns are computed in each instrument's own quote currency, with NO FX conversion and NO hedging applied. A multi-currency book is therefore not comparable to a single-currency benchmark without an external FX step.
- **A.universe_rules** — What are the exact universe rules per asset class, and are they point-in-time?
  - *[engine]* NO point-in-time fundamentals, index membership, credit ratings, sector classifications or classification history are available in this engine - there is no such data source at all. Universe membership is a STATIC list: either a named preset (UNIVERSE_PRESETS) or an explicit symbols list, and a symbol's eligibility never changes over the sample. Two further filters apply and BOTH are not point-in-time: the optional liquidity screen (screen.min_adv_usd) keeps a symbol only if its MEDIAN dollar volume over the ENTIRE panel is at or above the threshold, so the screen is computed with FUTURE liquidity information and can admit or exclude a symbol on the strength of data that post-dates the bars being traded; and the date axis drops any date on which fewer than half the universe traded. max_names caps the number of simultaneously active names. Sector exposure exists only as separate sector ETFs in the universe, never as a classification applied to holdings.
- **A.rebalance_horizon** — What are the rebalancing frequency, holding period, and signal horizon per asset class?
  - *[engine]* One rebalance per period, on the period's first available bar. 'daily' = every session; 'weekly', 'monthly', 'quarterly' and 'yearly' = the first bar of each period. No orders are sent between rebalances.
- **A.allocation** — How is capital allocated across asset classes - fixed weights, risk parity, vol targeting, optimisation, or a discretionary overlay?
  - *[engine]* The engine allocates WITHIN one universe - it sizes positions and rescales to the target gross exposure. The sizing models available are equal weight, inverse-volatility (vol_target) and a hard per-name cap; there is NO stop-loss-based fixed-fractional sizing model, so 'risk per trade' sizing is not directly expressible. It does NOT allocate across asset classes: a multi-class book requires either a single combined universe or an explicit external allocation rule.
- **A.constraints** — What are the portfolio constraints: max weight per asset, class, sector, country, factor, liquidity bucket, and gross/net leverage?
  - *[engine]* Enforced: per-name max_weight (hard cap, applied LAST - after the gross normalisation, the volatility target and the net-target shift, none of which may silently undo it), gross_leverage, and net_target. net_target is applied as a SHIFT (the same constant added to every weight), not a uniform scale, so it can reach a target of the opposite sign without inverting the strategy. NOT enforced: per-class, per-sector, per-country, per-factor or per-liquidity-bucket limits.
- **A.benchmark** — What is the benchmark, and is it multi-asset and investable?
  - *[engine]* Optional - the user must name one; the engine can run any universe as a buy-and-hold comparator, but correlation to a benchmark is NOT computed.
- **A.direction** — Is the strategy long-only, long/short, or market-neutral, and what sets the direction of each sleeve?
  - *[engine]* Direction is set by the spec, not inferred. long_only suppresses the short leg and net_target forces a specified net exposure. A time-series signal is long/short by the SIGN of the feature against its threshold; a cross-sectional signal is ranked across the universe each bar, going long above long_rank and short below short_rank.
- **A.null_hypothesis** — What is the null hypothesis - e.g. zero net-of-cost expectancy and no marginal diversification benefit?
  - *[engine]* The engine tests the null of ZERO NET-OF-COST EXPECTANCY: a strategy whose pooled out-of-sample Sharpe is below 0.5, or whose edge disappears under 2x cost stress, is REFUTED. The 'no marginal diversification benefit' half of that null is NOT tested directly, because that requires a leave-one-out comparison this engine does not perform.
- **A.rejection_criteria** — What would make you REJECT the strategy before running the test?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine has no verified view of this: it is a statement about the user's own reasoning, hypothesis or process, which no amount of market data can supply. The engine's role is to test the stated rule, not to vouch for the story behind it. The engine does apply its OWN fixed objective refutation criteria to every run, independently of the user's pre-registration: REFUTED if pooled OOS Sharpe < 0.5, or if the edge does not survive 2x cost stress, or if the causality audit fails (unconditional - the numbers are void); INCONCLUSIVE if fewer than 30 trades; and FRAGILE (SUPPORTED downgraded) if fewer than 50% of calendar years are profitable, fewer than 60% of walk-forward folds are profitable, parameter-sweep stability < 0.6, Monte Carlo P(profitable) < 0.85, OOS Sharpe retention < 40% of in-sample, or a negative deflated Sharpe.
- **A.discretionary_overrides** — Are there discretionary overrides? If so, how are they modeled and logged?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine has NO discretionary-override mechanism: every position comes from the spec's signal and portfolio rules. Any manual override would be invisible to the backtest, so it would have to be reported outside it.

### B. Data integrity and cross-asset alignment

- **B.data_sources** — What are the exact data sources, vendor, extraction date, and version per asset class?
  - *[engine]* Single source for EVERY asset class: the Yahoo Finance chart API v8 endpoint query1.finance.yahoo.com/v8/finance/chart/{symbol} - free, no API key, no account, no rate-limit contract. Yahoo is an AGGREGATOR, so the ultimate venue is Yahoo's chosen feed per listing and is not exposed; the returned volume is exchange-consolidated, not venue-level. VERSION: API v8; the engine identifies itself as btengine 1.0.0. EXTRACTION DATE: each symbol/interval is cached as JSON under .cache/{SYMBOL}__{interval}.json and the payload records a 'fetched' epoch timestamp; the cache is considered stale after 3 days (daily) or 1 day (intraday) and is re-fetched on the next run. There is NO dataset version, NO vintage, NO revision history and NO point-in-time snapshot - re-running after a corporate action returns a different history for the same symbol.
- **B.timestamps** — Are all asset classes timestamped consistently?
  - *[engine]* Bars are epoch UTC. Yahoo anchors intraday bars to EXCHANGE-LOCAL time; daily bars are exchange session dates.
- **B.timezones** — How are time zones and daylight-saving changes handled across global markets?
  - *[engine]* Session boundaries are detected per-day by grouping on the UTC calendar date of each bar, which is DST-robust and needs no tz database.
- **B.async_closes** — How are asynchronous market closes handled (US equities, FX 24/5, crypto 24/7, futures sessions)?
  - *[engine]* NOT modelled as a synchronisation constraint. The panel's date axis is the UNION of every symbol's trading dates; a date is kept only if at least half the universe (and at least one symbol) has a bar on it, and then each symbol's series is FORWARD-FILLED onto that axis. A market that did not trade on a retained date therefore carries its LAST close forward at a STALE price, and it IS still tradable that day -- the stale price is carried into the signal, the target weights and the fill.
- **B.holidays** — How are holidays, half-days, and closures treated per asset class?
  - *[engine]* Handled implicitly: a closed market produces no bar for that symbol, that date is absent for that symbol, and the symbol is FORWARD-FILLED from its last traded bar - so it can still be traded at a stale price (see B.async_closes). The date itself survives on the axis if at least half the universe traded. HALF-DAYS are treated as a normal short session: the daily bar is a normal daily bar, and in session mode the 09:30-10:00 ET opening window is unaffected by a 13:00 close, so the session extraction still returns the same opening bar. There is NO holiday calendar, NO early-close calendar and NO per-class session model - the engine does not know which market was closed on which date.
- **B.bad_data** — How are missing bars, stale prices, bad ticks, duplicate rows, zero-volume periods, and outliers detected and cleaned?
  - *[engine]* Stage 1 audits every series and reports: fewer than 120 bars, calendar gaps over 12 days (possible halt or delisting), non-positive prices, more than 30% zero-volume bars, 8 or more identical consecutive closes (a stale feed), and single-bar moves above 55%. Findings are WARNINGS, not automatic corrections - the data is reported, not silently patched, because a silent fix hides the problem it was meant to reveal.
- **B.survivorship** — Is the universe survivorship-free per asset class, including delisted equities, defaulted bonds, expired futures, and delisted crypto pairs?
  - *[engine]* NOT survivorship-free for individual equities - Yahoo serves only current listings, so any stock universe silently drops delistings (prefer ETFs). ETFs, FX, index series and crypto majors are survivorship-free WITH RESPECT TO THE INSTRUMENT LIST, but: the crypto preset is a FIXED list of 10 surviving majors, so failed or delisted crypto pairs are absent by construction; futures are represented by Yahoo's continuous series, so individual contract expiries are not modelled and the roll is undocumented and not point-in-time; there are NO individual bonds in any universe (rates/credit are ETF proxies and yield indices), so defaulted bonds are OUT OF SCOPE rather than survivorship-biased - a bond default reaches the backtest only through its ETF's price history; and OPTIONS ARE UNSUPPORTED entirely, so expired option contracts are out of scope. Membership of every universe is a static list, so there is no point-in-time index membership or delisting-driven reconstitution.
- **B.pit_classification** — Are index membership, credit ratings, sector classifications, and liquidity filters point-in-time?
  - *[engine]* NO point-in-time fundamentals, index membership, credit ratings, sector classifications or classification history are available in this engine - there is no such data source at all. Universe membership is a STATIC list: either a named preset (UNIVERSE_PRESETS) or an explicit symbols list, and a symbol's eligibility never changes over the sample. Two further filters apply and BOTH are not point-in-time: the optional liquidity screen (screen.min_adv_usd) keeps a symbol only if its MEDIAN dollar volume over the ENTIRE panel is at or above the threshold, so the screen is computed with FUTURE liquidity information and can admit or exclude a symbol on the strength of data that post-dates the bars being traded; and the date axis drops any date on which fewer than half the universe traded. max_names caps the number of simultaneously active names. Sector exposure exists only as separate sector ETFs in the universe, never as a classification applied to holdings.
- **B.corporate_actions** — Are corporate actions handled correctly per asset class - splits, dividends, mergers, spin-offs, coupons, defaults, calls?
  - *[engine]* Daily bars ARE split- AND dividend-adjusted: the engine back-adjusts open/high/low/close by the multiplicative per-bar factor adjclose/close, so returns include dividends and the series is continuous across splits (volume is NOT scaled). INTRADAY (60m) bars are NOT adjusted -- no adjclose is published at that interval -- so an ex-dividend date inside a 60m sample leaves a small uncompensated drop, and mergers, spin-offs, delisting returns and splits inside a 60m session are not modelled.
- **B.dividend_adjustment** — Are dividends reflected in the returns, and how is the adjustment applied?
  - *[engine]* Daily bars are back-adjusted by a MULTIPLICATIVE per-bar factor adjclose/close read from Yahoo's chart API, applied to open/high/low/close (volume is NOT scaled), so daily returns include dividends and the series is continuous across splits. The factor is sanity-bounded (0.05 < factor < 20) and a malformed factor is ignored rather than allowed to corrupt the series. The local cache carries a schema marker (CACHE_SCHEMA = 2): a daily cache written under the older schema holds UNADJUSTED prices and is REFETCHED rather than silently reused, so stale unadjusted data cannot leak into a backtest. INTRADAY 60m bars have NO adjclose published for that interval, so they are NOT dividend-adjusted and an ex-dividend date inside a 60m sample leaves a small uncompensated drop.
- **B.fx_rates** — What FX conversion rates are used, from what source, at what timestamp?
  - *[engine]* NOT modelled. All instruments are priced in their quote currency and returns are computed in that currency. A multi-currency book is NOT converted to a base currency.
- **B.curves** — How are risk-free curves, swap curves, credit spreads, inflation curves, and funding rates sourced and aligned?
  - *[engine]* NO curves of any kind are sourced, fitted or aligned: no risk-free curve, no swap curve, no credit-spread curve, no inflation curve. Consequently there is NO discounting, NO carry accrual and NO financing rate on cash. Critically, the risk-free rate used in Sharpe and Sortino is hard-coded to 0.0, so every reported Sharpe is a ZERO-HURDLE Sharpe, not an excess-return Sharpe - at prevailing risk-free rates this flatters the result. The only funding-like charge in the engine is the crypto borrow rate, used as a proxy for perp funding, and it is charged only on short notional.
- **B.regimes** — Does the sample cover multiple regimes - bull, bear, sideways, high/low vol, crisis, illiquidity, inflation and rate shocks?
  - *[engine]* The engine does NOT classify regimes - there is no regime classifier and no way to request one. It reports (a) a per-calendar-year return, Sharpe and bar-count table and (b) a high/low realised-volatility split of the portfolio return series (trailing 20-bar stdev, split at the median). That is the entirety of the regime facility: there is NO tagging of bull/bear, sideways, crisis, illiquidity, inflation-shock or rate-shock windows. Sample length is set by the user: daily presets typically yield 10-30 years of history (sector ETFs are shorter - XLC starts 2018, XLRE 2015), while the 60m intraday path is provider-capped at roughly 2 years, so an intraday sample can contain at most one full cycle and no meaningful regime coverage. Whether the window contains the regimes the question asks about is NOT verified by the engine and must be asserted by the user.
- **B.observations** — How many independent observations and trades exist per asset class and for the combined portfolio?
  - *[engine]* Reported per run: n_bars (panel bars with a non-null return) and n_trades (closed round-trip position lifecycles). The engine does NOT split those counts by asset class or instrument - a run simulates ONE universe, so there is no per-sleeve observation count to report.
- **B.granularity** — Is the data granularity sufficient for the execution assumptions per asset class?
  - *[engine]* Bar resolution must match the execution assumption. Daily bars cannot realistically model intraday futures stops, option fills, or an opening-window entry and exit - a daily backtest of an intraday rule is not a conservative approximation, it is a different strategy. The session path (60m bars collapsed to the 09:30-10:00 ET opening window) is the supported way to test intraday rules, and the provider caps it at roughly 2 years of history.

### C. Asset-class-specific instrument modeling

- **C.equities** — Equities: splits, dividends, mergers, spin-offs, delistings, borrow, auctions, halts, tick sizes, market-on-close mechanics.
  - *[engine]* Daily bars ARE split- and dividend-adjusted (the engine back-adjusts OHLC by the per-bar adjclose/close factor), so daily returns include dividends. INTRADAY (60m) bars are NOT adjusted, so an ex-dividend date inside a 60m sample leaves a small uncompensated drop. Mergers, spin-offs, delisting returns, and splits inside a 60m session are not modelled. Withholding taxes on dividends are NOT modelled. Point-in-time index membership and sector classification are NOT available. Borrow: annualised borrow cost charged on short notional; locate fees and availability not modelled. Auctions, halts, tick sizes and market-on-close mechanics are not modelled.
- **C.fixed_income** — Fixed income and credit: clean/dirty price, accrued interest, coupon cash flows, curve construction, duration, convexity, spread, default, recovery, calls.
  - *[engine]* BOND-LEVEL ANALYTICS ARE NOT SUPPORTED: no clean/dirty price, no accrued interest, no coupon cash flow schedule, no duration or convexity, no credit-spread decomposition, no default or recovery modelling, no call/put feature handling. But rates and credit ARE testable at the ETF/index level: the rates_credit preset (TLT, IEF, SHY, LQD, HYG, EMB, TIP, BND, plus ^TNX/^TYX/^FVX/^IRX) provides total-return series, so duration exposure is embedded in the ETF price rather than modelled, and coupon income is captured only in the ETF's own adjusted price. There is no bond-level data: no liquidity metrics, no bid-ask or spread data, no issue-level identifiers, no point-in-time rating changes and no point-in-time index inclusion. Defaults are visible only as a price move inside an ETF's history. Inflation-linked exposure (TIP) is a price series with no CPI linkage modelled.
- **C.fx** — FX: spot, forward points, carry, rollover, swap rates, weekend gaps, settlement, NDFs, conversion costs, hedging.
  - *[engine]* Spot only. Forward points, carry, rollover, swap rates, weekend gaps, settlement conventions and NDFs are not modelled. Bid-ask and conversion costs are approximated by the class spread. Hedging is not modelled - FX exposure is left unhedged in quote currency.
- **C.commodities** — Commodities: which contract is traded, continuous-series construction, roll dates and costs, contango/backwardation, storage, seasonality, multipliers, margin.
  - *[engine]* Yahoo's CONTINUOUS futures series is used; the specific contract traded is not recorded, the ROLL METHODOLOGY IS UNDOCUMENTED AND NOT POINT-IN-TIME, and ROLL COST IS NOT MODELLED - there is no contango/backwardation pricing, no seasonal adjustment and no delivery or expiry handling. NO PHYSICAL CONSTRAINTS are modelled at all: NO STORAGE, NO physical inventory or deliverability, NO local basis, and NO physical/liquidity constraints - the series is treated as a continuously tradable financial instrument. No contract multiplier, tick size or exchange margin model exists. Note that infer_asset_class recognises only a fixed list of futures symbols, so commodity futures outside it (e.g. PL=F, PA=F, ZC=F) fall back to the ETF cost schedule.
- **C.crypto** — Crypto: 24/7 trading, exchange fragmentation, outages, stablecoin risk, fees, funding, borrow, custody, delisted pairs, venue liquidity and slippage.
  - *[engine]* A SINGLE aggregated Yahoo series per symbol - no exchange fragmentation, no per-venue book, no venue outage handling, no custody or wallet risk, and NO stablecoin de-peg risk (a USDT-quoted pair would be treated as a normal spot pair with no basis or collateral model). FEES ARE CHARGED on the standard crypto schedule: commission 10bps + half-spread 5bps + slippage 5bps, with a borrow rate of 30bps annualised. FUNDING IS NOT MODELLED: perp funding is APPROXIMATED BY the crypto class borrow rate, and because borrow is charged only on SHORT notional, a LONG crypto position pays NO funding at all - the long leg's funding cost, which on a perpetual is paid for holding the position, is entirely absent. The engine trades 10 MAJORS ONLY (BTC, ETH, LTC, BCH, XRP, SOL, ADA, DOGE, AVAX, LINK): delisted pairs, failed tokens and exchange failures are ABSENT BY CONSTRUCTION. Crypto trades 7 DAYS A WEEK, so in a mixed book weekend dates enter the axis only where the coverage filter allows, and against STALE equity marks (see B.async_closes). Slippage is a constant 5bps with no venue-level liquidity or depth model.
- **C.derivatives** — Listed derivatives: pricing models, IV surfaces, expiry, assignment, exercise, settlement, margin, Greeks, basis, term structure, roll costs, option spreads.
  - *[engine]* Split by instrument. OPTIONS: not supported at all - no pricing model, no Greeks, no implied-vol surface, no expiry/exercise/assignment, no settlement, no margin, no option bid-ask or liquidity data; an option hypothesis cannot be tested in this engine. FUTURES: supported, but only as Yahoo's continuous series - the specific contract traded is not recorded, the roll methodology is undocumented and not point-in-time, roll cost is NOT modelled, and there is no basis, term-structure, delivery-rule, contract-multiplier, tick-size or margin modelling; costs are charged as if the series were a continuous ETF-like instrument. Daily futures bars are dividend-adjusted, but the rolls are not costed.
- **C.alts** — Alternatives and real assets: valuation lags, appraisal smoothing, liquidity gates, transaction costs, point-in-time valuation, leverage and redemption constraints.
  - *[engine]* ALTERNATIVES/REAL-ASSET VALUATION MECHANICS ARE NOT SUPPORTED: no appraisal smoothing, no valuation lag, no stale-price or staleness adjustment, no liquidity gates, no redemption/suspension modelling, no NAV-vs-market-price distinction. What IS tradeable is the listed proxy sleeve (VNQ, XLRE, REM, RWO, DBC, DBA, TIP), traded as an ordinary exchange-traded instrument with the standard ETF cost schedule and a daily close - so any appraisal lag embedded in the underlying is invisible, and the instrument's own redemption/liquidity risk is not modelled. Transaction costs are the standard ETF commission/half-spread/slippage plus borrow on shorts. LEVERAGE AND FINANCING ARE NOT MODELLED at all: no margin, no financing rate, no collateral haircut.

### D. Look-ahead bias and information leakage

- **D.signal_timing** — Is every signal computed using only information available before execution in that asset's market?
  - *[engine]* features[i] use only data at indices <= i; a signal decided at bar i fills at bar i+1. The engine's own causality audit recomputes every feature on a truncated panel and fails if any first-half value changes - that is how centred windows and full-sample normalisation get caught.
- **D.bar_close_exec** — If a signal uses a bar close, is execution at that close, the next open, or later?
  - *[engine]* Bar-resolution and causal: the signal is computed at bar t and the order is filled at bar t+1's open by default (fill_at: 'open'), or at bar t+1's close (fill_at: 'close', still causal because the decision uses bar t). Orders are sent ONLY on rebalance-marked bars. Precisely: an ORDER IS GENERATED only on a rebalance-marked bar and fills on the NEXT bar, whether or not that next bar is itself marked; between marked bars no order exists and the previous target is simply held. Gating the FILL on the mask instead would leave every order pending until the next rebalance bar, so a monthly strategy would execute each rebalance a full month late. In session mode (execution.mode: 'session') the panel is DAILY - one 09:30-10:00 ET opening-window bar per session - and with flat_at_close: true the position opens at that bar's open and CLOSES AT THAT SAME BAR'S CLOSE, so there is NO OVERNIGHT EXPOSURE and the trade is a single-bar round trip.
- **D.publication_lag** — Are fundamentals, earnings, macro releases, credit ratings, and news lagged by actual publication time?
  - *[engine]* The question does not arise, because every built-in feature is derived from the instrument's own PRICE and VOLUME series (return, momentum, sma_gap, volatility, vol_ratio, zscore, rsi, max_drawdown, skew, volume_ratio, bollinger_pct, atr_pct, ma_crossover, dist_to_high, plus the session-mode session_drift, session_gap, session_return). NO fundamentals, earnings, macro releases, ratings or news are ingested, so NO publication-time lag can leak - but equally, NO fundamental information is tested.
- **D.cross_asset_alignment** — Are cross-asset signals aligned so no asset uses another asset's future close?
  - *[engine]* Features are computed PER SYMBOL from a shared date axis and each feature at bar i uses only data at indices <= i, so NO ASSET READS ANOTHER ASSET'S FUTURE CLOSE - the causality audit (recompute every feature on a truncated panel and require the first half to match) verifies this for all 14 built-in features. Two caveats the audit does NOT cover: (a) the axis is the UNION of all symbols' dates filtered to >=50% coverage, NOT an intersection; and (b) a symbol that did not trade on a retained date carries its PREVIOUS CLOSE FORWARD, so on that date a STALE price is presented to the cross-sectional rank as though it were a live observation - a stale-versus-live comparison, not a future-leak. No ORDER is filled on such a bar (the simulation drops it and counts it under stale_skips), but the stale value still participates in the cross-sectional RANK, so a halted name can occupy a top or bottom rank slot on a date it did not trade. The audit tests FEATURES ONLY: it says nothing about universe construction, and the liquidity screen uses full-sample ADV (see A.universe_rules).
- **D.fx_timing** — Are FX conversions using the rate available at the trade timestamp?
  - *[engine]* NOT modelled. All instruments are priced in their quote currency and returns are computed in that currency. A multi-currency book is NOT converted to a base currency.
- **D.holdout** — Was the out-of-sample/holdout period truly untouched across all asset classes?
  - *[engine]* Purged + embargoed expanding-window walk-forward. The layout is [train_0][purge_0][test_0][embargo_0][train_1][purge_1][test_1] ... : each fold's in-sample set is its own train segment PLUS every earlier train segment, with the `purge` bars immediately before each test block excluded from EVERY training set (a training bar whose label horizon reaches into the test block would leak the test period) and the `embargo` bars immediately after each test block excluded from every later training set. Purge and embargo default to the maximum feature lookback in the spec and are overridable; the sizes actually used are printed. A DISJOINTNESS ASSERTION runs on every walk-forward and reports four checks: (a) no date appears in two out-of-sample blocks, (b) no out-of-sample bar was in its own fold's training set, (c) no training bar of fold f+1 falls inside fold f's test block or embargo band, (d) no training bar of any fold falls inside any test block. A violation is SURFACED, not swallowed. Features are computed on the FULL causal history and the panel is sliced afterwards, so a long lookback does not lose its warm-up at a fold boundary. If the sample cannot support the requested purge and embargo bands, the planner reduces the FOLD COUNT (never quietly halves the band size, which is the leak guarantee) and says so in a note that is printed with the results. NO PARAMETER IS RE-OPTIMISED PER FOLD - the same global parameters are used throughout - so the walk-forward tests whether a FIXED hypothesis generalises, not whether an optimiser can refit it, and therefore does NOT control for the user's own parameter selection (that is handled by the declared --n-variants penalty). The walk-forward is run on a SINGLE COMBINED universe, so per-asset-class holdout behaviour is not separately demonstrated.
- **D.multiple_testing** — Were multiple asset-class variants tested on the same data? How is multiple-testing bias corrected?
  - *[engine]* Implemented, but as a SIMPLIFIED PENALTY, not the Bailey/Lopez de Prado Deflated Sharpe Ratio: the observed Sharpe is reduced by an EXPECTED-MAX-UNDER-THE-NULL term 1/sqrt(n_obs) * ((1-gamma)*sqrt(2 ln n_variants) + gamma) with gamma = 0.5772. It applies NO non-normality (skew/kurtosis) term, NO trials-variance term and NO selection-bias correction, and it is applied to the IN-SAMPLE base Sharpe, NOT to the pooled OOS Sharpe that determines the verdict - so it is not a deflated OOS statistic. --n-variants DEFAULTS TO 1, in which case NO penalty is applied at all and the reported value equals the raw Sharpe; the correction is only active if the user supplies an honest count (intake.variants_tried must be confirmed). A negative deflated value raises a flag and downgrades an otherwise SUPPORTED verdict to FRAGILE.
- **D.asset_selection** — Were asset classes added or removed after seeing results?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine has no verified view of this: it is a statement about the user's own reasoning, hypothesis or process, which no amount of market data can supply. The engine's role is to test the stated rule, not to vouch for the story behind it. The engine does apply its OWN fixed objective refutation criteria to every run, independently of the user's pre-registration: REFUTED if pooled OOS Sharpe < 0.5, or if the edge does not survive 2x cost stress, or if the causality audit fails (unconditional - the numbers are void); INCONCLUSIVE if fewer than 30 trades; and FRAGILE (SUPPORTED downgraded) if fewer than 50% of calendar years are profitable, fewer than 60% of walk-forward folds are profitable, parameter-sweep stability < 0.6, Monte Carlo P(profitable) < 0.85, OOS Sharpe retention < 40% of in-sample, or a negative deflated Sharpe.

### E. Costs, execution, financing, and capacity

- **E.commissions** — Are commissions, exchange fees, taxes, stamp duties, and levies included per asset class?
  - *[engine]* Per asset class the engine charges EXACTLY FOUR components on traded notional, from DEFAULT_COSTS: COMMISSION, HALF-SPREAD (half the bid-ask), SLIPPAGE, and BORROW (annualised, charged daily on short notional). Rates (bps): etf 0.5 / 1.0 / 1.0 / 10.0; index_or_future 0.2 / 0.5 / 0.5 / 5.0; fx 0.0 / 0.5 / 0.5 / 15.0; crypto 10.0 / 5.0 / 5.0 / 30.0. EXCHANGE FEES, TRANSACTION TAXES, STAMP DUTIES and LEVIES ARE NOT MODELLED for any asset class - a strategy in a jurisdiction with stamp duty is being charged a cost stack that omits it. Note also that infer_asset_class classifies by symbol string, so a symbol it does not recognise falls back to the etf schedule. The only user lever is a SINGLE GLOBAL execution.cost_multiplier (the gauntlet re-runs at 1.0x/1.5x/2.0x/3.0x) - per-class rates CANNOT be overridden. Realised costs are reported as one scalar costs_paid; per-class attribution of realised costs is NOT available - the per-class table states the ASSUMED rates, not what each class actually paid.
- **E.spread** — Is bid-ask spread modelled per asset class, including wider spreads in stress and illiquidity?
  - *[engine]* A constant half-spread per asset class is charged on every trade. Spread WIDENING IN STRESS OR ILLIQUIDITY is NOT modelled - so a strategy that trades into a volatility spike is flattered.
- **E.slippage** — Is slippage a function of volatility, order size, liquidity, and order type?
  - *[engine]* Constant slippage per asset class, plus an order cap at max_participation (default 10%) of the TRAILING dollar volume (strictly before the fill bar). Slippage does NOT widen with volatility, and market impact is NOT modelled.
- **E.stop_fills** — Are stops assumed to fill at the stop price even when markets gap?
  - *[engine]* An order is filled at the bar's OPEN, never at a worse intra-bar level. Gap risk is therefore NOT overstated in favour of the strategy.
- **E.limit_fills** — Are limit orders assumed filled on touch, and is queue position considered?
  - *[engine]* Not modelled. Every order is treated as a market order at the next bar's open/close.
- **E.partial_fills** — Are partial fills, rejected orders, and missed signals modelled?
  - *[engine]* Partially modelled: the ADV participation cap can truncate an order, but there is no queue position, no rejection, and no latency.
- **E.borrow** — Are short borrow costs, locate fees, and short-sale constraints included?
  - *[engine]* An annualised borrow rate per asset class is charged DAILY ON SHORT NOTIONAL (etf 10bps, index_or_future 5bps, fx 15bps, crypto 30bps annualised). LOCATE FEES ARE NOT MODELLED, and BORROW AVAILABILITY, SHORT-SALE CONSTRAINTS, LOCATES AND RECALLS ARE NOT MODELLED at all - the engine assumes any short is fillable and never recalls it. The crypto rate doubles as the perp funding proxy, and because it is charged only on short notional a long crypto position pays no funding (see C.crypto).
- **E.roll_carry_funding** — Are futures roll costs, FX swap costs, crypto funding, and options spreads included?
  - *[engine]* Futures roll cost, FX swap/rollover, and option bid-ask spreads are NOT MODELLED. Crypto funding is APPROXIMATED BY the crypto class borrow rate (30bps annualised), but because borrow is charged only on SHORT NOTIONAL, a LONG crypto position pays NO FUNDING AT ALL - the long leg's funding cost, which on a perpetual is paid for holding the position, is entirely absent.
- **E.financing** — Are financing, margin interest, collateral haircuts, and leverage costs included?
  - *[engine]* NOT MODELLED - no margin interest, no collateral haircuts, and no financing cost on gross exposure. There is no margin, collateral, haircut or financing model of any kind: gross exposure above 1.0 is UNFUNDED, short proceeds earn 0%, and there is NO NETTING SET - every symbol is treated as margined independently and gross is computed on a per-symbol sum, so no offsetting credit between an equity short and a bond long is recognised.
- **E.fx_costs** — Are FX conversion costs and hedging costs included?
  - *[engine]* No FX CONVERSION is performed, so there is no conversion cost to model - the book is never converted to a base currency. The FX class still carries a trading spread and slippage (0.5bps half-spread + 0.5bps slippage, 0bps commission) and a 15bps annualised BORROW on short notional; that borrow is the only carry-like charge and it is NOT a modelled swap or rollover rate. Hedging costs are not modelled because no hedging is performed - FX exposure is left unhedged in quote currency.
- **E.adv_participation** — What percentage of average daily volume would your orders represent per asset class?
  - *[engine]* Two DISTINCT participation rules exist and must not be conflated. (1) THE ORDER CAP THE SIMULATION ENFORCES: every order is truncated at max_participation - DEFAULT 10% - of the TRAILING dollar volume (the mean dollar volume of the bars STRICTLY BEFORE the fill bar, over a 20-bar window). Using the fill bar's own volume would be intra-bar look-ahead, since a bar's volume is not knowable at its open, and when that volume was zero the cap silently disappeared and let an order of any size through. If no trailing volume is available the order is NOT filled, and the skip is counted in the simulation result under the key liquidity_skips. THERE IS ONE EXCEPTION: an instrument with NO volume series at all (FX pairs and most OTC instruments have no consolidated screen volume) is not blocked - the participation cap simply does not apply to it, because there is no screen volume to participate in. Such instruments are listed in the simulation result under symbols_without_volume, and the order is still sized and costed normally. on daily bars that is up to 10% of one session's volume in a single order, so it is a PER-BAR, not per-day, limit. (2) THE CAPACITY CEILING THE CAPACITY STAGE ESTIMATES: the capital at which the binding symbol's DAILY traded notional would reach 5% of its median daily dollar volume, assuming turnover scales linearly with capital and NO market impact - so the true capacity is LOWER. The engine NEVER reports realised participation per asset class; per-symbol capacity limits are exposed by the capacity stage (per_symbol_limits), but a per-class participation statistic does not exist.
- **E.size_decay** — How does performance degrade at 2x, 5x, and 10x intended size?
  - *[engine]* NOT automated. The capacity stage reports the capital at which the binding instrument would exceed 5% of ADV; explicit 2x/5x/10x size runs are not built in.
- **E.limits** — Are there position limits, borrow limits, contract limits, or regulatory constraints per asset class?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine enforces only per-name max_weight, gross_leverage and net_target. Regulatory, contract, borrow-availability and position limits are outside it entirely and have to come from the user's broker and risk policy.

### F. Portfolio construction, cross-asset risk, and correlation

- **F.covariance** — Is the covariance/correlation matrix estimated point-in-time and free of look-ahead bias?
  - *[engine]* NOT computed. The engine estimates NO covariance matrix and NO correlation matrix at all - there is no risk model, no correlation estimate, and therefore no point-in-time correlation to leak. Nothing about correlations is look-ahead-free or otherwise, because correlations are simply absent from the output.
- **F.stress_correlation** — How do correlations behave in stress? Are crisis correlations modelled?
  - *[engine]* NOT modelled. There is no crisis-correlation regime, no correlation stress scenario and no conditional-correlation model - and no correlation matrix to stress in the first place (see F.covariance). A multi-asset book is therefore NOT tested for the correlation spikes that historically define a crisis.
- **F.diversification_decay** — Does the strategy rely on diversification that disappears in drawdowns?
  - *[engine]* Not directly tested. The regime split shows whether performance differs between high and low volatility periods; it does not measure correlation decay specifically.
- **F.factor_exposure** — What are factor exposures across asset classes - value, momentum, carry, trend, quality, liquidity, duration, credit?
  - *[engine]* NOT decomposed. No Barra/Fama-French style factor attribution.
- **F.risk_contribution** — Are risk contributions per asset class measured and within limits?
  - *[engine]* NONE of the three bundled sub-topics is computed. RISK CONTRIBUTION BY ASSET CLASS: not computed - there is no risk model, no COVARIANCE matrix and no marginal/contribution-to-risk decomposition (the engine estimates no covariance or correlation at all). FACTOR EXPOSURE: not decomposed - no value/momentum/carry/trend/quality/liquidity/duration/credit attribution, and no benchmark-relative exposure. CONCENTRATION BY ASSET/SECTOR/COUNTRY/CURRENCY: only a per-name max_position cap, max_names, gross_leverage and net_target are enforced; there is NO reported concentration statistic by sector, country, currency or class, and no class/sector/country/currency/factor limits are enforced. The only exposure figures reported are portfolio-level gross exposure and time-in-market.
- **F.concentration** — Are concentration limits enforced by asset, class, country, sector, currency, and factor?
  - *[engine]* Only per-name max_weight, gross_leverage and net_target are enforced. Limits by class, sector, country, currency and factor are NOT enforced.
- **F.vol_target_impl** — How is volatility targeting or risk parity implemented across assets with different vol and liquidity?
  - *[engine]* THE VOL-TARGET LEVEL IS NOW HONOURED: the book is scaled so the PORTFOLIO's estimated annual volatility equals vol_target, so vol_target 0.10 and vol_target 0.40 produce genuinely different books. The shape comes from RELATIVE inverse-volatility (1/sigma) scaling across names; the size comes from the volatility target. PORTFOLIO VOLATILITY IS ESTIMATED WITH A DIAGONAL COVARIANCE (pairwise correlations assumed zero), which OVERSTATES the volatility of a genuinely diversified multi-asset book - so REALISED VOLATILITY LANDS BELOW THE TARGET, and vol_target should be read as an UPPER BOUND on realised vol, not an exact setting. LIQUIDITY PLAYS NO PART in the sizing: the inverse-vol scaling uses trailing realised volatility only (default vol_lookback 60 bars, annualised at sqrt(252)) and is blind to ADV, spread and depth. A thin, high-vol instrument therefore receives a small weight but can still dominate realised risk.
- **F.turnover_costs** — Are rebalancing costs and turnover modelled at the portfolio level?
  - *[engine]* Turnover and total costs are tracked and reported per run, and the cost-stress stage re-runs the strategy at 1.0x/1.5x/2.0x/3.0x the base costs.
- **F.margin_netting** — Are margin, collateral, and netting assumptions consistent across asset classes?
  - *[engine]* NOT MODELLED - no margin interest, no collateral haircuts, and no financing cost on gross exposure. There is no margin, collateral, haircut or financing model of any kind: gross exposure above 1.0 is UNFUNDED, short proceeds earn 0%, and there is NO NETTING SET - every symbol is treated as margined independently and gross is computed on a per-symbol sum, so no offsetting credit between an equity short and a bond long is recognised.
- **F.sleeve_sum** — Does the combined portfolio outperform the sum of sleeves after costs, or is diversification illusory?
  - *[engine]* NOT computed directly. The cross-market replication stage reports the Sharpe of the same signal on alternative universes (in-sample on those universes), which indicates whether the edge is portable or specific to one sleeve.
- **F.leave_one_out** — What happens if one asset class is removed, and does performance collapse?
  - *[engine]* NOT implemented as a dedicated stage - there is NO leave-one-asset-out test anywhere in the engine. Cross-market replication is a DIFFERENT experiment: it re-runs the same signal on ALTERNATIVE universes and reports each one's IN-SAMPLE Sharpe of the full sample. It indicates whether the signal is portable to other instruments; it does NOT measure what happens to a fixed multi-asset book when one sleeve is removed, because it never removes a sleeve from the original book and the alternative universes overlap the original. The required question - does performance collapse if one asset class is removed? - CANNOT be answered by this engine and must be produced by re-running the gauntlet on hand-built sub-universes, or not at all.
- **F.cross_asset_stability** — Are cross-asset signals stable, or driven by one regime or one asset class?
  - *[engine]* Indicated by the replication stage and the per-year breakdown, but NOT by a dedicated leave-one-out test, which is not implemented.

### G. Robustness, overfitting, and statistical validity

- **G.variants_tested** — How many parameter combinations, asset subsets, and allocation rules were tested?
  - *[user]* 1 variants declared by the user
  - _engine note:_ The engine cannot see how many variants were tried; it applies the deflated-Sharpe penalty for the count the user DECLARES (--n-variants). An understated count makes the penalty too weak.
- **G.plateau** — Does performance form a stable plateau across nearby parameters and asset-class weights?
  - *[engine]* The sweep perturbs EACH NUMERIC PARAMETER OF EVERY DECLARED FEATURE, at -25% and +25%, and reports each perturbed IN-SAMPLE Sharpe, the retention ratio against the base in-sample Sharpe, and a STABILITY FRACTION defined as the share of perturbations that preserve the SIGN of the Sharpe - a sign-consistency measure, not a retention magnitude; a broad plateau is reported at stability >= 0.75. NOT perturbed: all signal thresholds, all portfolio/sizing parameters, the rebalance cadence, and all execution and cost parameters. ASSET-CLASS WEIGHTS ARE NEVER PERTURBED AT ALL - there is no allocation parameter to perturb, because the engine does not allocate across classes (see A.allocation), so the plateau across asset-class weights half of this question cannot be tested in this engine. The sweep is IN-SAMPLE; it does not re-run walk-forward at the perturbed settings. Degenerate (no-op) perturbations are skipped.
- **G.walk_forward** — Does it survive walk-forward testing with rolling optimisation across all assets?
  - *[engine]* Purged + embargoed expanding-window walk-forward. The layout is [train_0][purge_0][test_0][embargo_0][train_1][purge_1][test_1] ... : each fold's in-sample set is its own train segment PLUS every earlier train segment, with the `purge` bars immediately before each test block excluded from EVERY training set (a training bar whose label horizon reaches into the test block would leak the test period) and the `embargo` bars immediately after each test block excluded from every later training set. Purge and embargo default to the maximum feature lookback in the spec and are overridable; the sizes actually used are printed. A DISJOINTNESS ASSERTION runs on every walk-forward and reports four checks: (a) no date appears in two out-of-sample blocks, (b) no out-of-sample bar was in its own fold's training set, (c) no training bar of fold f+1 falls inside fold f's test block or embargo band, (d) no training bar of any fold falls inside any test block. A violation is SURFACED, not swallowed. Features are computed on the FULL causal history and the panel is sliced afterwards, so a long lookback does not lose its warm-up at a fold boundary. If the sample cannot support the requested purge and embargo bands, the planner reduces the FOLD COUNT (never quietly halves the band size, which is the leak guarantee) and says so in a note that is printed with the results. NO PARAMETER IS RE-OPTIMISED PER FOLD - the same global parameters are used throughout - so the walk-forward tests whether a FIXED hypothesis generalises, not whether an optimiser can refit it, and therefore does NOT control for the user's own parameter selection (that is handled by the declared --n-variants penalty). The walk-forward is run on a SINGLE COMBINED universe, so per-asset-class holdout behaviour is not separately demonstrated.
- **G.oos_breadth** — Does it survive out-of-sample testing on different instruments, countries, and asset classes?
  - *[engine]* The strategy is re-run on ALTERNATIVE universes (usually different asset classes) over the SAME historical window. Each alternative run is IN-SAMPLE for that alternative universe: same dates, same features, no walk-forward split, no re-optimisation. It therefore tests whether the SIGNAL is portable to another market, NOT whether it survives out-of-sample -- it is not an out-of-sample breadth result. The share of alternative universes with a positive Sharpe is reported as the replication rate and is flagged below 50%.
- **G.subperiods** — Does it survive subperiod analysis - rate shocks, credit crises, commodity spikes, crypto drawdowns?
  - *[engine]* Per-calendar-year return and Sharpe are computed and printed, plus a high/low realised-volatility regime split. Specific macro events (rate shocks, credit crises) are not tagged automatically.
- **G.monte_carlo** — Does it survive Monte Carlo resampling of trades, returns, and trade order?
  - *[engine]* Bootstrap over the realised trade P&L sequence: each resample rebuilds an equity curve from the sampled trades and re-derives Sharpe and drawdown, annualised by the observed trade frequency. Seeded (seed=7) for reproducibility, and it needs at least 20 trades to run at all.
- **G.randomized** — Does it survive randomized asset inclusion or randomized rebalancing dates?
  - *[engine]* NOT implemented. Randomized asset inclusion and randomized rebalancing dates are stronger robustness tests than the parameter sweep for a multi-asset book, because they test whether the result depends on the specific assets or calendar chosen rather than on the signal. A strategy that survives only on one asset set has not been shown to work.
- **G.concentration_of_result** — Are results driven by one asset class, one instrument, one year, or one event?
  - *[engine]* Partially. The per-year breakdown shows whether one year carried the result, and replication shows whether one asset class carried it. There is no single-instrument attribution.
- **G.trade_counts** — Are trade counts per asset class sufficient - at least 30-50 per sleeve?
  - *[engine]* A COMBINED trade count is reported and fewer than 30 trades raises a flag (THRESHOLDS.min_trades) and, with no OOS evidence, forces INCONCLUSIVE. THE THRESHOLD IS COMBINED, NOT PER SLEEVE: there is NO per-asset-class or per-instrument trade count, so a book with 120 trades concentrated in one sleeve passes the bar while a sleeve with 5 trades is statistically meaningless. One trade = one complete position lifecycle (partial rebalance adjustments are not counted).
- **G.confidence_intervals** — Are confidence intervals reported for expectancy, profit factor, Sharpe, and drawdown?
  - *[engine]* NOT reported for expectancy, profit factor, Sharpe, or drawdown. Only Monte Carlo percentiles for the resampled distribution.
- **G.deflated_sharpe** — Is the Sharpe ratio adjusted for multiple testing and selection bias?
  - *[engine]* Implemented, but as a SIMPLIFIED PENALTY, not the Bailey/Lopez de Prado Deflated Sharpe Ratio: the observed Sharpe is reduced by an EXPECTED-MAX-UNDER-THE-NULL term 1/sqrt(n_obs) * ((1-gamma)*sqrt(2 ln n_variants) + gamma) with gamma = 0.5772. It applies NO non-normality (skew/kurtosis) term, NO trials-variance term and NO selection-bias correction, and it is applied to the IN-SAMPLE base Sharpe, NOT to the pooled OOS Sharpe that determines the verdict - so it is not a deflated OOS statistic. --n-variants DEFAULTS TO 1, in which case NO penalty is applied at all and the reported value equals the raw Sharpe; the correction is only active if the user supplies an honest count (intake.variants_tried must be confirmed). A negative deflated value raises a flag and downgrades an otherwise SUPPORTED verdict to FRAGILE.
- **G.non_normality** — Are returns fat-tailed, autocorrelated, or clustered in ways that invalidate standard statistics?
  - *[engine]* Skew, kurtosis and a lag-1 autocorrelation Sharpe adjustment are computed: sharpe_lag1 = S / sqrt(1 + (1 + 2*rho1)) - a SINGLE-LAG correction, NOT Lo (2002)'s estimator, which sums all autocorrelations up to the series length. The adjusted figure is returned in the scorecard but is NOT SHOWN in the rendered report metric table and does NOT enter the verdict. Fat tails and serial correlation are therefore visible but not acted on; there is no clustering test (runs/variance-ratio) and no bootstrap-based tail diagnostic.
- **G.top_trades** — What happens if you remove the top 1-5 trades per asset class and overall?
  - *[engine]* NOT implemented. Removing the top 1-5 trades is the standard test for whether a result depends on a few outliers, and this engine does not run it.
- **G.drawdown_attribution** — Are drawdowns and tail losses attributed correctly by asset class?
  - *[engine]* NOT implemented per asset class or per period.

### H. Performance and risk metrics to report

- **H.core_metrics** — CAGR, annualised volatility, Sharpe, Sortino, Calmar, profit factor, expectancy per trade.
  - *[engine]* Computed and reported: CAGR, Sharpe, Sortino, Calmar, profit factor, expectancy per trade, win rate, t-statistic, skew, kurtosis, VaR(95%), CVaR(95%), max drawdown, total return, final equity, turnover, time in market, average gross exposure, costs paid, and a lag-1 autocorrelation Sharpe adjustment. PROFIT FACTOR, EXPECTANCY AND WIN RATE ARE COMPUTED FROM THE NET-OF-COSTS TRADE LEDGER, so they are on the same basis as Sharpe and CAGR, and the report labels them as such. NOT computed: annualised volatility and drawdown duration - the engine produces neither, so no figure for them can be quoted.
- **H.drawdown_metrics** — Maximum drawdown, longest drawdown, time to recovery, worst daily/weekly/monthly loss.
  - *[engine]* Maximum drawdown (magnitude) is computed and reported. Drawdown DURATION, time-to-recovery and worst daily/weekly/monthly loss are NOT computed or reported: the engine derives the drawdown depth from the return series and never exposes a duration metric.
- **H.exposure_metrics** — Turnover, holding period, exposure, gross/net leverage, margin usage.
  - *[engine]* Computed: turnover_total (cumulative traded notional over the run; the capacity stage separately derives turnover per year), time_in_market - DEFINED AS THE FRACTION OF BARS IN WHICH GROSS EXPOSURE EXCEEDED 5%, not calendar time invested - and avg_gross_exposure (mean gross exposure over equity). NOT computed: an average HOLDING PERIOD (per-trade bars_held is recorded in the ledger but never aggregated) and NET EXPOSURE / NET LEVERAGE (only gross exposure is tracked, so a dollar-neutral or net-target book's realised net drift is invisible). MARGIN USAGE IS NOT APPLICABLE - the engine models no margin, no collateral and no financing, so gross exposure above 1.0 is unfunded by construction.
- **H.risk_attribution** — Risk contribution by asset class, factor exposure, concentration by asset/sector/country/currency.
  - *[engine]* NONE of the three bundled sub-topics is computed. RISK CONTRIBUTION BY ASSET CLASS: not computed - there is no risk model, no COVARIANCE matrix and no marginal/contribution-to-risk decomposition (the engine estimates no covariance or correlation at all). FACTOR EXPOSURE: not decomposed - no value/momentum/carry/trend/quality/liquidity/duration/credit attribution, and no benchmark-relative exposure. CONCENTRATION BY ASSET/SECTOR/COUNTRY/CURRENCY: only a per-name max_position cap, max_names, gross_leverage and net_target are enforced; there is NO reported concentration statistic by sector, country, currency or class, and no class/sector/country/currency/factor limits are enforced. The only exposure figures reported are portfolio-level gross exposure and time-in-market.
- **H.tail_risk** — Tail risk: skew, kurtosis, CVaR, worst gap, crisis performance.
  - *[engine]* Skew, kurtosis, VaR(95%) and CVaR(95%) are computed, plus a high/low realised-volatility regime split. VaR(95%) is the 5th PERCENTILE return and CVaR(95%) is the MEAN OF THE TAIL (not the worst observation); both require at least 20 return observations and are None below that. Worst single gap and a tagged crisis slice are NOT computed.
- **H.benchmark_corr** — Correlation to benchmarks and to an existing portfolio.
  - *[engine]* NOT computed. The engine can run any universe as a buy-and-hold comparator, but correlation to a benchmark or to an existing portfolio is not reported.
- **H.gross_net** — Performance gross and net of costs, with cost attribution by asset class.
  - *[engine]* The gauntlet runs the strategy a SECOND TIME WITH COSTS ZEROED, so a gross-of-costs run and the net-of-costs run are compared side by side (Sharpe and CAGR, plus costs paid and turnover) with a plain-English reading of the gap across the four QUADRANTS: an edge that is positive gross but negative net is real but untradeable at this size and frequency; an edge that is not positive gross is not an edge at all. PER-ASSET-CLASS ATTRIBUTION of realised costs is NOT auto-split - the class cost table holds ASSUMED rates, not realised per-class costs.
- **H.capacity** — Capacity analysis by asset class and combined portfolio.
  - *[engine]* Linear turnover scaling against a 5% ADV participation ceiling on the most illiquid traded symbol. Does NOT model market impact, so real capacity is LOWER.

### I. Forward testing: multi-asset execution and behavior

- **I.forward_test_type** — Is this paper trading or small live capital across all asset classes?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine is retrospective only: it never paper trades, routes orders or captures fills, and it keeps no live log. Every forward-test fact therefore comes from the user's own records; the engine's only contribution is the backtest baseline those facts are compared against.
- **I.duration** — How long will the forward test run - minimum trades, weeks, and regime coverage per asset class?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine is retrospective only: it never paper trades, routes orders or captures fills, and it keeps no live log. Every forward-test fact therefore comes from the user's own records; the engine's only contribution is the backtest baseline those facts are compared against.
- **I.rule_parity** — Are rules identical to the backtest? If not, what changed and why?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine is retrospective only: it never paper trades, routes orders or captures fills, and it keeps no live log. Every forward-test fact therefore comes from the user's own records; the engine's only contribution is the backtest baseline those facts are compared against.
- **I.success_criteria** — What are the predefined success/failure criteria before starting?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine is retrospective only: it never paper trades, routes orders or captures fills, and it keeps no live log. Every forward-test fact therefore comes from the user's own records; the engine's only contribution is the backtest baseline those facts are compared against.
- **I.fill_parity** — Did signals, fills, and timestamps match across asset classes?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine is retrospective only: it never paper trades, routes orders or captures fills, and it keeps no live log. Every forward-test fact therefore comes from the user's own records; the engine's only contribution is the backtest baseline those facts are compared against.
- **I.slippage_actual** — What was actual slippage versus modelled slippage per asset class?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine is retrospective only: it never paper trades, routes orders or captures fills, and it keeps no live log. Every forward-test fact therefore comes from the user's own records; the engine's only contribution is the backtest baseline those facts are compared against.
- **I.rejected_orders** — Were there rejected, delayed, partial, or missed orders?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine is retrospective only: it never paper trades, routes orders or captures fills, and it keeps no live log. Every forward-test fact therefore comes from the user's own records; the engine's only contribution is the backtest baseline those facts are compared against.
- **I.feed_discrepancy** — Did data-feed discrepancies occur between signal source and broker across assets?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine is retrospective only: it never paper trades, routes orders or captures fills, and it keeps no live log. Every forward-test fact therefore comes from the user's own records; the engine's only contribution is the backtest baseline those facts are compared against.
- **I.funding_behaviour** — Did FX conversion, funding, borrow, roll, or margin behave as modelled?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine is retrospective only: it never paper trades, routes orders or captures fills, and it keeps no live log. Every forward-test fact therefore comes from the user's own records; the engine's only contribution is the backtest baseline those facts are compared against.
- **I.signals_vs_trades** — How many signals were generated versus taken per asset class?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine is retrospective only: it never paper trades, routes orders or captures fills, and it keeps no live log. Every forward-test fact therefore comes from the user's own records; the engine's only contribution is the backtest baseline those facts are compared against.
- **I.skipped_trades** — For every skipped trade, what was the reason - fear, news, liquidity, sizing, rule ambiguity?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine is retrospective only: it never paper trades, routes orders or captures fills, and it keeps no live log. Every forward-test fact therefore comes from the user's own records; the engine's only contribution is the backtest baseline those facts are compared against.
- **I.overrides** — Did you override the system? How often, why, and with what outcome?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine is retrospective only: it never paper trades, routes orders or captures fills, and it keeps no live log. Every forward-test fact therefore comes from the user's own records; the engine's only contribution is the backtest baseline those facts are compared against.
- **I.sizing_adherence** — Were position sizing, stops, exposure limits, and loss limits honoured?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine is retrospective only: it never paper trades, routes orders or captures fills, and it keeps no live log. Every forward-test fact therefore comes from the user's own records; the engine's only contribution is the backtest baseline those facts are compared against.
- **I.unintended_concentration** — Did correlated positions create unintended concentration across asset classes?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine is retrospective only: it never paper trades, routes orders or captures fills, and it keeps no live log. Every forward-test fact therefore comes from the user's own records; the engine's only contribution is the backtest baseline those facts are compared against.
- **I.first_losing_streak** — How did you behave during the first multi-asset losing streak?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine is retrospective only: it never paper trades, routes orders or captures fills, and it keeps no live log. Every forward-test fact therefore comes from the user's own records; the engine's only contribution is the backtest baseline those facts are compared against.
- **I.regime_similarity** — Is the current regime similar to the backtest sample across asset classes?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine is retrospective only: it never paper trades, routes orders or captures fills, and it keeps no live log. Every forward-test fact therefore comes from the user's own records; the engine's only contribution is the backtest baseline those facts are compared against.
- **I.live_vs_backtest** — What are live expectancy, profit factor, win rate, drawdown, and slippage versus backtest per sleeve and combined?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine is retrospective only: it never paper trades, routes orders or captures fills, and it keeps no live log. Every forward-test fact therefore comes from the user's own records; the engine's only contribution is the backtest baseline those facts are compared against.
- **I.degradation** — Is degradation within acceptable range - e.g. 5-10% lower win rate or higher costs?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine is retrospective only: it never paper trades, routes orders or captures fills, and it keeps no live log. Every forward-test fact therefore comes from the user's own records; the engine's only contribution is the backtest baseline those facts are compared against.
- **I.statistical_maturity** — Are results statistically meaningful yet, or still too few trades?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine is retrospective only: it never paper trades, routes orders or captures fills, and it keeps no live log. Every forward-test fact therefore comes from the user's own records; the engine's only contribution is the backtest baseline those facts are compared against.
- **I.operational_failures** — Did operational failures occur - data outage, broker API, reconciliation error, manual order error?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine is retrospective only: it never paper trades, routes orders or captures fills, and it keeps no live log. Every forward-test fact therefore comes from the user's own records; the engine's only contribution is the backtest baseline those facts are compared against.
- **I.decision** — Does the strategy meet graduation criteria, need revision, or should it be rejected?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine is retrospective only: it never paper trades, routes orders or captures fills, and it keeps no live log. Every forward-test fact therefore comes from the user's own records; the engine's only contribution is the backtest baseline those facts are compared against.
- **I.scale_pause_evidence** — What evidence would justify scaling capital, and what evidence would force a pause?
  - *[UNKNOWN]* UNKNOWN
  - _engine note:_ The engine is retrospective only: it never paper trades, routes orders or captures fills, and it keeps no live log. Every forward-test fact therefore comes from the user's own records; the engine's only contribution is the backtest baseline those facts are compared against.

## Interpretation Notes

- In-sample metrics are for comparison only; the walk-forward/OOS result is the decision-relevant number.
- This report is a hypothesis test, not a forecast. Even a SUPPORTED verdict warrants paper trading before live capital.
