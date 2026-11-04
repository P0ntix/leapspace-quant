# TESTING THE UNTESTED CLAIMS — a proposal

**Date:** 2026-11-04
**Scope:** the 51 daily-testable, never-built claims from
`reports/PAPER_CLAIM_INVENTORY.md` (293 claims total, 80 directional).
**Status:** every data source below was **probed live on this host**;
the probe output is quoted. Nothing here is a plan for a source that
might exist — it is a plan for sources that answered.

---

## 0. WHERE THE 51 CLAIMS ACTUALLY SIT

| Family | Claims | Needs | Buildable now? |
|---|---|---|---|
| **Stop-loss / trailing / ratchet** | RET-74, 76, 77, 86, 87, 89, 90, 91, 92, 95 (10) | price only | **yes — and the engine has no stop support at all** |
| **Pairs trading** | RET-24, 25, 28, 31, 32, 33, 48 (7) | price, volume | **yes — `leapspace/trend.py` has it; it has never been through the gauntlet** |
| **Regime model design** | REG-03, 07, 13, 17, 18, 19, 20, 22, 47, 48, 52 (11) | price, volume, macro | mostly yes; the crypto variants need market-level on-chain |
| **Crypto market-level on-chain** | RET-01, 03, 07; REG-07, 13, 31, 46, 48, 52 (10) | market-level on-chain, sentiment, macro | **yes — Coin Metrics Community API, verified** |
| **Horizon / asymmetry** | NAS-38, REG-31, REG-40, RET-85 (4) | price | yes |
| **Momentum horizons** | RET-15, RET-02, RET-21 (3) | price | yes |
| **Method / ablation** | NAS-92, IND-07, IND-12 (3) | mixed | yes — and NAS-92 asks for exactly the ablation protocol this proposal is |
| **Other** | REG-35, REG-54, REG-56, REG-57, NAS-28, NAS-32, NAS-39 (7) | price | yes, mostly as NEGATIVE controls |

**The biggest and cheapest win is the stop family.** Ten claims, price
data only, and the engine currently has *no stop-loss support* — so
they were not skipped for lack of data, they were never implemented.

---

## 1. THE DATA LAYER — where to get it

### 1.1 What already exists

| Need | Already in the package? |
|---|---|
| OHLCV for 6 asset classes | yes — `market.py` |
| Implied volatility (equity, crypto) | yes — `leading.py` (DVOL, ^VIX, ^VXN) |
| Funding rate, open interest (crypto) | yes — `cryptoderivs.py` |
| Dealer gamma, option flow | yes — `gamma.py` |
| Wallet-level on-chain (Solana) | yes — `onchain.py` |
| Social / narrative / sentiment (token-level) | yes — `social.py`, `socialedge.py` |
| **Market-level on-chain (active addresses, hashrate, exchange flows)** | **NO — this is the gap** |
| **Macro (global)** | documented in `LEADING_DATA_SOURCES.md`, not wired into the features |

The crypto claims (RET-01/03/07, REG-07/13/31/46/48/52) name
*market-level* on-chain variables — "active users, hashrate, wallet
activity, transaction volume". The package has *wallet-level* on-chain
data. Different thing.

### 1.2 The source that closes it — Coin Metrics Community API

**Verified live, 2026-11-04:**

```
GET https://community-api.coinmetrics.io/v4/timeseries/asset-metrics
    ?assets=btc
    &metrics=AdrActCnt,TxCnt,HashRate,FlowInExUSD,FlowOutExUSD,PriceUSD
    &frequency=1d&page_size=3&start_time=2024-01-01

-> 200 OK
   last: time=2026-11-03T00:00:00Z
         AdrActCnt    683,862        (active addresses)
         HashRate     1.03e18        (hash rate)
         FlowInExUSD  2.86e9        (exchange inflow, USD)
         FlowOutExUSD (exchange outflow, USD)
```

| Asset | Metrics available at daily frequency (verified) |
|---|---|
| `btc` | `AdrActCnt`, `TxCnt`, `HashRate`, `FlowInExUSD`, `FlowOutExUSD`, `PriceUSD` |
| `eth` | `AdrActCnt`, `TxCnt`, `PriceUSD` |
| `sol` | **`AdrActCnt` at daily frequency returns 403** — available only at other frequencies |

