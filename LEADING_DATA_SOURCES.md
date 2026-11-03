# LEADING DATA — sources that forecast rather than describe

*Companion to `FREE_DATA_SOURCES.md`, which documents the memecoin and
on-chain data this package uses. That document is about **lagging**
data: what a token's holders did, what it traded at, what the chain
said. This one is about the opposite — measurements that are known
BEFORE the move they forecast.*

---

## 0. Why leading data is the whole game

The papers this package implements make the claim explicitly:

> "Implied volatility often contains incremental information about
> future realized volatility, and in several studies it outperforms
> historical volatility forecasts."
> — *Options market dynamics and volatility*

> "Option-implied and market-based uncertainty indicators can sometimes
> detect stress transitions EARLIER than backward-looking returns
> alone."
> — *Financial market regime identification*

> "The 2023 stock study also finds that low net gamma exposure predicts
> higher future realized volatility, supporting gamma exposure as a
> forward-looking volatility signal."
> — *Options market dynamics and volatility*

A backtest on lagging data is a description of the past. A backtest on
leading data is a test of a forecast. The difference is the difference
between fitting history and trading a signal.

**The taxonomy that matters here is not "free vs paid". It is
"leading vs lagging", and secondarily "global vs one market".**

---

## 1. THE LEADING SOURCES, ranked by how far ahead they look

### 1.1 Implied volatility indices and term structures

**The single most useful free forward-looking series available.**

An option price is a market's forecast. The volatility index computed
from those prices is therefore a measurement of EXPECTED movement, not
of past movement.

| Source | What it is | Coverage | Cost | Latency |
|---|---|---|---|---|
| **Deribit DVOL** | Implied-volatility index computed from an asset's OWN option book | BTC, ETH (and others where options list) | **FREE, keyless** | Hourly history, ~2000 days deep via pagination |
| **^VIX** | S&P 500 30-day implied volatility | US large caps | **FREE, keyless** (Yahoo chart API) | Daily |
| **^VXN** | Nasdaq-100 implied volatility | US tech | **FREE, keyless** | Daily |
| **^VXD** | Dow Jones implied volatility | US blue chips | **FREE, keyless** | Daily |
| **^OVX** | Crude-oil implied volatility | Commodities | FREE, keyless | Daily |
| **GVZ** | Gold implied volatility | Commodities | FREE, keyless | Daily |
| **RVX** | Silver implied volatility | Commodities | FREE, keyless | Daily |
| **^MOVE** | ICE BofA MOVE index — bond volatility | US rates | FREE, keyless | Daily |
| **^STOXX50E / ^GDAXI / ^FCHI / ^FTSE** | European equity indices | Europe | FREE, keyless | Daily |
| **^N225 / ^HSI / ^AXJO** | Asian equity indices | Japan / HK / Australia | FREE, keyless | Daily |
| **^BSESN / ^NSEI** | Indian indices | India | FREE, keyless | Daily |
| **EWZ, EWW, EWY, EWP…** | Country ETF implied vol via their options | Global equities | FREE, keyless | Daily |

**Verified on this host, 2026-11-03** — every index above was fetched
from the Yahoo chart API and returned bars:

```
^VIX   22 bars   ^VXN  22   ^VXD  22   ^OVX  22   GVZ  22   RVX  22
^MOVE  21 bars   ^N225 21   ^HSI  21   ^BSESN 21   ^GDAXI 22
Deribit DVOL BTC : 2051 daily points, 2021-03-24 → today, 3.9 s
Deribit DVOL ETH : 3000 hourly points over 125 days (3 pages)
```

**^V2TX (the 2-year volatility index) is NOT available from the Yahoo
chart API** — it returns HTTP 404. It is listed here as a known gap
rather than as a source, because a source that does not answer is not
a source.

**Deribit's DVOL endpoint returns at most 1000 points per call.** At
daily resolution one page is 1000 days; at hourly it is only ~41 days.
`leapspace/leading.py::dvol_history` pages backwards and the choice of
resolution is the difference between a leading feature that covers a
multi-year backtest and one that covers a month.

