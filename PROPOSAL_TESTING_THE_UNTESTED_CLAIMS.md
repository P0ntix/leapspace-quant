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

## 7. WHAT THE IMPLEMENTATION AND THE FIRST RUN CHANGED

The proposal above was written from the inventory. Two of its phases
have now been BUILT and one has been RUN. Building and running them
changed seven things. The changes are recorded here rather than
quietly absorbed, because each one invalidates a claim the proposal
would otherwise have made.

### 7.0 The Phase A result, and what it means

**The paper's own long/short rule was tested for the first time, on six
markets, with its inverted twin. One concept is FRAGILE with its
control REFUTED** — the first genuine discrimination in the project.

| Spec | Verdict | OOS Sharpe | OOS max DD | Folds profitable |
|---|---|---|---|---|
| `paper_trend_longshort_us_equity_style` | **FRAGILE** | **+0.77** | **3.4%** | **5 / 5** |
| `..._CONTROL` | REFUTED | −0.88 | 20.4% | 0 / 5 |

All five of the real rule's walk-forward folds are positive
(+0.157, +1.183, +0.344, +1.617, +0.442); all five of the control's
are negative. It stays FRAGILE because there are only **6 trades**
(gate needs ≥ 30), the t-stat is 0.97 (needs ≥ 2.0), PBO is 0.6 and
Monte Carlo could not run.

**And the run produced a finding that cuts against the paper:** on
crypto, the *inverted* pairs control scored **+0.97** against the real
rule's **−1.43** — trading the spread reversion the wrong way was
better by 2.4 Sharpe points. The pair-selection criterion picks the
most *stable* spreads, and on crypto the most stable spreads were the
*trending* ones. That is a finding about the implementation, and it is
reported as one.

Full detail: `reports/PHASE_A_RESULTS.md`.

### 7.1 The ratchet is redundant with a plain trailing stop — unless the band can move

The proposal said the ratchet (RET-92) is a distinct control. It is
not, in the default design.

A trailing stop's band is proportional to the running extreme, and
the running extreme is **monotonic in the position's favour** — a
long's only rises, a short's only falls. So the band can never
loosen, and the ratchet has nothing to reject. In `vol_mode="entry"`
the ratcheted stop and the plain trailing stop produce **identical
signals**. The first draft of the test asserted they differed; it was
wrong.

The ratchet only binds when the band is recomputed from the CURRENT
volatility (`vol_mode="current"`), because a volatility spike then
*widens* the band and pushes the stop **away** from the price —
loosening it exactly when the market is most dangerous. The ratchet is
what prevents that.

This is not a small correction. It changes what the claim means:
RET-92 and RET-90 are not independent controls; they are one
mechanism with two regimes, and only one of the regimes has any
effect.

### 7.2 A stop-based inverted control is not a bitwise mirror

The proposal implied the inverted twin is the exact opposite. It is
not, and it cannot be: a long is stopped out when the price *falls*
and a short when it *rises*, so the two exit on different bars and
re-enter on different schedules.

The control is the **polarity-flipped position with the stop on the
correct side**. It still trades, and it can still fail — which is
what a control has to do — but asserting exact negation is asserting
something false. The test now asserts the invariant that actually
holds: wherever both hold a position, their signs are opposite, and
their FIRST entry is the same bar (the entry trigger is not
inverted).

### 7.3 A volatility-normalised band needs a series with volatility

A constant-return series has a realised volatility of exactly zero, so
a band measured in units of volatility is **undefined** and the entry
is correctly refused. The first test fixture had constant returns and
was therefore testing the refusal path instead of the stop.

The fixture now has realistic daily noise. This is worth stating
plainly because it is a general rule for this project: **a synthetic
fixture that is too clean can test the wrong branch.**

### 7.4 The Coin Metrics status vocabulary is not what it looks like

The proposal said to carry the per-observation availability status
through to provenance. Implementing that surfaced two things:

1. The status values are `flash` / `available` / unusable — **not**
   `AVAILABLE`. The first implementation filtered on a value the API
   never sends, and silently dropped **every** exchange-flow
   observation: 2,133 rows fetched, 0 usable.
2. `flash` is the **best** status, not a bad one. It means the value
   was published in real time and **never revised** — exactly what a
   point-in-time backtest wants. A series of `flash` observations has
   no revision risk at all.

A filter that silently drops 100% of the data while reporting
"2,133 rows fetched" is the exact failure mode this package's
provenance layer exists to prevent, and it survived a live probe
because the probe checked the row count rather than the value count.

### 7.5 The signal registry under-reported itself

`register_extensions` returned **nine** signal names while
**fourteen** were actually registered — and four of the missing ones
were the paper-derived signals. A registry that reports less than it
holds misleads whoever reads it. Now returns all fifteen.

### 7.6 The trade-count gate is structurally hostile to low-turnover rules

This is the most consequential finding, and it changes how Phase A's
FRAGILE verdict should be read.

A 12-month time-series momentum on five ETFs generated **6 trades in
15 years**. The gate requires **≥ 30**. The trade counts across the
whole run:

| Rule class | Trade counts produced | Gate threshold |
|---|---|---|
| Trend (252 / 20 / 60-day momentum) | 6, 8, 10, 12, 13, 15 | 30 |
| Pairs mean-reversion | 190, 321, 491, 502, 647, 880 | 30 |

**The gate is calibrated for the second class and structurally rejects
the first.** It will refuse a 12-month momentum on daily bars
essentially every time, on a criterion that has nothing to do with
whether the signal works.

This is **not** a reason to lower the gate. A gate that refuses a
6-trade result is doing its job — 6 trades cannot be distinguished
from luck, and FRAGILE is the correct verdict. But the verdict must
be read for what it is: *"6 trades is too few to distinguish from
luck"*, not *"the paper's rule fails"*.

**The fix is more names, not more windows.** Independence comes from
breadth: the same 12-month signal on a universe with many more
independent names produces more independent trades, and the gate stays
unchanged. A shorter window would also raise the count, but it would
be testing a different rule from the one the paper states.

Note also that the equity row generated 6 trades but **30
out-of-sample** trades — the in-sample window held most of the
positions and the out-of-sample window re-traded them. So the 30 OOS
trades are not 30 independent bets either. They are the same few
positions, re-entered.

### 7.7 The replication stage is untested on every row in the matrix

The stage ledger says it on all 120 rows (the original 96 and Phase
A's 24):

> `replication: SKIPPED — the gauntlet only runs cross-market
> replication when alternative universes are supplied, and the matrix
> runner supplies none, so NO spec in this matrix was tested for
> whether it transfers to a different market.`

Testing on six markets is **breadth, not replication** — it is the
same universe each time. Whether a surviving concept transfers to a
*different* universe is untested everywhere, and it is the one stage
that decides whether a concept is an edge or a market curiosity.

---

## 8. THE DATA-SOURCE PROBE LOG

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