**Three traps, all found by probing:**

1. **The parameter is `page_size`, NOT `limit`.** Passing `limit`
   returns `400 {"error":{"type":"unsupported_parameter","message":
   "Unsupported parameter 'limit'."}}` — which looks like a metric-name
   error and is not. It cost two probe rounds.
2. **Availability is per asset AND per frequency.** `sol` +
   `AdrActCnt` + `1d` → `403 forbidden`. The API states the
   restriction in the error, and every row also carries
   `<metric>-status` / `<metric>-status-time` fields that say whether
   that particular observation was actually reported. **Those status
   fields must be carried into the provenance** — a gap in the series
   is not a zero.
3. **It is free and keyless**, and it updates daily, so the series is
   a genuine forward-looking input rather than a backfill.

This one source covers RET-01's "active users, hashrate, wallet
activity, transaction volume" **and** gives the exchange-netflow
leading indicator, which is the one genuinely *leading* on-chain
measure — coins leaving exchanges precede the supply squeeze.

### 1.3 The second source — DeFiLlama (verified)

```
GET https://stablecoins.llama.fi/stablecoins?includePrices=true
-> 200, 435 pegged assets
GET https://api.llama.fi/v2/chains
-> 200, 420 chains (Bitcoin TVL $408.29bn)
GET https://api.llama.fi/overview/dexs?excludeTotalDataChart=true
-> 200, 1,578 protocols
```

Stablecoin supply growth is the "dry powder entering the market"
measure (RET-01/REG-47). DEX volume is the "microstructure stress"
input REG-48 asks for ("combining volume collapse with..."). TVL is
the DeFi leg of a crypto regime model.

### 1.4 The third — CoinGecko market data (verified)

```
GET https://api.coingecko.com/api/v3/global
-> 200, total_market_cap = $2.63tn
```