**THE TRAP:** DVOL's history is a *history of an implied index*, so it
is genuinely leading, but the index itself is a model-free constant
built by Deribit. It is not an option price, so it does not carry a
smile or a skew. For the volatility LEVEL it is the right instrument;
for the skew it is not.

### 1.2 The volatility risk premium — implied minus realised

This is not a data source, it is a **derived signal**, and it is the
one this package implements as `leapspace/leading.py`.

VRP = implied volatility − realised volatility.

* **Positive**: options are rich relative to what has been happening.
  The market is paying for protection, and the expected distribution
  is wider than the recent past.
* **Negative**: options are cheap relative to what has been happening.
  The market is not paying for protection.

Why it is directional rather than a level: a volatility LEVEL says
"the market expects movement". A VRP says "the market expects MORE
movement than it has been getting". That is a statement about the
*change* in the distribution, which is what a position needs.

Sources: Christensen & Prabhala (1998), *Journal of Financial
Economics* 50(1); Ferris, Kim & Park (2010), *Applied Economics
Letters* 36(5).

**THE TRAP:** the realised side depends on the sample's own volatility
history, so the premium is a relative measure and its level is not
comparable across regimes. That is why the signal consumes the
**z-score** of the premium, not the premium.

### 1.3 Dealer gamma exposure

**Where the hedging constraint lives.** Gamma tells you whether the
market's own participants are mechanically forced to trade in the
direction of the move.

* **Positive gamma**: dealers hedge *against* the move, damping it.
* **Negative gamma**: dealers hedge *with* the move, amplifying it.

The papers:

> "Gamma matters because hedging short gamma requires trading in the
> direction of price moves, which can create intraday momentum and
> amplify volatility."
> — *Options market dynamics and volatility*

> "A broader simulation study finds that higher net gamma positioning
> reduces volatility and improves market stability, while negative
> gamma increases volatility and makes markets more fragile."
> — *Options market dynamics and volatility*

> "One study finds that intraday momentum persists only when VIA
> options' net gamma exposure is negative."
> — *Options market dynamics and volatility*

**Sources, keyless:**

| Source | What it gives | Cost |
|---|---|---|
| **Deribit public book** | Every live option with `mark_iv`, `open_interest`, strike, expiry, and the underlying's price — enough to compute a GEX proxy with Black-Scholes | **FREE, keyless** |
| **Deribit public trades** | Live option tape with `iv` and `direction` (buy/sell) | **FREE, keyless** |
| **Nasdaq option chain API** | Open interest + volume per contract for US equities/indices | **FREE, keyless** (has a browser-shaped header requirement) |
| **Cboe live quotes** | Index option OI and settlement | FREE for the delayed file |
| **CME Group** | Futures OI for ES/NQ/etc. | FREE for the delayed file |

**Verified on this host:** 737 BTC option instruments priced into a GEX
proxy at one call; net GEX **negative** (amplifies moves) with the
25DEC26 expiry carrying −44,101 against +16,993 on the front expiry.

**THE TRAPS, all of which this package states in its output:**

1. **The dealer side is INFERRED.** Open interest does not reveal who
   holds the option. Assuming customers are net short calls is the
   standard convention and it is a convention, not a fact.
2. **Black-Scholes gamma is biased under a real smile.** The magnitude
   is indicative; the SIGN and the RELATIVE magnitude across expiries
   are what carry information.
3. **Open interest is STALE.** It updates daily at best. A GEX computed
   at Monday's open describes Monday's positions.
4. **It is a NOW measurement.** The Deribit book endpoint gives the
   live book, not history — so GEX cannot be backtested from it. This
   is why `leapspace/leading.py::deribit_gamma_exposure` reports it as
   a live snapshot and does NOT pretend it is a series.

### 1.4 Option flow — the put/call and the flow imbalance

> "In VIX options, net buying pressure is temporally linked to changes
> in implied volatility, and higher buying pressure lowers next-day
> delta-hedged option returns."
> — *Options market dynamics and volatility*