Market cap, volume and market-cap dominance are the regime-level
"risk-on/risk-off" state that REG-46 needs ("crypto-equity
correlation is regime-dependent"). Note the free tier rate-limits, so
it must go through the package's cache.

### 1.5 Macro, for REG-47 — already documented, not wired

`LEADING_DATA_SOURCES.md` already names FRED, IMF IFS, BIS, the World
Bank and the OECD for global macro. REG-47 asks that a *crypto* regime
model include macro, not only internal features. The wiring is a
feature, not a research project.

### 1.6 What still cannot be tested here, and must be labelled

129 of the 194 never-built claims are **NOT** testable on daily bars:
the options-chain and order-flow claims (OPT-*, RET-40 to RET-61), the
intraday scalping claims, and the sentiment claims that need a
retail-flow panel.

**These must be marked "NOT testable here", not proxied.** The one
exception the package already takes — C7's session drift — is labelled
as a proxy in the feature docstring, the spec notes and the report.

---

## 2. THE PROCESSING LAYER — how to turn raw into features

Six rules, each of which exists because breaking it produced a real
bug in this package.

### 2.1 Alignment: a measurement published after a bar never reaches it

Every leading series is aligned with a **one-bar publication lag**:
bar *T* may only use a measurement published before *T*. This is
already implemented in `leading.py::align_to_bars` and must be used for
every new source.

### 2.2 Normalisation: scale-free, and stated

Coin Metrics' `AdrActCnt` is a count, `HashRate` is a rate, `PriceUSD`
is a price. They cannot be combined without normalisation. The
regime-classifier features in `regime.py` already do this; the rule
is **z-score against a trailing window**, never against the whole
sample.

> The whole-sample z-score was a live look-ahead bug in this package:
> the leading-VRP feature normalised over the entire panel, so bar
> *i*'s value depended on bars after *i*. The causality audit caught it
> with 10 violations. It is now an expanding window, and
> `test_leading_causality.py` asserts it by truncation.

### 2.3 Missing is None, never zero

Every new source must follow this. Coin Metrics makes it explicit with
its `-status` fields: a gap in the series is **not** a zero
active-address count, and treating it as zero would tell the regime
model that activity collapsed.

### 2.4 Revisions and late-arriving data

Macro series are revised. A revised series is a look-ahead hazard in a
backtest. Rule: **use the real-time vintage (ALFRED for FRED) or do not
use the series in a backtest at all.**

### 2.5 Provenance on every fetch

URL, HTTP status, what was actually measured, and the availability
status of each observation. `provenance.py` is the single chokepoint
and the credential-redaction boundary — every new source goes through
it.

### 2.6 Cache, and say so

The package's cache distinguishes a live fetch from a cache hit. A
report that says "CACHE" where it says "LIVE" is honest about the
fact that the upstream has not been re-contacted.

---

## 3. THE IMPLEMENTATION LAYER — what to build

### 3.1 `leapspace/onchainmarket.py` — NEW, the market-level on-chain layer

```
fetch_coinmetrics_series(asset, metrics, frequency, start, end)
    -> Coin Metrics Community API, paged, with per-observation status
    -> cache-backed, provenance recorded

fetch_defillama_stablecoin_supply()
fetch_defillama_chain_tvl()
fetch_defillama_dex_volume()

build_onchain_features(panel, asset)
    -> active_addresses_zscore        (RET-01 "active users")
    -> transaction_count_zscore       (RET-01 "transaction volume")
    -> hashrate_zscore                (RET-01 "hashrate")
    -> exchange_netflow_zscore        (the genuinely LEADING one)
    -> stablecoin_supply_growth       (RET-01 "dry powder")
    -> tvl_growth                     (REG-47 macro)
    -> dex_volume_trend               (REG-48 "microstructure stress")
```

All features are **z-scored against a trailing window** and **aligned
with a one-bar lag**. The exchange-netflow feature is the only one
that is *leading* rather than contemporaneous, and it must be labelled
as such.

### 3.2 `leapspace/stops.py` — NEW, the ten stop-loss claims

The engine has **no stop support**. A stop is not a portfolio
parameter — it needs the entry price and the position state, so it
belongs in the signal, tracking its own state across bars.

```
sig_stop_momentum(panel, features, feature="momentum",
                  stop_sd=1.5, trail_sd=None, ratchet=False,
                  max_bars=None, invert_signal=False)
```

The variants, one per claim:

| Claim | Paper's rule | Parameter |
|---|---|---|
| RET-74, 76 | stop-loss momentum improves downside control | `stop_sd=1.5`, fixed band |
| RET-87 | a 1.0-SD band is a volatility warning, not an exit | `stop_sd=1.0` as a *warning* leg |
| RET-89, 90 | a **volatility-normalised** stop band: the distance is measured in units of the asset's own volatility, so it widens when volatility rises | stop distance = `stop_sd * realised_vol` |
| RET-91 | trailing stop, ratcheted up as price rises | `trail_sd=1.5` |
| RET-92 | do not anchor to the original entry — ratchet the stop up | `ratchet=True` |
| RET-95 | 1.0 SD is the early warning, 1.5 SD the trigger | two-band exit |
| RET-77 | **avoid a tight trailing stop** — mean reversion needs room | the NESTED control: a tight trail vs a wide one |
| RET-86 | stop-losses help momentum but too-tight stops hurt | the tight-vs-wide comparison |

**This family is the best test in the whole proposal** because it is
*falsifiable by construction*: RET-77 and RET-86 are the paper's own
negative claims, and a SPEC that implements the tight stop should
LOSE to the one that implements the wide stop. If the tight stop wins,
the paper is wrong, and the package says so.

**The key detail:** a volatility-normalised stop must use the
volatility as of the **entry bar**, not the current bar. Using the
current bar means the stop distance moves as the position moves, which
is a different rule and can quietly make the stop un-hittable.

### 3.3 `leapspace/trend.py` — ALREADY WRITTEN, never run

`sig_trend_long_short` and `sig_pairs_mean_reversion` exist and are
unit-tested, but have **never been through the gauntlet**. That is the
single cheapest remaining result: the code exists, the negative
control works, and only the run is missing.

Two additions the claims need:
- **Hurst exponent** (RET-25, RET-32) — "the Hurst exponent can
  identify faster reversion". Implementable in stdlib via the
  aggregated-variance method (variance of *k*-lag differences scales
  as *k*^(2H)); H < 0.5 means mean-reverting, H > 0.5 persistent.
  Use it to **select** pairs, or to size the holding period.
- **Dynamic cointegration** (RET-32) — a rolling hedge ratio rather
  than a static one. The OLS slope already computed in
  `select_pairs` can be re-fitted on a trailing window.

### 3.4 `leapspace/regime.py` — the eleven regime-design claims

The regime classifier is currently a single Gaussian HMM fit on the
whole panel, with a disclosed in-sample limitation. The claims ask for
variations that can be tested as **ablation specs** — the same signal
with one component changed:

| Claim | Ablation |
|---|---|
| REG-20, 22 | feature ablation: drop volatility, then trend, then drawdown, then liquidity |
| REG-18, 19 | state-count ablation: 4 vs 5 vs 6 states |
| REG-17, REG-03 | state-DURATION modelling (an HSMM) vs a plain HMM |
| REG-13, REG-52 | per-horizon classifiers (daily / weekly) instead of one shared |
| REG-47, 48 | crypto feature set: add macro, TVL, stablecoin supply, DEX-volume collapse |

**The ablation protocol is what NAS-92 explicitly asks for**: "Because
no retrieved paper integrates all components, the most defensible
approach is incremental ablation." That is a *method* claim, and it is
testable: build the components up one at a time and record what each
one adds.

---

## 4. THE VALIDATION LAYER — industry standard

### 4.1 What the engine already does

`btvalidate.full_gauntlet` runs, on every spec:

walk-forward (purged + embargoed, 5 folds) · gross-vs-net ·
cost stress · parameter sweep · Monte Carlo · subperiod & regime
breakdown · capacity estimate · causality audit · deflated Sharpe
penalty.

The package adds the **negative control**, the **intake gate**, the
**leading-coverage measurement**, the **stage ledger** and the
**per-fold table**.

### 4.2 What has to be added for these claims

| Addition | Why | Where |
|---|---|---|
| **Real cross-market replication** | the stage is currently SKIPPED for every spec because the runner passes no alternative universes. It is the one stage that says whether an edge **transfers to another market** — which is exactly what a "market curiosity" claim needs | `paperrun.run_matrix` must pass `alt_universes` |
| **A benchmark line** | every equity curve needs a buy-and-hold reference, or "the strategy made money" cannot be separated from "the market made money" | `backtestviz.py` |
| **A t-stat on the OOS return series** | the gauntlet has one; the visualisation should show it | `backtestviz.py` |
| **Multiple-testing accounting across the matrix** | 51 more claims means 51 more chances to find a false positive. The deflated Sharpe handles *within-spec* variants; it does not handle *across-matrix* selection. **The honest fix is to report the whole matrix and to state how many specs were run** | `paperreport.py` |
| **Real-time macro vintages** | for any macro-fed feature | `leadingcache.py` |

### 4.3 The industry-standard rules the package already honours

1. Purged and embargoed walk-forward — no leakage around the split.
2. Costs stressed to **2×** the engine default.
3. A **constant risk block** across every spec, so a difference in the
   result is attributable to the signal and the market, not to the
   bookkeeping.
4. A **net target of 0.0** and `long_only=False`, so a result cannot
   be a beta bet dressed up as alpha.
5. A **volatility target** so the book is sized to a risk, not a
   notional.
6. An **inverted-polarity twin** for every spec, with a test that the
   twin can actually fail.
7. A **causality audit** on every feature.
8. **PBO** (probability of backtest overfitting) via CSCV.

---

## 5. THE SEQUENCING

Ordered by **result per unit of work**, not by elegance.

### Phase A — run what already exists (0 new code)

`trend.py`'s long/short trend rule and pairs construction are written
and unit-tested but have never been through the gauntlet. Run them on
all six asset classes, with their inverted twins. **12 rows, one
worker, ~30 minutes.** This is the cheapest result in the proposal and
it directly addresses the requirement's "long/short, hedging" clause.

### Phase B — the stop family (price data only)

`stops.py` + 10 claim specs + 10 inverted twins + the tight-vs-wide
nested comparisons. **The tightest scientific payoff in the
proposal**, because the paper states its own negative claims.

### Phase C — the market-level on-chain layer

`onchainmarket.py` + the crypto claims (RET-01, 03, 07) + the crypto
regime variants (REG-07, 13, 48, 52). **The genuinely leading
crypto data** — exchange netflow — and the claims that name it.

### Phase D — the regime ablations

The ablation protocol NAS-92 asks for. Same signal, components added
one at a time. This answers "which of the features is actually doing
the work" for the whole regime family.

### Phase E — cross-market replication

Turn the SKIPPED stage into a real one, then re-run the whole matrix
with it. This is the stage that decides whether any surviving
concept is an edge or a market curiosity — and it is currently the
biggest single gap in the validation.

### Phase F — the full matrix, one code version

All of the above, then one re-run of everything under one code
version. **A results file that mixes rows from two code versions is
not reportable** — that is the rule from
`research-claims-to-backtest-matrix` §9, and this package has already
been bitten by it three times.

---

## 6. THE HONEST LIMITS

1. **129 of the 194 never-built claims cannot be tested here at all.**
   The options-chain, order-flow and intraday claims need data this
   package does not have. Saying so takes minutes; building a
   stand-in that answers a different question takes days and misleads.
2. **More claims means more false positives.** 51 more specs is 51 more
   chances to find noise. The controls protect against a *signal*
   that does not work; they do not protect against *selecting* the one
   spec that happened to. The deflated Sharpe handles within-spec
   variants. **Across-matrix selection needs the whole matrix
   reported and the spec count stated.**
3. **The crypto on-chain layer is BTC and ETH at daily frequency.**
   `sol` daily active-addresses is 403. Crypto claims that need Solana
   market-level data must use a different frequency or a different
   source.
4. **The equity panels have 22.8% leading-data coverage.** Any equity
   result from the leading layer is a result over the last five years,
   not twenty. That is a limitation of the *history available*, not of
   the source.
5. **A SUPPORTED verdict still warrants paper trading, not money.**
   `LIVE_CAPITAL_READINESS.md` says so, and the gate before stage A is
   now "at least one concept survives with its control failing".

---

## 7. THE DATA-SOURCE PROBE LOG

Everything quoted above was fetched on 2026-11-04 from this host:

| Source | Endpoint | Result |
|---|---|---|
| Coin Metrics | `/v4/timeseries/asset-metrics?assets=btc&metrics=AdrActCnt,TxCnt,HashRate,FlowInExUSD,FlowOutExUSD,PriceUSD&frequency=1d&page_size=3` | **200** — 3 rows through 2026-11-03 |
| Coin Metrics | same, `assets=eth` | **200** — `AdrActCnt`, `TxCnt`, `PriceUSD` |
| Coin Metrics | same, `assets=sol`, `AdrActCnt` at `1d` | **403** — not available at that frequency |
| Coin Metrics | same with `limit=` instead of `page_size=` | **400** — `Unsupported parameter 'limit'` |
| Coin Metrics | `/v4/catalog/asset-metrics` | **200** — metric names confirmed |
| DeFiLlama | `stablecoins.llama.fi/stablecoins?includePrices=true` | **200** — 435 pegged assets |
| DeFiLlama | `api.llama.fi/v2/chains` | **200** — 420 chains |
| DeFiLlama | `api.llama.fi/overview/dexs` | **200** — 1,578 protocols |
| CoinGecko | `api.coingecko.com/api/v3/global` | **200** — total market cap $2.63tn |
| Deribit | DVOL / option book | **200** — 2,051 daily DVOL points; 737 option instruments |
| Yahoo | ^VIX ^VXN ^VXD ^OVX GVZ RVX ^MOVE | **200** — all confirmed, daily |
| Bybit / Binance | funding history, open-interest history | **200** — 200 funding and 200 daily OI points each |

Already verified in earlier sessions and re-confirmed in the probes
above: DefiLlama, CoinGecko, Coin Metrics, Deribit, Yahoo, Bybit and
Binance are all reachable, keyless and return real history.