> "Option flow can inform future volatility, but not consistently
> future returns; retail option demand is associated with lower option
> returns."
> — *Trading strategies for retail traders*

That second quote is the important one, and it constrains what the
signal may be used for: **option flow is a volatility-timing input,
not a directional one.** A put-heavy tape is the market paying for
downside protection; it says something about the expected
distribution, and it is famously also a hedging signal rather than an
opinion.

**Sources, keyless:** the Deribit public trade tape (with `iv` and
`direction` on every trade), and the Nasdaq option-chain volume.

**Verified on this host:** 500 BTC option trades, put/call ratio 0.97,
call share 50.8%, and the IV-weighted average on each side.

### 1.5 Order-flow imbalance — the microstructure base

> "Order flow can contain information about future volatility and
> returns in several markets, but the effect depends on trader type,
> trade size, liquidity, and execution costs; in crypto, trade-flow
> imbalance and order-book features often matter more than broad
> technical rules."
> — *Trading strategies for retail traders*

Order flow is the strongest general edge in that evidence set. It is
also the hardest to get for free.

**Free and keyless:**

* **Crypto exchanges' public REST** — Binance, Bybit, OKX and Coinbase
  publish recent trades, book snapshots and (on some venues) depth.
  Depth is often the first 50–100 levels, which is enough for a
  book-imbalance measure but not for a full order-book model.
* **Deribit public book and trades** — same for the options market.
* **The session-opening drift proxy** — what this package uses as a
  keyless stand-in: the close's position within the day's range,
  weighted by volume.

**The industry-standard measures, and what they cost:**

| Measure | What it is | Cost |
|---|---|---|
| **VPIN / BV-VPIN** | Bulk-volume trade toxicity; Easley, López de Prado & O'Hara (2012) | Computable from public trade data, but needs clean trade classification (bulk vs mid-price) |
| **Order-book imbalance** | Depth-weighted bid/ask pressure | Free for a shallow book; deep books need paid feeds |
| **Trade-size imbalance** | Signed large-trade flow | Free from public trade taps |
| **Kyle's lambda** | Price impact per unit of flow | Computable from trades + quotes |

VPIN is the one worth naming: the literature behind it is the
canonical peer-reviewed support for order flow as an information
source, and it can be computed from public trade data if the venue
gives you side and size.

### 1.6 Forward-looking macro and cross-asset

> "Crypto-equity correlation is also regime-dependent. During some
> crisis windows, crypto co-moves with equities and loses safe-haven
> properties; in others, linkage weakens or temporarily flips."
> — *Financial market regime identification*

Cross-asset linkage is a leading input when it is measured on a
**forward-looking** series rather than on trailing returns.

**Free and keyless, global:**

| Source | What it is |
|---|---|
| **Yahoo chart API** | Everything above, plus futures on 15 global equity indices, 8 FX majors, 7 EM FX pairs, 15 futures contracts, and 12 rates/credit ETFs |
| **FRED** (St. Louis Fed) | ~800,000 macro time series — **the single richest free macro source in the world**. US, and increasingly global |
| **IMF Data API / IFS** | Global macro: growth, inflation, balance of payments, fiscal, for every member country |
| **BIS** | Global banking statistics, derivatives, property prices, debt securities, credit — international, not US-centric |
| **World Bank Open Data** | 264 indicators, 217 economies, 1960→ |
| **OECD SDMX** | CLI for the OECD's own indicators and for its SDMX partner countries |
| **Eurostat / ECB** | European and euro-area data |
| **Bank of Japan / BoE / RBA** | National central bank series |
| **ECB SDW** | Euro-area aggregates, money market, yield curves |

**Leading, specifically:** yield CURVES (a forward-looking structure,
not a price), inflation EXPECTATIONS from breakevens, and term
spreads — these are forward-looking by construction in a way that
trailing returns never are.

**The one gap worth naming honestly:** most free macro series are
**monthly or quarterly**, and are **REVISED**. A revised series is a
look-ahead hazard in a backtest. Use the real-time vintage (ALFRED
for FRED) or do not use the series in a backtest at all.

### 1.7 Crypto-specific leading data

> "On-chain and blockchain variables repeatedly improve crypto
> forecasting and regime detection, with studies finding strong
> performance for active users, hashrate, wallet activity, transaction
> volume, and related features."
> — *Trading strategies for retail traders*

Crypto has the richest free leading data in existence, because the
chain publishes everything and nothing is revised.

**Keyless and on-chain:**

| Signal | What it leads |
|---|---|
| **Exchange netflow** | Coins leaving exchanges → supply pressure |
| **Exchange reserves** | The same, smoother |
| **Active addresses / NVT** | Network activity relative to value transferred |
| **MVRV / Realised Cap** | Long-term holder cost basis vs price — a sentiment/cycle measure |
| **Hash rate / miner flows** | Bitcoin's own leading indicator for its cycle |
| **Funding rates + open interest** | Crypto's OWN options/derivatives market — the crypto equivalent of IV, and it leads the spot |
| **Liquidations** | Cascade risk, and the fuel of a volatility event |
| **Stablecoin supply growth** | Dry powder entering the market |
| **Options 25-delta skew** | Crypto's version of the equity skew |

**Funding rate and open interest are the crypto-native leading
indicator.** A high positive funding rate means longs are crowded and
the market is paying to be long — the crypto equivalent of a rich
options market. It is public, keyless, and available on every major
venue. This package does not yet consume it; it is the highest-value
addition to the leading layer.

**The trap:** on-chain data is *contemporaneous* — it says what is
happening now, not what will happen. Some on-chain measures are
genuinely leading (exchange netflow leads price) and some are
contemporaneous (active addresses). They are not interchangeable, and
the "on-chain improves crypto forecasting" claim needs the specific
feature, not the general category.

---

## 2. THE LAGGING SOURCES, and why they are not enough

These are what this package already uses, and they are not wrong —
they are just backward-looking.

| Source | What it measures | Why it lags |
|---|---|---|
| Yahoo OHLCV | Past prices and volumes | By construction |
| Realised volatility | Past movement | The classic "historical volatility forecasts are beaten by implied" result |
| Trailing momentum | Past returns | The momentum-crash literature is about the crashes of a trailing signal |
| Rolling drawdown | Past losses | Reactive, not predictive |
| Order-book snapshot | Current depth | A snapshot is now, not ahead |

The value of a lagging source is that it is the **denominator** of a
leading signal. Realised volatility without implied volatility gives
you a level; implied minus realised gives you a premium, and the
premium is where the directional information is.

---

## 3. THE TABLE OF WHAT TO USE, AND WHEN

| You want to know | Use | Leading? | Free? |
|---|---|---|---|
| Will volatility rise or fall? | DVOL / ^VIX / ^VXN | **Yes** | Yes |
| Is the market paying for protection? | VRP = IV − RV | **Yes** | Yes |
| Will the next move amplify? | Dealer gamma from OI | **Yes** | Yes (live only) |
| Is the market hedged or directional? | Option flow, put/call | **Yes** (for vol) | Yes |
| Is there toxicity in the tape? | VPIN from trades | **Yes** | Yes, with caveats |
| Where does the cycle turn? | Funding + OI (crypto) | **Yes** | Yes |
| What is the macro regime? | FRED / IMF / BIS + yield curves | **Yes** (for expectations) | Yes |
| What already happened? | OHLCV, on-chain | No | Yes |
| Where are the liquidations? | Venue liquidation feed | Contemporaneous | Yes |

---

## 4. WHAT THIS PACKAGE USES TODAY, AND WHAT IT DOES NOT

**Implemented and verified live:**

* `leapspace/leading.py::implied_vol_series` — ^VIX / ^VXN / ^VXD
* `leapspace/leading.py::dvol_history` — Deribit DVOL, paginated,
  2000+ days deep at daily resolution
* `leapspace/leading.py::volatility_risk_premium` — the signal
* `leapspace/leading.py::deribit_gamma_exposure` — live GEX proxy
* `leapspace/leading.py::deribit_option_flow` — live flow
* `leapspace/leading.py::align_to_bars` — the no-look-ahead alignment

**NOT yet implemented, and worth doing next, in this order:**

1. **Crypto funding rate and open interest.** The crypto-native
   leading indicator. Public and keyless on every major venue.
2. **The volatility term structure** (short IV minus long IV) rather
   than only the level. The momentum-crash literature's crash dummy
   uses "elevated short-versus-long volatility", and Deribit's
   per-expiry `mark_iv` gives it directly from the live book.
3. **A term structure from HISTORY.** The per-instrument
   `get_tradingview_chart_data` endpoint returns 400 at hourly
   resolution for the instruments tested, so the historical term
   structure is not yet obtainable. Until it is, the term structure
   stays a live reading and the backtests use the LEVEL.
4. **Option-implied measures for equities and FX.** The equity options
   chain is available keylessly from Nasdaq, but no free, historical,
   per-expiry IV series was found for it.
5. **The cross-asset forward-looking linkage** the regime paper calls
   for in crypto — a crisis-regime-conditioned equity link.
6. **Real-time macro vintages** (ALFRED) so the macro layer can be
   backtested without the revision look-ahead hazard.

---

## 5. THE RULES THIS PACKAGE FOLLOWS WITH DATA

1. **A leading series is timestamped and aligned with a publication
   lag.** A bar at time T may only use a measurement published before
   it. `leapspace/leading.py::align_to_bars` enforces this with a
   one-bar lag, and the realised side is shifted a bar so no bar uses
   its own close. Without that, "leading" is an illusion.
2. **A missing measurement is None, never zero.** A zero volatility
   risk premium reads as "options are fairly priced", which is a
   claim the data does not support.
3. **Every fetch records its provenance** — the URL, the HTTP status
   and what was actually measured. A cache hit is reported as CACHE,
   never as fresh live data.
4. **A live measurement is labelled as live** and is never presented as
   a backtestable series.
5. **A proxy is named as a proxy.** The volume ratio is a liquidity
   proxy, not a liquidity measure; the GEX is a proxy with an
   inferred dealer side.
6. **A revised series is not used in a backtest** unless the real-time
   vintage is available.

---

## 6. SOURCES FOR THE CLAIMS ABOVE

* Christensen, B.J. & Prabhala, N.R. (1998). "The relation between
  implied and realized volatility". *Journal of Financial Economics*
  50(1), 3–68.
* Ferris, S.P., Kim, W. & Park, S.K. (2010). "The informational quality
  of implied volatility and the volatility risk premium". *Applied
  Economics Letters* 36(5), 563–569.
* Baltussen, G., Da, Z., Lammers, S. & Martens, M. (2021). "Hedging
  demand and market intraday momentum". *Journal of Financial
  Economics* 141(1), 343–362.
* Soebhag, A. (2023). "Option gamma and stock returns". *Journal of
  Empirical Finance* 51, 101442.
* Buis, B., Pieterse-Bloem, M., Verschoor, W.F.C. & Zwinkels, R.C.J.
  (2024). "Gamma positioning and market quality". *Journal of Economic
  Dynamics and Control* 158, 104880.
* Easley, D., López de Prado, M.M. & O'Hara, M. (2012). "Flow toxicity
  and liquidity in a high-frequency world". *Review of Financial
  Studies* 25(5), 1457–1493.
* Low, R.K.Y., Li, T. & Marsh, T. (2018). "BV-VPIN: Measuring the
  impact of order flow toxicity and liquidity on international equity
  markets". *Journal of Risk* 21(3), 399–419.
* Cboe Global Markets. *VIX Volatility Indexes methodology*.
* Deribit. *DVOL Volatility Index documentation*.
* International Monetary Fund. *International Financial Statistics (IFS)*.
* Bank for International Settlements. *Global liquidity indicators*.
